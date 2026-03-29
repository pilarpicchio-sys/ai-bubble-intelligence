import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from fredapi import Fred
from dotenv import load_dotenv
from news_analyzer import analyze_news

# ================================
# CONFIG
# ================================

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")
fred = Fred(api_key=FRED_API_KEY)

CSV_FILE = Path("bubble_risk_history.csv")

# ================================
# FRED DATA
# ================================

def collect_fred_data():
    series_ids = {
        "vix": "VIXCLS",
        "spread": "BAMLH0A0HYM2",
        "sentiment": "UMCSENT"
    }

    data = {}

    for key, sid in series_ids.items():
        try:
            data[key] = fred.get_series(sid)
        except:
            data[key] = pd.Series(dtype=float)

    return data

# ================================
# HELPERS
# ================================

def zscore(series):
    s = series.dropna()
    if len(s) < 10:
        return 0
    return (s.iloc[-1] - s.mean()) / (s.std() + 1e-6)

def compute_hype(sentiment, volume):
    return round(np.tanh(sentiment)*0.6 + np.log1p(volume)*0.4, 3)

# ================================
# SCORE
# ================================

def evaluate_score(data, hype):

    score = 0

    score += max(0, zscore(data["vix"])) * 1.5
    score += max(0, zscore(data["spread"]))
    score += max(0, -zscore(data["sentiment"]))

    score += np.tanh(hype) * 2

    return round(score, 2)

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
# SAVE CSV
# ================================

def save_to_csv(row):

    if CSV_FILE.exists():
        df = pd.read_csv(CSV_FILE, sep=";")
        if row["date"] in df["date"].values:
            return

    import csv

    write_header = not CSV_FILE.exists()

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys(), delimiter=";")

        if write_header:
            writer.writeheader()

        writer.writerow(row)

# ================================
# MAIN
# ================================

def main():

    print("\n=== AI BUBBLE AGENT (CSV REGIME) ===\n")

    data = collect_fred_data()

    headlines, sentiment, volume = analyze_news()

    hype = compute_hype(sentiment, volume)
    score = evaluate_score(data, hype)

    regime = classify_regime(score)

    row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bubble_score": score,
        "hype_score": hype,
        "regime": regime
    }

    print(row)

    save_to_csv(row)

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
