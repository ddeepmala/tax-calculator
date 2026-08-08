# India Salary Tax Planner (FY 2026-27)

A personal-use web app for comparing India's Old vs New income tax regimes, with detailed deduction and exemption planning for salaried individuals.

> Built by Deepmala of Sweco India for learning purposes and personal use only. Not affiliated with the Indian Income Tax Department — results are estimates and should not be treated as professional tax advice.

## Features

- **Old vs New Regime comparison** — side-by-side tax liability with the recommended regime highlighted
- **Section 87A rebate & marginal relief** — including the New Regime marginal relief around the Rs. 12L threshold
- **HRA exemption calculator** — Metro/Non-Metro aware, computed from basic salary, DA, HRA received, and rent paid
- **Deduction planning** — 80C, 80CCD(1B) additional NPS, 80D health insurance, 80E education loan interest, 80G donations, 80EE/80EEA/80U/80DD, home loan interest (Section 24b)
- **Employer retirement contributions** — combined employer PF + NPS + superannuation taxed on the excess over Rs. 7,50,000/year (both regimes)
- **State-wise professional tax** — configurable per-state slabs
- **Capital gains** — STCG and LTCG on equity taxed at special rates
- **Interactive dashboard** — regime comparison chart, deductions/exemptions breakup, and a tax-liability projection across income levels
- **PDF report export** — downloadable summary of the full computation
- **Dark/light theme**, fully responsive wizard-style form

## Project Structure

```
tax-calculator/
├── app.py                  # Flask app & API routes
├── config/
│   └── taxConfig.json      # Tax slabs, rebates, surcharge, deduction limits, state PT rules
├── src/
│   ├── tax_engine.py       # Core tax calculation logic (old & new regime)
│   └── pdf_generator.py    # PDF report generation (ReportLab)
├── public/
│   ├── index.html          # Single-page app (landing + wizard + dashboard)
│   ├── script.js           # Form wizard, live totals, charts, API calls
│   └── styles.css
├── tests/
│   ├── test_tax_engine.py  # Unit tests for the tax engine
│   └── test_api.py         # API endpoint smoke tests
├── temp/                   # Scratch dir for generated PDFs (auto-created, cleaned per request)
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
pip install -r requirements.txt
```

### Run the app

```bash
python app.py
```

By default the server starts at `http://127.0.0.1:5000`. Configure with environment variables:

| Variable      | Default | Description                        |
|---------------|---------|-------------------------------------|
| `PORT`        | `5000`  | Port to run the server on          |
| `FLASK_DEBUG` | `false` | Set to `true` to enable debug mode |

Then open `http://127.0.0.1:5000` in your browser.

## Running Tests

```bash
python tests/test_tax_engine.py   # Unit tests for the calculation engine
python tests/test_api.py          # API tests (requires the server running locally)
```

## API

| Endpoint             | Method | Description                                      |
|-----------------------|--------|--------------------------------------------------|
| `/api/calculate`      | POST   | Computes old/new regime tax breakdown from salary & deduction inputs |
| `/api/download-pdf`   | POST   | Generates and downloads a PDF tax summary report |

## Configuration

All tax slabs, rebate thresholds, surcharge rates, deduction limits, and state professional tax rules live in [`config/taxConfig.json`](config/taxConfig.json) — update this file each tax year rather than editing calculation code directly.

## Disclaimer

This application is for informational and educational purposes only and should not be considered professional tax, legal, or financial advice. Always consult a qualified tax professional or refer to official Income Tax Department guidelines before making financial decisions.
