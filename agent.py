import pandas as pd
from datetime import datetime
from pathlib import Path
import requests
import os
import yfinance as yf
import matplotlib.pyplot as plt

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
CHART_FILE = BASE_DIR / "bubble_chart.png"

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

def get_fred(series):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1
    }
    r = requests.get(url, params=params)
    return float(r.json()["observations"][0]["value"])

# ================================
# MARKET DATA
# ================================

def get_sp500():
    data = yf.download("^GSPC", period="5d", interval="1d", progress=False)
    return float(data["Close"].iloc[-1])

# ================================
# MACRO
# ================================

def get_macro():

    try:
        return {
            "m2": get_fred("M2SL"),
            "vix": get_fred("VIXCLS"),
            "rate": get_fred("FEDFUNDS"),
            "sp500": get_sp500()
        }
    except Exception as e:
        print("Data error:", e)
        return None

# ================================
# SCORING
# ================================

def compute_score(m):

    if m is None:
        return 2.5

    score = 0

    # liquidity
    if m["m2"] > 20000:
        score += 2

    # low volatility = complacency
    if m["vix"] < 15:
        score += 2

    # low rates = fuel
    if m["rate"] < 2:
        score += 1

    # high equity level (proxy)
    if m["sp500"] > 4500:
        score += 1

    return min(score, 6)

# ================================
# REGIME
# ================================

def regime(score):
    if score < 2:
        return "LOW RISK"
    elif score < 3.5:
        return "CAUTION"
    elif score < 5:
        return "HIGH RISK"
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
# TREND / PERSISTENCE
# ================================

def trend(df):
    if df is None or len(df) < 3:
        return "insufficient"

    vals = df.tail(3)["score"].astype(float).values

    if vals[2] > vals[1] > vals[0]:
        return "uptrend"
    elif vals[2] < vals[1] < vals[0]:
        return "downtrend"
    return "sideways"

def persistence(df):
    if df is None:
        return 0

    count = 0
    for v in reversed(df["score"].astype(float)):
        if v >= 3.5:
            count += 1
        else:
            break

    return count

# ================================
# ALERT
# ================================

def should_alert(regime, trend, persistence, score):

    if regime == "BUBBLE":
        return True

    if persistence >= 3 and regime == "HIGH RISK":
        return True

    if trend == "uptrend" and score > 4:
        return True

    return False

# ================================
# CHART
# ================================

def generate_chart(df):

    if df is None or len(df) < 2:
        return

    plt.figure()
    plt.plot(df["score"].astype(float))
    plt.title("Bubble Risk Score")
    plt.savefig(CHART_FILE)
    plt.close()

# ================================
# AI REPORT
# ================================

def generate_ai(regime, score, m, trend, persistence):

    if not OPENAI_API_KEY:
        return "AI unavailable"

    from openai import OpenAI
    client = OpenAI()

    prompt = f"""
You are a macro strategist.

Regime: {regime}
Score: {score}
Trend: {trend}
Persistence: {persistence}
M2: {m['m2']}
VIX: {m['vix']}
Rates: {m['rate']}
SP500: {m['sp500']}

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

    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return r.choices[0].message.content.strip()

# ================================
# WEBHOOK
# ================================

def send(payload):

    if not ZAPIER_WEBHOOK:
        print("No webhook")
        return

    r = requests.post(ZAPIER_WEBHOOK, json=payload)
    print("Webhook:", r.status_code)

# ================================
# MAIN
# ================================

def main():

    print("\n=== AI BUBBLE INTELLIGENCE SYSTEM ===\n")

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    m = get_macro()
    score = compute_score(m)
    reg = regime(score)

    df = load_history()

    tr = trend(df)
    pers = persistence(df)

    append_csv(date, score, reg)
    df = load_history()

    generate_chart(df)

    print({
        "regime": reg,
        "score": score,
        "trend": tr,
        "persistence": pers
    })

    if should_alert(reg, tr, pers, score):

        report = generate_ai(reg, score, m, tr, pers)

        payload = {
            "date": date,
            "regime": reg,
            "score": score,
            "trend": tr,
            "persistence": pers,
            "analysis": report
        }

        send(payload)

    else:
        print("No alert")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()