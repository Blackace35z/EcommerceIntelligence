# E-commerce Intelligence Dashboard

An interactive business intelligence dashboard built with Python, Pandas, Dash, and Plotly to explore online retail transactions and uncover sales trends, customer activity, product performance, and geographic patterns.

## Overview

E-commerce Intelligence transforms raw retail transaction data into an interactive dashboard designed to make business performance easier to explore and understand.

The project covers the data analysis workflow, from data inspection and cleaning to business metrics and interactive visualizations.

## Features

- **Sales KPIs:** Positive sales value, invoices with sales, average order value, monthly sales growth, identifiable customers, and transaction lines.
- **Interactive filters:** Filter results by country and date range.
- **Quick date ranges:** Select preset periods to explore recent performance.
- **Monthly sales trends:** Examine how sales change over time.
- **Country analysis:** Compare sales across countries.
- **Product performance:** Identify leading products by sales value.
- **Data preparation:** Inspect data quality, identify anomalies, and generate an analysis-ready dataset.

## Technology Stack

- Python
- Pandas
- NumPy
- OpenPyXL
- Plotly
- Dash

## Project Structure

```text
EcommerceIntelligence/
├── dashboard/
│   ├── app.py
│   └── assets/
│       └── style.css
├── data/
│   ├── Online Retail.xlsx
│   └── online_retail_cleaned.csv
├── notebooks/
├── src/
│   ├── inspect_data.py
│   ├── inspect_anomalies.py
│   ├── clean_data.py
│   └── business_metrics.py
├── .gitignore
├── README.md
└── requirements.txt
```

The dataset files are kept locally and are not included in this GitHub repository.

## Dataset

This project uses the **Online Retail** dataset from the UCI Machine Learning Repository.

The dataset contains transaction-level records from a UK-based online retailer, including invoice numbers, product codes, descriptions, quantities, invoice dates, unit prices, customer identifiers, and countries.

Original dataset: https://archive.ics.uci.edu/dataset/352/online+retail

Download the Excel dataset and place it in the `data/` directory with this exact filename:

`Online Retail.xlsx`

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Blackace35z/EcommerceIntelligence.git
cd EcommerceIntelligence
```


### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows Command Prompt:

```bat
.venv\Scripts\activate
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Prepare the dataset

After placing `Online Retail.xlsx` inside `data/`, run:

```bash
python src/clean_data.py
```

This creates `data/online_retail_cleaned.csv`.

The cleaning script removes exact duplicate rows, creates flags for unusual transactions, and calculates transaction-line values. It preserves negative quantities so returns remain available for analysis.

### 6. Launch the dashboard

```bash
cd dashboard
python app.py
```

Open the local address displayed in your terminal, usually:

http://127.0.0.1:8050/

## Data and Metric Considerations

- The source dataset covers December 2010 through December 2011.
- Exact duplicate rows are removed during cleaning.
- Missing customer identifiers limit customer-level analysis.
- Cancellation-style invoices, returns, and accounting adjustments require careful treatment.
- Positive sales figures in the dashboard are analytical measures, not audited accounting revenue.
- Average order value and monthly growth depend on the dashboard's transaction and date-selection rules.

These limitations are important when interpreting the results.

## Future Improvements

- Add quantity-based best-seller analysis.
- Add downloadable CSV exports.
- Expand customer segmentation and retention analysis.
- Add dashboard screenshots and deployment instructions.

## Author

Developed as a portfolio project exploring Python data analytics, business intelligence, data cleaning, and interactive dashboard development.
