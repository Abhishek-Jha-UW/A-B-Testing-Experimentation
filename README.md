# A/B Testing: Experimentation

## The Problem
Most A/B tests fail not because the ideas are bad, but because they are **underpowered** or **stopped too early**. Business stakeholders often ask: *"Can we trust this 2% lift after only 3 days?"*

## The Solution
The **Experimentation Architect** is a decision-support tool designed to help Data Analysts and Product Managers design statistically sound experiments and simulate outcomes before spending a single dollar on traffic.

### Key Features:
* **Pre-Test Power Analysis:** Calculate required sample sizes based on Baseline Conversion and Minimum Detectable Effect (MDE).
* **Monte Carlo Simulations:** Run 1,000+ "Parallel Universes" to visualize the probability of Type I (False Positive) and Type II (False Negative) errors.
* **Interactive Distributions:** Real-time visualization of PDF (Probability Density Function) overlaps to understand statistical "noise."
* **Business Impact Calculator:** Translates "Statistical Significance" into "Estimated Annual Revenue Lift."

## How It Works (The Logic)
1. **Input Phase:** User defines the current Baseline (e.g., 5% conversion) and the "Goal" (e.g., a 10% relative lift).
2. **Calculation Phase:** Using frequentist formulas, the app determines the **Sample Size ($n$)** required to achieve 80% Power at a 95% Confidence Level.
3. **Simulation Phase:** The app uses a Monte Carlo approach to generate synthetic data for Group A and Group B. It runs the test 1,000 times to see how often the "True Effect" is actually captured.
4. **Interpretation:** It provides a "Go / No-Go" recommendation based on the simulated risk profile.
