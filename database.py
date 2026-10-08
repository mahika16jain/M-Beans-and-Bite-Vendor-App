"""SQLite persistence for the M Beans & Bites procurement app."""
import datetime as dt
import os
import sqlite3
import tempfile
from contextlib import contextmanager

from scoring import PRODUCT_COFFEE, PRODUCT_CUPS


def _resolve_path():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "procurement.db")
    try:
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE IF NOT EXISTS _probe (x INTEGER)")
        conn.commit()
        conn.close()
        return path
    except Exception:
        return os.path.join(tempfile.gettempdir(), "procurement.db")


DB_PATH = _resolve_path()


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def q(sql, params=()):
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def q1(sql, params=()):
    rows = q(sql, params)
    return rows[0] if rows else None


def now_str():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return dt.date.today().strftime("%Y-%m-%d")


# ---------------------------------------------------------------- schema
SCHEMA = """
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY, legal_name TEXT, trade_name TEXT, gstin TEXT, pan TEXT,
    address TEXT, contact_person TEXT, email TEXT, phone TEXT, category TEXT,
    bank_name TEXT, account_holder TEXT, account_number TEXT, ifsc TEXT,
    products_supplied TEXT, status TEXT, completeness_percentage REAL,
    quality_rating INTEGER, quality_evidence TEXT,
    duplicate_of TEXT, duplicate_note TEXT, summary TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY, name TEXT UNIQUE, qty_unit TEXT, price_unit TEXT);
CREATE TABLE IF NOT EXISTS quotations (
    quotation_id INTEGER PRIMARY KEY AUTOINCREMENT, vendor_id TEXT, product_id INTEGER,
    unit_price REAL, quoted_quantity REAL, total_price REAL, delivery_days INTEGER,
    validity TEXT, taxes TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS documents (
    document_id INTEGER PRIMARY KEY AUTOINCREMENT, vendor_id TEXT, document_name TEXT,
    document_type TEXT, upload_date TEXT);
CREATE TABLE IF NOT EXISTS purchase_requests (
    request_id TEXT PRIMARY KEY, vendor_id TEXT, product_id INTEGER, quantity REAL,
    quoted_unit_price REAL, order_value REAL, requested_delivery_date TEXT,
    special_instructions TEXT, email_subject TEXT, email_body TEXT,
    request_date TEXT, sent_date TEXT, received_date TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, entity_type TEXT,
    entity_id TEXT, action TEXT, details TEXT);
"""


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            conn.execute("INSERT INTO products (product_id, name, qty_unit, price_unit) VALUES (1, ?, 'kg', 'kg')",
                         (PRODUCT_COFFEE,))
            conn.execute("INSERT INTO products (product_id, name, qty_unit, price_unit) VALUES (2, ?, 'cups', 'cup')",
                         (PRODUCT_CUPS,))


def reset_all():
    """Delete every vendor, quotation, document, purchase request and audit entry."""
    with connect() as conn:
        for t in ("vendors", "quotations", "documents", "purchase_requests", "audit_log"):
            conn.execute(f"DELETE FROM {t}")


# ------------------------------------------------------------------ audit
def add_audit(conn, entity_type, entity_id, action, details="", ts=None):
    conn.execute(
        "INSERT INTO audit_log (timestamp, entity_type, entity_id, action, details) VALUES (?,?,?,?,?)",
        (ts or now_str(), entity_type, entity_id, action, details))


# ---------------------------------------------------------------- queries
def get_products():
    return q("SELECT * FROM products ORDER BY product_id")


def get_product_by_name(name):
    return q1("SELECT * FROM products WHERE name = ?", (name,))


def get_vendors():
    return q("SELECT * FROM vendors ORDER BY vendor_id")


def get_vendor(vendor_id):
    return q1("SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,))


def next_vendor_id():
    r = q1("SELECT MAX(CAST(SUBSTR(vendor_id, 2) AS INTEGER)) AS m FROM vendors")
    return f"V{(r['m'] or 0) + 1:03d}"


def next_request_id():
    r = q1("SELECT MAX(CAST(SUBSTR(request_id, 3) AS INTEGER)) AS m FROM purchase_requests")
    return f"PR{(r['m'] or 0) + 1:03d}"


def dashboard_stats():
    s = {}
    s["total_vendors"] = q1("SELECT COUNT(*) AS n FROM vendors")["n"]
    s["orders_placed"] = q1("SELECT COUNT(*) AS n FROM purchase_requests "
                            "WHERE status IN ('Request Sent','Order Received')")["n"]
    s["orders_received"] = q1("SELECT COUNT(*) AS n FROM purchase_requests WHERE status='Order Received'")["n"]
    s["pending_review"] = q1("SELECT COUNT(*) AS n FROM vendors WHERE status='Pending Review'")["n"]
    s["missing_info"] = q1("SELECT COUNT(*) AS n FROM vendors WHERE completeness_percentage < 100")["n"]
    s["duplicates"] = q1("SELECT COUNT(*) AS n FROM vendors WHERE duplicate_of IS NOT NULL AND duplicate_of <> ''")["n"]
    s["active"] = q1("SELECT COUNT(*) AS n FROM vendors WHERE status='Active'")["n"]
    s["incomplete"] = q1("SELECT COUNT(*) AS n FROM vendors WHERE status='Incomplete'")["n"]
    s["request_sent"] = q1("SELECT COUNT(*) AS n FROM purchase_requests WHERE status='Request Sent'")["n"]
    return s


def get_quotes_for_product(product_id):
    """Latest quotation per vendor for one product, joined with vendor info."""
    return q("""
        SELECT v.vendor_id, v.legal_name, v.status, v.quality_rating, v.quality_evidence,
               q.unit_price, q.delivery_days, q.quoted_quantity, q.validity, q.taxes
        FROM quotations q JOIN vendors v ON v.vendor_id = q.vendor_id
        WHERE q.product_id = ?
          AND q.quotation_id = (SELECT MAX(q2.quotation_id) FROM quotations q2
                                WHERE q2.vendor_id = q.vendor_id AND q2.product_id = q.product_id)
        ORDER BY v.vendor_id""", (product_id,))


def get_vendor_quotes(vendor_id):
    return q("""
        SELECT p.product_id, p.name AS product, p.price_unit, p.qty_unit, q.unit_price, q.quoted_quantity,
               q.total_price, q.delivery_days, q.validity, q.taxes
        FROM quotations q JOIN products p ON p.product_id = q.product_id
        WHERE q.vendor_id = ?
          AND q.quotation_id = (SELECT MAX(q2.quotation_id) FROM quotations q2
                                WHERE q2.vendor_id = q.vendor_id AND q2.product_id = q.product_id)
        ORDER BY p.product_id""", (vendor_id,))


def get_all_quotes():
    return q("""
        SELECT v.legal_name AS vendor, p.name AS product, p.price_unit, q.unit_price, q.quoted_quantity,
               q.delivery_days, q.validity, v.status
        FROM quotations q JOIN vendors v ON v.vendor_id = q.vendor_id
        JOIN products p ON p.product_id = q.product_id
        WHERE q.quotation_id = (SELECT MAX(q2.quotation_id) FROM quotations q2
                                WHERE q2.vendor_id = q.vendor_id AND q2.product_id = q.product_id)
        ORDER BY p.product_id, q.unit_price""")


def get_documents(vendor_id):
    return q("SELECT * FROM documents WHERE vendor_id = ? ORDER BY document_id", (vendor_id,))


# ----------------------------------------------------------------- writes
def save_vendor(vendor, quotes, documents, audit_note=""):
    """Insert a vendor with its quotations and documents (one transaction). Returns the vendor_id."""
    with connect() as conn:
        r = conn.execute("SELECT MAX(CAST(SUBSTR(vendor_id, 2) AS INTEGER)) FROM vendors").fetchone()
        vendor_id = f"V{(r[0] or 0) + 1:03d}"
        conn.execute(
            "INSERT INTO vendors (vendor_id, legal_name, trade_name, gstin, pan, address, contact_person, email, "
            "phone, category, bank_name, account_holder, account_number, ifsc, products_supplied, status, "
            "completeness_percentage, quality_rating, quality_evidence, duplicate_of, duplicate_note, summary, "
            "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (vendor_id, vendor["legal_name"], vendor.get("trade_name"), vendor.get("gstin"), vendor.get("pan"),
             vendor.get("address"), vendor.get("contact_person"), vendor.get("email"), vendor.get("phone"),
             vendor.get("category"), vendor.get("bank_name"), vendor.get("account_holder"),
             vendor.get("account_number"), vendor.get("ifsc"), "; ".join(vendor.get("products_supplied", [])),
             vendor["status"], vendor["completeness_percentage"], vendor.get("quality_rating"),
             vendor.get("quality_evidence"), vendor.get("duplicate_of"), vendor.get("duplicate_note"),
             vendor.get("summary"), now_str()))
        for qt in quotes:
            conn.execute(
                "INSERT INTO quotations (vendor_id, product_id, unit_price, quoted_quantity, total_price, "
                "delivery_days, validity, taxes, notes) VALUES (?,?,?,?,?,?,?,?,?)",
                (vendor_id, qt["product_id"], qt["unit_price"], qt.get("quoted_quantity"), qt.get("total_price"),
                 qt.get("delivery_days"), qt.get("validity"), qt.get("taxes"), qt.get("notes")))
        for doc in documents:
            conn.execute("INSERT INTO documents (vendor_id, document_name, document_type, upload_date) "
                         "VALUES (?,?,?,?)", (vendor_id, doc["name"], doc.get("type", "Uploaded"), now_str()))
        add_audit(conn, "vendor", vendor_id, "Vendor created",
                  f"Status: {vendor['status']}. {audit_note}".strip())
    return vendor_id


def update_vendor_quality(vendor_id, rating, evidence):
    with connect() as conn:
        conn.execute("UPDATE vendors SET quality_rating=?, quality_evidence=? WHERE vendor_id=?",
                     (rating, evidence, vendor_id))
        add_audit(conn, "vendor", vendor_id, "Quality evidence updated",
                  f"Rating: {rating if rating else 'none'}. {evidence or ''}")


def update_vendor_status(vendor_id, status, note=""):
    with connect() as conn:
        conn.execute("UPDATE vendors SET status=? WHERE vendor_id=?", (status, vendor_id))
        add_audit(conn, "vendor", vendor_id, f"Status changed to {status}", note)


def create_purchase_request(vendor_id, product_id, quantity, unit_price, order_value, delivery_date,
                            instructions, subject, body, email_generated_at):
    with connect() as conn:
        r = conn.execute("SELECT MAX(CAST(SUBSTR(request_id, 3) AS INTEGER)) FROM purchase_requests").fetchone()
        rid = f"PR{(r[0] or 0) + 1:03d}"
        ts = now_str()
        conn.execute(
            "INSERT INTO purchase_requests (request_id, vendor_id, product_id, quantity, quoted_unit_price, "
            "order_value, requested_delivery_date, special_instructions, email_subject, email_body, "
            "request_date, sent_date, received_date, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, vendor_id, product_id, quantity, unit_price, order_value, delivery_date, instructions,
             subject, body, ts[:10], ts[:10], None, "Request Sent"))
        add_audit(conn, "purchase_request", rid, "Purchase request created", ts=ts)
        add_audit(conn, "purchase_request", rid, "Email generated", ts=email_generated_at or ts)
        add_audit(conn, "purchase_request", rid, "Request marked as sent", ts=ts)
    return rid



VENDOR_FIELDS = ["legal_name", "trade_name", "gstin", "pan", "address", "contact_person", "email", "phone",
                 "category", "bank_name", "account_holder", "account_number", "ifsc"]


def update_vendor_from_documents(vendor_id, vendor, quotes, documents, status, completeness):
    """Merge new information into an EXISTING vendor (user chose 'update existing')."""
    old = get_vendor(vendor_id)
    merged = {f: (vendor.get(f) or old.get(f)) for f in VENDOR_FIELDS}
    products = set(filter(None, (old.get("products_supplied") or "").split("; "))) | set(vendor.get("products_supplied", []))
    with connect() as conn:
        conn.execute(
            "UPDATE vendors SET " + ", ".join(f"{f}=?" for f in VENDOR_FIELDS) +
            ", products_supplied=?, status=?, completeness_percentage=?, quality_rating=COALESCE(?, quality_rating), "
            "quality_evidence=COALESCE(?, quality_evidence), summary=COALESCE(?, summary) WHERE vendor_id=?",
            [merged[f] for f in VENDOR_FIELDS] + ["; ".join(sorted(products)), status, completeness,
             vendor.get("quality_rating"), vendor.get("quality_evidence"), vendor.get("summary"), vendor_id])
        for qt in quotes:
            conn.execute(
                "INSERT INTO quotations (vendor_id, product_id, unit_price, quoted_quantity, total_price, "
                "delivery_days, validity, taxes, notes) VALUES (?,?,?,?,?,?,?,?,?)",
                (vendor_id, qt["product_id"], qt["unit_price"], qt.get("quoted_quantity"), qt.get("total_price"),
                 qt.get("delivery_days"), qt.get("validity"), qt.get("taxes"), qt.get("notes")))
        for doc in documents:
            conn.execute("INSERT INTO documents (vendor_id, document_name, document_type, upload_date) "
                         "VALUES (?,?,?,?)", (vendor_id, doc["name"], doc.get("type", "Uploaded"), now_str()))
        add_audit(conn, "vendor", vendor_id, "Vendor updated from new documents",
                  f"{len(quotes)} quotation(s), {len(documents)} document(s) added.")
    return merged


def update_vendor_details(vendor_id, fields, status, completeness):
    with connect() as conn:
        conn.execute("UPDATE vendors SET " + ", ".join(f"{f}=?" for f in fields) +
                     ", status=?, completeness_percentage=? WHERE vendor_id=?",
                     list(fields.values()) + [status, completeness, vendor_id])
        add_audit(conn, "vendor", vendor_id, "Vendor details edited", ", ".join(fields))


def delete_vendor(vendor_id):
    with connect() as conn:
        for t in ("quotations", "documents"):
            conn.execute(f"DELETE FROM {t} WHERE vendor_id=?", (vendor_id,))
        conn.execute("DELETE FROM vendors WHERE vendor_id=?", (vendor_id,))
        add_audit(conn, "vendor", vendor_id, "Vendor deleted by user")


def mark_received(request_id):
    ts = now_str()
    with connect() as conn:
        cur = conn.execute("UPDATE purchase_requests SET status='Order Received', received_date=? "
                           "WHERE request_id=? AND status='Request Sent'", (ts, request_id))
        if cur.rowcount:
            add_audit(conn, "purchase_request", request_id, "Order marked as received", ts=ts)
    return bool(cur.rowcount)


def get_purchase_requests():
    return q("""
        SELECT r.*, v.legal_name AS vendor, p.name AS product, p.qty_unit, p.price_unit
        FROM purchase_requests r JOIN vendors v ON v.vendor_id = r.vendor_id
        JOIN products p ON p.product_id = r.product_id
        ORDER BY CAST(SUBSTR(r.request_id, 3) AS INTEGER) DESC""")


def get_audit(entity_type, entity_id):
    return q("SELECT * FROM audit_log WHERE entity_type=? AND entity_id=? ORDER BY log_id",
             (entity_type, entity_id))
