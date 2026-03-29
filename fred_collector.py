from fredapi import Fred
import pandas as pd
import os
from datetime import datetime

FRED_API_KEY = "2bba47361c7e947fcd62c7db58fe1212"

fred = Fred(api_key=FRED_API_KEY)

SERIES = {
    "productivity_yoy": "PRS85006091",
    "unit_labor_cost_yoy": "PRS85006111",
    "consumer_sentiment": "UMCSENT",
    "vix": "VIXCLS",
    "high_yield_spread": "BAMLH0A0HYM2"
}

def get_latest_fred_data():
    results = {}

    for name, series_id in SERIES.items():
        try:
            data = fred.get_series(series_id)
            data = data.dropna()
            latest_date = data.index[-1]
            latest_value = data.iloc[-1]

            results[name] = {
                "series_id": series_id,
                "date": latest_date.strftime("%Y-%m-%d"),
                "value": round(float(latest_value), 2)
            }
        except Exception as e:
            results[name] = {
                "series_id": series_id,
                "date": None,
                "value": None,
                "error": str(e)
            }

    return results

def evaluate_bubble_risk(data):
    score = 0
    notes = []

    productivity = data.get("productivity_yoy", {}).get("value")
    ulc = data.get("unit_labor_cost_yoy", {}).get("value")
    sentiment = data.get("consumer_sentiment", {}).get("value")
    vix = data.get("vix", {}).get("value")
    hy = data.get("high_yield_spread", {}).get("value")

    # Productivity
    if productivity is not None:
        if productivity < 1.0:
            score += 2
            notes.append("Produttività debole: l'AI hype potrebbe non riflettersi nei dati reali.")
        elif productivity < 2.0:
            score += 1
            notes.append("Produttività moderata: benefici AI ancora poco visibili.")
        else:
            notes.append("Produttività discreta: alcuni benefici reali potrebbero emergere.")

    # Unit Labor Cost
    if ulc is not None:
        if ulc > 3.5:
            score += 2
            notes.append("Costo del lavoro elevato: l'efficienza promessa dall'AI non si vede ancora.")
        elif ulc > 2.0:
            score += 1
            notes.append("Costo del lavoro ancora relativamente alto.")

    # Consumer Sentiment
    if sentiment is not None:
        if sentiment < 60:
            score += 2
            notes.append("Sentiment consumatori debole: possibile disallineamento con narrativa ottimista.")
        elif sentiment < 70:
            score += 1
            notes.append("Sentiment moderato: entusiasmo non pienamente confermato dall'economia reale.")

    # VIX
    if vix is not None:
        if vix < 15:
            score += 2
            notes.append("VIX molto basso: compiacenza di mercato potenzialmente pericolosa.")
        elif vix < 20:
            score += 1
            notes.append("VIX relativamente basso: mercato ancora fiducioso.")

    # High Yield Spread
    if hy is not None:
        if hy < 3.0:
            score += 2
            notes.append("Spread high yield molto compresso: possibile eccesso di rischio.")
        elif hy < 4.0:
            score += 1
            notes.append("Spread high yield relativamente basso.")
    else:
        notes.append("High Yield Spread non disponibile oggi.")

    # Risk label
    if score <= 2:
        risk = "Scarso"
    elif score <= 5:
        risk = "Medio"
    else:
        risk = "Alto"

    return score, risk, notes

def save_to_excel(data, score, risk, notes):
    today = datetime.now().strftime("%Y-%m-%d")

    row = {
        "analysis_date": today,
        "productivity_yoy": data.get("productivity_yoy", {}).get("value"),
        "unit_labor_cost_yoy": data.get("unit_labor_cost_yoy", {}).get("value"),
        "consumer_sentiment": data.get("consumer_sentiment", {}).get("value"),
        "vix": data.get("vix", {}).get("value"),
        "high_yield_spread": data.get("high_yield_spread", {}).get("value"),
        "bubble_risk_score": score,
        "bubble_risk_level": risk,
        "notes": " | ".join(notes)
    }

    file_name = "bubble_risk_history.xlsx"

    if os.path.exists(file_name):
        df_existing = pd.read_excel(file_name)
        df_new = pd.concat([df_existing, pd.DataFrame([row])], ignore_index=True)
    else:
        df_new = pd.DataFrame([row])

    df_new.to_excel(file_name, index=False)
    print(f"\nDati salvati in {file_name}")

if __name__ == "__main__":
    data = get_latest_fred_data()
    score, risk, notes = evaluate_bubble_risk(data)

    print("\n=== DATI FRED ===")
    print(data)

    print("\n=== RISCHIO BOLLA AI ===")
    print(f"Bubble Risk Score: {score}")
    print(f"Livello di rischio: {risk}")

    print("\n=== NOTE ===")
    for note in notes:
        print(f"- {note}")

    save_to_excel(data, score, risk, notes)