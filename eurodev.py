import os, sys, requests, hashlib, time, re
from datetime import datetime, timedelta

ETH_PRICE_USD     = 3000 
MIN_USD_AMOUNT    = 25.00
ETH_ADDRESS       = os.environ.get("CRYPTO_ADDRESS_ETH", "")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY", "")
GITHUB_TOKEN      = os.environ.get("GITHUB_TOKEN", "")
PAT_TOKEN         = os.environ.get("PAT_TOKEN", GITHUB_TOKEN)
REPO              = os.environ.get("GITHUB_REPOSITORY", "")
ISSUE_NUMBER      = os.environ.get("ISSUE_NUMBER", "").strip()
ISSUE_USER        = os.environ.get("ISSUE_USER", "mystery_user")
ISSUE_BODY        = os.environ.get("ISSUE_BODY", "").lower()
COMMENT_BODY      = os.environ.get("COMMENT_BODY", "")
EVENT_NAME        = os.environ.get("EVENT_NAME", "")
MODE              = os.environ.get("MODE", "interact")

headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
pat_headers = {"Authorization": f"token {PAT_TOKEN}", "Accept": "application/vnd.github.v3+json"}

def post(text, issue_num=ISSUE_NUMBER):
    if not issue_num: return
    url = f"https://api.github.com/repos/{REPO}/issues/{issue_num}/comments"
    requests.post(url, headers=headers, json={"body": text}, timeout=20)

def create_issue(title, body):
    url = f"https://api.github.com/repos/{REPO}/issues"
    r = requests.post(url, headers=headers, json={"title": title, "body": body}, timeout=20)
    return r.json().get("html_url", "")

def verify_tx(tx_hash):
    try:
        r = requests.get("https://api.etherscan.io/api", params={
            "module": "proxy", "action": "eth_getTransactionByHash",
            "txhash": tx_hash, "apikey": ETHERSCAN_API_KEY
        }, timeout=20).json()
        if r.get("result") is None: return False, "TX not found."
        tx = r["result"]
        if tx["to"].lower() != ETH_ADDRESS.lower(): return False, "Wrong address."
        eth = int(tx["value"], 16) / 1e18
        usd = eth * ETH_PRICE_USD
        if usd >= MIN_USD_AMOUNT: return True, f"{eth:.6f} ETH verified (≈${usd:.2f})"
        return False, f"Insufficient amount (Requires $25.00)."
    except Exception as e:
        return False, f"Etherscan error: {e}"

def is_tx_used(tx_hash):
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments?per_page=100"
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        for c in r.json():
            if tx_hash.lower() in c["body"].lower(): return True
    return False

# --- FUNCIÓN DE ANÁLISIS AVANZADO ---
def analyze_repo():
    report = "## 🛡️ Advanced GDPR & Security Report\n\n"
    report += "Our AI scanned your repository files for potential privacy leaks and exposed secrets.\n\n"
    findings = []
    
    for root, dirs, files in os.walk("."):
        if ".git" in root: continue
        for file in files:
            if file.endswith((".md", ".json", ".yml", ".yaml", ".py", ".js", ".txt", ".env")):
                try:
                    with open(os.path.join(root, file), "r", errors="ignore") as f:
                        content = f.read()
                        if re.search(r"(password|secret|api_key|token)\s*[:=]", content, re.IGNORECASE):
                            findings.append(f"- **`{file}`**: Contains hardcoded keywords (password/secret/token).")
                except: pass
                
    if findings:
        report += "### ⚠️ Potential Secret Exposure Detected:\n"
        report += "\n".join(findings[:10]) + "\n\n"
    else:
        report += "✅ No obvious hardcoded secrets found in the top-level files.\n\n"
        
    report += "### 📋 Actionable GDPR Checklist:\n"
    report += "- [ ] Ensure all `.env` files are listed in `.gitignore`.\n"
    report += "- [ ] Verify that user emails are hashed before storage.\n"
    report += "- [ ] Add a `PRIVACY.md` file to your repository.\n"
    report += "- [ ] Implement a 72-hour breach notification protocol.\n"
    return report

# --- FUNCIÓN CAZADOR DE CLIENTES ---
def hunt_leads():
    report = "## 🎯 Daily Lead Generation (EU Developers)\n\n"
    report += "Here are potential clients who recently opened issues mentioning data/privacy keywords in Europe.\n\n"
    date_since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    q = f'is:issue is:open "password" OR "email" OR "user data" created:>{date_since}'
    
    r = requests.get(f"https://api.github.com/search/issues?q={q}&per_page=5", headers=pat_headers, timeout=20)
    
    if r.status_code == 200:
        items = r.json().get("items", [])
        for item in items:
            user = item["user"]["login"]
            if user == "alfrexo95": continue
            
            u_resp = requests.get(f"https://api.github.com/users/{user}", headers=pat_headers, timeout=10)
            loc = u_resp.json().get("location", "")
            eu = ["Germany", "France", "UK", "Spain", "Italy", "Netherlands", "Poland", "Sweden", "Belgium", "Austria", "Switzerland", "Ireland"]
            
            if any(c.lower() in loc.lower() for c in eu) or "europe" in loc.lower():
                report += f"### 👤 @{user} ({loc})\n"
                report += f"- **Issue:** [{item['title']}]({item['html_url']})\n"
                report += f"- **Suggested Comment:**\n> Hey! I saw your issue about data handling. If you need to ensure GDPR compliance, check out the **EuroDev Oracle Action** (free on GitHub Marketplace) or unlock our advanced $25 compliance checklist.\n\n"
    else:
        report += f"❌ Search failed: {r.status_code}\n"
        
    if "### 👤" not in report:
        report += "No new European leads found today.\n"
    return report

def generate_response(user, num, salt=""):
    r = int(hashlib.sha256(f"{user}-{num}-{salt}".encode()).hexdigest(), 16)
    facts = ["🇪🇺 The EU AI Act is the world's first comprehensive AI law.", "💻 Europe is home to over 1.5 million developers.", "🔒 GDPR fines can reach up to €20 million.", "🌍 Open Source contributes €95B to the EU economy."]
    return (f"🇪🇺 **EuroDev Oracle** 🇪🇺\n\nHello **@{user}**!\n\n💡 **EU Fact:** {facts[r % len(facts)]}\n\n---\n💎 **Premium:** Need an Advanced Code Scan + GDPR Checklist? Send **$25 in ETH** to `{ETH_ADDRESS}` and comment `/premium <tx_hash>`.")

if (EVENT_NAME == "workflow_dispatch" and MODE == "hunt") or EVENT_NAME == "schedule":
    url = create_issue(f"🎯 Leads Report - {datetime.now().strftime('%Y-%m-%d')}", hunt_leads())
    print(f"Created report: {url}")
    sys.exit(0)

if EVENT_NAME == "issues":
    post(generate_response(ISSUE_USER, ISSUE_NUMBER))

elif EVENT_NAME == "issue_comment":
    body = COMMENT_BODY.strip()
    if body.startswith("/premium"):
        parts = body.split()
        if len(parts) < 2:
            post("❌ Usage: `/premium <tx_hash>`")
        else:
            tx = parts[1]
            if is_tx_used(tx):
                post("⚠️ TX already used.")
                sys.exit(0)
            ok, msg = verify_tx(tx)
            if ok:
                adv_report = analyze_repo()
                post(f"✅ **{msg}**\n\n{adv_report}")
            else:
                post(f"❌ **Payment failed:** {msg}")
    else:
        post(generate_response(ISSUE_USER, ISSUE_NUMBER, salt=COMMENT_BODY[:20]))
