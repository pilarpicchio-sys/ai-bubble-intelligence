import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go

# ================================
# CONFIG
# ================================

st.set_page_config(layout="wide")

CSV_FILE = Path("bubble_risk_history.csv")
STATE_FILE = Path("regime_state.txt")

# ================================
# LOAD DATA
# ================================

@st.cache_data(ttl=10)
def load_data():
    if not CSV_FILE.exists():
        return None

    try:
        df = pd.read_csv(CSV_FILE, sep=";")

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["bubble_score"] = pd.to_numeric(df["bubble_score"], errors="coerce")
        df["hype_score"] = pd.to_numeric(df["hype_score"], errors="coerce")

        df = df.dropna()
        df = df.sort_values("date")

        return df

    except:
        return None

# ================================
# SAFE REGIME LOADER (🔥 FIX)
# ================================

def load_regime_state():
    if not STATE_FILE.exists():
        return "N/A", None

    try:
        raw = STATE_FILE.read_text().strip()

        parts = raw.split("|")

        if len(parts) != 2:
            return "N/A", None

        regime = parts[0].strip()

        try:
            time = datetime.fromisoformat(parts[1].strip())
        except:
            time = None

        return regime, time

    except:
        return "N/A", None

# ================================
# STYLE
# ================================

def regime_emoji(regime):
    return {
        "LOW RISK": "🟢",
        "CAUTION": "🟡",
        "HIGH RISK": "🔴",
        "BUBBLE": "🚨"
    }.get(regime, "⚪")

# ================================
# APP
# ================================

st.title("AI Bubble Intelligence")
st.caption("Detect structural shifts in AI-driven market risk")

df = load_data()

if df is None or len(df) == 0:
    st.warning("No data available")
    st.stop()

latest = df.iloc[-1]

# ================================
# REGIME
# ================================

regime, last_change = load_regime_state()
emoji = regime_emoji(regime)

# ================================
# HERO
# ================================

st.markdown("## 🧠 Regime Status")

st.markdown(f"### {emoji} {regime}")

col1, col2 = st.columns(2)

col1.metric("Bubble Score", round(latest["bubble_score"], 2))
col2.metric("Hype Score", round(latest["hype_score"], 2))

if last_change:
    st.caption(f"Last change: {last_change.strftime('%Y-%m-%d %H:%M')}")

st.markdown("---")

# ================================
# INTERPRETATION
# ================================

st.subheader("Interpretation")

if regime == "LOW RISK":
    st.write("Market conditions are stable. No bubble dynamics detected.")

elif regime == "CAUTION":
    st.write("Early imbalance signals. Narrative and macro are starting to diverge.")

elif regime == "HIGH RISK":
    st.write("Elevated risk environment. Market fragility increasing.")

elif regime == "BUBBLE":
    st.write("Late-stage bubble dynamics. High probability of correction.")

else:
    st.write("Regime not available.")

# ================================
# CHART
# ================================

st.subheader("Risk & Hype Dynamics")

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
    name="Hype (scaled)",
    line=dict(dash="dot")
))

fig.update_layout(
    template="plotly_dark",
    height=400,
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)

# ================================
# DATA
# ================================

st.subheader("Recent Data")

for _, row in df.tail(8).iterrows():
    st.write(f"{row['date']} → Score: {row['bubble_score']}")

with st.expander("Advanced data"):
    st.dataframe(df.tail(20), use_container_width=True)

# ================================
# FOOTER
# ================================

st.caption("System designed to detect regime shifts, not short-term noise.")
