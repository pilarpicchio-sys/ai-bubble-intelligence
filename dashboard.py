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
# REGIME SAFE (🔥 FIX)
# ================================

if "regime" in df.columns:
    regime = latest.get("regime", "N/A")
else:
    regime = "N/A"

emoji, color = regime_style(regime)

# ================================
# HERO
# ================================

st.markdown("## 🧠 AI Regime")

st.markdown(f"""
<div style="padding:20px;border-radius:12px;background:{color}20;">
<h2 style="color:{color};margin:0;">{emoji} {regime}</h2>
<p style="margin:0;">Bubble Score: {round(latest["bubble_score"],2)} | Hype: {round(latest["hype_score"],2)}</p>
</div>
""", unsafe_allow_html=True)

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
    st.write("Regime not available yet (older data).")

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
# REGIME TIMELINE (🔥 FIXATA)
# ================================

st.subheader("Regime Timeline")

if "regime" in df.columns:

    timeline = df[["date", "regime"]].tail(10)

    for _, row in timeline.iterrows():
        e, _ = regime_style(row["regime"])
        st.write(f"{row['date']} → {e} {row['regime']}")

else:
    st.info("Regime tracking started recently. No historical regime data yet.")

# ================================
# DATA
# ================================

with st.expander("Advanced data"):
    st.dataframe(df.tail(20), use_container_width=True)

# ================================
# FOOTER
# ================================

st.caption("System designed to detect regime shifts, not short-term noise.")
