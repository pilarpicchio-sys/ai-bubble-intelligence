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
FRED_API_KEY = get_env("FRED_API_KEY")

# ================================
# FRED DATA
# ================================

def get_fred_series(series_id):
    url = f"https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1
    }
    r = requests.get(url, params=params)
    data = r.json()
    return float(data["observations"][0]["value"])

# ================================
# MACRO INDICATORS
# ================================

def get_macro_data():
    try:
        m2 = get_fred_series("M2SL")              # liquidità
        vix = get_fred_series("VIXCLS")           # volatilità
        rate = get_fred_series("FEDFUNDS")        # tassi

        return {
            "m2": m2,
            "vix": vix,
            "rate": rate
        }
    except Exception as e:
        print("FRED error:", e)
        return None

# ================================
# SCORE MACRO
# ================================

def compute_macro_score(data):

    if data is None:
        return 2.5

    score = 0

    # liquidità alta → rischio bolla
    if data["m2"] > 20000:
        score += 2

    # volatilità bassa → euforia
    if data["vix"] < 15:
        score += 2

    # tassi bassi → fuel
    if data["rate"] < 2:
        score += 1

    return min(score, 6)

# ================================
# REGIME
# ================================

def classify_regime(score):

    if score < 2:
        return "LOW RISK"
    elif score < 3.5:
        return "CAUTION"
    elif score < 5:
        return "HIGH RISK"
    else:
        return "BUBBLE"

# ================================
# HISTORY
# ================================

def append_csv(date, score, regime):
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w") as f:
            f.write("date;score;regime\n")

    with open(CSV_FILE, "a") as f:
        f.write(f"{date};{score};{regime}\n")

def load_history():
    if not CSV_FILE.exists():
        return None
    return pd.read_csv(CSV_FILE, sep=";")

# ================================
# TREND + PERSISTENCE
# ================================

def compute_trend(df):
    if df is None or len(df) < 3:
        return "insufficient"

    vals = df.tail(3)["score"].astype(float).values

    if vals[2] > vals[1] > vals[0]:
        return "uptrend"
    elif vals[2] < vals[1] < vals[0]:
        return "downtrend"
    return "sideways"

def compute_persistence(df):
    if df is None:
        return 0

    count = 0
    for val in reversed(df["score"].astype(float).values):
        if val >= 3.5:
            count += 1
        else:
            break

    return count

# ================================
# ALERT LOGIC
# ================================

def should_send_alert(regime, trend, persistence, score):

    if regime == "BUBBLE":
        return True

    if persistence >= 3 and regime == "HIGH RISK":
        return True

    if trend == "uptrend" and score > 4:
        return True

    return False

# ================================
# AI ANALYSIS
# ================================

def generate_ai_text(regime, score, macro, trend, persistence):

    if not OPENAI_API_KEY:
        return "AI unavailable"

    from openai import OpenAI
    client = OpenAI()

    prompt = f"""
You are a macro analyst.

Data:
Regime: {regime}
Score: {score}
Trend: {trend}
Persistence: {persistence}
M2: {macro['m2']}
VIX: {macro['vix']}
Rates: {macro['rate']}

Write a professional report:

TITLE: ...
---
Overview:
...
Market Dynamics:
...
Risk Outlook:
...
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content.strip()

# ================================
# WEBHOOK
# ================================

def send_webhook(payload):
    if not ZAPIER_WEBHOOK:
        print("No webhook")
        return

    r = requests.post(ZAPIER_WEBHOOK, json=payload)
    print("Webhook:", r.status_code)

# ================================
# MAIN
# ================================

def main():

    print("\n=== AI MACRO BUBBLE AGENT ===\n")

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    macro = get_macro_data()
    score = compute_macro_score(macro)
    regime = classify_regime(score)

    df = load_history()

    trend = compute_trend(df)
    persistence = compute_persistence(df)

    append_csv(date, score, regime)

    print({
        "regime": regime,
        "score": score,
        "trend": trend,
        "persistence": persistence
    })

    if should_send_alert(regime, trend, persistence, score):

        analysis = generate_ai_text(regime, score, macro, trend, persistence)

        payload = {
            "date": date,
            "regime": regime,
            "score": score,
            "trend": trend,
            "persistence": persistence,
            "analysis": analysis
        }

        send_webhook(payload)

    else:
        print("No alert")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()