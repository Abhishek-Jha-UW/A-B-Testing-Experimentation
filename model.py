import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.power import NormalIndPower


# ---------------------------------------------------------
# SAMPLE SIZE CALCULATION
# ---------------------------------------------------------
def calculate_sample_size(baseline_rate, mde, alpha=0.05, power=0.80):
    """
    Compute required sample size per group for a two-sided A/B test.

    Parameters
    ----------
    baseline_rate : float
        Current conversion rate (e.g., 0.10).
    mde : float
        Minimum detectable effect as a *relative* lift (e.g., 0.10 for +10%).
    alpha : float
        Significance level (default 0.05).
    power : float
        Desired statistical power (default 0.80).

    Returns
    -------
    int
        Required sample size per group.
    """
    target_rate = baseline_rate * (1 + mde)

    # Cohen's h effect size for proportions
    h = 2 * (np.arcsin(np.sqrt(target_rate)) - np.arcsin(np.sqrt(baseline_rate)))

    analysis = NormalIndPower()
    n_required = analysis.solve_power(
        effect_size=h,
        alpha=alpha,
        power=power,
        ratio=1.0,
        alternative="two-sided"
    )

    return int(np.ceil(n_required))


# ---------------------------------------------------------
# MONTE CARLO SIMULATION
# ---------------------------------------------------------
def run_monte_carlo_simulation(baseline_rate, mde, n_samples, iterations=1000, alpha=0.05):
    """
    Faster version: Uses the binomial distribution property to avoid 
    massive memory allocation.
    """
    true_rate = baseline_rate * (1 + mde)

    # Instead of (iterations, n_samples), we just generate the TOTAL SUMS
    # This generates 1,000 totals directly.
    count_a = np.random.binomial(n_samples, baseline_rate, iterations)
    count_b = np.random.binomial(n_samples, true_rate, iterations)

    results = []
    for a, b in zip(count_a, count_b):
        # We pass the sums directly to the z-test
        stat, p_value = proportions_ztest([a, b], [n_samples, n_samples])
        lift = (b / n_samples) - (a / n_samples)

        results.append({
            "p_value": p_value,
            "significant": p_value < alpha,
            "lift": lift
        })

    return pd.DataFrame(results)

# ---------------------------------------------------------
# BUSINESS IMPACT CALCULATOR
# ---------------------------------------------------------
def get_business_impact(baseline_conv, lift, annual_visitors, avg_order_value):
    """
    Convert statistical lift into estimated annual revenue impact.

    Parameters
    ----------
    baseline_conv : float
        Current conversion rate.
    lift : float
        Observed or expected absolute lift.
    annual_visitors : int
        Total yearly traffic.
    avg_order_value : float
        Average revenue per conversion.

    Returns
    -------
    float
        Estimated annual revenue lift.
    """
    current_revenue = annual_visitors * baseline_conv * avg_order_value
    new_revenue = annual_visitors * (baseline_conv + lift) * avg_order_value
    return new_revenue - current_revenue
