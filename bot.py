import json
import os
from pathlib import Path

import requests

API_URL = os.environ["API_URL"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

STATE_DIR = Path("state")
STATE_FILE = STATE_DIR / "state.json"

def load_state():
    STATE_DIR.mkdir(exist_ok=True)

    if not STATE_FILE.exists() or STATE_FILE.stat().st_size == 0:  
        return {"posted": []}  

    try:  
        with open(STATE_FILE, "r", encoding="utf-8") as f:  
            data = json.load(f)  

        if not isinstance(data, dict):  
            return {"posted": []}  

        data.setdefault("posted", [])  
        return data  

    except Exception:  
        return {"posted": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def send_telegram(deal):
    # Removed the inline 🛒 Buy Now text link from the bottom of the text body
    text = f"""
<blockquote><b>{deal.get("name", "Unknown Product")}</b></blockquote>

<blockquote>💰 <b>Price:</b> ₹{deal.get("currentPrice", "N/A")}</blockquote>

<blockquote>📉 <b>Lowest in 6 Months:</b> ₹{deal.get("stats", {}).get("lowestPrice6Months", "N/A")}</blockquote>

<blockquote>🏷 <b>Discount:</b> {deal.get("stats", {}).get("discountPercent", 0)}%</blockquote>

<blockquote>⭐ <b>Deal Score:</b> <a href="{deal.get("mainImage")}">{deal.get("stats", {}).get("dealScore", 0)}</a></blockquote>

<blockquote>📦 <b>Platform:</b> {deal.get("platform", "").title()}</blockquote>
"""
    # Create the modern styled URL Inline Keyboard Button
    # Note: "success" tints the button green; you can change this to "primary" for blue, or "danger" for red.
    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "🛒 Buy Now",
                    "url": deal.get("originalLink"),
                    "style": "success"
                }
            ]
        ]
    }

    r = requests.post(  
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",  
        json={  
            "chat_id": CHANNEL_ID,  
            "text": text,  
            "parse_mode": "HTML",  
            "disable_web_page_preview": False,
            "reply_markup": reply_markup  # Injects the colored CTA button block directly below the message
        },  
        timeout=30,  
    )  

    r.raise_for_status()

def main():
    state = load_state()
    posted = set(state["posted"])

    response = requests.get(API_URL, timeout=30)  
    response.raise_for_status()  

    payload = response.json()  

    if isinstance(payload, dict):  
        deals = payload.get("data", [])  
    else:  
        deals = payload  

    if not deals:  
        print("No deals found.")  
        return  

    new_count = 0  

    # Send oldest first  
    for deal in reversed(deals):  
        deal_id = deal.get("_id")  

        if not deal_id:  
            continue  

        if deal_id in posted:  
            continue  

        try:  
            send_telegram(deal)  
            posted.add(deal_id)  
            new_count += 1  
            print(f"Posted: {deal_id}")  
        except Exception as e:  
            print(f"Failed to post {deal_id}: {e}")  

    state["posted"] = list(posted)  
    save_state(state)  

    print(f"Finished. {new_count} new deal(s) posted.")

if __name__ == "__main__":
    main()
  
