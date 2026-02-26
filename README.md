# A/B Testing : Experimentation Architect

A lightweight decision-support tool to design statistically sound A/B tests and simulate outcomes before running real experiments.

## The Problem
Most A/B tests fail because they are:
- **Underpowered** (too little traffic)
- **Stopped early** (false lifts)
- **Misinterpreted** (noise mistaken for signal)

Teams often ask: *“Can we trust this 2% lift after 3 days?”*

## The Solution
The **Experimentation Architect** helps analysts and PMs validate experiment quality *before* spending traffic.

### Key Features
- **Power Analysis** — Computes required sample size using baseline conversion + MDE.  
- **Monte Carlo Simulation** — Runs 1,000+ synthetic A/B tests to estimate Type I & II errors.  
- **Distribution Visualizations** — Shows PDF overlaps for control vs. treatment.  
- **Business Impact Calculator**
