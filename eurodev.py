import os, sys, requests, hashlib, base64, re, random
from datetime import datetime, timedelta

# ================= PRECIOS Y DIRECCIONES =================
ETH_PRICE_USD     = random.uniform(2480, 3420)
BTC_PRICE_USD     = random.uniform(78000, 90000)
MIN_USD_AMOUNT    = 25.00
ETH_ADDRESS       = os.environ.get("CRYPTO_ADDRESS_ETH", "")
BTC_ADDRESS       = os.environ.get("CRYPTO_ADDRESS_BTC", "")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
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

def post(text, issue_num=ISSUE_NUMBER):
    if not issue_num: return
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}/comments"
    requests.post(url, headers=headers, json={"body": text}, timeout=20)

def verify_eth_tx(tx_hash):
    try:
        r = requests.get("https://api.etherscan.io/api", params={
            "module": "proxy", "action": "eth_getTransactionByHash",
            "txhash": tx_hash, "apikey": ETHERSCAN_API_KEY
        }, timeout=20).json()
        if r.get("result") is None: return False, "ETH TX not found."
        tx = r["result"]
        if tx["to"].lower() != ETH_ADDRESS.lower(): return False, "Wrong ETH address."
        eth = int(tx["value"], 16) / 1e18
        usd = eth * ETH_PRICE_USD
        if usd >= MIN_USD_AMOUNT: return True, f"{eth:.6f} ETH verified (≈${usd:.2f})"
        return False, f"Insufficient ETH amount (Requires $25.00)."
    except Exception as e:
        return False, f"Etherscan error: {e}"

def verify_btc_tx(tx_hash):
    try:
        r = requests.get(f"https://blockstream.info/api/tx/{tx_hash}", timeout=20)
        if r.status_code != 200: return False, "BTC TX not found."
        tx = r.json()
        
        for vout in tx.get("vout", []):
            if vout.get("scriptpubkey_address") == BTC_ADDRESS:
                sats = vout.get("value", 0)
                btc = sats / 100000000
                usd = btc * BTC_PRICE_USD
                if usd >= MIN_USD_AMOUNT:
                    return True, f"{btc:.6f} BTC verified (≈${usd:.2f})"
                return False, f"Insufficient BTC amount (Requires $25.00)."
        return False, "BTC address not found in outputs."
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
    report = "## 🛡️ Advanced GDPR & Security Report\n\n"
    findings = []
    for root, dirs, files in os.walk("."):
        if ".git" in root: continue
        for file in files:
            if file.endswith((".md", ".json", ".yml", ".yaml", ".py", ".js", ".txt", ".env")):
                try:
                    with open(os.path.join(root, file), "r", errors="ignore") as f:
                        content = f.read()
                        if re.search(r"(password|secret|api_key|token)\s*[:=]", content, re.IGNORECASE):
                            findings.append(f"- **`{file}`**: Contains hardcoded keywords.")
                except: pass
    if findings:
        report += "### ⚠️ Potential Secret Exposure:\n" + "\n".join(findings[:10]) + "\n\n"
    else:
        report += "✅ No obvious hardcoded secrets found.\n\n"
    report += "### 📋 GDPR Checklist:\n- [ ] Ensure `.env` is in `.gitignore`.\n- [ ] Hash user emails.\n- [ ] Add `PRIVACY.md`.\n- [ ] Implement 72-hour breach notification."
    return report

def save_file(path, content, commit_msg):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None
    
    data = {
        "message": commit_msg,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": "main"
    }
    if sha: data["sha"] = sha
    requests.put(url, headers=headers, json=data)

def keep_alive():
    save_file("heartbeat.txt", f"Alive: {datetime.now()}", "💓 Auto-heartbeat")

def hunt_leads():
    report = f"# 🎯 Autonomous EU Leads Report\n*Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
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
                report += f"- **Issue:** [{item['title']}]({item['html_url']})\n"
                report += f"- **Suggested Comment:**\n> Hey! I saw your issue about data handling. If you need to ensure GDPR compliance, check out the **EuroDev Oracle Action** or unlock our advanced $25 checklist.\n\n"
    else:
        report += f"❌ Search failed: {r.status_code}\n"
    if "## 👤" not in report: report += "No new European leads found today.\n"
    save_file("LEADS.md", report, "🤖 Auto-update: Daily EU Leads")

def generate_response(user, num, salt=""):
    r = int(hashlib.sha256(f"{user}-{num}-{salt}".encode()).hexdigest(), 16)
    facts = ["🇪🇺 The EU AI Act is the world's first comprehensive AI law.", "💻 Europe is home to over 1.5 million developers.", "🔒 GDPR fines can reach up to €20 million.", "🌍 Open Source contributes €95B to the EU economy."]
    return (f"🇪🇺 **EuroDev Oracle** 🇪🇺\n\nHello **@{user}**!\n\n"
            f"💡 **EU Fact:** {facts[r % len(facts)]}\n\n---\n"
            f"💎 **Premium Service ($25.00):** Advanced Code Scan + GDPR Checklist.\n"
            f"**Pay with ETH:** `{ETH_ADDRESS}`\n"
            f"**Pay with BTC:** `{BTC_ADDRESS}`\n\n"
            f"After paying, comment: `/premium eth <tx_hash>` or `/premium btc <tx_hash>`")

# --- LÓGICA DE EJECUCIÓN ---
if EVENT_NAME == "schedule" or (EVENT_NAME == "workflow_dispatch" and not ISSUE_NUMBER):
    print("Ciclo autónomo iniciado...")
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
            post("❌ Usage: `/premium eth <tx_hash>` or `/premium btc <tx_hash>`")
        else:
            currency = parts[1]
            tx_hash = parts[2]
            
            if is_tx_used(tx_hash):
                post("⚠️ TX already used.")
                sys.exit(0)
                
            if currency == "eth":
                ok, msg = verify_eth_tx(tx_hash)
            elif currency == "btc":
                ok, msg = verify_btc_tx(tx_hash)
            else:
                post("❌ Invalid currency. Use `eth` or `btc`.")
                sys.exit(0)
                
            if ok:
                post(f"✅ **{msg}**\n\n{analyze_repo()}")
            else:
                post(f"❌ **Payment failed:** {msg}")
    else:
        post(generate_response(ISSUE_USER, ISSUE_NUMBER, salt=COMMENT_BODY[:20]))
