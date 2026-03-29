import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

# ================================
# CONFIG
# ================================

st.set_page_config(layout="wide")

CSV_FILE = Path("bubble_risk_history.csv")

# ================================
# LOAD DATA
# ================================

@st.cache_data(ttl=10)
def load_data():
    if not CSV_FILE.exists():
        return None

    df = pd.read_csv(CSV_FILE, sep=";")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["bubble_score"] = pd.to_numeric(df["bubble_score"], errors="coerce")
    df["hype_score"] = pd.to_numeric(df["hype_score"], errors="coerce")

    df = df.dropna()
    df = df.sort_values("date")

    return df

# ================================
# STYLE
# ================================

def regime_style(regime):
    return {
        "LOW RISK": ("🟢", "#16a34a"),
        "CAUTION": ("🟡", "#f59e0b"),
        "HIGH RISK": ("🔴", "#dc2626"),
        "BUBBLE": ("🚨", "#7c3aed")
    }.get(regime, ("⚪", "#999"))

# ================================
# REGIME DURATION
# ================================

def regime_duration(df):
    if "regime" not in df.columns or len(df) < 2:
        return "N/A"

    current = df.iloc[-1]["regime"]
    count = 0

    for r in reversed(df["regime"]):
        if r == current:
            count += 1
        else:
            break

    return f"{count} periods"

# ================================
# ANALYST COMMENTARY (🔥 CORE)
# ================================

def generate_commentary(df):
    if len(df) < 3:
        return "Insufficient data."

    last = df.iloc[-1]
    prev = df.iloc[-2]

    delta = last["bubble_score"] - prev["bubble_score"]
    hype = last["hype_score"]

    regime = last.get("regime", "N/A")

    # STRUCTURED ANALYSIS
    if regime == "LOW RISK":
        return "Macro and narrative signals remain aligned. No evidence of speculative excess. Environment stable."

    if regime == "CAUTION":
        return "Early divergence between narrative intensity and macro stability. Monitoring phase. No structural stress yet."

    if regime == "HIGH RISK":
        if delta > 0:
            return "Risk is building with increasing momentum. Narrative expansion not fully supported by macro conditions. Fragility rising."
        else:
            return "Elevated risk but stabilizing. No further acceleration. Monitoring for potential reversal."

    if regime == "BUBBLE":
        return "Late-stage dynamics. Narrative dominance over fundamentals. Conditions consistent with terminal phase behavior."

    return "No clear regime identified."

# ================================
# APP
# ================================

st.title("AI Bubble Intelligence")

df = load_data()

if df is None or len(df) == 0:
    st.warning("No data available")
    st.stop()

latest = df.iloc[-1]

regime = latest.get("regime", "N/A")
emoji, color = regime_style(regime)

# ================================
# HERO
# ================================

st.markdown(f"""
<div style="padding:30px;border-radius:15px;background:{color};color:white;text-align:center;">
<h1 style="margin:0;">{emoji} {regime}</h1>
</div>
""", unsafe_allow_html=True)

# ================================
# KPI STRIP
# ================================

col1, col2, col3 = st.columns(3)

col1.metric("Bubble Score", round(latest["bubble_score"], 2))
col2.metric("Hype Score", round(latest["hype_score"], 2))
col3.metric("Regime Duration", regime_duration(df))

# ================================
# ANALYST VIEW (🔥 DIFFERENZA VERA)
# ================================

st.subheader("Analyst Commentary")

st.write(generate_commentary(df))

# ================================
# RISK DECOMPOSITION
# ================================

st.subheader("Risk Decomposition")

col4, col5 = st.columns(2)

col4.metric("Macro Proxy (Score)", round(latest["bubble_score"], 2))
col5.metric("Narrative Pressure", round(latest["hype_score"], 2))

# ================================
# GAUGE
# ================================

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=latest["bubble_score"],
    gauge={
        "axis": {"range": [0, 6]},
        "bar": {"color": color},
    }
))

fig_gauge.update_layout(height=250)
st.plotly_chart(fig_gauge, use_container_width=True)

# ================================
# CHART
# ================================

st.subheader("Dynamics")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["bubble_score"],
    name="Risk",
    line=dict(width=3)
))

fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["hype_score"] * 5,
    name="Hype",
    line=dict(dash="dot")
))

fig.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig, use_container_width=True)

# ================================
# EVENT LOG
# ================================

st.subheader("Regime Log")

if "regime" in df.columns:
    recent = df.tail(8)

    for _, row in recent.iterrows():
        e, _ = regime_style(row["regime"])
        st.write(f"{e} {row['regime']} — {row['date']}")

# ================================
# FOOTER
# ================================

st.caption("Designed for structural regime detection.")
