import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# Import your model functions
from model import (
    calculate_sample_size,
    run_monte_carlo_simulation,
    get_business_impact,
    interpret_simulation,
    check_srm
)

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Experimentation Architect", 
    page_icon="🧪", 
    layout="wide"
)

st.title("🧪 Experimentation Architect")
st.markdown("Structure your A/B tests with statistical rigor and business clarity.")

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Test Parameters")
    baseline = st.slider(
        "Baseline Conversion Rate (%)", 0.1, 50.0, 5.0, 
        help="Current conversion rate of your Control group."
    ) / 100

    mde = st.slider(
        "Min. Detectable Effect (%)", 1.0, 50.0, 10.0, 
        help="The relative lift you want to be able to detect."
    ) / 100

    alpha = st.selectbox(
        "Significance Level (α)", [0.01, 0.05, 0.10], index=1,
        help="Probability of a Type I error (False Positive)."
    )

    power = st.slider(
        "Statistical Power (1 - β)", 0.70, 0.99, 0.80,
        help="Probability of detecting an effect if there actually is one."
    )

    st.header("2. Business Context")
    annual_traffic = st.number_input("Annual Visitors", min_value=1, value=1_000_000)
    aov = st.number_input("Average Order Value ($)", min_value=1, value=50)

# --- CALCULATIONS ---
n_required = calculate_sample_size(baseline, mde, alpha, power)
total_needed = n_required * 2
days_to_complete = round(total_needed / (annual_traffic / 365)) if annual_traffic > 0 else 0

# --- MAIN UI LAYOUT ---
# High-level Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Sample Size (Per Group)", f"{n_required:,}")
m2.metric("Total Traffic Required", f"{total_needed:,}")
m3.metric("Est. Duration", f"{days_to_complete} Days")

st.divider()

# Organize content into Tabs
tab_viz, tab_sim, tab_audit = st.tabs([
    "📈 Statistical Design", 
    "🎲 Monte Carlo Simulation", 
    "🛡️ Integrity Audit (SRM)"
])

# --- TAB 1: VISUALIZATION ---
with tab_viz:
    st.subheader("Statistical Overlap")
    st.caption("This chart visualizes the expected distribution of results for Control vs. Variant.")
    
    # PDF Math
    mean_a, mean_b = baseline, baseline * (1 + mde)
    std_a = np.sqrt(baseline * (1 - baseline) / n_required)
    std_b = np.sqrt(mean_b * (1 - mean_b) / n_required)
    
    x = np.linspace(mean_a - 4*std_a, mean_b + 4*std_b, 500)
    y_a = (1 / (std_a * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_a) / std_a)**2)
    y_b = (1 / (std_b * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean_b) / std_b)**2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_a, fill='tozeroy', name='Control', line_color='#636EFA'))
    fig.add_trace(go.Scatter(x=x, y=y_b, fill='tozeroy', name='Variant', line_color='#EF553B'))
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Conversion Rate",
        yaxis_title="Density",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Business Impact Box
    absolute_lift = baseline * mde
    annual_rev_impact = get_business_impact(baseline, absolute_lift, annual_traffic, aov)
    st.success(f"**Potential Impact:** A successful {mde*100:.1f}% lift could generate **${annual_rev_impact:,.2f}** in additional annual revenue.")

# --- TAB 2: SIMULATION ---
with tab_sim:
    st.subheader("The 'Parallel Universes' Test")
    st.write("We simulate 1,000 experiments using your parameters to see how often we find a significant result.")

    if st.button("🚀 Run Simulation", type="primary"):
        with st.spinner("Simulating 1,000 experiments..."):
            # We use the model function here
            sim_df = run_monte_carlo_simulation(baseline, mde, n_required, 1000, alpha)
            
            # Interpretation
            st.info(interpret_simulation(sim_df, power))

            # Plotting the results
            hist_fig = px.histogram(
                sim_df, x="lift", color="significant",
                title="Distribution of Observed Lifts",
                color_discrete_map={True: "#00CC96", False: "#EF553B"},
                labels={"lift": "Absolute Lift Observed", "significant": "Is Statistically Significant?"}
            )
            st.plotly_chart(hist_fig, use_container_width=True)

# --- TAB 3: SRM AUDIT ---
with tab_audit:
    st.subheader("Sample Ratio Mismatch (SRM) Check")
    st.markdown("""
    Use this **during** or **after** your test. If the traffic split is not roughly 50/50, 
    your results might be biased due to a technical bug in your randomization engine.
    """)
    
    c1, c2 = st.columns(2)
    obs_a = c1.number_input("Actual Visitors: Control (A)", min_value=0, value=0)
    obs_b = c2.number_input("Actual Visitors: Variant (B)", min_value=0, value=0)

    if obs_a > 0 and obs_b > 0:
        p_val, is_mismatch = check_srm(obs_a, obs_b)
        
        if is_mismatch:
            st.error(f"🚨 **SRM Warning!** (p-value: {p_val:.5f})")
            st.markdown("The difference in traffic is statistically highly unlikely. **Do not trust these results.** Check your tracking and assignment logic.")
        else:
            st.success(f"✅ **Randomization looks healthy.** (p-value: {p_val:.4f})")
            st.write("The traffic split is within the expected range of variance.")
