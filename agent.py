import pandas as pd
from datetime import datetime
from pathlib import Path
import requests
import os

# ================================
# LOAD ENV
# ================================

BASE_DIR = Path(__file__).parent

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=BASE_DIR / ".env")
except:
    pass

# ================================
# PATHS
# ================================

CSV_FILE = BASE_DIR / "bubble_risk_history.csv"
STATE_FILE = BASE_DIR / "regime_state.txt"

# ================================
# ENV
# ================================

def get_env(key):
    val = os.getenv(key)
    return val.strip() if val else ""

ZAPIER_WEBHOOK = get_env("ZAPIER_WEBHOOK")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")

# ================================
# HISTORY
# ================================

def append_csv(date, bubble, hype, regime):
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w") as f:
            f.write("date;bubble_score;hype_score;regime\n")

    with open(CSV_FILE, "a") as f:
        f.write(f"{date};{bubble};{hype};{regime}\n")

def load_history():
    if not CSV_FILE.exists():
        return None
    return pd.read_csv(CSV_FILE, sep=";")

# ================================
# BUBBLE MODEL
# ================================

def compute_bubble_score(df):

    if df is None or len(df) < 5:
        return 2.5

    recent = df.tail(5)["bubble_score"].astype(float)

    momentum = recent.iloc[-1] - recent.iloc[0]
    accel = recent.iloc[-1] - recent.iloc[-2]

    score = 2.5 + momentum * 0.8 + accel * 1.2
    score = max(0, min(6, score))

    return round(score, 2)

# ================================
# MODEL
# ================================

def compute_scores():

    df = load_history()

    bubble = compute_bubble_score(df)
    hype = 0.4

    if bubble < 2:
        regime = "LOW RISK"
    elif bubble < 3.5:
        regime = "CAUTION"
    elif bubble < 5:
        regime = "HIGH RISK"
    else:
        regime = "BUBBLE"

    return bubble, hype, regime

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
# ALERT LOGIC
# ================================

def should_send_alert(event, regime, bubble, prev_bubble):

    if event is None:
        return False

    if "REGIME CHANGE" in event:
        if "HIGH RISK" in event or "BUBBLE" in event:
            return True

    if prev_bubble is not None:
        delta = bubble - prev_bubble
        if delta > 0.8:
            return True

    if bubble >= 5:
        return True

    return False

# ================================
# AI ARTICLE (PRO)
# ================================

def generate_ai_text(regime, bubble, hype, event):

    if not OPENAI_API_KEY:
        return "AI analysis unavailable"

    try:
        from openai import OpenAI
        client = OpenAI()

        prompt = f"""
You are a financial journalist writing a short market report.

Data:
Regime: {regime}
Bubble Score: {bubble}
Hype Score: {hype}
Event: {event}

Write:

1. A strong headline
2. A structured report with:

Overview:
Market Signals:
Risk Outlook:

Style:
- Professional (Bloomberg / FT style)
- Clear and concise
- 120–180 words
- No bullet points

Format:

TITLE: ...
---
Overview:
...
Market Signals:
...
Risk Outlook:
...
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("AI error:", e)
        return "AI analysis unavailable"

# ================================
# WEBHOOK
# ================================

def send_webhook(payload):
    if not ZAPIER_WEBHOOK:
        print("Webhook not configured")
        return

    try:
        r = requests.post(ZAPIER_WEBHOOK, json=payload, timeout=10)
        print("Webhook status:", r.status_code)
    except Exception as e:
        print("Webhook error:", e)

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
# MAIN
# ================================

def main():

    print("\n=== AI BUBBLE AGENT PRO ===\n")

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    bubble, hype, regime = compute_scores()

    df = load_history()

    prev_regime = load_last_regime()
    prev_bubble = None

    if df is not None and not df.empty:
        prev_bubble = float(df.iloc[-1]["bubble_score"])

    event = detect_event(prev_regime, regime, prev_bubble, bubble)

    append_csv(date, bubble, hype, regime)
    save_last_regime(regime)

    print({
        "regime": regime,
        "bubble": bubble,
        "hype": hype
    })

    if should_send_alert(event, regime, bubble, prev_bubble):

        print("🚨 EVENT:", event)

        analysis = generate_ai_text(regime, bubble, hype, event)

        payload = {
            "date": date,
            "regime": regime,
            "bubble": bubble,
            "hype": hype,
            "event": event,
            "analysis": analysis
        }

        send_webhook(payload)

    else:
        print("No significant event")

    print("\n=== DONE ===")

# ================================
# RUN
# ================================

if __name__ == "__main__":
    main()