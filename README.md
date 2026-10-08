# ☕ M Beans & Bites — AI Vendor Selection & Procurement App
Streamlit + Gemini (free API key). Upload vendor documents → AI builds & checks the vendor profile →
rank vendors on your priorities → raise a purchase request email → track Request Sent → Order Received.

## Files in this repository (upload ALL to the repo root)
| File / folder | Purpose |
|---|---|
| `app.py` | The app (main file for Streamlit) |
| `database.py` | SQLite storage |
| `gemini_helper.py` | All Gemini calls (key read from Streamlit secrets) |
| `scoring.py` | Validation, scoring, ranking, duplicate checks (plain Python, no AI) |
| `requirements.txt` | Python packages |
| `.streamlit/config.toml` | App theme (light coffee theme) — keep the `.streamlit` folder |
| `.streamlit/secrets.toml.example` | Example only — no real key |
| `.gitignore` | Keeps the database and real secrets out of GitHub |
| `sample_documents/` | 3 demo vendors (4 PDFs each) to upload inside the app |

## Deploy on Streamlit Community Cloud
1. Upload the files to GitHub (repo root). Hidden items `.streamlit/` and `.gitignore` start with a dot.
2. share.streamlit.io → Create app → repo, branch `main`, **main file path `app.py`**.
3. Advanced settings → Secrets:  `GEMINI_API_KEY = "your-key"`  → Deploy.
Already deployed? Just replace the files on GitHub — the app updates automatically.

## Demo flow (3 vendors)
1. **Add Vendor** → upload the 4 PDFs of `Vendor_1_FreshBean_Suppliers` → ✨ Extract with AI → review → Continue → Save.
2. Repeat for `Vendor_2_BeanHouse_India` and `Vendor_3_CoffeeCraft_Foods`.
   Vendor 3 shows: missing **Email**, a document inconsistency (bank account holder name) and
   "Chocolate Syrup — product outside current procurement scope". Type an email in Review, or use the override.
3. **Duplicate demo:** upload Vendor 1's files again → the app flags the duplicate (matching GSTIN/PAN/account) →
   choose **Update the existing vendor** or **Create as a new, separate vendor**.
4. **Compare & Order** → Arabica Coffee Beans → Cost High / Delivery Medium / Quality High → FreshBean ranks #1.
   Change to Cost Low / Delivery Very High → **Ranking Changed** (CoffeeCraft moves up). Click **Why?**.
5. Click **Order** → quantity, date, instructions → **Generate Purchase Request Email** → edit →
   📤 Open in email app / 📋 Copy → **Mark as Request Sent**.
6. **Purchase Requests** → **📦 Order Received** → Dashboard updates (Orders Placed / Orders Received).
7. **AI Assistant** → tap a suggested question.

## Notes
* Data is stored in SQLite. On Streamlit Cloud it is wiped when the app restarts/redeploys — record your demo in one go.
  Settings → "Delete all data" clears everything.
* Speed: one Gemini call reads the documents AND checks duplicates, quality evidence and summary; validation is instant.
* If Gemini is busy (free-tier limit) wait a minute; the app still works manually.
* Quality rating = transparent rule from documented evidence (certifications, on-time %, defect %), editable by you.
