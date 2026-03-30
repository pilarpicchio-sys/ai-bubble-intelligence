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

# ================================
# ENV
# ================================

def get_env(key):
    val = os.getenv(key)
    return val.strip() if val else None

FRED_API_KEY = get_env("FRED_API_KEY")

# ================================
# DATA
# ================================

def fred(series):

    if not FRED_API_KEY:
        fallback = {
            "VIXCLS": 15,
            "FEDFUNDS": 2.5,
            "M2SL": 21000
        }
        return fallback.get(series, 0)

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


def sp500():
    d = yf.download("^GSPC", period="6mo", interval="1d", progress=False)
    return d["Close"]

# ================================
# FEATURES
# ================================

def compute_features():

    sp = sp500()

    return {
        "spx": float(sp.iloc[-1].item()),
        "ret": float(sp.iloc[-60:].pct_change().sum().item()),
        "trend": float(sp.iloc[-1] / sp.iloc[-200:].mean()) if len(sp) > 200 else 1,
        "vix": fred("VIXCLS"),
        "rate": fred("FEDFUNDS"),
        "m2": fred("M2SL"),
    }

# ================================
# SCORE
# ================================

def compute_score(f):

    score = 0

    if f["m2"] > 20000:
        score += 2

    if f["vix"] < 15:
        score += 2

    if f["rate"] < 3:
        score += 1

    if f["ret"] > 0.1:
        score += 1

    return min(score, 6)

def regime(score):
    if score < 2: return "Low"
    if score < 4: return "Medium"
    return "High"

# ================================
# SAVE (COMPATIBILE STREAMLIT)
# ================================

def save():

    f = compute_features()

    score = compute_score(f)
    reg = regime(score)

    row = pd.DataFrame([{
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bubble_score": score,
        "risk_level": reg,
        "news_sentiment": 0.0,
        "news_volume": 1,
        "hype_score": round(score / 6, 3)
    }])

    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE, sep=";")
        df = pd.concat([df, row])
    else:
        df = row

    df.to_csv(CSV_FILE, index=False, sep=";")

# ================================
# MAIN
# ================================

def main():

    print("\n=== STREAMLIT AGENT ===\n")

    save()

    print("Data updated successfully")

    print("\n=== DONE ===\n")


if __name__ == "__main__":
    main()