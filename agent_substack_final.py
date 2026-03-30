import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import requests
import os
import yfinance as yf
import matplotlib.pyplot as plt

# ================================
# CONFIG
# ================================

BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "bubble_risk_history.csv"
CHART_FILE = BASE_DIR / "bubble_chart.png"

# ================================
# ENV
# ================================

def get_env(key):
    val = os.getenv(key)
    return val.strip() if val else None

FRED_API_KEY = get_env("FRED_API_KEY")
OPENAI_API_KEY = get_env("OPENAI_API_KEY")
ZAPIER_WEBHOOK = get_env("ZAPIER_WEBHOOK")

# ================================
# DATA
# ================================

def fred(series):

    if not FRED_API_KEY:
        print(f"[WARN] No FRED key → fallback for {series}")
        fallback = {
            "VIXCLS": 15,
            "FEDFUNDS": 2.5,
            "M2SL": 21000
        }
        return fallback.get(series, 0)

    try:
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

    except Exception as e:
        print("[ERROR] FRED:", e)
        return 0


def sp500():

    try:
        d = yf.download("^GSPC", period="6mo", interval="1d", progress=False)

        if d.empty:
            raise ValueError("Empty data")

        return d["Close"]

    except Exception as e:
        print("[WARN] yfinance fallback:", e)
        return pd.Series([5000] * 200)

# ================================
# FEATURES
# ================================

def compute_features():

    sp = sp500()

    sp_last = float(sp.iloc[-1].item())
    sp_ret = float(sp.iloc[-60:].pct_change().sum().item())

    return {
        "spx": sp_last,
        "spx_3m_return": sp_ret,
        "spx_trend": float(sp_last / sp.iloc[-200:].mean()) if len(sp) > 200 else 1,
        "vix": fred("VIXCLS"),
        "rate": fred("FEDFUNDS"),
        "m2": fred("M2SL"),
    }

# ================================
# FACTORS
# ================================

def factor_liquidity(f):
    return 1 if f["m2"] > 20000 else 0.5 if f["m2"] > 18000 else 0

def factor_volatility(f):
    return 1 if f["vix"] < 14 else 0.5 if f["vix"] < 18 else 0

def factor_rates(f):
    return 1 if f["rate"] < 3 else 0

def factor_momentum(f):
    return 1 if f["spx_3m_return"] > 0.2 else 0.5 if f["spx_3m_return"] > 0.1 else 0

def factor_trend(f):
    return 1 if f["spx_trend"] > 1.1 else 0

FACTORS = [
    factor_liquidity,
    factor_volatility,
    factor_rates,
    factor_momentum,
    factor_trend
]

# ================================
# SCORE
# ================================

def compute_score(f):
    raw = sum(func(f) for func in FACTORS)
    return round((raw / len(FACTORS)) * 100, 2)

def regime(score):
    if score < 30: return "LOW RISK"
    if score < 50: return "CAUTION"
    if score < 70: return "HIGH RISK"
    return "BUBBLE"

# ================================
# HISTORY
# ================================

def load():
    if not CSV_FILE.exists():
        return None
    return pd.read_csv(CSV_FILE, sep=";")

def save(date, score, reg):

    row = pd.DataFrame([{
        "date": date,
        "score": score,
        "regime": reg
    }])

    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE, sep=";")
        df = pd.concat([df, row])
    else:
        df = row

    df.to_csv(CSV_FILE, index=False, sep=";")

# ================================
# ANALYTICS
# ================================

def trend(df):
    if df is None or len(df) < 5:
        return "building"

    vals = df["score"].astype(float).tail(5)
    slope = np.polyfit(range(len(vals)), vals, 1)[0]

    if slope > 2: return "accelerating"
    if slope < -2: return "cooling"
    return "stable"

def persistence(df):
    if df is None:
        return 0

    count = 0
    for v in reversed(df["score"].astype(float)):
        if v > 60:
            count += 1
        else:
            break
    return count

# ================================
# DRIVERS
# ================================

def drivers(f):
    d = []

    if f["vix"] < 16:
        d.append("compressed volatility")

    if f["spx_3m_return"] > 0.1:
        d.append("strong momentum")
    elif f["spx_3m_return"] < -0.05:
        d.append("negative momentum")

    if f["rate"] < 3:
        d.append("accommodative rates")

    if f["spx_trend"] > 1.05:
        d.append("extended trend")

    return d

# ================================
# CHART
# ================================

def chart(df):

    if df is None or len(df) < 2:
        return

    plt.figure(figsize=(10,5))

    x = range(len(df))
    y = df["score"].astype(float)

    plt.plot(x, y, linewidth=2)

    plt.axhline(30, linestyle="--")
    plt.axhline(50, linestyle="--")
    plt.axhline(70, linestyle="--")

    plt.title("Bubble Risk Score")

    plt.tight_layout()
    plt.savefig(CHART_FILE)
    plt.close()

# ================================
# AI REPORT
# ================================

def ai_report(score, reg, tr, pers, drv):

    if not OPENAI_API_KEY:
        return f"""
TITLE: Risk is building, not breaking

OVERVIEW:
Risk conditions remain {reg.lower()} with gradual pressure building.

WHAT IS HAPPENING:
- Score at {score}
- Trend is {tr}
- Persistence at {pers}
- Drivers: {", ".join(drv)}

RISK TAKE:
Markets are not breaking, but risk is quietly rising.
"""

    from openai import OpenAI
    client = OpenAI()

    prompt = f"""
You are a macro strategist writing for Substack.

Be sharp and concise.

Score: {score}
Regime: {reg}
Trend: {tr}
Drivers: {drv}
"""

    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return r.choices[0].message.content.strip()

# ================================
# SEND
# ================================

def send_email(payload):

    if not ZAPIER_WEBHOOK:
        print("\n[INFO] No webhook → printing instead\n")
        print(payload)
        return

    try:
        r = requests.post(ZAPIER_WEBHOOK, json=payload)
        print("Webhook status:", r.status_code)

    except Exception as e:
        print("[ERROR] Webhook:", e)

# ================================
# MAIN
# ================================

def main():

    print("\n=== SUBSTACK AGENT FINAL ===\n")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    f = compute_features()
    score = compute_score(f)
    reg = regime(score)

    df = load()

    tr = trend(df)
    pers = persistence(df)
    drv = drivers(f)

    save(now, score, reg)
    df = load()

    chart(df)

    report = ai_report(score, reg, tr, pers, drv)

    payload = {
        "date": now,
        "score": score,
        "regime": reg,
        "trend": tr,
        "persistence": pers,
        "drivers": ", ".join(drv),
        "report": report
    }

    print("RESULT:", payload)

    send_email(payload)

    print("\n=== DONE ===\n")


if __name__ == "__main__":
    main()