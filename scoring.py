"""Deterministic business logic (NO AI here):
required-field validation, preference weights, vendor scoring/ranking,
exact duplicate matching and a simple fallback fuzzy matcher."""
import re
from difflib import SequenceMatcher

PRODUCT_COFFEE = "Arabica Coffee Beans — 1 kg"
PRODUCT_CUPS = "Food-Grade Paper Cups — 250 ml"
PRODUCT_NAMES = [PRODUCT_COFFEE, PRODUCT_CUPS]

NOT_AVAILABLE = "Not available in submitted documents."
OUT_OF_SCOPE = "Product outside current procurement scope."

LEVELS = {"Very Low": 1, "Low": 2, "Medium": 3, "High": 4, "Very High": 5}
LEVEL_OPTIONS = list(LEVELS.keys())
DEFAULT_PREFS = ("High", "Medium", "High")  # cost, delivery, quality

QUALITY_LABELS = {5: "Excellent", 4: "Good", 3: "Average", 2: "Below Average", 1: "Poor"}
INSUFFICIENT_QUALITY = "Insufficient evidence to assess quality."

MANDATORY_FIELDS = {
    "legal_name": "Legal Vendor Name",
    "gstin": "GSTIN",
    "pan": "PAN",
    "address": "Registered Address",
    "contact_person": "Contact Person",
    "email": "Email",
    "bank_name": "Bank Name",
    "account_number": "Account Number",
    "ifsc": "IFSC",
}

GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
PAN_RE = re.compile(r"^[A-Z]{5}\d{4}[A-Z]$")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ---------------------------------------------------------------- helpers
def clean(value):
    """Return a trimmed string, or '' if the value is empty / a 'not found' marker."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in ("", "none", "null", "n/a", "na", "nan", "not available",
                     "not available in submitted documents",
                     "not available in submitted documents."):
        return ""
    return s


def fmt_money(x):
    if x is None:
        return "—"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if abs(x - round(x)) < 1e-9:
        return f"₹{int(round(x)):,}"
    return f"₹{x:,.2f}"


def fmt_qty(q, unit):
    if q is None:
        return "—"
    q = float(q)
    num = f"{int(q):,}" if abs(q - round(q)) < 1e-9 else f"{q:,.2f}"
    return f"{num} {unit}"


def match_product(name):
    """Map any product text to one of the two supported products (or None)."""
    n = clean(name).lower()
    if not n:
        return None
    sizes = re.findall(r"(\d+)\s*ml", n)
    if "cup" in n:
        if sizes and any(int(s) != 250 for s in sizes):
            return None
        return PRODUCT_CUPS
    if "arabica" in n or ("coffee" in n and "robusta" not in n and "instant" not in n):
        return PRODUCT_COFFEE
    return None


# ------------------------------------------------------------ validation
def completeness(vendor):
    """Return (percentage, list_of_missing_labels) for the mandatory fields."""
    missing = [label for key, label in MANDATORY_FIELDS.items() if not clean(vendor.get(key))]
    pct = round((len(MANDATORY_FIELDS) - len(missing)) / len(MANDATORY_FIELDS) * 100)
    return pct, missing


def format_warnings(v):
    """Soft format checks. These are warnings only - they never block saving."""
    w = []
    gstin = clean(v.get("gstin")).upper().replace(" ", "")
    pan = clean(v.get("pan")).upper().replace(" ", "")
    ifsc = clean(v.get("ifsc")).upper().replace(" ", "")
    email = clean(v.get("email"))
    acct = clean(v.get("account_number")).replace(" ", "")
    if gstin and not GSTIN_RE.match(gstin):
        w.append("GSTIN format looks unusual (expected 15 characters, e.g. 07AABCF1234L1Z5).")
    if pan and not PAN_RE.match(pan):
        w.append("PAN format looks unusual (expected 10 characters, e.g. AABCF1234L).")
    if ifsc and not IFSC_RE.match(ifsc):
        w.append("IFSC format looks unusual (expected 11 characters, e.g. HDFC0001234).")
    if email and not EMAIL_RE.match(email):
        w.append("Email format looks unusual.")
    if acct and not (acct.isdigit() and 9 <= len(acct) <= 18):
        w.append("Account number should normally be 9–18 digits.")
    if gstin and pan and GSTIN_RE.match(gstin) and PAN_RE.match(pan) and gstin[2:12] != pan:
        w.append("GSTIN does not contain the PAN entered (characters 3–12 of a GSTIN equal the PAN) — please verify both.")
    return w


# ------------------------------------------------------ preference weights
def compute_weights(cost_level, delivery_level, quality_level):
    """Convert 3 preference levels into weights (in %) that ALWAYS total 100."""
    raw = {
        "cost": LEVELS[cost_level],
        "delivery": LEVELS[delivery_level],
        "quality": LEVELS[quality_level],
    }
    total = sum(raw.values())
    w = {k: round(v / total * 100, 1) for k, v in raw.items()}
    diff = round(100 - sum(w.values()), 1)
    if diff:
        biggest = max(w, key=w.get)
        w[biggest] = round(w[biggest] + diff, 1)
    return w


# ---------------------------------------------------------------- ranking
def rank_vendors(candidates, weights):
    """Vendor Suitability Score (out of 100) = weighted cost + delivery + quality.

    cost ratio     = lowest quoted price / vendor price      (best = 1.0)
    delivery ratio = fastest delivery days / vendor days     (best = 1.0)
    quality ratio  = recorded rating (1-5) / 5               (no evidence = 0)
    points         = weight% x ratio
    """
    prices = [c["unit_price"] for c in candidates if c.get("unit_price") and c["unit_price"] > 0]
    days = [c["delivery_days"] for c in candidates if c.get("delivery_days") and c["delivery_days"] > 0]
    best_price = min(prices) if prices else None
    best_days = min(days) if days else None

    rows = []
    for c in candidates:
        price, d, rating = c.get("unit_price"), c.get("delivery_days"), c.get("quality_rating")
        cost_ratio = (best_price / price) if (price and price > 0 and best_price) else 0.0
        delivery_ratio = (best_days / d) if (d and d > 0 and best_days) else 0.0
        quality_ratio = (rating / 5.0) if rating else 0.0
        cp = weights["cost"] * cost_ratio
        dp = weights["delivery"] * delivery_ratio
        qp = weights["quality"] * quality_ratio
        rows.append({
            "vendor_id": c["vendor_id"],
            "vendor_name": c["vendor_name"],
            "unit_price": price,
            "delivery_days": d,
            "quality_rating": rating,
            "quality_label": QUALITY_LABELS.get(rating) if rating else None,
            "cost_ratio": cost_ratio,
            "delivery_ratio": delivery_ratio,
            "quality_ratio": quality_ratio,
            "cost_points": round(cp, 1),
            "delivery_points": round(dp, 1),
            "quality_points": round(qp, 1),
            "total": round(cp + dp + qp, 1),
            "_raw_total": cp + dp + qp,
        })
    rows.sort(key=lambda r: (-r["_raw_total"], r["unit_price"] or 1e12))
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
        r.pop("_raw_total", None)
    return rows


def key_advantage_and_tradeoff(row, rows, weights):
    """Deterministic 'Key Advantage' and 'Main Trade-off' texts."""
    prices = [r["unit_price"] for r in rows if r["unit_price"]]
    days = [r["delivery_days"] for r in rows if r["delivery_days"]]
    ratings = [r["quality_rating"] for r in rows if r["quality_rating"]]
    min_price = min(prices) if prices else None
    min_days = min(days) if days else None
    max_rating = max(ratings) if ratings else None

    adv = []
    if row["unit_price"] and row["unit_price"] == min_price and len(rows) > 1:
        adv.append("lowest price")
    if row["delivery_days"] and row["delivery_days"] == min_days and len(rows) > 1:
        adv.append("fastest delivery")
    if row["quality_rating"] and row["quality_rating"] == max_rating and len(rows) > 1:
        adv.append("highest quality/reliability rating")
    if adv:
        advantage = "Offers the " + ", ".join(adv) + " among the compared vendors."
    else:
        advantage = "Strong balance between price, delivery time, and quality."

    losses = {
        "cost": weights["cost"] * (1 - row["cost_ratio"]),
        "delivery": weights["delivery"] * (1 - row["delivery_ratio"]),
        "quality": weights["quality"] * (1 - row["quality_ratio"]),
    }
    worst = max(losses, key=losses.get)
    if losses[worst] < 0.5:
        tradeoff = "No significant trade-off under your current priorities."
    elif worst == "cost":
        tradeoff = f"Not the lowest-priced vendor ({fmt_money(row['unit_price'])} vs {fmt_money(min_price)})."
    elif worst == "delivery":
        tradeoff = f"Not the fastest delivery ({row['delivery_days']} days vs {min_days} days)."
    else:
        if not row["quality_rating"]:
            tradeoff = INSUFFICIENT_QUALITY
        else:
            tradeoff = "Quality/reliability rating is lower than the best-rated vendor."
    return advantage, tradeoff


def describe_ranking_change(old_rows, new_rows, old_w, new_w):
    """Return (changed: bool, message) comparing two rankings."""
    old_pos = {r["vendor_id"]: r["rank"] for r in old_rows}
    moves = [(old_pos[r["vendor_id"]] - r["rank"], r) for r in new_rows if r["vendor_id"] in old_pos]
    if not moves or all(m == 0 for m, _ in moves):
        return False, "Ranking unchanged — the order stays the same under your new priorities."
    names = {"cost": "cost", "delivery": "delivery time", "quality": "quality / reliability"}
    crit = max(names, key=lambda c: new_w[c] - old_w[c])
    up_move, up_row = max(moves, key=lambda x: x[0])
    down_move, down_row = min(moves, key=lambda x: x[0])
    parts = []
    if up_move > 0:
        txt = f"{up_row['vendor_name']} moved up from #{up_row['rank'] + up_move} to #{up_row['rank']}"
        if new_w[crit] > old_w[crit]:
            txt += (f" because {names[crit]} now carries more weight "
                    f"({old_w[crit]:g}% → {new_w[crit]:g}%)")
        parts.append(txt + ".")
    if down_move < 0:
        parts.append(f"{down_row['vendor_name']} moved down from #{down_row['rank'] - down_move} "
                     f"to #{down_row['rank']}.")
    return True, " ".join(parts)


# ----------------------------------------------------- duplicate detection
def _norm_id(s):
    return re.sub(r"[^A-Z0-9]", "", clean(s).upper())


def exact_duplicates(new, existing):
    """Exact matching on GSTIN, PAN and bank account number (normal programming)."""
    found = {}
    for key, label in (("gstin", "GSTIN"), ("pan", "PAN"), ("account_number", "Bank account number")):
        nv = _norm_id(new.get(key))
        if not nv:
            continue
        for v in existing:
            if _norm_id(v.get(key)) == nv:
                entry = found.setdefault(v["vendor_id"], {
                    "vendor_id": v["vendor_id"], "name": v["legal_name"],
                    "similarity": 100, "reasons": []})
                entry["reasons"].append(f"Matching {label}")
    return list(found.values())


_STOP = {"pvt", "ltd", "private", "limited", "co", "company", "llp", "the", "and", "&"}


def _norm_name(s):
    words = re.findall(r"[a-z0-9]+", clean(s).lower())
    return "".join(w for w in words if w not in _STOP)


def _norm_addr(s):
    return " ".join(re.findall(r"[a-z0-9]+", clean(s).lower()))


def fuzzy_duplicates(new, existing, threshold=70):
    """Fallback (used only if Gemini is unavailable): simple text similarity."""
    out = []
    nn, na = _norm_name(new.get("legal_name")), _norm_addr(new.get("address"))
    for v in existing:
        en, ea = _norm_name(v.get("legal_name")), _norm_addr(v.get("address"))
        name_sim = SequenceMatcher(None, nn, en).ratio() if nn and en else 0
        addr_sim = SequenceMatcher(None, na, ea).ratio() if na and ea else 0
        sim = round((0.6 * name_sim + 0.4 * addr_sim if addr_sim else name_sim) * 100)
        if sim >= threshold:
            reasons = []
            if name_sim >= 0.7:
                reasons.append("Similar vendor name")
            if addr_sim >= 0.6:
                reasons.append("Similar address")
            out.append({"vendor_id": v["vendor_id"], "name": v["legal_name"],
                        "similarity": sim, "reasons": reasons or ["Similar vendor details"]})
    return out


def duplicate_risk(matches):
    if not matches:
        return "Low"
    top = max(m["similarity"] for m in matches)
    if top >= 85:
        return "High"
    if top >= 60:
        return "Medium"
    return "Low"


# ------------------------------------------------- quality from evidence
def suggest_quality_rating(certifications, on_time_pct, defect_pct):
    """Transparent rule-based rating (1-5) from documented evidence only.
    Returns None when the documents contain no quality evidence.
      start at 3
      +1 if 2 or more certifications (e.g. FSSAI, ISO 22000, Rainforest Alliance)
      +1 if on-time delivery >= 95% and defect/return rate <= 1%
      -1 if on-time delivery < 90% or defect/return rate > 2%
    """
    certs = [c for c in (certifications or []) if clean(c)]
    if not certs and on_time_pct is None and defect_pct is None:
        return None
    r = 3
    if len(certs) >= 2:
        r += 1
    if on_time_pct is not None and on_time_pct >= 95 and (defect_pct is None or defect_pct <= 1):
        r += 1
    if (on_time_pct is not None and on_time_pct < 90) or (defect_pct is not None and defect_pct > 2):
        r -= 1
    return max(1, min(5, r))


QUALITY_RULE_TEXT = ("Rule: start at 3 · +1 if 2+ certifications · +1 if on-time ≥95% and defects ≤1% · "
                     "−1 if on-time <90% or defects >2%. No evidence → not rated.")
