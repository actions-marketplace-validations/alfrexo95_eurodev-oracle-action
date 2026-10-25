import os, sys, requests, hashlib, base64, re
from datetime import datetime, timedelta

# ================= CONFIGURACIÓN =================
MIN_USD_AMOUNT    = 25.00
ETH_ADDRESS       = os.environ.get("CRYPTO_ADDRESS_ETH", "0xA5E6eB31868A85127B1ED82b8C760193356206ED")
BTC_ADDRESS       = os.environ.get("CRYPTO_ADDRESS_BTC", "bc1qt3rukpe7qp737zj5j5xpxxmcqv90cfefhg5e00")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "SSNXPNG7VZ53A2ZZYG4K73G2PPFUM8G96D")
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
PAT_TOKEN         = os.environ.get("PAT_TOKEN", GITHUB_TOKEN)
REPO              = os.environ.get("GITHUB_REPOSITORY", "")
ISSUE_NUMBER      = os.environ.get("ISSUE_NUMBER", "").strip()
ISSUE_USER        = os.environ.get("ISSUE_USER", "mystery_user")
ISSUE_BODY        = os.environ.get("ISSUE_BODY", "").lower()
COMMENT_BODY      = os.environ.get("COMMENT_BODY", "")
EVENT_NAME        = os.environ.get("EVENT_NAME", "")

headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
pat_headers = {"Authorization": f"token {PAT_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# ================= FUNCIONES DE PRECIO =================
def get_eth_price():
    try:
        r = requests.get("https://api.etherscan.io/api", params={
            "module": "stats", "action": "ethprice", "apikey": ETHERSCAN_API_KEY
        }, timeout=10).json()
        return float(r["result"]["ethusd"])
    except Exception: return 3000.0

def get_btc_price():
    try:
        r = requests.get("https://pricing.bitcoin.block.xyz/current-price", timeout=10).json()
        return float(r["amount"])
    except Exception: return 85000.0

# ================= LÓGICA DEL BOT =================
def post(text, issue_num=ISSUE_NUMBER):
    if not issue_num: return
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}/comments"
    requests.post(url, headers=headers, json={"body": text}, timeout=20)

def verify_eth_tx(tx_hash):
    eth_price = get_eth_price()
    try:
        r = requests.get("https://api.etherscan.io/api", params={
            "module": "proxy", "action": "eth_getTransactionByHash",
            "txhash": tx_hash, "apikey": ETHERSCAN_API_KEY
        }, timeout=20).json()
        if r.get("result") is None: return False, "ETH TX not found / ETH TX nicht gefunden."
        tx = r["result"]
        if tx["to"].lower() != ETH_ADDRESS.lower(): return False, "Wrong ETH address / Falsche ETH-Adresse."
        
        eth_amount = int(tx["value"], 16) / 1e18
        usd = eth_amount * eth_price
        if usd >= MIN_USD_AMOUNT: 
            return True, f"{eth_amount:.6f} ETH verified / verifiziert (≈${usd:.2f} at ${eth_price:,.2f}/ETH)"
        return False, f"Insufficient ETH amount / Unzureichender ETH-Betrag. Got ≈${usd:.2f}, requires $25.00 (Rate: ${eth_price:,.2f}/ETH)"
    except Exception as e:
        return False, f"Etherscan error: {e}"

def verify_btc_tx(tx_hash):
    btc_price = get_btc_price()
    try:
        r = requests.get(f"https://blockstream.info/api/tx/{tx_hash}", timeout=20)
        if r.status_code != 200: return False, "BTC TX not found / BTC TX nicht gefunden."
        tx = r.json()
        
        for vout in tx.get("vout", []):
            if vout.get("scriptpubkey_address") == BTC_ADDRESS:
                sats = vout.get("value", 0)
                btc_amount = sats / 100000000
                usd = btc_amount * btc_price
                if usd >= MIN_USD_AMOUNT:
                    return True, f"{btc_amount:.6f} BTC verified / verifiziert (≈${usd:.2f} at ${btc_price:,.2f}/BTC)"
                return False, f"Insufficient BTC amount / Unzureichender BTC-Betrag. Got ≈${usd:.2f}, requires $25.00 (Rate: ${btc_price:,.2f}/BTC)"
        return False, "BTC address not found in outputs / BTC-Adresse nicht in den Ausgaben gefunden."
    except Exception as e:
        return False, f"Blockstream error: {e}"

def is_tx_used(tx_hash):
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments?per_page=100"
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        for c in r.json():
            if tx_hash.lower() in c["body"].lower(): return True
    return False

def analyze_repo():
    report = "## 🛡️ Advanced GDPR & Security Report / Erweiterter DSGVO- & Sicherheitsbericht\n\n"
    findings = []
    for root, dirs, files in os.walk("."):
        if ".git" in root: continue
        for file in files:
            if file.endswith((".md", ".json", ".yml", ".yaml", ".py", ".js", ".txt", ".env")):
                try:
                    with open(os.path.join(root, file), "r", errors="ignore") as f:
                        content = f.read()
                        if re.search(r"(password|secret|api_key|token)\s*[:=]", content, re.IGNORECASE):
                            findings.append(f"- **`{file}`**: Contains hardcoded keywords / Enthält hartcodierte Schlüsselwörter.")
                except: pass
    if findings:
        report += "### ⚠️ Potential Secret Exposure / Mögliche Offenlegung von Geheimnissen:\n" + "\n".join(findings[:10]) + "\n\n"
    else:
        report += "✅ No obvious hardcoded secrets found / Keine offensichtlichen hartcodierten Geheimnisse gefunden.\n\n"
    report += ("### 📋 GDPR Checklist / DSGVO-Checkliste:\n"
               "- [ ] Ensure `.env` is in `.gitignore` / Stellen Sie sicher, dass `.env` in `.gitignore` steht.\n"
               "- [ ] Hash user emails / Hashen Sie Benutzer-E-Mails.\n"
               "- [ ] Add `PRIVACY.md` / Fügen Sie `PRIVACY.md` hinzu.\n"
               "- [ ] Implement 72-hour breach notification / Implementieren Sie die 72-Stunden-Benachrichtigung bei Datenschutzverletzungen.")
    return report

def save_file(path, content, commit_msg):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    
    data = {"message": commit_msg, "content": base64.b64encode(content.encode()).decode(), "branch": "main"}
    if sha: data["sha"] = sha
    requests.put(url, headers=headers, json=data)

def keep_alive():
    save_file("heartbeat.txt", f"Alive: {datetime.now()}", "💓 Auto-heartbeat / Automatischer Herzschlag")

def hunt_leads():
    report = f"# 🎯 Autonomous EU Leads Report / Autonomer EU-Lead-Bericht\n*Last update / Letztes Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    date_since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    q = f'is:issue is:open "password" OR "email" OR "user data" created:>{date_since}'
    
    r = requests.get(f"https://api.github.com/search/issues?q={q}&per_page=5", headers=pat_headers, timeout=20)
    if r.status_code == 200:
        for item in r.json().get("items", []):
            user = item["user"]["login"]
            if user == "alfrexo95": continue
            u_resp = requests.get(f"https://api.github.com/users/{user}", headers=pat_headers, timeout=10)
            loc = u_resp.json().get("location", "")
            eu = ["Germany", "France", "UK", "Spain", "Italy", "Netherlands", "Poland", "Sweden", "Belgium", "Austria", "Switzerland", "Ireland"]
            
            if any(c.lower() in loc.lower() for c in eu) or "europe" in loc.lower():
                report += f"## 👤 @{user} ({loc})\n"
                report += f"- **Issue / Problem:** [{item['title']}]({item['html_url']})\n"
                report += (f"- **Suggested Comment / Vorgeschlagener Kommentar:**\n"
                           f"> Hey! I saw your issue about data handling. If you need to ensure GDPR compliance, check out the **EuroDev Oracle Action** or unlock our advanced $25 checklist.\n"
                           f"> Hallo! Ich habe Ihr Problem bezüglich des Datenumgangs gesehen. Wenn Sie die DSGVO-Konformität sicherstellen müssen, schauen Sie sich die **EuroDev Oracle Action** an oder schalten Sie unsere erweiterte 25-Dollar-Checkliste frei.\n\n")
    else:
        report += f"❌ Search failed / Suche fehlgeschlagen: {r.status_code}\n"
    if "## 👤" not in report: report += "No new European leads found today / Heute wurden keine neuen europäischen Leads gefunden.\n"
    save_file("LEADS.md", report, "🤖 Auto-update: Daily EU Leads / Tägliche EU-Leads")

def generate_response(user, num, salt=""):
    r = int(hashlib.sha256(f"{user}-{num}-{salt}".encode()).hexdigest(), 16)
    facts = [
        "🇪🇺 The EU AI Act is the world's first comprehensive AI law. / Das EU-KI-Gesetz ist das weltweit erste umfassende KI-Gesetz.",
        "💻 Europe is home to over 1.5 million developers. / Europa ist die Heimat von über 1,5 Millionen Entwicklern.",
        "🔒 GDPR fines can reach up to €20 million. / DSGVO-Geldstrafen können bis zu 20 Millionen Euro betragen.",
        "🌍 Open Source contributes €95B to the EU economy. / Open Source trägt 95 Milliarden Euro zur EU-Wirtschaft bei."
    ]
    
    warning = ""
    if any(w in ISSUE_BODY for w in ["password", "passwort", "email", "user_data", "address", "adresse", "credit card", "personal data"]):
        warning = ("\n\n⚠️ **GDPR Alert / DSGVO-Warnung:** We detected potential personal data keywords in your issue. "
                   "Ensure you are not exposing PII publicly. / Wir haben mögliche personenbezogene Daten in Ihrem Problem erkannt. "
                   "Stellen Sie sicher, dass Sie keine personenbezogenen Daten öffentlich preisgeben.")

    return (f"🇪🇺 **EuroDev Oracle** 🇪🇺\n\nHello **@{user}**! / Hallo **@{user}**!\n\n"
            f"💡 **EU Tech Fact / EU-Tech-Fakt:**\n{facts[r % len(facts)]}\n"
            f"{warning}\n\n---\n"
            f"💎 **Premium Service ($25.00):** Advanced Code Scan + GDPR Checklist.\n"
            f"💎 **Premium-Dienst (25,00 $):** Erweiterter Code-Scan + DSGVO-Checkliste.\n\n"
            f"**Pay with ETH / Mit ETH bezahlen:** `{ETH_ADDRESS}`\n"
            f"**Pay with BTC / Mit BTC bezahlen:** `{BTC_ADDRESS}`\n\n"
            f"After paying, comment / Kommentieren Sie nach der Zahlung:\n"
            f"`/premium eth <tx_hash>` or / oder `/premium btc <tx_hash>`")

# --- LÓGICA DE EJECUCIÓN ---
if EVENT_NAME == "schedule" or (EVENT_NAME == "workflow_dispatch" and not ISSUE_NUMBER):
    print("Ciclo autónomo iniciado / Autonomer Zyklus gestartet...")
    keep_alive()
    hunt_leads()
    sys.exit(0)

if EVENT_NAME == "issues":
    post(generate_response(ISSUE_USER, ISSUE_NUMBER))

elif EVENT_NAME == "issue_comment":
    body = COMMENT_BODY.strip().lower()
    if body.startswith("/premium"):
        parts = body.split()
        if len(parts) < 3:
            post("❌ Usage / Verwendung: `/premium eth <tx_hash>` or / oder `/premium btc <tx_hash>`")
        else:
            currency = parts[1]
            tx_hash = parts[2]
            
            if is_tx_used(tx_hash):
                post("⚠️ TX already used / TX bereits verwendet.")
                sys.exit(0)
                
            if currency == "eth":
                ok, msg = verify_eth_tx(tx_hash)
            elif currency == "btc":
                ok, msg = verify_btc_tx(tx_hash)
            else:
                post("❌ Invalid currency / Ungültige Währung. Use `eth` or `btc`.")
                sys.exit(0)
                
            if ok:
                post(f"✅ **{msg}**\n\n{analyze_repo()}")
            else:
                post(f"❌ **Payment failed / Zahlung fehlgeschlagen:** {msg}")
    else:
        post(generate_response(ISSUE_USER, ISSUE_NUMBER, salt=COMMENT_BODY[:20]))
