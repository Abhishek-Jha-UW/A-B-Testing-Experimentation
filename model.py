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

# ---------------------------------------------------------
# INTERPRETATION & AUDITING
# ---------------------------------------------------------

def interpret_simulation(df, power_target):
    """
    Translates Monte Carlo results into plain English.
    
    Parameters
    ----------
    df : pd.DataFrame
        The results from run_monte_carlo_simulation.
    power_target : float
        The user-defined statistical power (e.g., 0.80).
    """
    # Calculate how many simulations were significant (Green bars)
    success_rate = df['significant'].mean()
    
    summary = (
        f"In 1,000 simulated 'parallel universes' where your change was actually better, "
        f"the test correctly identified the winner {success_rate:.1%} of the time."
    )
    
    # Check if we met the "Target Power"
    if success_rate < power_target:
        advice = (
            f" **Note:** This is slightly lower than your goal of {power_target:.0%}. "
            "This means there is a higher risk of missing a winning idea due to random noise."
        )
    else:
        advice = " **Great!** This meets your certainty goals, and your results should be highly reliable."
        
    return summary + advice

def check_srm(observed_a, observed_b, expected_ratio=0.5):
    """
    Checks for Sample Ratio Mismatch (SRM).
    If the p-value is extremely low (e.g., < 0.001), the split is 'unnatural.'
    
    This is used when you have ACTUAL data from a running test.
    """
    from scipy.stats import chisquare
    
    total = observed_a + observed_b
    if total == 0:
        return 1.0, False
        
    expected_a = total * expected_ratio
    expected_b = total * (1 - expected_ratio)
    
    # Chi-square test compares the 'actual' split to the 'perfect' 50/50 split
    stat, p_val = chisquare([observed_a, observed_b], f_obs=[expected_a, expected_b])
    
    # If p-value is tiny, the randomization is likely broken (SRM exists)
    is_mismatch = p_val < 0.001
    return p_val, is_mismatch
