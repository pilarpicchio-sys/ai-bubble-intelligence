import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

# ================================
# CONFIG
# ================================

st.set_page_config(layout="wide")

BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / "bubble_risk_history.csv"

# ================================
# LOAD DATA (USA SOLO MODELLO NUOVO)
# ================================

@st.cache_data(ttl=10)
def load_data():
    if not CSV_FILE.exists():
        return None

    try:
        df = pd.read_csv(CSV_FILE, sep=";")

        # 🔥 tieni solo righe con score (modello nuovo)
        df = df[df["score"].notna()]

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["score"] = pd.to_numeric(df["score"], errors="coerce")

        df = df.dropna(subset=["date", "score"])
        df = df.sort_values("date")

        return df

    except Exception as e:
        st.error(f"Data error: {e}")
        return None

# ================================
# REGIME (0–100)
# ================================

def get_regime(score):
    if score < 30:
        return "LOW RISK"
    elif score < 50:
        return "CAUTION"
    elif score < 70:
        return "HIGH RISK"
    else:
        return "BUBBLE"

def regime_style(regime):
    return {
        "LOW RISK": ("🟢", "#16a34a"),
        "CAUTION": ("🟡", "#f59e0b"),
        "HIGH RISK": ("🔴", "#dc2626"),
        "BUBBLE": ("🚨", "#7c3aed"),
    }.get(regime, ("⚪", "#999"))

# ================================
# APP
# ================================

st.title("AI Bubble Intelligence")
st.caption("Where risk builds before it breaks")

df = load_data()

if df is None or len(df) == 0:
    st.warning("No valid data available")
    st.stop()

latest = df.iloc[-1]

score = latest["score"]
regime = get_regime(score)

emoji, color = regime_style(regime)

# ================================
# HERO
# ================================

st.markdown("## 🧠 AI Regime")

st.markdown(f"""
<div style="padding:20px;border-radius:12px;background:{color}20;">
<h2 style="color:{color};margin:0;">{emoji} {regime}</h2>
<p style="margin:0;">Bubble Score: {round(score,2)}</p>
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
    st.write("Early imbalance signals. Risk is starting to build.")

elif regime == "HIGH RISK":
    st.write("Elevated risk environment. Market fragility increasing.")

elif regime == "BUBBLE":
    st.write("Late-stage bubble dynamics. High probability of correction.")

# ================================
# CHART
# ================================

st.subheader("Bubble Risk Score")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["date"],
    y=df["score"],
    name="Score",
    line=dict(width=3)
))

# threshold lines
fig.add_hline(y=30, line_dash="dash")
fig.add_hline(y=50, line_dash="dash")
fig.add_hline(y=70, line_dash="dash")

fig.update_layout(
    template="plotly_dark",
    height=400,
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)

# ================================
# TIMELINE
# ================================

st.subheader("Recent Evolution")

recent = df.tail(10)

for _, row in recent.iterrows():
    r = get_regime(row["score"])
    e, _ = regime_style(r)
    st.write(f"{row['date']} → {e} {r} ({round(row['score'],1)})")

# ================================
# CLEAN DATA TABLE (🔥 FIX QUI)
# ================================

st.subheader("Recent Data")

clean_df = df[["date", "score", "regime"]]

st.dataframe(clean_df.tail(20), use_container_width=True)

# ================================
# FOOTER
# ================================

st.caption("Systematic detection of structural risk shifts.")