# ================================
# AI BUBBLE AGENT PRO (CLEAN VERSION)
# ================================

import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from fredapi import Fred
from dotenv import load_dotenv
from send_email import send_email
from news_analyzer import analyze_news
from ai_report import generate_ai_report

# ================================
# CONFIG
# ================================

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")

fred = Fred(api_key=FRED_API_KEY)

CSV_FILE = Path("bubble_risk_history.csv")

# ================================
# UTILS
# ================================

def safe_last(series):
    s = series.dropna()
    if len(s) == 0:
        return None
    return s.iloc[-1]

def zscore(series):
    s = series.dropna()
    if len(s) < 10:
        return 0
    return (s.iloc[-1] - s.mean()) / (s.std() + 1e-6)

# ================================
# FRED DATA
# ================================

def collect_fred_data():

    series_ids = {
        "productivity": "PRS85006091",
        "unit_labor_cost": "PRS85006111",
        "consumer_sentiment": "UMCSENT",
        "vix": "VIXCLS",
        "high_yield_spread": "BAMLH0A0HYM2"
    }

    data = {}

    for key, sid in series_ids.items():
        try:
            data[key] = fred.get_series(sid)
        except:
            data[key] = pd.Series(dtype=float)

    return data

# ================================
# HYPE MODEL
# ================================

def compute_hype(sentiment, volume):

    hype = (
        np.tanh(sentiment) * 0.6 +
        np.log1p(volume) * 0.4
    )

    return round(hype, 3)

# ================================
# MACRO ENGINE
# ================================

def evaluate_bubble_risk(fred_data, hype):

    score = 0

    score += max(0, zscore(fred_data["vix"])) * 1.5
    score += max(0, zscore(fred_data["high_yield_spread"]))
    score += max(0, -zscore(fred_data["consumer_sentiment"]))

    try:
        prod = safe_last(fred_data["productivity"])
        labor = safe_last(fred_data["unit_labor_cost"])

        if prod and labor and prod < labor:
            score += 1
    except:
        pass

    score += np.tanh(hype) * 2

    level = (
        "Basso" if score < 2 else
        "Medio" if score < 4 else
        "Alto"
    )

    return round(score, 2), level

# ================================
# SAVE CSV (ANTI-DUPLICATE)
# ================================

def save_to_csv(data):

    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE, sep=";")

        # evita duplicati stesso timestamp
        if data["date"] in df["date"].values:
            return

    write_header = not CSV_FILE.exists()

    import csv
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys(), delimiter=';')

        if write_header:
            writer.writeheader()

        writer.writerow(data)

# ================================
# MAIN
# ================================

def main():

    print("\n=== AI BUBBLE AGENT PRO ===\n")

    # FRED
    fred_data = collect_fred_data()

    # NEWS
    headlines, sentiment, volume = analyze_news()

    # HYPE
    hype = compute_hype(sentiment, volume)

    print("Hype:", hype)

    # MACRO RISK
    score, level = evaluate_bubble_risk(fred_data, hype)

    print("Risk:", score, level)

    # SAVE DATA (🔥 FIX TIMESTAMP)
    data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bubble_score": score,
        "risk_level": level,
        "news_sentiment": sentiment,
        "news_volume": volume,
        "hype_score": hype
    }

    save_to_csv(data)

    # REPORT
    report = generate_ai_report(
        fred_data,
        score,
        level,
        headlines,
        sentiment
    )

    # EMAIL
    send_email(
        subject=f"AI Bubble Agent - {level}",
        body=report,
        to_email=EMAIL_ADDRESS
    )

    print("\n=== DONE ===")

# ================================
# RUN
# ================================

if __name__ == "__main__":
    main()