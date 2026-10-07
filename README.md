# E-Commerce Performance & Growth Decision System

A lightweight decision-support prototype inspired by the responsibilities of an e-commerce market owner: sales & growth, site performance, merchandising, conversion, campaigns, pricing and growth experiments.

## What it does
- Tracks revenue, orders, conversion, AOV and target achievement.
- Visualizes the customer funnel and sales trend.
- Identifies high-traffic / low-conversion products.
- Compares campaign revenue and margin efficiency.
- Generates rule-based recommended actions from the data.

## Data integrity
All performance data included in this repository is **synthetic/demo data** created solely to demonstrate the analytical workflow. It is not Touché data and no private company information is used.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Why this prototype
The purpose is not to claim production readiness. It demonstrates how an analyst/market owner can move from raw commerce metrics to prioritized business actions. A production version could connect to GA4/e-commerce/ads APIs, use SQL for historical storage, automate alerts, and support experiment measurement.
