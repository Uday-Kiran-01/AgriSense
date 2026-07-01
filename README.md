---
title: AgriSense AI
emoji: 🌱
colorFrom: green
colorTo: amber
sdk: streamlit
sdk_version: 1.36.0
python_version: "3.11"
app_file: app.py
pinned: false
license: mit
---

# 🌱 AgriSense AI

**Explainable AI Decision Support for Agricultural Finance**

A three-role Streamlit dashboard simulating the agricultural lending workflow:
- 👨‍🌾 **Farmer** — 5-step wizard: Welcome → Documents → Farm Details → Analysis → Results
- 🏢 **Credit Analyst** — Pipeline review, financial analysis, decision memo generation
- 🏦 **Bank Officer** — Final decision with AI recommendation and human oversight

## Features
- Random Forest ML models (credit risk, repayment probability, debt capacity)
- Colorful filter cards with emoji indicators
- Dark-themed responsive UI (desktop + mobile)
- Real-time timestamps
- Scenario simulation (tractor purchase, etc.)
- Decision memo with AI-generated recommendations
- 8-step application timeline

## Tech Stack
- Streamlit 1.36+
- scikit-learn Random Forest
- Plotly charts
- SQLite + SQLAlchemy (backend)
- FastAPI (backend)

## Disclaimer
⚠️ **Advisory Only** — Final lending decisions are made by qualified human officers.
All data is synthetic. Swedish demo (SEK currency, GDPR compliant).
short_description: Explainable AI for Agricultural Financing
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
