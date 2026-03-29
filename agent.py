import pandas as pd
from datetime import datetime
from pathlib import Path
import requests
import os

# ================================
# LOAD ENV (SAFE)
# ================================

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass  # dotenv opzionale (per GitHub/cloud)

# ================================
# CONFIG
# ================================

DEBUG = True

# ================================
# FILES
# ================================

CSV_FILE = Path("bubble_risk_history.csv")
STATE_FILE = Path("regime_state.txt")
EVENT_LOG = Path("events.log")

# ================================
# ENV VARIABLES (SAFE FALLBACK)
# ================================

ZAPIER_WEBHOOK = os.getenv("ZAPIER_WEBHOOK", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

if DEBUG:
    print("DEBUG WEBHOOK SET:", bool(ZAPIER_WEBHOOK))

# ================================
# TELEGRAM
# ================================

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        if DEBUG:
            print("⚠️ Telegram not configured")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)

        if DEBUG:
            print("📱 Telegram status:", r.status_code)

    except Exception as e:
        print("Telegram error:", e)

# ================================
# WEBHOOK (ZAPIER)
# ================================

def send_webhook(event, regime, bubble, hype, date):
    if not ZAPIER_WEBHOOK:
        if DEBUG:
            print("⚠️ Webhook not configured")
        return

    payload = {
        "event": event,
        "regime": regime,
        "bubble": float(bubble),
        "hype": float(hype),
        "date": date
    }

    try:
        r = requests.post(ZAPIER_WEBHOOK, json=payload, timeout=10)

        if DEBUG:
            print("🌐 Webhook status:", r.status_code)

        if r.status_code != 200:
            print("⚠️ Webhook error response:", r.text)

    except Exception as e:
        print("Webhook error:", e)

# ================================
# MODEL
# ================================

def compute_scores():
    # 🔧 QUI collegherai il tuo vero modello
    bubble_score = 5.5  # forzato per test Zapier
    hype_score = 0.439

    if bubble_score < 2:
        regime = "LOW RISK"
    elif bubble_score < 3.5:
        regime = "CAUTION"
    elif bubble_score < 5:
        regime = "HIGH RISK"
    else:
        regime = "BUBBLE"

    return bubble_score, hype_score, regime

# ================================
# STATE
# ================================

def load_last_regime():
    if not STATE_FILE.exists():
        return None
    return STATE_FILE.read_text().strip()

def save_last_regime(regime):
    STATE_FILE.write_text(regime)

# ================================
# CSV
# ================================

def append_csv(date, bubble, hype, regime):
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w") as f:
            f.write("date;bubble_score;hype_score;regime\n")

    with open(CSV_FILE, "a") as f:
        f.write(f"{date};{bubble};{hype};{regime}\n")

def load_last_row():
    if not CSV_FILE.exists():
        return None

    df = pd.read_csv(CSV_FILE, sep=";")

    if df.empty:
        return None

    return df.iloc[-1]

# ================================
# EVENT DETECTION
# ================================

def detect_event(prev_regime, new_regime, prev_bubble, new_bubble):

    if prev_regime is None:
        return "INIT"

    if prev_regime != new_regime:
        return f"REGIME CHANGE: {prev_regime} -> {new_regime}"

    if prev_bubble is not None:
        delta = float(new_bubble) - float(prev_bubble)

        if delta > 0.5:
            return "RISK SPIKE UP"

        if delta < -0.5:
            return "RISK DROP DOWN"

    return None

# ================================
# LOG
# ================================

def log_event(event, date):
    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        f.write(f"{date} | {event}\n")

# ================================
# MAIN
# ================================

def main():
    print("\n=== AI BUBBLE AGENT ===\n")

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    bubble, hype, regime = compute_scores()

    prev_regime = load_last_regime()
    last_row = load_last_row()

    prev_bubble = None
    if last_row is not None:
        prev_bubble = last_row["bubble_score"]

    if DEBUG:
        print("Previous regime:", prev_regime)

    event = detect_event(prev_regime, regime, prev_bubble, bubble)

    append_csv(date, bubble, hype, regime)
    save_last_regime(regime)

    print({
        "date": date,
        "bubble_score": bubble,
        "hype_score": hype,
        "regime": regime
    })

    if event:
        print(f"\n🚨 EVENT: {event}")

        log_event(event, date)

        msg = f"""AI Bubble Alert

Event: {event}
Regime: {regime}
Bubble Score: {bubble}
Hype Score: {hype}
Time: {date}
"""

        send_telegram(msg)
        send_webhook(event, regime, bubble, hype, date)

    else:
        print("No significant event")

    print("\n=== DONE ===")

# ================================
# RUN
# ================================

if __name__ == "__main__":
    main()
