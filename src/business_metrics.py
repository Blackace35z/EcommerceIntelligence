
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "online_retail_cleaned.csv"


def main():
    df = pd.read_csv(DATA_PATH, parse_dates=["InvoiceDate"])

    # Identify cancellation invoices and ordinary positive sales lines.
    cancellation = df["IsCancellationInvoice"].astype(bool)
    positive_sales = (
        (~cancellation)
        & (df["Quantity"] > 0)
        & (df["UnitPrice"] > 0)
    )

    df["PositiveSalesValue"] = (
        df["Quantity"] * df["UnitPrice"]
    ).where(positive_sales, 0.0)

    print("\n=== SALES SUMMARY ===")
    print(f"All invoice references: {df['InvoiceNo'].nunique():,}")
    print(
        "Cancellation-style invoices:",
        f"{df.loc[cancellation, 'InvoiceNo'].nunique():,}",
    )
    print(
        "Invoices with positive sales lines:",
        f"{df.loc[positive_sales, 'InvoiceNo'].nunique():,}",
    )
    print(
        "Positive sales-line value:",
        f"{df['PositiveSalesValue'].sum():,.2f}",
    )
    print(
        "Identifiable customers:",
        f"{df['CustomerID'].nunique():,}",
    )

    # Exclude known service/adjustment descriptions from the
    # physical merchandise ranking. This is a first-pass rule,
    # not a definitive classification of every StockCode.
    non_merchandise_terms = (
        "POSTAGE",
        "DOTCOM POSTAGE",
        "MANUAL",
        "DISCOUNT",
        "ADJUST BAD DEBT",
    )

    description = df["Description"].fillna("").str.upper()
    is_non_merchandise = description.apply(
        lambda value: any(term in value for term in non_merchandise_terms)
    )

    merchandise = df.loc[
        positive_sales & (~is_non_merchandise)
    ].copy()

    product_summary = (
        merchandise.groupby("Description")
        .agg(
            UnitsSold=("Quantity", "sum"),
            SalesValue=("PositiveSalesValue", "sum"),
        )
        .sort_values("SalesValue", ascending=False)
    )

    print("\n=== TOP 10 PHYSICAL-PRODUCT CANDIDATES ===")
    print(product_summary.head(10).round(2).to_string())

    country_summary = (
        df.loc[positive_sales]
        .groupby("Country")
        .agg(
            SalesValue=("PositiveSalesValue", "sum"),
            InvoiceCount=("InvoiceNo", "nunique"),
        )
        .sort_values("SalesValue", ascending=False)
    )

    print("\n=== TOP 10 COUNTRIES BY POSITIVE SALES ===")
    print(country_summary.head(10).round(2).to_string())

    monthly = df.loc[positive_sales].copy()
    monthly["Month"] = monthly["InvoiceDate"].dt.to_period("M").astype(str)

    monthly_summary = (
        monthly.groupby("Month")["PositiveSalesValue"]
        .sum()
        .sort_index()
    )

    print("\n=== MONTHLY POSITIVE SALES ===")
    print(monthly_summary.round(2).to_string())

    print("\nAnalysis complete.")
    print("These are positive sales-line values, not net revenue.")
    print("Returns and accounting adjustments require separate analysis.")


if __name__ == "__main__":
    main()
