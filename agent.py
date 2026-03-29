import pandas as pd
from datetime import datetime
from pathlib import Path
import requests
import os

# ================================
# FILES
# ================================

CSV_FILE = Path("bubble_risk_history.csv")
STATE_FILE = Path("regime_state.txt")
EVENT_LOG = Path("events.log")

# ================================
# TELEGRAM (SAFE - ENV VARS)
# ================================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("⚠️ Telegram not configured")
        return

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

# ================================
# MODEL
# ================================

def compute_scores():
    bubble_score = 4.46
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
# STATE MANAGEMENT
# ================================

def load_last_regime():
    if not STATE_FILE.exists():
        return None

    content = STATE_FILE.read_text().strip()
    content = content.split("|")[0]

    return content

def save_last_regime(regime):
    STATE_FILE.write_text(regime)

# ================================
# CSV WRITE
# ================================

def append_csv(date, bubble, hype, regime):

    if not CSV_FILE.exists():
        with open(CSV_FILE, "w") as f:
            f.write("date;bubble_score;hype_score;regime\n")

    with open(CSV_FILE, "a") as f:
        f.write(f"{date};{bubble};{hype};{regime}\n")

# ================================
# LOAD LAST ROW
# ================================

def load_last_row():
    if not CSV_FILE.exists():
        return None

    df = pd.read_csv(CSV_FILE, sep=";")

    if len(df) == 0:
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
        delta = new_bubble - prev_bubble

        if delta > 0.5:
            return "RISK SPIKE UP"

        if delta < -0.5:
            return "RISK DROP DOWN"

    return None

# ================================
# EVENT LOG
# ================================

def log_event(event, date):
    with open(EVENT_LOG, "a", encoding="utf-8") as f:
        f.write(f"{date} | {event}\n")

# ================================
# MAIN
# ================================

def main():
    print("\n=== AI BUBBLE AGENT PRO ===\n")

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    bubble, hype, regime = compute_scores()

    prev_regime = load_last_regime()
    last_row = load_last_row()

    prev_bubble = None
    if last_row is not None:
        prev_bubble = last_row["bubble_score"]

    print("DEBUG prev_regime:", prev_regime)

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

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
