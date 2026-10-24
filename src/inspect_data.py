
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "Online Retail.xlsx"


def main():
    print("Loading the Online Retail dataset...")
    df = pd.read_excel(DATA_PATH)

    print("\n=== DATASET OVERVIEW ===")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Date range: {df['InvoiceDate'].min()} to {df['InvoiceDate'].max()}")

    print("\n=== MISSING VALUES ===")
    missing = df.isnull().sum()
    missing_percent = (missing / len(df) * 100).round(2)

    missing_report = pd.DataFrame({
        "MissingCount": missing,
        "MissingPercent": missing_percent,
    })
    print(missing_report.to_string())

    print("\n=== DUPLICATE RECORDS ===")
    duplicate_count = df.duplicated().sum()
    print(f"Exact duplicate rows: {duplicate_count:,}")

    print("\n=== QUANTITY CHECK ===")
    negative_quantity = (df["Quantity"] < 0).sum()
    zero_quantity = (df["Quantity"] == 0).sum()
    print(f"Rows with negative quantity: {negative_quantity:,}")
    print(f"Rows with zero quantity: {zero_quantity:,}")

    print("\n=== UNIT PRICE CHECK ===")
    negative_price = (df["UnitPrice"] < 0).sum()
    zero_price = (df["UnitPrice"] == 0).sum()
    print(f"Rows with negative unit price: {negative_price:,}")
    print(f"Rows with zero unit price: {zero_price:,}")

    print("\n=== INVOICE CHECK ===")
    cancelled = df["InvoiceNo"].astype(str).str.startswith("C")
    print(f"Rows with cancellation-style invoice numbers: {cancelled.sum():,}")
    print(f"Unique invoices: {df['InvoiceNo'].nunique():,}")

    print("\n=== TOP 10 COUNTRIES BY ROW COUNT ===")
    print(df["Country"].value_counts().head(10).to_string())

    print("\n=== AUDIT COMPLETE ===")
    print("No data has been deleted or modified.")


if __name__ == "__main__":
    main()
