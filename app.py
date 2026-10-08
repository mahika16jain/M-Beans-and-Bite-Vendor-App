"""M Beans & Bites — AI Vendor Selection & Procurement Management System.
Run locally:  streamlit run app.py
"""
import datetime as dt
import json
import time
import urllib.parse

import pandas as pd
import streamlit as st

import database as db
import gemini_helper as ai
import scoring as sc

st.set_page_config(page_title="M Beans & Bites · Procurement", page_icon="☕", layout="wide",
                   initial_sidebar_state="expanded")
db.init_db()

DEFAULT_DELIVERY_ADDRESS = "M Beans & Bites Pvt. Ltd., New Delhi"

# =============================================================== DESIGN SYSTEM
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp, button, input, textarea, select { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, [data-testid="stDecoration"] { display: none !important; }
header[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1250px; }

/* ---------- sidebar = app navigation ---------- */
section[data-testid="stSidebar"] { background: #2B1D14; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] div { color: #EADBC8; }
section[data-testid="stSidebar"] input { color: #2B1D14 !important; }
section[data-testid="stSidebar"] .stButton button {
    width: 100%; justify-content: flex-start; text-align: left; border: none; border-radius: 10px;
    background: transparent; color: #EADBC8; padding: 0.55rem 0.9rem; font-weight: 500; box-shadow: none; }
section[data-testid="stSidebar"] .stButton button:hover { background: rgba(255,255,255,0.08); color: #fff; }
section[data-testid="stSidebar"] .stButton button[kind="primary"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] { background: #C8A27A !important; color: #2B1D14 !important; font-weight: 700; }
section[data-testid="stSidebar"] .stButton button p { color: inherit !important; }
.brand { display:flex; align-items:center; gap:10px; padding: 4px 4px 14px 4px; }
.brand-logo { width:42px; height:42px; border-radius:12px; background:#C8A27A; display:flex; align-items:center;
              justify-content:center; font-size:22px; }
.brand-name { font-weight:800; font-size:1.02rem; color:#fff !important; line-height:1.15; }
.brand-sub { font-size:0.74rem; color:#BFA78D !important; }
.side-label { font-size:0.7rem; letter-spacing:0.08em; text-transform:uppercase; color:#9C8570 !important; margin:10px 4px 4px; }
.side-status { font-size:0.8rem; padding:8px 10px; border-radius:10px; background:rgba(255,255,255,0.06); }

/* ---------- main area ---------- */
.topbar { display:flex; justify-content:space-between; align-items:flex-end; margin-bottom: 18px; }
.topbar h1 { font-size: 1.75rem; font-weight: 800; margin: 0; color:#2B1D14; padding:0; }
.topbar p { margin: 2px 0 0 0; color: #7A6555; font-size: 0.95rem; }
.chip { background:#fff; border:1px solid #E6DACD; border-radius:999px; padding:6px 14px; font-size:0.82rem; color:#5C4636; white-space:nowrap; }
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) { background: #FFFFFF; border-radius: 16px; }
div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 16px; }
.stButton button, .stDownloadButton button, .stLinkButton a { border-radius: 10px; font-weight: 600; }
.kpi { background:#fff; border-radius:16px; padding:18px 20px; display:flex; gap:16px; align-items:center;
       box-shadow: 0 1px 2px rgba(43,29,20,0.06), 0 4px 16px rgba(43,29,20,0.05); border:1px solid #EFE6DC; }
.kpi-icon { width:52px; height:52px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:24px; }
.kpi-label { color:#7A6555; font-size:0.85rem; font-weight:500; }
.kpi-value { font-size:2rem; font-weight:800; color:#2B1D14; line-height:1.1; }
.kpi-sub { color:#9C8570; font-size:0.75rem; }
.hero { background: linear-gradient(120deg,#3B2A20 0%,#6F4E37 60%,#8B5E3C 100%); border-radius:18px; padding:22px 26px; color:#fff; margin-bottom:18px; }
.hero h2 { color:#fff; margin:0; font-size:1.45rem; font-weight:800; padding:0; }
.hero p { color:#EADBC8; margin:6px 0 0 0; font-size:0.92rem; }
.badge { display:inline-block; padding:3px 10px; border-radius:999px; font-size:0.74rem; font-weight:600; margin:2px 4px 2px 0; }
.b-green { background:#E3F4E8; color:#1E7B3A; } .b-amber { background:#FFF2D6; color:#9A6400; }
.b-red { background:#FDE4E1; color:#B3261E; } .b-grey { background:#EFEAE4; color:#5C4636; }
.b-brown { background:#F1E4D6; color:#6F4E37; }
.muted { color:#7A6555; font-size:0.85rem; }
.vname { font-weight:700; font-size:1.02rem; color:#2B1D14; }
.big { font-size:1.5rem; font-weight:800; color:#2B1D14; }
.rowline { padding:10px 0; border-bottom:1px solid #F1E8DF; }
.stepper { display:flex; align-items:center; gap:10px; margin: 4px 0 18px 0; }
.step { display:flex; align-items:center; gap:8px; font-weight:600; color:#9C8570; font-size:0.92rem; }
.step .num { width:28px; height:28px; border-radius:50%; background:#EFE6DC; display:flex; align-items:center;
             justify-content:center; font-size:0.85rem; color:#7A6555; }
.step.active { color:#2B1D14; } .step.active .num { background:#8B5E3C; color:#fff; }
.step.done { color:#1E7B3A; } .step.done .num { background:#1E7B3A; color:#fff; }
.line { flex:1; height:2px; background:#E6DACD; max-width:90px; }
.summary-card { background:#FBF7F2; border:1px solid #EFE6DC; border-radius:14px; padding:14px 18px; }
.summary-card b { color:#3B2A20; }
.empty { text-align:center; padding:40px 20px; color:#7A6555; }
.empty .icon { font-size:46px; }

[class*="st-key-card"] { background:#FFFFFF !important; border:1px solid #EFE6DC !important; border-radius:16px !important;
    box-shadow: 0 1px 2px rgba(43,29,20,0.05), 0 4px 16px rgba(43,29,20,0.04); }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.2rem; }
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.stButton),
section[data-testid="stSidebar"] .stButton, section[data-testid="stSidebar"] .stButton button { width: 100% !important; }
section[data-testid="stSidebar"] .stButton button > div { justify-content: flex-start; }
section[data-testid="stSidebar"] button[kind="primary"] *, section[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] * { color: #2B1D14 !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

PAGES = [("Dashboard", "🏠"), ("Add Vendor", "➕"), ("Vendors", "🏢"), ("Compare & Order", "⚖️"),
         ("Purchase Requests", "🧾"), ("AI Assistant", "💬")]
SUBTITLES = {
    "Dashboard": "Your procurement at a glance",
    "Add Vendor": "Upload documents — AI builds and checks the vendor profile",
    "Vendors": "Your vendor master",
    "Compare & Order": "Rank suppliers on your priorities and raise a purchase request",
    "Purchase Requests": "Track every request from sent to received",
    "AI Assistant": "Ask anything about your vendors and orders",
}
FIELD_LABELS = {
    "legal_name": "Legal Vendor Name *", "trade_name": "Trade Name", "gstin": "GSTIN *", "pan": "PAN *",
    "address": "Registered Address *", "category": "Vendor Category", "contact_person": "Contact Person *",
    "email": "Email *", "phone": "Phone Number", "bank_name": "Bank Name *",
    "account_holder": "Account Holder Name", "account_number": "Account Number *", "ifsc": "IFSC *",
}
FIELD_KEYS = list(FIELD_LABELS)
PRICE_UNIT_TEXT = {sc.PRODUCT_COFFEE: "per kg", sc.PRODUCT_CUPS: "per cup"}
SHORT = {sc.PRODUCT_COFFEE: "Arabica Coffee Beans", sc.PRODUCT_CUPS: "Paper Cups 250 ml"}


# ===================================================================== HELPERS
_CARD = {"n": 0}


def card():
    """A white, rounded app 'card' (bordered container with a CSS hook)."""
    _CARD["n"] += 1
    return st.container(border=True, key=f"card{_CARD['n']}")


def go(page):
    st.session_state["page"] = page
    if page == "Add Vendor" and st.session_state.get("av_step") == 4:
        st.session_state["vf_reset"] = True      # finished wizard -> start a fresh one


def badge(text, kind="grey"):
    return f'<span class="badge b-{kind}">{text}</span>'


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def topbar(title):
    today = dt.date.today().strftime("%a, %d %b %Y")
    html(f'<div class="topbar"><div><h1>{title}</h1><p>{SUBTITLES.get(title, "")}</p></div>'
         f'<span class="chip">📅 {today}</span></div>')


def kpi(icon, bg, label, value, sub=""):
    return (f'<div class="kpi"><div class="kpi-icon" style="background:{bg}">{icon}</div><div>'
            f'<div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>'
            f'<div class="kpi-sub">{sub}</div></div></div>')


def fmt_date(s):
    if not s:
        return "—"
    try:
        return dt.datetime.strptime(str(s)[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return str(s)


def fmt_dt(s):
    if not s:
        return "—"
    try:
        return dt.datetime.strptime(str(s)[:19], "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y, %H:%M")
    except ValueError:
        return fmt_date(s)


def quality_text(rating):
    return f"{'★' * rating}{'☆' * (5 - rating)} {sc.QUALITY_LABELS[rating]}" if rating else "Insufficient evidence"


def team_name(v):
    name = sc.clean(v.get("trade_name")) or sc.clean(v.get("legal_name"))
    for suf in (" Pvt. Ltd.", " Pvt Ltd", " Private Limited", " Ltd.", " Ltd", " LLP"):
        if name.endswith(suf):
            name = name[: -len(suf)]
    return name.strip(" ,.")


def vendor_flags(v):
    pct, missing = sc.completeness(v)
    out = badge("Complete", "green") if not missing else badge(f"Missing: {', '.join(missing)}", "amber")
    if v.get("duplicate_of"):
        out += badge(f"Possible duplicate of {v['duplicate_of']}", "red")
    return out


def persist_widget_state():
    """Keep form values when the user moves between pages / steps."""
    for k in list(st.session_state.keys()):
        if k.startswith(("vf_", "pref_", "pr_", "cmp_")):
            try:
                st.session_state[k] = st.session_state[k]
            except Exception:
                pass


def ai_note(source, what):
    if source == "ai":
        st.caption(f"🤖 AI interpretation — {what} written by Gemini from the application data.")
    else:
        st.caption(f"ℹ️ Gemini unavailable — standard {what} used.")


# ===================================================================== SIDEBAR
def sidebar():
    with st.sidebar:
        html('<div class="brand"><div class="brand-logo">☕</div><div><div class="brand-name">M Beans &amp; Bites</div>'
             '<div class="brand-sub">Procurement · AI Vendor Selection</div></div></div>')
        html('<div class="side-label">Menu</div>')
        current = st.session_state.get("page", "Dashboard")
        for name, icon in PAGES:
            st.button(f"{icon}  {name}", key=f"nav_{name}", on_click=go, args=(name,),
                      type="primary" if name == current else "secondary")
        html('<div class="side-label">AI engine</div>')
        if ai.get_api_key():
            model = ai.last_model()
            html(f'<div class="side-status">🟢 Gemini connected{(" · " + model) if model else ""}</div>')
        else:
            html('<div class="side-status">🔴 No Gemini API key</div>')
            k = st.text_input("Paste Gemini API key (this session only)", type="password")
            if k:
                st.session_state["gemini_api_key"] = k
                st.rerun()
        with st.expander("Settings"):
            if st.button("Test Gemini connection"):
                with st.spinner("Testing…"):
                    try:
                        msg, _ = ai.test_connection()
                        st.success(msg)
                    except ai.GeminiError as e:
                        st.error(str(e))
            st.caption("Delete every vendor and purchase request.")
            if st.checkbox("I understand", key="adm_confirm"):
                if st.button("Delete all data"):
                    db.reset_all()
                    for k in list(st.session_state.keys()):
                        if k.startswith(("vf_", "pr_", "pref_", "cmp_", "av_", "why", "rank_state", "chat")):
                            st.session_state.pop(k, None)
                    st.session_state["vf_reset"] = True
                    st.rerun()
    return st.session_state.get("page", "Dashboard")


# =================================================================== DASHBOARD
def page_dashboard():
    hour = dt.datetime.now().hour
    greet = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
    html(f'<div class="hero"><h2>{greet}, Procurement Team 👋</h2>'
         '<p>Upload vendor documents once → AI builds &amp; validates the profile → rank suppliers on your '
         'priorities → raise and track purchase requests.</p></div>')
    s = db.dashboard_stats()
    c1, c2, c3 = st.columns(3)
    c1.markdown(kpi("🏢", "#F1E4D6", "Total Vendors", s["total_vendors"], "in vendor master"), unsafe_allow_html=True)
    c2.markdown(kpi("📨", "#E3EEFB", "Orders Placed", s["orders_placed"], "requests sent to vendors"),
                unsafe_allow_html=True)
    c3.markdown(kpi("📦", "#E3F4E8", "Orders Received", s["orders_received"], "delivered and closed"),
                unsafe_allow_html=True)
    st.write("")

    vendors = db.get_vendors()
    if not vendors:
        with card():
            html('<div class="empty"><div class="icon">📂</div><h3>No vendors yet</h3>'
                 '<p>Start by uploading the documents of your first vendor.</p></div>')
            st.button("➕ Add your first vendor", type="primary", on_click=go, args=("Add Vendor",))
        return

    left, right = st.columns([1, 1.4])
    with left:
        with card():
            st.markdown("**Quick actions**")
            st.button("➕ Add a new vendor", on_click=go, args=("Add Vendor",), key="qa1")
            st.button("⚖️ Compare vendors & order", on_click=go, args=("Compare & Order",), key="qa2")
            st.button("🧾 Track purchase requests", on_click=go, args=("Purchase Requests",), key="qa3")
        with card():
            st.markdown("**Needs attention**")
            missing = [(v, sc.completeness(v)[1]) for v in vendors]
            missing = [(v, m) for v, m in missing if m]
            dups = [v for v in vendors if v.get("duplicate_of")]
            if not missing and not dups:
                st.markdown(badge("All vendor records are complete", "green"), unsafe_allow_html=True)
            for v, m in missing:
                html(f'<div class="rowline">⚠️ <b>{v["legal_name"]}</b><br><span class="muted">Missing: '
                     f'{", ".join(m)}</span></div>')
            for v in dups:
                html(f'<div class="rowline">🔁 <b>{v["legal_name"]}</b><br><span class="muted">Possible duplicate of '
                     f'{v["duplicate_of"]}</span></div>')
    with right:
        with card():
            st.markdown("**Recent purchase requests**")
            reqs = db.get_purchase_requests()[:6]
            if not reqs:
                st.caption("No purchase requests yet — create one from Compare & Order.")
            for r in reqs:
                b = badge("Order Received", "green") if r["status"] == "Order Received" else badge("Request Sent", "brown")
                html(f'<div class="rowline"><b>{r["request_id"]}</b> · {r["vendor"]} {b}<br>'
                     f'<span class="muted">{r["product"].split(" — ")[0]} · {sc.fmt_qty(r["quantity"], r["qty_unit"])}'
                     f' · {sc.fmt_money(r["order_value"])} · {fmt_date(r["request_date"])}</span></div>')


# ================================================================== ADD VENDOR
def blank_quote_df():
    df = pd.DataFrame([{"Product": n, "Unit": PRICE_UNIT_TEXT[n], "Unit Price (₹)": None, "Quoted Quantity": None,
                        "Delivery (days)": None, "Validity": "", "Taxes": ""} for n in sc.PRODUCT_NAMES])
    for c in ("Unit Price (₹)", "Quoted Quantity", "Delivery (days)"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


AV_KEYS = ("ai_values", "quote_df", "out_of_scope", "extraction", "failed_docs", "av_files", "av_draft",
           "av_done", "av_suggested_q", "av_time")


def init_form_state():
    if st.session_state.pop("vf_reset", False):
        for k in list(st.session_state.keys()):
            if k.startswith("vf_"):
                st.session_state.pop(k, None)
        for k in AV_KEYS:
            st.session_state.pop(k, None)
        st.session_state["av_step"] = 1
        st.session_state["uploader_ver"] = st.session_state.get("uploader_ver", 0) + 1
        st.session_state["quote_ver"] = st.session_state.get("quote_ver", 0) + 1
    for k in FIELD_KEYS:
        st.session_state.setdefault(f"vf_{k}", "")
    st.session_state.setdefault("vf_products", [])
    st.session_state.setdefault("vf_quality_rating", 0)
    st.session_state.setdefault("vf_quality_evidence", "")
    st.session_state.setdefault("vf_override", False)
    st.session_state.setdefault("av_step", 1)
    st.session_state.setdefault("quote_ver", 0)
    st.session_state.setdefault("uploader_ver", 0)
    if "quote_df" not in st.session_state:
        st.session_state["quote_df"] = blank_quote_df()


def apply_extraction(res, files):
    merged = {**res["vendor"], **res["bank"]}
    ai_values = {}
    for k in FIELD_KEYS:
        val = sc.clean(merged.get(k))
        st.session_state[f"vf_{k}"] = val
        ai_values[k] = val
    rows = {n: {"price": None, "qty": None, "days": None, "validity": "", "taxes": ""} for n in sc.PRODUCT_NAMES}
    out_of_scope, products = [], set()
    for qd in res["quotations"]:
        canon = sc.match_product(qd["product_name"])
        if canon is None:
            out_of_scope.append(qd["product_name"])
            continue
        r = rows[canon]
        if r["price"] is None and qd["unit_price"]:
            r.update(price=qd["unit_price"], qty=qd["quoted_quantity"], days=qd["delivery_days"],
                     validity=qd["validity"] or "", taxes=qd["taxes"] or "")
    for p in res["vendor"]["products_supplied"]:
        canon = sc.match_product(p)
        if canon:
            products.add(canon)
        elif not any(p.lower() in o.lower() or o.lower() in p.lower() for o in out_of_scope):
            out_of_scope.append(p)
    products |= {n for n, r in rows.items() if r["price"]}
    st.session_state["vf_products"] = [n for n in sc.PRODUCT_NAMES if n in products]
    df = pd.DataFrame([{"Product": n, "Unit": PRICE_UNIT_TEXT[n], "Unit Price (₹)": rows[n]["price"],
                        "Quoted Quantity": rows[n]["qty"], "Delivery (days)": rows[n]["days"],
                        "Validity": rows[n]["validity"], "Taxes": rows[n]["taxes"]} for n in sc.PRODUCT_NAMES])
    for c in ("Unit Price (₹)", "Quoted Quantity", "Delivery (days)"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    st.session_state["quote_df"] = df
    st.session_state["quote_ver"] = st.session_state.get("quote_ver", 0) + 1

    # quality evidence from documents -> transparent rule-based suggestion
    q = res["quality"]
    parts = []
    if q["certifications"]:
        parts.append("Certifications: " + ", ".join(q["certifications"]))
    if q["on_time"] is not None:
        parts.append(f"On-time delivery {q['on_time']:g}%")
    if q["defect"] is not None:
        parts.append(f"Defect/return rate {q['defect']:g}%")
    if q["other"]:
        parts.append(q["other"])
    suggested = sc.suggest_quality_rating(q["certifications"], q["on_time"], q["defect"])
    st.session_state["vf_quality_evidence"] = "; ".join(parts) + (" (from vendor documents)" if parts else "")
    st.session_state["vf_quality_rating"] = suggested or 0
    st.session_state["av_suggested_q"] = suggested

    st.session_state["ai_values"] = ai_values
    st.session_state["out_of_scope"] = list(dict.fromkeys(out_of_scope))
    st.session_state["extraction"] = res
    types = {d["file_name"]: d["document_type"] for d in res["documents"]}
    st.session_state["av_files"] = [{"name": f.name, "type": types.get(f.name, "Uploaded")} for f in files]


def collect_vendor():
    v = {k: str(st.session_state.get(f"vf_{k}", "") or "").strip() for k in FIELD_KEYS}
    for k in ("gstin", "pan", "ifsc"):
        v[k] = v[k].upper().replace(" ", "")
    v["account_number"] = v["account_number"].replace(" ", "")
    v["products_supplied"] = list(st.session_state.get("vf_products", []))
    return v


def collect_quotes(edited_df):
    quotes = []
    for _, row in edited_df.iterrows():
        price = row["Unit Price (₹)"]
        if pd.isna(price) or float(price) <= 0:
            continue
        prod = db.get_product_by_name(row["Product"])
        qty = None if pd.isna(row["Quoted Quantity"]) else float(row["Quoted Quantity"])
        days = None if pd.isna(row["Delivery (days)"]) else int(row["Delivery (days)"])
        quotes.append({"product_id": prod["product_id"], "product": row["Product"], "unit_price": float(price),
                       "quoted_quantity": qty, "total_price": round(float(price) * qty, 2) if qty else None,
                       "delivery_days": days, "validity": str(row["Validity"] or "").strip(),
                       "taxes": str(row["Taxes"] or "").strip()})
    return quotes


def stepper(current):
    names = ["Upload documents", "Review details", "Validate & save"]
    out = '<div class="stepper">'
    for i, n in enumerate(names, start=1):
        cls = "done" if i < current else ("active" if i == current else "")
        out += f'<div class="step {cls}"><span class="num">{"✓" if i < current else i}</span>{n}</div>'
        if i < len(names):
            out += '<div class="line"></div>'
    html(out + "</div>")


def page_add_vendor():
    init_form_state()
    step = st.session_state["av_step"]
    if step == 4:
        return add_vendor_done()
    stepper(step)
    if step == 1:
        add_step_upload()
    elif step == 2:
        add_step_review()
    else:
        add_step_validate()


def add_step_upload():
    with card():
        st.markdown("#### 📄 Upload the vendor's documents")
        st.caption("Upload all documents of ONE vendor together — GST certificate, bank details / cancelled cheque, "
                   "quotation and company profile. PDF, images, DOCX, XLSX, CSV or TXT.")
        files = st.file_uploader("Vendor documents", type=ai.SUPPORTED_TYPES, accept_multiple_files=True,
                                 key=f"uploader_{st.session_state['uploader_ver']}", label_visibility="collapsed")
        c1, c2, _ = st.columns([1.2, 1.2, 2])
        extract = c1.button("✨ Extract with AI", type="primary", disabled=not files)
        if c2.button("✍️ Enter manually"):
            st.session_state["av_step"] = 2
            st.rerun()
    if extract:
        parts, ok, failed = ai.prepare_documents(files)
        st.session_state["failed_docs"] = failed
        if not parts:
            st.error("This document could not be processed. Please enter the information manually.")
            return
        t0 = time.time()
        with st.spinner(f"Gemini is reading {len(ok)} document(s)…"):
            try:
                res = ai.extract_vendor_documents(parts, db.get_vendors())
            except ai.GeminiError as e:
                st.error(f"{e}\n\nThis document could not be processed. Please enter the information manually.")
                return
        apply_extraction(res, files)
        st.session_state["av_time"] = round(time.time() - t0, 1)
        st.session_state["av_step"] = 2
        st.rerun()


def add_step_review():
    if st.session_state.get("av_time"):
        st.toast(f"Documents read in {st.session_state.pop('av_time')} s", icon="✨")
    for name in st.session_state.get("failed_docs", []):
        st.warning(f"“{name}”: This document could not be processed. Please enter the information manually.")
    vendor = collect_vendor()
    pct, missing = sc.completeness(vendor)
    left, right = st.columns([2.3, 1])
    with left:
        with card():
            st.markdown("#### 🏢 Company")
            st.caption(f"Vendor ID {db.next_vendor_id()} is assigned on save · empty field = “{sc.NOT_AVAILABLE}”")
            a, b = st.columns(2)
            a.text_input(FIELD_LABELS["legal_name"], key="vf_legal_name", placeholder=sc.NOT_AVAILABLE)
            b.text_input(FIELD_LABELS["trade_name"], key="vf_trade_name", placeholder=sc.NOT_AVAILABLE)
            a.text_input(FIELD_LABELS["gstin"], key="vf_gstin", placeholder=sc.NOT_AVAILABLE)
            b.text_input(FIELD_LABELS["pan"], key="vf_pan", placeholder=sc.NOT_AVAILABLE)
            st.text_input(FIELD_LABELS["address"], key="vf_address", placeholder=sc.NOT_AVAILABLE)
            st.text_input(FIELD_LABELS["category"], key="vf_category", placeholder=sc.NOT_AVAILABLE)
        with card():
            st.markdown("#### 👤 Contact")
            a, b, c = st.columns(3)
            a.text_input(FIELD_LABELS["contact_person"], key="vf_contact_person", placeholder=sc.NOT_AVAILABLE)
            b.text_input(FIELD_LABELS["email"], key="vf_email", placeholder=sc.NOT_AVAILABLE)
            c.text_input(FIELD_LABELS["phone"], key="vf_phone", placeholder=sc.NOT_AVAILABLE)
        with card():
            st.markdown("#### 🏦 Bank details")
            a, b = st.columns(2)
            a.text_input(FIELD_LABELS["bank_name"], key="vf_bank_name", placeholder=sc.NOT_AVAILABLE)
            b.text_input(FIELD_LABELS["account_holder"], key="vf_account_holder", placeholder=sc.NOT_AVAILABLE)
            a.text_input(FIELD_LABELS["account_number"], key="vf_account_number", placeholder=sc.NOT_AVAILABLE)
            b.text_input(FIELD_LABELS["ifsc"], key="vf_ifsc", placeholder=sc.NOT_AVAILABLE)
        with card():
            st.markdown("#### 🧾 Products & quotation")
            st.multiselect("Products supplied", sc.PRODUCT_NAMES, key="vf_products")
            for name in st.session_state.get("out_of_scope", []):
                st.info(f"**{name}** — {sc.OUT_OF_SCOPE}")
            st.caption("Only the two supported products are accepted. Leave the price empty if not quoted.")
            edited = st.data_editor(
                st.session_state["quote_df"], key=f"quote_editor_{st.session_state['quote_ver']}",
                hide_index=True, num_rows="fixed", disabled=["Product", "Unit"],
                column_config={
                    "Unit Price (₹)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
                    "Quoted Quantity": st.column_config.NumberColumn(min_value=0.0),
                    "Delivery (days)": st.column_config.NumberColumn(min_value=1, step=1, format="%d"),
                    "Validity": st.column_config.TextColumn(), "Taxes": st.column_config.TextColumn()})
        with card():
            st.markdown("#### ⭐ Quality / reliability evidence")
            a, b = st.columns([1, 2.2])
            a.selectbox("Quality rating", [0, 1, 2, 3, 4, 5], key="vf_quality_rating",
                        format_func=lambda x: "Not rated" if x == 0 else f"{x}/5 – {sc.QUALITY_LABELS[x]}")
            b.text_input("Evidence (only real, documented evidence)", key="vf_quality_evidence")
            sug = st.session_state.get("av_suggested_q")
            st.caption((f"Suggested from documents: **{sug}/5**. " if sug else
                        "No quality evidence found in the documents. ") + sc.QUALITY_RULE_TEXT)
    with right:
        with card():
            st.markdown("**Profile completeness**")
            st.progress(pct / 100)
            html(f'<div class="big">{pct}%</div>')
            if missing:
                html("".join(badge(m, "amber") for m in missing))
                st.caption("Missing required fields")
            else:
                html(badge("All required fields filled", "green"))
        issues = sc.format_warnings(vendor) + [f"Document inconsistency: {t}" for t in
                                                (st.session_state.get("extraction") or {}).get("inconsistencies", [])]
        if issues:
            with card():
                st.markdown("**Things to check**")
                for t in issues:
                    st.warning(t)
        ai_vals = st.session_state.get("ai_values")
        if ai_vals:
            with card():
                st.markdown("**Field source**")
                n_ai = sum(1 for k in FIELD_KEYS if vendor[k] and vendor[k] == ai_vals.get(k))
                n_user = sum(1 for k in FIELD_KEYS if vendor[k] and vendor[k] != ai_vals.get(k))
                html(badge(f"🤖 {n_ai} AI extracted", "brown") + badge(f"✍️ {n_user} user edited", "grey"))
                edited_f = [FIELD_LABELS[k].replace(" *", "") for k in FIELD_KEYS
                            if vendor[k] and vendor[k] != ai_vals.get(k)]
                if edited_f:
                    st.caption("User edited: " + ", ".join(edited_f))
    st.write("")
    c1, c2, _ = st.columns([1, 1.6, 3])
    if c1.button("← Back"):
        st.session_state["av_step"] = 1
        st.rerun()
    if c2.button("Continue to validation →", type="primary"):
        if not vendor["legal_name"]:
            st.error("Please enter at least the Legal Vendor Name.")
        else:
            quotes = collect_quotes(edited)
            for qd in quotes:
                if qd["product"] not in vendor["products_supplied"]:
                    vendor["products_supplied"].append(qd["product"])
            st.session_state["quote_df"] = edited
            st.session_state["quote_ver"] += 1
            st.session_state["av_draft"] = {"vendor": vendor, "quotes": quotes}
            st.session_state["av_step"] = 3
            st.rerun()


def find_duplicates(vendor):
    existing = db.get_vendors()
    extraction = st.session_state.get("extraction")
    found = sc.exact_duplicates(vendor, existing)
    found += extraction["duplicate_matches"] if extraction else sc.fuzzy_duplicates(vendor, existing)
    merged = {}
    for m in found:
        if not db.get_vendor(m["vendor_id"]):
            continue
        e = merged.setdefault(m["vendor_id"], {"vendor_id": m["vendor_id"], "name": m["name"], "similarity": 0,
                                               "reasons": []})
        e["similarity"] = max(e["similarity"], m["similarity"])
        e["reasons"] += [r for r in m["reasons"] if r not in e["reasons"]]
    return sorted(merged.values(), key=lambda x: -x["similarity"])


def add_step_validate():
    draft = st.session_state.get("av_draft")
    if not draft:
        st.session_state["av_step"] = 2
        st.rerun()
    vendor, quotes = draft["vendor"], draft["quotes"]
    pct, missing = sc.completeness(vendor)
    matches = find_duplicates(vendor)
    risk = sc.duplicate_risk(matches)
    extraction = st.session_state.get("extraction") or {}
    facts = {
        "vendor": vendor["legal_name"], "category": vendor["category"] or None,
        "products": ", ".join(SHORT[p] for p in vendor["products_supplied"]) or None,
        "quoted_prices": "; ".join(f"{sc.fmt_money(q['unit_price'])} {PRICE_UNIT_TEXT[q['product']]}" for q in quotes) or None,
        "delivery": ", ".join(f"{q['delivery_days']} days" for q in quotes if q["delivery_days"]) or None,
        "documentation": "Complete" if not missing else "Incomplete (missing: " + ", ".join(missing) + ")",
        "duplicate_risk": risk}
    summary = extraction.get("summary")
    sum_src = "ai" if summary else "fallback"
    summary = summary or ai.fallback_summary(facts)

    left, right = st.columns([1.5, 1])
    with left:
        with card():
            st.markdown("#### 📋 Vendor summary")
            html(f'<div class="summary-card"><div class="vname">{vendor["legal_name"]}</div><br>'
                 f'<b>Category:</b> {facts["category"] or sc.NOT_AVAILABLE}<br>'
                 f'<b>Products:</b> {facts["products"] or sc.NOT_AVAILABLE}<br>'
                 f'<b>Quoted Price:</b> {facts["quoted_prices"] or sc.NOT_AVAILABLE}<br>'
                 f'<b>Delivery:</b> {facts["delivery"] or sc.NOT_AVAILABLE}<br>'
                 f'<b>Documentation:</b> {facts["documentation"]}<br>'
                 f'<b>Duplicate Risk:</b> {risk}<br><br><b>AI Summary</b><br><i>“{summary}”</i></div>')
            ai_note(sum_src, "summary")
    with right:
        with card():
            st.markdown("#### ✅ Profile completeness")
            st.progress(pct / 100)
            html(f'<div class="big">{pct}% Complete</div>')
            if missing:
                html("".join(badge(m, "amber") for m in missing))
                st.error("Incomplete — Additional Information Required")
            else:
                st.success("All required fields are present")

    action = "new"
    with card():
        if matches:
            top = matches[0]
            st.markdown("#### ⚠️ Potential Duplicate Vendor")
            sim_badge = badge("Similarity: " + str(top["similarity"]) + "%", "red")
            html(f'<b>Possible Match:</b> {top["name"]} ({top["vendor_id"]}) &nbsp; {sim_badge}')
            st.markdown("**Why?**\n" + "\n".join(f"- {r}" for r in top["reasons"]))
            if not extraction:
                st.caption("Potential duplicate — manual review recommended.")
            st.markdown("**Recommended Action:** Review Existing Vendor — choose what to do:")
            options = [f"update:{m['vendor_id']}" for m in matches] + ["new"]
            labels = {f"update:{m['vendor_id']}": f"🔄 Update the existing vendor {m['name']} ({m['vendor_id']}) with this information"
                      for m in matches}
            labels["new"] = "➕ Create as a new, separate vendor"
            if st.session_state.get("vf_dup_action") not in options:
                st.session_state["vf_dup_action"] = options[0]
            action = st.radio("Decision", options, format_func=lambda o: labels[o], key="vf_dup_action",
                              label_visibility="collapsed")
        else:
            st.markdown("#### ✅ No duplicate found")
            st.caption("Checked GSTIN, PAN and bank account (exact match) and vendor name & address (AI similarity).")

    target = action.split(":")[1] if action.startswith("update:") else None
    if target:
        old = db.get_vendor(target)
        merged_view = {k: (vendor.get(k) or old.get(k)) for k in FIELD_KEYS}
        f_pct, f_missing = sc.completeness(merged_view)
        st.info(f"After the update, {old['legal_name']} will be {f_pct}% complete. Empty fields in the new documents "
                f"keep the existing values; new quotations replace the old ones.")
    else:
        f_pct, f_missing = pct, missing
    if f_missing:
        st.checkbox("Override: treat this vendor as onboarded even though required fields are missing",
                    key="vf_override")
    override = st.session_state.get("vf_override", False)
    status = "Active" if (not f_missing or override) else "Incomplete"

    c1, c2, _ = st.columns([1, 1.6, 3])
    if c1.button("← Back to edit"):
        st.session_state["av_step"] = 2
        st.rerun()
    label = "🔄 Update existing vendor" if target else "💾 Save vendor"
    if c2.button(label, type="primary"):
        rating = st.session_state.get("vf_quality_rating") or None
        evidence = st.session_state.get("vf_quality_evidence", "").strip() or None
        docs = st.session_state.get("av_files", [])
        if target:
            rec = dict(vendor, quality_rating=rating, quality_evidence=evidence, summary=summary)
            db.update_vendor_from_documents(target, rec, quotes, docs, status, f_pct)
            st.session_state["av_done"] = {"vid": target, "name": db.get_vendor(target)["legal_name"],
                                           "status": status, "action": "updated"}
        else:
            top = matches[0] if matches else None
            rec = dict(vendor, status=status, completeness_percentage=pct, quality_rating=rating,
                       quality_evidence=evidence, summary=summary,
                       duplicate_of=top["vendor_id"] if top else None,
                       duplicate_note=(f"Possible match: {top['name']} — Similarity {top['similarity']}% — "
                                       + "; ".join(top["reasons"]).lower() + ".") if top else None)
            note = "Missing-field override used." if (missing and override) else ""
            vid = db.save_vendor(rec, quotes, docs, audit_note=note)
            st.session_state["av_done"] = {"vid": vid, "name": vendor["legal_name"], "status": status,
                                           "action": "created"}
        st.session_state["av_step"] = 4
        st.rerun()


def reset_wizard():
    st.session_state["vf_reset"] = True


def add_vendor_done():
    d = st.session_state.get("av_done") or {}
    with card():
        html(f'<div class="empty"><div class="icon">🎉</div><h3>Vendor {d.get("action", "saved")}</h3>'
             f'<p><b>{d.get("vid", "")} — {d.get("name", "")}</b><br>Status: {d.get("status", "")}</p></div>')
        c1, c2, c3 = st.columns(3)
        c1.button("➕ Add another vendor", type="primary", on_click=reset_wizard)
        c2.button("🏢 View vendors", on_click=lambda: (reset_wizard(), go("Vendors")))
        c3.button("⚖️ Compare & order", on_click=lambda: (reset_wizard(), go("Compare & Order")))


# ===================================================================== VENDORS
def page_vendors():
    vendors = db.get_vendors()
    if not vendors:
        with card():
            html('<div class="empty"><div class="icon">🏢</div><h3>No vendors yet</h3></div>')
            st.button("➕ Add vendor", type="primary", on_click=go, args=("Add Vendor",))
        return
    sel = st.session_state.get("vendor_open")
    if sel and db.get_vendor(sel):
        return vendor_detail(sel)
    search = st.text_input("🔍 Search vendors", placeholder="Type a vendor name…", label_visibility="collapsed")
    shown = [v for v in vendors if search.lower() in (v["legal_name"] or "").lower()]
    cols = st.columns(3)
    for i, v in enumerate(shown):
        with cols[i % 3]:
            with card():
                html(f'<div class="vname">{v["legal_name"]}</div><div class="muted">{v["vendor_id"]} · '
                     f'{v["category"] or "Supplier"}</div>')
                quotes = db.get_vendor_quotes(v["vendor_id"])
                html("".join(badge(f'{SHORT[q["product"]]} · {sc.fmt_money(q["unit_price"])}/{q["price_unit"]}', "brown")
                             for q in quotes) or badge("No quotation", "grey"))
                html(vendor_flags(v))
                html(f'<div class="muted" style="margin-top:6px">Quality: {quality_text(v["quality_rating"])}</div>')
                st.button("Open →", key=f"open_{v['vendor_id']}", on_click=lambda vid=v["vendor_id"]:
                          st.session_state.__setitem__("vendor_open", vid))


def vendor_detail(vid):
    v = db.get_vendor(vid)
    st.button("← All vendors", on_click=lambda: st.session_state.pop("vendor_open", None))
    pct, missing = sc.completeness(v)
    html(f'<h2 style="margin:6px 0 0 0">{v["legal_name"]}</h2><div class="muted">{vid} · {v["category"] or "Supplier"}'
         f' · Profile {pct}% complete</div>')
    html(vendor_flags(v))
    if v["duplicate_note"]:
        st.warning(v["duplicate_note"])
    t1, t2, t3, t4 = st.tabs(["Profile", "Quotations", "Documents & history", "Edit"])
    with t1:
        a, b = st.columns(2)
        with a:
            with card():
                for k in ("legal_name", "trade_name", "gstin", "pan", "address", "contact_person", "email", "phone"):
                    st.markdown(f"**{FIELD_LABELS[k].replace(' *', '')}:** {v[k] or sc.NOT_AVAILABLE}")
        with b:
            with card():
                for k in ("bank_name", "account_holder", "account_number", "ifsc"):
                    st.markdown(f"**{FIELD_LABELS[k].replace(' *', '')}:** {v[k] or sc.NOT_AVAILABLE}")
                st.markdown(f"**Quality (recorded):** {quality_text(v['quality_rating'])}")
                st.markdown(f"**Evidence:** {v['quality_evidence'] or sc.INSUFFICIENT_QUALITY}")
            if v["summary"]:
                html(f'<div class="summary-card"><b>AI Summary</b><br><i>“{v["summary"]}”</i></div>')
    with t2:
        quotes = db.get_vendor_quotes(vid)
        if quotes:
            st.dataframe(pd.DataFrame([{
                "Product": x["product"], "Unit Price": f"{sc.fmt_money(x['unit_price'])}/{x['price_unit']}",
                "Quoted Qty": sc.fmt_qty(x["quoted_quantity"], x["qty_unit"]) if x["quoted_quantity"] else "—",
                "Total": sc.fmt_money(x["total_price"]) if x["total_price"] else "—",
                "Delivery": f"{x['delivery_days']} days" if x["delivery_days"] else "—",
                "Validity": x["validity"] or "—", "Taxes": x["taxes"] or "—"} for x in quotes]), hide_index=True)
        else:
            st.caption("No quotation on record.")
    with t3:
        docs = db.get_documents(vid)
        for d in docs:
            st.markdown(f"📄 **{d['document_name']}** · {d['document_type']} · {fmt_date(d['upload_date'])}")
        st.markdown("**History**")
        for a_ in db.get_audit("vendor", vid):
            st.caption(f"{fmt_dt(a_['timestamp'])} — {a_['action']}" + (f" ({a_['details']})" if a_["details"] else ""))
    with t4:
        with st.form(f"edit_{vid}"):
            vals = {}
            c = st.columns(2)
            for i, k in enumerate(FIELD_KEYS):
                vals[k] = c[i % 2].text_input(FIELD_LABELS[k], value=v[k] or "")
            r = st.selectbox("Quality rating", [0, 1, 2, 3, 4, 5], index=v["quality_rating"] or 0,
                             format_func=lambda x: "Not rated" if x == 0 else f"{x}/5 – {sc.QUALITY_LABELS[x]}")
            ev = st.text_input("Quality evidence", value=v["quality_evidence"] or "")
            ovr = st.checkbox("Override missing required fields (treat as onboarded)", value=v["status"] == "Active")
            if st.form_submit_button("💾 Save changes", type="primary"):
                vals = {k: x.strip() for k, x in vals.items()}
                for k in ("gstin", "pan", "ifsc"):
                    vals[k] = vals[k].upper().replace(" ", "")
                p2, m2 = sc.completeness(vals)
                db.update_vendor_details(vid, vals, "Active" if (not m2 or ovr) else "Incomplete", p2)
                if (r or None) != v["quality_rating"] or (ev or None) != v["quality_evidence"]:
                    db.update_vendor_quality(vid, r or None, ev.strip() or None)
                st.success("Saved.")
                st.rerun()
        has_orders = any(r_["vendor_id"] == vid for r_ in db.get_purchase_requests())
        with st.expander("Delete vendor"):
            if has_orders:
                st.caption("This vendor has purchase requests, so it cannot be deleted.")
            elif st.checkbox("Yes, permanently delete this vendor", key=f"del_ok_{vid}"):
                if st.button("Delete vendor", key=f"del_{vid}"):
                    db.delete_vendor(vid)
                    st.session_state.pop("vendor_open", None)
                    st.rerun()


# ============================================================ COMPARE & ORDER
def build_candidates(product_id):
    quotes = [x for x in db.get_quotes_for_product(product_id) if x["unit_price"]]
    cands = [dict(vendor_id=x["vendor_id"], vendor_name=x["legal_name"], unit_price=x["unit_price"],
                  delivery_days=x["delivery_days"], quality_rating=x["quality_rating"]) for x in quotes]
    return quotes, cands


def page_compare():
    prods = db.get_products()
    pmap = {p["product_id"]: p for p in prods}
    st.session_state.setdefault("cmp_product", prods[0]["product_id"])
    with card():
        st.markdown("**1 · Select Product**")
        pid = st.radio("Select Product", [p["product_id"] for p in prods], key="cmp_product", horizontal=True,
                       format_func=lambda i: ("☕ " if pmap[i]["qty_unit"] == "kg" else "🥤 ") + pmap[i]["name"],
                       label_visibility="collapsed")
    product = pmap[pid]
    quotes, cands = build_candidates(pid)
    if not cands:
        with card():
            html(f'<div class="empty"><div class="icon">🔎</div><h3>No quotations for {product["name"]}</h3>'
                 '<p>Add vendors whose quotation includes this product.</p></div>')
            st.button("➕ Add vendor", type="primary", on_click=go, args=("Add Vendor",))
        return

    with card():
        st.markdown("**2 · Your procurement priorities** — how important is each factor right now?")
        for k, d in zip(("pref_cost", "pref_delivery", "pref_quality"), sc.DEFAULT_PREFS):
            st.session_state.setdefault(k, d)
        a, b, c = st.columns(3)
        cost = a.select_slider("💰 Cost", sc.LEVEL_OPTIONS, key="pref_cost")
        deliv = b.select_slider("🚚 Delivery Time", sc.LEVEL_OPTIONS, key="pref_delivery")
        qual = c.select_slider("⭐ Quality / Reliability", sc.LEVEL_OPTIONS, key="pref_quality")
        weights = sc.compute_weights(cost, deliv, qual)
        html(badge(f"Cost {weights['cost']:g}%", "brown") + badge(f"Delivery {weights['delivery']:g}%", "brown") +
             badge(f"Quality {weights['quality']:g}%", "brown") +
             badge(f"Total {round(sum(weights.values()), 1):g}%", "green"))

    ranked = sc.rank_vendors(cands, weights)
    key = json.dumps([pid, [(c_["vendor_id"], c_["unit_price"], c_["delivery_days"], c_["quality_rating"]) for c_ in cands]])
    prefs = (cost, deliv, qual)
    state = st.session_state.get("rank_state")
    if state is None or state["key"] != key:
        st.session_state["rank_state"] = {"key": key, "prefs": prefs, "rows": ranked, "weights": weights, "msg": None}
    elif state["prefs"] != prefs:
        st.session_state["rank_state"] = {"key": key, "prefs": prefs, "rows": ranked, "weights": weights,
                                          "msg": sc.describe_ranking_change(state["rows"], ranked, state["weights"], weights)}
    msg = st.session_state["rank_state"]["msg"]

    with card():
        st.markdown(f"**3 · Recommended Vendors** for {product['name']}")
        if msg:
            (st.warning if msg[0] else st.info)(f"**{'🔀 Ranking Changed' if msg[0] else 'What-if result'}** — {msg[1]}")
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        widths = [0.5, 2.6, 1.2, 1.1, 1.5, 1.4, 0.8, 0.9]
        for col, h in zip(st.columns(widths), ["", "Vendor", "Price", "Delivery", "Quality", "Score", "", ""]):
            col.caption(h)
        vmap = {x["vendor_id"]: x for x in quotes}
        for r in ranked:
            cols = st.columns(widths, vertical_alignment="center")
            cols[0].markdown(f"### {medals.get(r['rank'], r['rank'])}")
            warn = "" if vmap[r["vendor_id"]]["status"] == "Active" else " " + badge("Incomplete", "amber")
            cols[1].markdown(f"**{r['vendor_name']}**{warn}", unsafe_allow_html=True)
            cols[2].write(f"{sc.fmt_money(r['unit_price'])}/{product['price_unit']}")
            cols[3].write(f"{r['delivery_days']} days" if r["delivery_days"] else "—")
            cols[4].write(quality_text(r["quality_rating"]) if r["quality_rating"] else "Insufficient evidence")
            with cols[5]:
                st.markdown(f"**{r['total']:g}**/100")
                st.progress(min(r["total"] / 100, 1.0))
            if cols[6].button("Why?", key=f"why_{pid}_{r['vendor_id']}"):
                st.session_state["why"] = (pid, r["vendor_id"])
            if cols[7].button("Order", key=f"ord_{pid}_{r['vendor_id']}", type="primary" if r["rank"] == 1 else "secondary"):
                st.session_state["pr_vendor"] = r["vendor_id"]
                st.session_state["pr_open"] = True
        with st.expander("How the score is calculated"):
            st.dataframe(pd.DataFrame([{
                "Rank": r["rank"], "Vendor": r["vendor_name"],
                f"Cost (max {weights['cost']:g})": f"{r['cost_points']:g}",
                f"Delivery (max {weights['delivery']:g})": f"{r['delivery_points']:g}",
                f"Quality (max {weights['quality']:g})": f"{r['quality_points']:g}",
                "Total /100": f"{r['total']:g}"} for r in ranked]), hide_index=True)
            st.caption("Cost = weight × lowest price ÷ vendor price · Delivery = weight × fastest days ÷ vendor days · "
                       "Quality = weight × rating ÷ 5 (no evidence = 0). Calculated by the app, not by AI. "
                       "✅ Price, delivery and quality are recorded data; 🤖 only explanations are AI interpretation.")

    why = st.session_state.get("why")
    row = next((r for r in ranked if why and why[0] == pid and r["vendor_id"] == why[1]), None)
    if row:
        advantage, tradeoff = sc.key_advantage_and_tradeoff(row, ranked, weights)
        ctx = {"product": product["name"], "selected_vendor": row["vendor_name"], "selected_rank": row["rank"],
               "preferences": {"cost": cost, "delivery_time": deliv, "quality": qual}, "weights_percent": weights,
               "ranking": [{"rank": r["rank"], "vendor": r["vendor_name"], "score": r["total"], "price": r["unit_price"],
                            "delivery_days": r["delivery_days"], "quality_rating_out_of_5": r["quality_rating"],
                            "cost_points": r["cost_points"], "delivery_points": r["delivery_points"],
                            "quality_points": r["quality_points"]} for r in ranked],
               "key_advantage": advantage, "main_trade_off": tradeoff}
        ck = json.dumps(ctx, sort_keys=True, default=str)
        cache = st.session_state.setdefault("why_cache", {})
        if ck not in cache:
            with st.spinner("Gemini is explaining the ranking…"):
                cache[ck] = ai.explain_ranking(ctx)
        text, src = cache[ck]
        with card():
            st.markdown(f"#### 💡 Why {row['vendor_name']} is ranked #{row['rank']}")
            st.write(text)
            ai_note(src, "explanation")
            a, b = st.columns(2)
            a.success(f"**Key Advantage**\n\n{advantage}")
            b.warning(f"**Main Trade-off**\n\n{tradeoff}")

    if st.session_state.get("pr_open"):
        purchase_request_form(ranked, pid, pmap)
    else:
        st.caption("Click **Order** next to a vendor to raise a purchase request.")


def purchase_request_form(ranked, pid, pmap):
    with card():
        st.markdown("#### 🛒 New Purchase Request")
        labels = {r["vendor_id"]: f"#{r['rank']} {r['vendor_name']} (score {r['total']:g})" for r in ranked}
        if st.session_state.get("pr_vendor") not in labels:
            st.session_state["pr_vendor"] = ranked[0]["vendor_id"]
        a, b = st.columns(2)
        vendor_id = a.selectbox("Select Vendor", list(labels), format_func=lambda x: labels[x], key="pr_vendor")
        vendor = db.get_vendor(vendor_id)
        vquotes = db.get_vendor_quotes(vendor_id)
        options = [x["product_id"] for x in vquotes]
        pkey = f"pr_product_{vendor_id}"
        if st.session_state.get(pkey) not in options:
            st.session_state[pkey] = pid if pid in options else options[0]
        prod_id = b.selectbox("Product", options, format_func=lambda i: pmap[i]["name"], key=pkey)
        pr_prod = pmap[prod_id]
        quote = next(x for x in vquotes if x["product_id"] == prod_id)
        if vendor["status"] != "Active":
            st.warning("This vendor's profile is incomplete — review it before ordering.")
        st.session_state.setdefault(f"pr_qty_{prod_id}", 100 if pr_prod["qty_unit"] == "kg" else 2000)
        st.session_state.setdefault("pr_date", dt.date.today() + dt.timedelta(days=7))
        if st.session_state["pr_date"] < dt.date.today():
            st.session_state["pr_date"] = dt.date.today()
        st.session_state.setdefault("pr_address", DEFAULT_DELIVERY_ADDRESS)
        c, d = st.columns(2)
        qty = c.number_input(f"Quantity ({pr_prod['qty_unit']})", min_value=1, step=1, key=f"pr_qty_{prod_id}")
        delivery = d.date_input("Required Delivery Date", min_value=dt.date.today(), key="pr_date",
                                format="DD/MM/YYYY")
        address = st.text_input("Delivery address", key="pr_address")
        instructions = st.text_area("Special Instructions (optional)", key="pr_instr", height=68,
                                    placeholder="e.g. Please provide the GST invoice with delivery.")
        unit_price = quote["unit_price"]
        order_value = round(unit_price * qty, 2) if unit_price else None
        st.markdown("**Purchase Request Summary**")
        html(f'<div class="summary-card"><b>Vendor:</b> {vendor["legal_name"]}<br><b>Product:</b> {pr_prod["name"]}<br>'
             f'<b>Quantity:</b> {sc.fmt_qty(qty, pr_prod["qty_unit"])}<br>'
             f'<b>Requested Delivery Date:</b> {delivery.strftime("%d %B %Y")}<br>'
             f'<b>Quoted Unit Price:</b> {sc.fmt_money(unit_price)}/{pr_prod["price_unit"]}<br>'
             f'<b>Estimated Order Value:</b> {sc.fmt_money(order_value)}'
             f'{(" (" + quote["taxes"] + ")") if quote["taxes"] else ""}<br>'
             f'<b>Special Instructions:</b> {instructions.strip() or "—"}</div>')
        st.write("")
        snapshot = {"vendor_id": vendor_id, "product_id": prod_id, "qty": int(qty), "date": str(delivery),
                    "instr": instructions.strip(), "addr": address.strip()}
        if st.button("✉️ Generate Purchase Request Email", type="primary"):
            facts = {"vendor": vendor["legal_name"], "vendor_team": team_name(vendor), "product": pr_prod["name"],
                     "product_short": pr_prod["name"].split(" — ")[0], "quantity": sc.fmt_qty(qty, pr_prod["qty_unit"]),
                     "delivery_date": delivery.strftime("%d %B %Y"),
                     "unit_price": f"{sc.fmt_money(unit_price)} per {pr_prod['price_unit']}" if unit_price else None,
                     "order_value": sc.fmt_money(order_value) if order_value else None,
                     "taxes": quote["taxes"] or None, "delivery_address": address.strip() or None,
                     "special_instructions": instructions.strip() or None}
            with st.spinner("Drafting the email…"):
                subject, body, src = ai.generate_email(facts)
            st.session_state["pr_to"] = vendor["email"] or ""
            st.session_state["pr_subject"] = subject
            st.session_state["pr_body"] = body
            st.session_state["pr_draft"] = {"snapshot": snapshot, "generated_at": db.now_str(), "source": src}
            st.session_state["pr_show_copy"] = False

    draft = st.session_state.get("pr_draft")
    if draft:
        with card():
            st.markdown("#### 📧 Purchase Request Email")
            st.caption("Review and edit — the email is NOT sent automatically." +
                       (" Polished by Gemini." if draft["source"] == "ai" else ""))
            st.text_input("To", key="pr_to", placeholder="Vendor email not available — type it here")
            st.text_input("Subject", key="pr_subject")
            st.text_area("Message", key="pr_body", height=420)
            stale = draft["snapshot"] != snapshot
            if stale:
                st.warning("The request details changed — generate the email again.")
            to, subj, body = st.session_state.get("pr_to", ""), st.session_state.get("pr_subject", ""), st.session_state.get("pr_body", "")
            c1, c2, c3, _ = st.columns([1.3, 1, 1.4, 1])
            if to.strip():
                c1.link_button("📤 Open in email app",
                               f"mailto:{to.strip()}?subject={urllib.parse.quote(subj)}&body={urllib.parse.quote(body)}")
            else:
                c1.caption("Add the vendor email to open it in your email app.")
            if c2.button("📋 Copy email"):
                st.session_state["pr_show_copy"] = True
            if c3.button("✅ Mark as Request Sent", type="primary", disabled=stale):
                rid = db.create_purchase_request(vendor_id, prod_id, float(qty), unit_price, order_value, str(delivery),
                                                 instructions.strip(), subj, body, draft["generated_at"])
                st.session_state["pr_draft"] = None
                st.session_state["pr_open"] = False
                st.session_state["pr_sent_msg"] = f"{rid} saved as “Request Sent” — Orders Placed +1"
                st.rerun()
            if st.session_state.get("pr_show_copy"):
                st.caption("Use the copy icon on the top-right of the box.")
                st.code(f"To: {to}\nSubject: {subj}\n\n{body}", language=None)


# ========================================================== PURCHASE REQUESTS
def receive(rid):
    db.mark_received(rid)
    st.session_state["toast"] = f"{rid} marked as Order Received — Orders Received +1"


def page_purchase_requests():
    reqs = db.get_purchase_requests()
    if not reqs:
        with card():
            html('<div class="empty"><div class="icon">🧾</div><h3>No purchase requests yet</h3>'
                 '<p>Rank vendors and click “Order” to raise one.</p></div>')
            st.button("⚖️ Compare & order", type="primary", on_click=go, args=("Compare & Order",))
        return
    flt = st.radio("Filter", ["All", "Request Sent", "Order Received"], horizontal=True, label_visibility="collapsed")
    for r in reqs:
        if flt != "All" and r["status"] != flt:
            continue
        with card():
            cols = st.columns([1, 2.6, 1.5, 1.4, 1.6], vertical_alignment="center")
            cols[0].markdown(f"**{r['request_id']}**")
            cols[1].markdown(f"**{r['vendor']}**<br><span class='muted'>{r['product']}</span>", unsafe_allow_html=True)
            cols[2].markdown(f"{sc.fmt_qty(r['quantity'], r['qty_unit'])}<br><span class='muted'>"
                             f"{sc.fmt_money(r['order_value'])}</span>", unsafe_allow_html=True)
            cols[3].markdown(f"<span class='muted'>Requested</span><br>{fmt_date(r['request_date'])}", unsafe_allow_html=True)
            if r["status"] == "Order Received":
                cols[4].markdown(badge("✓ Order Received", "green"), unsafe_allow_html=True)
            else:
                cols[4].markdown(badge("Request Sent", "brown"), unsafe_allow_html=True)
                cols[4].button("📦 Order Received", key=f"recv_{r['request_id']}", on_click=receive,
                               args=(r["request_id"],), type="primary")
            with st.expander("View"):
                a, b = st.columns(2)
                a.markdown(f"**Vendor:** {r['vendor']}  \n**Product:** {r['product']}  \n"
                           f"**Quantity:** {sc.fmt_qty(r['quantity'], r['qty_unit'])}  \n"
                           f"**Requested Delivery Date:** {fmt_date(r['requested_delivery_date'])}  \n"
                           f"**Special Instructions:** {r['special_instructions'] or '—'}")
                b.markdown(f"**Quoted Unit Price:** {sc.fmt_money(r['quoted_unit_price'])}/{r['price_unit']}  \n"
                           f"**Order Value:** {sc.fmt_money(r['order_value'])}  \n"
                           f"**Request Date:** {fmt_date(r['request_date'])}  \n**Status:** {r['status']}  \n"
                           f"**Received Date:** {fmt_dt(r['received_date']) if r['received_date'] else '—'}")
                st.markdown("**Audit trail**")
                for a_ in db.get_audit("purchase_request", r["request_id"]):
                    st.caption(f"{fmt_dt(a_['timestamp'])} — {a_['action']}")
                if r["email_body"]:
                    st.markdown(f"**Email sent:** {r['email_subject']}")
                    st.text(r["email_body"])


# ================================================================ AI ASSISTANT
def build_assistant_context():
    prefs = tuple(st.session_state.get(k, d) for k, d in
                  zip(("pref_cost", "pref_delivery", "pref_quality"), sc.DEFAULT_PREFS))
    weights = sc.compute_weights(*prefs)
    vlist = []
    for v in db.get_vendors():
        pct, missing = sc.completeness(v)
        vlist.append({"vendor_id": v["vendor_id"], "name": v["legal_name"], "completeness_percent": pct,
                      "missing_required_fields": missing, "possible_duplicate_of": v["duplicate_of"],
                      "products": v["products_supplied"], "quality_rating_out_of_5": v["quality_rating"],
                      "quality_evidence": v["quality_evidence"], "email": v["email"], "contact": v["contact_person"]})
    rankings, lowest, fastest = {}, {}, {}
    for p in db.get_products():
        quotes, cands = build_candidates(p["product_id"])
        if not cands:
            continue
        rankings[p["name"]] = [{"rank": r["rank"], "vendor": r["vendor_name"], "score": r["total"],
                                "price": r["unit_price"], "delivery_days": r["delivery_days"],
                                "quality": r["quality_rating"], "cost_points": r["cost_points"],
                                "delivery_points": r["delivery_points"], "quality_points": r["quality_points"]}
                               for r in sc.rank_vendors(cands, weights)]
        lo = min(quotes, key=lambda x: x["unit_price"])
        lowest[p["name"]] = {"vendor": lo["legal_name"], "price": lo["unit_price"]}
        timed = [x for x in quotes if x["delivery_days"]]
        if timed:
            fa = min(timed, key=lambda x: x["delivery_days"])
            fastest[p["name"]] = {"vendor": fa["legal_name"], "delivery_days": fa["delivery_days"]}
    return {"company": "M Beans & Bites Pvt. Ltd.",
            "current_priorities": dict(zip(("cost", "delivery", "quality"), prefs), weights_percent=weights),
            "dashboard": {k: v for k, v in db.dashboard_stats().items() if k in ("total_vendors", "orders_placed", "orders_received")},
            "vendors": vlist, "rankings": rankings, "lowest_price": lowest, "fastest_delivery": fastest,
            "purchase_requests": [{"request_id": r["request_id"], "vendor": r["vendor"], "product": r["product"],
                                   "quantity": r["quantity"], "unit": r["qty_unit"], "status": r["status"],
                                   "request_date": r["request_date"], "received_date": r["received_date"],
                                   "order_value": r["order_value"]} for r in db.get_purchase_requests()]}


SUGGESTIONS = ["Which vendor is ranked first for coffee beans?", "Which vendors have missing information?",
               "Which vendor offers the lowest price for paper cups?", "Which vendor has the fastest delivery?",
               "How many orders have been placed?", "Which orders have been received?"]


def page_assistant():
    history = st.session_state.setdefault("chat", [])
    if not history:
        with card():
            st.markdown("**Try asking**")
            cols = st.columns(3)
            for i, q in enumerate(SUGGESTIONS):
                cols[i % 3].button(q, key=f"sugg_{i}", on_click=lambda q=q: st.session_state.__setitem__("ask", q))
    for m in history:
        with st.chat_message(m["role"], avatar="🧑‍💼" if m["role"] == "user" else "☕"):
            st.write(m["content"])
    question = st.chat_input("Ask about vendors, rankings or orders…") or st.session_state.pop("ask", None)
    if question:
        with st.chat_message("user", avatar="🧑‍💼"):
            st.write(question)
        with st.chat_message("assistant", avatar="☕"):
            with st.spinner("Looking at your data…"):
                try:
                    answer = ai.ask_assistant(question, build_assistant_context(), history)
                except ai.GeminiError as e:
                    answer = f"Sorry, the assistant is unavailable right now. {e}"
            st.write(answer)
        history += [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
    if history:
        st.button("🗑️ Clear conversation", on_click=lambda: st.session_state.__setitem__("chat", []))


# ======================================================================== MAIN
persist_widget_state()
page = sidebar()
topbar(page)
if st.session_state.get("pr_sent_msg"):
    st.toast(st.session_state.pop("pr_sent_msg"), icon="✅")
if st.session_state.get("toast"):
    st.toast(st.session_state.pop("toast"), icon="📦")
{"Dashboard": page_dashboard, "Add Vendor": page_add_vendor, "Vendors": page_vendors,
 "Compare & Order": page_compare, "Purchase Requests": page_purchase_requests,
 "AI Assistant": page_assistant}.get(page, page_dashboard)()
