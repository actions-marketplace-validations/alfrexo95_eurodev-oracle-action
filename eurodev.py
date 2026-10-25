import os, sys, requests, hashlib, time

ETH_PRICE_USD     = 3000 
MIN_USD_AMOUNT    = 25.00
ETH_ADDRESS       = os.environ.get("CRYPTO_ADDRESS_ETH", "")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
REPO              = os.environ.get("GITHUB_REPOSITORY", "")
ISSUE_NUMBER      = os.environ.get("ISSUE_NUMBER", "").strip()
ISSUE_USER        = os.environ.get("ISSUE_USER", "mystery_user")
ISSUE_BODY        = os.environ.get("ISSUE_BODY", "").lower()
COMMENT_BODY      = os.environ.get("COMMENT_BODY", "")
EVENT_NAME        = os.environ.get("EVENT_NAME", "")

headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def post(text):
    if not ISSUE_NUMBER: return
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
    requests.post(url, headers=headers, json={"body": text}, timeout=20)

def verify_tx(tx_hash):
    try:
        r = requests.get("https://api.etherscan.io/api", params={
            "module": "proxy", "action": "eth_getTransactionByHash",
            "txhash": tx_hash, "apikey": ETHERSCAN_API_KEY
        }, timeout=20).json()
        
        if r.get("result") is None: return False, "TX not found / Nicht gefunden."
        tx = r["result"]
        if tx["to"].lower() != ETH_ADDRESS.lower(): return False, "Wrong address / Falsche Adresse."
        
        eth = int(tx["value"], 16) / 1e18
        usd = eth * ETH_PRICE_USD
        if usd >= MIN_USD_AMOUNT:
            return True, f"{eth:.6f} ETH verified (≈${usd:.2f})"
        return False, f"Insufficient amount / Unzureichender Betrag. (Requires $25.00, got ≈${usd:.2f})"
    except Exception as e:
        return False, f"Etherscan error: {e}"

def is_tx_used(tx_hash):
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments?per_page=100"
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        for c in r.json():
            if tx_hash.lower() in c["body"].lower(): return True
    return False

EU_FACTS = [
    "🇪🇺 The EU AI Act is the world's first comprehensive legal framework on AI.",
    "💻 Europe is home to over 1.5 million professional software developers.",
    "🔒 GDPR fines can reach up to €20 million or 4% of global annual turnover.",
    "🌍 The European Open Source ecosystem contributes over €95 billion to the EU economy.",
    "⚡ Germany is the largest software market in Europe, followed by the UK and France."
]

GDPR_WORDS = ["password", "passwort", "email", "user_data", "address", "adresse", "credit card", "personal data"]

def generate_response(user, num, salt=""):
    r = int(hashlib.sha256(f"{user}-{num}-{salt}".encode()).hexdigest(), 16)
    fact = EU_FACTS[r % len(EU_FACTS)]
    
    warning = ""
    if any(w in ISSUE_BODY for w in GDPR_WORDS):
        warning = ("\n\n⚠️ **GDPR Alert / DSGVO-Warnung:** We detected potential personal data keywords in your issue. "
                   "Ensure you are not exposing PII (Personally Identifiable Information) publicly.")

    return (f"🇪🇺 **EuroDev Oracle** 🇪🇺\n\n"
            f"Hello / Hallo **@{user}**!\n\n"
            f"💡 **EU Tech Fact:**\n{fact}\n"
            f"{warning}\n\n"
            f"---\n"
            f"💎 **Premium Service:** Need a professional GDPR Compliance Checklist for your project? "
            f"Send **$25.00 in ETH** to `{ETH_ADDRESS}` and comment `/premium <tx_hash>`.")

def premium_response(user, num):
    return (f"🇪🇺 **Premium GDPR Checklist / DSGVO-Checkliste** 🇪🇺\n\n"
            f"Thank you for your payment, **@{user}**. Here is your professional compliance checklist for European Open Source:\n\n"
            f"✅ **1. Data Minimization / Datenminimierung:** Only collect what is strictly necessary.\n"
            f"✅ **2. Right to Erasure / Recht auf Löschung:** Provide a way for users to delete their data.\n"
            f"✅ **3. Privacy by Design:** Pseudonymize data (e.g., hashing emails before storing).\n"
            f"✅ **4. Cookie Consent:** Ensure explicit opt-in for tracking (ePrivacy Directive).\n"
            f"✅ **5. Data Processing Agreements (DPA):** If using 3rd party APIs, ensure they are GDPR compliant.\n"
            f"✅ **6. Data Breach Notification:** You must notify authorities within 72 hours of a breach.\n\n"
            f"*This premium checklist is provided for informational purposes. Always consult a lawyer.*")

if EVENT_NAME == "workflow_dispatch":
    sys.exit(0)

if EVENT_NAME == "issues":
    post(generate_response(ISSUE_USER, ISSUE_NUMBER))

elif EVENT_NAME == "issue_comment":
    body = COMMENT_BODY.strip()
    if body.startswith("/premium"):
        parts = body.split()
        if len(parts) < 2:
            post("❌ Usage / Verwendung: `/premium <tx_hash>`")
        else:
            tx = parts[1]
            if is_tx_used(tx):
                post("⚠️ TX already used / TX bereits verwendet.")
                sys.exit(0)
            ok, msg = verify_tx(tx)
            if ok:
                post(f"✅ **{msg}**\n\n{premium_response(ISSUE_USER, ISSUE_NUMBER)}")
            else:
                post(f"❌ **Payment failed / Zahlung fehlgeschlagen:** {msg}")
    else:
        post(generate_response(ISSUE_USER, ISSUE_NUMBER, salt=COMMENT_BODY[:20]))
