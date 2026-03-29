import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
from datetime import datetime

# ================================
# CONFIG
# ================================

st.set_page_config(layout="wide")

CSV_FILE = Path("bubble_risk_history.csv")
STATE_FILE = Path("regime_state.txt")

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
# LOAD REGIME STATE
# ================================

def load_regime_state():
    if not STATE_FILE.exists():
        return None, None

    content = STATE_FILE.read_text().split("|")

    regime = content[0]
    time = datetime.fromisoformat(content[1])

    return regime, time

# ================================
# STYLE HELPERS
# ================================

def regime_color(regime):
    return {
        "LOW RISK": "🟢",
        "CAUTION": "🟡",
        "HIGH RISK": "🔴",
        "BUBBLE": "🚨"
    }.get(regime, "⚪")

# ================================
# MAIN
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

current_regime, last_change = load_regime_state()

emoji = regime_color(current_regime)

# ================================
# HERO (🔥 CORE UI)
# ================================

st.markdown("## 🧠 Regime Status")

st.markdown(f"""
### {emoji} {current_regime or "N/A"}
""")

col1, col2 = st.columns(2)

col1.metric("Bubble Score", round(latest["bubble_score"], 2))
col2.metric("Hype Score", round(latest["hype_score"], 2))

if last_change:
    st.caption(f"Last regime change: {last_change.strftime('%Y-%m-%d %H:%M')}")

st.markdown("---")

# ================================
# INTERPRETATION (🔥 PRODUCT)
# ================================

st.subheader("Interpretation")

if current_regime == "LOW RISK":
    st.write("Macro and narrative conditions remain stable. No significant bubble dynamics detected.")

elif current_regime == "CAUTION":
    st.write("Early signs of imbalance are emerging. Narrative and macro conditions are starting to diverge.")

elif current_regime == "HIGH RISK":
    st.write("Risk conditions are elevated. Market structure shows increasing fragility and potential instability.")

elif current_regime == "BUBBLE":
    st.write("Late-stage bubble dynamics detected. Risk of sharp correction is elevated.")

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
    xaxis=dict(type="date"),
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)

# ================================
# TIMELINE (SIMPLE)
# ================================

st.subheader("Recent Data Points")

recent = df.tail(8)

for _, row in recent.iterrows():
    st.write(f"{row['date'].strftime('%Y-%m-%d %H:%M:%S')} → Score: {row['bubble_score']}")

# ================================
# ADVANCED DATA
# ================================

with st.expander("Advanced data"):
    st.dataframe(df.tail(20), use_container_width=True)

# ================================
# FOOTER
# ================================

st.caption("This model reflects structural shifts, not intraday market noise.")
