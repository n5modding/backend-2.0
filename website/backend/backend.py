from aiohttp import web
import json
from datetime import datetime, timedelta
import os

LINKED_ACCOUNTS_FILE = "linked_accounts.json"

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

    # Set cookie expiration for 2 days
    accounts["generated_codes"][found]["redeemed_by"] = found
    accounts["generated_codes"][found]["cookie_expires"] = (now + timedelta(days=2)).isoformat()
    save_accounts(accounts)
    return web.json_response({"status": "success", "message": "Code redeemed successfully!"})

app = web.Application()
app.router.add_post("/redeem", redeem_code)
app.router.add_get("/", lambda request: web.Response(text="Backend running"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
