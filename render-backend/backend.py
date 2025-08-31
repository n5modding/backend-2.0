import aiohttp
from aiohttp import web
import asyncio
import json
from datetime import datetime, timedelta
import secrets
import os

CODES_FILE = "codes.json"
CODE_EXPIRY_MINUTES = 10

# Load existing codes
try:
    with open(CODES_FILE, "r") as f:
        codes = json.load(f)
except FileNotFoundError:
    codes = {}  # {code: {"discord_id":..., "expires_at":..., "created_at":...}}

def save_codes():
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=2)

def generate_code(discord_id):
    # Prevent generating more than once per 24h
    now = datetime.utcnow()
    for c, data in codes.items():
        if data["discord_id"] == discord_id:
            created = datetime.fromisoformat(data["created_at"])
            if now - created < timedelta(hours=24):
                return None  # Already generated today
    code = secrets.token_urlsafe(6)
    expires_at = (now + timedelta(minutes=CODE_EXPIRY_MINUTES)).isoformat()
    codes[code] = {"discord_id": discord_id, "expires_at": expires_at, "created_at": now.isoformat()}
    save_codes()
    return code

def validate_code(code):
    now = datetime.utcnow()
    if code in codes:
        exp = datetime.fromisoformat(codes[code]["expires_at"])
        if now < exp:
            return True
        else:
            del codes[code]
            save_codes()
    return False

async def generate_handler(request):
    data = await request.json()
    discord_id = str(data.get("discord_id"))
    role = data.get("role")

    if role != "supporter":
        return web.json_response({"success": False, "error": "You need the 'supporter' role to generate a code."}, status=403)

    code = generate_code(discord_id)
    if code is None:
        return web.json_response({"success": False, "error": "You can only generate one code per day."}, status=403)

    return web.json_response({"success": True, "code": code, "expires_in_minutes": CODE_EXPIRY_MINUTES})

async def redeem_handler(request):
    data = await request.json()
    code = data.get("code")
    if not code:
        return web.json_response({"success": False, "error": "No code provided"}, status=400)
    if validate_code(code):
        return web.json_response({"success": True, "message": "Code valid!"})
    return web.json_response({"success": False, "error": "Invalid or expired code"}, status=400)

async def cleanup_expired_codes():
    while True:
        now = datetime.utcnow()
        to_delete = [c for c, d in codes.items() if datetime.fromisoformat(d["expires_at"]) < now]
        for c in to_delete: del codes[c]
        if to_delete: save_codes()
        await asyncio.sleep(60)

app = web.Application()
app.router.add_post("/generate", generate_handler)
app.router.add_post("/redeem", redeem_handler)

if __name__ == "__main__":
    asyncio.get_event_loop().create_task(cleanup_expired_codes())
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
