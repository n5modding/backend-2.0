from aiohttp import web
import os
import json
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = web.Application()

# Serve index.html and static files
async def index(request):
    return web.FileResponse(os.path.join(BASE_DIR, "../index.html"))

async def style(request):
    return web.FileResponse(os.path.join(BASE_DIR, "../style.css"))

async def redeem_js(request):
    return web.FileResponse(os.path.join(BASE_DIR, "../redeem.js"))

# Redeem endpoint
LINKED_ACCOUNTS_FILE = os.path.join(BASE_DIR, "linked_accounts.json")
def load_accounts():
    try:
        with open(LINKED_ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"generated_codes": {}}

def save_accounts(accounts):
    with open(LINKED_ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=2)

async def redeem_code(request):
    params = await request.json()
    code = params.get("code")
    accounts = load_accounts()
    now = datetime.utcnow()
    found = None

    for user_id, data in accounts.get("generated_codes", {}).items():
        if data.get("code") == code:
            expires = datetime.fromisoformat(data["expires"])
            if now > expires:
                return web.json_response({"status": "error", "message": "Code expired"})
            found = user_id
            break

    if not found:
        return web.json_response({"status": "error", "message": "Invalid code"})

    accounts["generated_codes"][found]["redeemed_by"] = found
    accounts["generated_codes"][found]["cookie_expires"] = (now + timedelta(days=2)).isoformat()
    save_accounts(accounts)
    return web.json_response({"status": "success", "message": "Code redeemed successfully!"})

# Routes
app.router.add_get('/', index)
app.router.add_get('/style.css', style)
app.router.add_get('/redeem.js', redeem_js)
app.router.add_post('/redeem', redeem_code)

# Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
