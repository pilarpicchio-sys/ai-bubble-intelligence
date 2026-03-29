import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go

# ================================
# CONFIG
# ================================

st.set_page_config(layout="wide")

CSV_FILE = Path("bubble_risk_history.csv")
st_autorefresh(interval=10000, key="refresh")

# ================================
# LOAD DATA
# ================================

@st.cache_data(ttl=5)
def load_data():
    if not CSV_FILE.exists():
        return None

    df = pd.read_csv(CSV_FILE, sep=";")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["bubble_score"] = pd.to_numeric(df["bubble_score"], errors="coerce")
    df["hype_score"] = pd.to_numeric(df["hype_score"], errors="coerce")

    df = df.dropna()
    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    return df

# ================================
# CORE LOGIC
# ================================

def forecast_probability(df):
    if len(df) < 10:
        return None

    y = df["bubble_score"]
    short = y.rolling(3).mean().iloc[-1]
    long = y.rolling(10).mean().iloc[-1]
    vol = y.rolling(10).std().iloc[-1]

    strength = (short - long) / (vol + 1e-6)
    return 50 + np.tanh(strength) * 50

def generate_signal(score, hype, prob):
    if prob is None:
        return "NEUTRAL"

    composite = score * 0.5 + hype * 2 + (prob / 100) * 2

    if composite > 6:
        return "BUBBLE"
    elif composite > 5:
        return "HIGH RISK"
    elif composite > 3.5:
        return "CAUTION"
    else:
        return "LOW RISK"

def detect_regime(score, hype):
    if hype > 2 and score > 4:
        return "LATE BUBBLE"
    if score > 5:
        return "UNWIND"
    if hype > 2:
        return "BUILDUP"
    return "NORMAL"

# ================================
# MAIN
# ================================

st.title("AI Bubble Intelligence")
st.caption("Detect AI bubbles before they burst")

df = load_data()

if df is None or len(df) == 0:
    st.warning("No data available")
    st.stop()

latest = df.iloc[-1]

risk = latest["bubble_score"]
hype = latest["hype_score"]

prob = forecast_probability(df)
signal = generate_signal(risk, hype, prob)
regime = detect_regime(risk, hype)

# ================================
# HERO
# ================================

st.markdown(f"""
### {signal}
Regime: {regime} | Confidence: {int(prob) if prob else 'N/A'}%
""")

# 🔥 LAST UPDATE
st.caption(f"Last update: {latest['date']}")

# ================================
# TIMELINE
# ================================

st.subheader("Recent Signal Changes")

signals = []

for i in range(10, len(df)):
    sub = df.iloc[:i]
    prob_i = forecast_probability(sub)

    sig = generate_signal(
        sub.iloc[-1]["bubble_score"],
        sub.iloc[-1]["hype_score"],
        prob_i
    )

    signals.append((df.iloc[i]["date"], sig))

for d, s in signals[-8:]:
    st.write(f"{d.strftime('%Y-%m-%d %H:%M:%S')} → {s}")

# ================================
# CHART (🔥 FIX VISIVO)
# ================================

fig = go.Figure()

# Risk
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["bubble_score"],
    name="Risk"
))

# 🔥 Hype scalato per visibilità
fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["hype_score"] * 5,
    name="Hype (scaled)",
    line=dict(dash="dot")
))

fig.update_layout(
    template="plotly_dark",
    height=400,
    xaxis=dict(type="date")
)

st.plotly_chart(fig, use_container_width=True)

# ================================
# DATA
# ================================

with st.expander("Advanced data"):
    st.dataframe(df.tail(20), use_container_width=True)