import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from model import (
    calculate_sample_size, run_monte_carlo_simulation,
    get_business_impact, interpret_simulation, check_srm
)

# Set page config
st.set_page_config(page_title="Experimentation Architect", layout="wide")
st.title("🧪 Experimentation Architect")

# Sidebar - Grouped inputs for clarity
with st.sidebar:
    st.header("1. Experiment Parameters")
    baseline = st.slider("Baseline Conversion Rate (%)", 0.1, 50.0, 5.0) / 100
    mde = st.slider("MDE (%)", 1.0, 50.0, 10.0) / 100
    alpha = st.selectbox("Significance Level (α)", [0.01, 0.05, 0.10], index=1)
    power = st.slider("Statistical Power (1 - β)", 0.70, 0.99, 0.80)
    
    st.header("2. Business Context")
    annual_traffic = st.number_input("Annual Visitors", min_value=1, value=1_000_000)
    aov = st.number_input("Average Order Value ($)", min_value=1, value=50)

# Calculations
n_required = calculate_sample_size(baseline, mde, alpha, power)

# Tabs for better organization
tab1, tab2, tab3 = st.tabs(["📊 Power Analysis", "🎲 Simulations", "🛡️ Integrity Audit"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Sample Size (per group)", f"{n_required:,}")
    col2.metric("Total Visitors", f"{n_required * 2:,}")
    days = round((n_required * 2) / (annual_traffic / 365))
    col3.metric("Estimated Days", f"{days}")
    
    # [Insert visual representation logic here]
    st.markdown("---")
    # ... your PDF visualization code goes here ...

with tab2:
    if st.button("Run 1,000 Simulations"):
        with st.spinner("Simulating..."):
            sim_results = run_monte_carlo_simulation(baseline, mde, n_required, 1000, alpha)
            st.info(interpret_simulation(sim_results, power))
            # ... Histogram plotting code ...

with tab3:
    st.write("Check for Sample Ratio Mismatch (SRM).")
    col_a, col_b = st.columns(2)
    obs_a = col_a.number_input("Control (A) Visitors", min_value=0)
    obs_b = col_b.number_input("Variant (B) Visitors", min_value=0)
    
    if obs_a and obs_b:
        p_val, is_mismatch = check_srm(obs_a, obs_b)
        if is_mismatch: st.error(f"SRM Detected! (p={p_val:.4f})")
        else: st.success(f"Split is fair. (p={p_val:.2f})")
