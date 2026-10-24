
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "Online Retail.xlsx"
OUTPUT_PATH = DATA_PATH.parent / "online_retail_cleaned.csv"


def main():
    print("Loading the original dataset...")
    df = pd.read_excel(DATA_PATH)

    original_rows = len(df)

    # Remove exact duplicate rows only.
    df = df.drop_duplicates().copy()
    duplicates_removed = original_rows - len(df)

    # Create flags so unusual transactions remain identifiable.
    df["IsCancellationInvoice"] = (
        df["InvoiceNo"].astype(str).str.startswith("C")
    )
    df["IsNegativeQuantity"] = df["Quantity"] < 0
    df["IsZeroPrice"] = df["UnitPrice"] == 0
    df["IsNegativePrice"] = df["UnitPrice"] < 0

    # Standard transaction line value.
    # Returns remain negative; this is not yet a final sales KPI.
    df["LineAmount"] = df["Quantity"] * df["UnitPrice"]

    # A standard product-sales measure excludes negative-price
    # accounting adjustments and cancellation-style invoices.
    # Negative quantities on other invoices remain visible.
    df["StandardSalesLineAmount"] = df["LineAmount"].where(
        (~df["IsCancellationInvoice"]) & (~df["IsNegativePrice"]),
        0.0,
    )

    # Save a separate analysis-ready copy.
    df.to_csv(OUTPUT_PATH, index=False)

    print("\n=== CLEANING SUMMARY ===")
    print(f"Original rows: {original_rows:,}")
    print(f"Exact duplicates removed: {duplicates_removed:,}")
    print(f"Rows after duplicate removal: {len(df):,}")
    print(
        "Rows with missing CustomerID:",
        f"{df['CustomerID'].isna().sum():,}",
    )
    print(
        "Cancellation-style invoice rows:",
        f"{df['IsCancellationInvoice'].sum():,}",
    )
    print(
        "Negative-quantity rows:",
        f"{df['IsNegativeQuantity'].sum():,}",
    )
    print(
        "Zero-price rows:",
        f"{df['IsZeroPrice'].sum():,}",
    )
    print(
        "Negative-price rows:",
        f"{df['IsNegativePrice'].sum():,}",
    )

    print(f"\nCleaned dataset saved to: {OUTPUT_PATH}")
    print("Original Excel file was not modified.")


if __name__ == "__main__":
    main()
