import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# 1. FIXED: Added the new functions to the import list
from model import (
    calculate_sample_size,
    run_monte_carlo_simulation,
    get_business_impact,
    interpret_simulation,
    check_srm
)

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Experimentation Architect", layout="wide")
st.title("🧪 Experimentation Architect")
st.markdown("A decision-support tool to prevent underpowered A/B tests and quantify business impact.")


# ---------------------------------------------------------
# SIDEBAR INPUTS
# ---------------------------------------------------------
st.sidebar.header("1. Experiment Parameters")

baseline = st.sidebar.slider(
    "Baseline Conversion Rate (%)",
    min_value=0.1, max_value=50.0, value=5.0,
    help="Your current performance before any changes."
) / 100

mde = st.sidebar.slider(
    "Minimum Detectable Effect (%)",
    min_value=1.0, max_value=50.0, value=10.0,
    help="The smallest improvement worth your time. Smaller lifts require significantly more data."
) / 100

# 2. FIXED: Re-added alpha so the functions have the variable they need
alpha = st.sidebar.selectbox(
    "Significance Level (α)",
    options=[0.01, 0.05, 0.10],
    index=1,
    help="The risk you're willing to take of a False Positive (False Alarm)."
)

power = st.sidebar.slider(
    "Statistical Power (1 - β)",
    min_value=0.70, max_value=0.99, value=0.80,
    help="The probability of correctly identifying a winner."
)

st.sidebar.header("2. Business Context")

annual_traffic = st.sidebar.number_input(
    "Annual Visitors",
    min_value=1,
    value=1_000_000
)

aov = st.sidebar.number_input(
    "Average Order Value ($)",
    min_value=1,
    value=50
)


# ---------------------------------------------------------
# SAMPLE SIZE CALCULATION
# ---------------------------------------------------------
n_required = calculate_sample_size(baseline, mde, alpha, power)

col1, col2, col3 = st.columns(3)
col1.metric("Required Sample Size (per group)", f"{n_required:,}")
col2.metric("Total Visitors Needed", f"{n_required * 2:,}")

# Avoid division by zero if traffic is 1
days_to_complete = round((n_required * 2) / (annual_traffic / 365)) if annual_traffic > 0 else 0
col3.metric("Estimated Days to Complete", f"{days_to_complete}")

st.divider()


# ---------------------------------------------------------
# PDF VISUALIZATION
# ---------------------------------------------------------
st.subheader("📊 Statistical Overlap (Control vs Variant)")
st.caption("Less overlap = higher power and better ability to detect true effects.")

mean_a = baseline
mean_b = baseline * (1 + mde)

std_a = np.sqrt(baseline * (1 - baseline) / n_required)
std_b = np.sqrt(mean_b * (1 - mean_b) / n_required)

x_min = max(0, min(mean_a - 4*std_a, mean_b - 4*std_b))
x_max = min(1, max(mean_a + 4*std_a, mean_b + 4*std_b))
x = np.linspace(x_min, x_max, 800)

y_a = (1 / (std_a * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_a) / std_a)**2)
y_b = (1 / (std_b * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_b) / std_b)**2)

fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=y_a, fill="tozeroy", name="Control (A)", line_color="#636EFA"))
fig.add_trace(go.Scatter(x=x, y=y_b, fill="tozeroy", name="Variant (B)", line_color="#EF553B"))

fig.update_layout(
    title="Probability Density Function (Normal Approximation)",
    xaxis_title="Conversion Rate",
    yaxis_title="Probability Density",
    showlegend=True
)
st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------
# MONTE CARLO SIMULATION
# ---------------------------------------------------------
st.divider()
st.subheader("🎲 Monte Carlo Simulation")
st.caption("We run 1,000 'parallel universes' where your lift is actually real.")

if st.button("Run 1,000 Simulated Experiments"):
    with st.spinner("Running simulations..."):
        sim_results = run_monte_carlo_simulation(
            baseline_rate=baseline,
            mde=mde,
            n_samples=n_required,
            iterations=1000,
            alpha=alpha
        )

    # 3. FIXED: This now works because interpret_simulation is imported
    summary_text = interpret_simulation(sim_results, power)
    st.info(summary_text) 

    hist_fig = px.histogram(
        sim_results,
        x="lift",
        color="significant",
        title="Distribution of Observed Lifts",
        labels={"lift": "Observed Lift (Absolute)"},
        color_discrete_map={True: "#00CC96", False: "#EF553B"}
    )
    st.plotly_chart(hist_fig, use_container_width=True)


# ---------------------------------------------------------
# BUSINESS IMPACT
# ---------------------------------------------------------
st.divider()
st.subheader("💰 Estimated Annual Revenue Impact")

absolute_lift = baseline * mde
annual_lift = get_business_impact(baseline, absolute_lift, annual_traffic, aov)

st.success(f"If the {mde*100:.1f}% lift is real, the projected annual revenue increase is **${annual_lift:,.2f}**.")


# ---------------------------------------------------------
# SRM AUDIT
# ---------------------------------------------------------
st.divider()
st.subheader("🛡️ Data Integrity Audit (SRM)")
st.caption("Enter your actual test traffic to ensure your randomization isn't broken.")

col_a, col_b = st.columns(2)
obs_a = col_a.number_input("Visitors in Control (A)", min_value=0, value=0)
obs_b = col_b.number_input("Visitors in Variant (B)", min_value=0, value=0)

if obs_a > 0 and obs_b > 0:
    # 4. FIXED: This now works because check_srm is imported
    p_val, is_mismatch = check_srm(obs_a, obs_b)
    if is_mismatch:
        st.error(f"🚨 **SRM Detected!** (p={p_val:.4f}). Your split is mathematically 'unnatural.'")
    else:
        st.success(f"✅ **Randomization looks good.** (p={p_val:.2f}). The split is fair.")
