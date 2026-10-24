
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "Online Retail.xlsx"


def main():
    df = pd.read_excel(DATA_PATH)

    cancelled = df["InvoiceNo"].astype(str).str.startswith("C")
    negative_quantity = df["Quantity"] < 0
    zero_price = df["UnitPrice"] == 0
    negative_price = df["UnitPrice"] < 0

    print("=== NEGATIVE QUANTITY EXAMPLES ===")
    print(
        df.loc[
            negative_quantity,
            ["InvoiceNo", "StockCode", "Description", "Quantity",
             "UnitPrice", "CustomerID"]
        ].head(10).to_string(index=False)
    )

    print("\n=== CANCELLATION INVOICE EXAMPLES ===")
    print(
        df.loc[
            cancelled,
            ["InvoiceNo", "StockCode", "Description", "Quantity",
             "UnitPrice", "CustomerID"]
        ].head(10).to_string(index=False)
    )

    print("\n=== ZERO-PRICE EXAMPLES ===")
    print(
        df.loc[
            zero_price,
            ["InvoiceNo", "StockCode", "Description", "Quantity",
             "UnitPrice", "CustomerID"]
        ].head(10).to_string(index=False)
    )

    print("\n=== NEGATIVE-PRICE EXAMPLES ===")
    print(
        df.loc[
            negative_price,
            ["InvoiceNo", "StockCode", "Description", "Quantity",
             "UnitPrice", "CustomerID"]
        ].to_string(index=False)
    )

    print("\n=== OVERLAP CHECK ===")
    print(
        "Cancellation-style invoices with negative quantity:",
        int((cancelled & negative_quantity).sum())
    )
    print(
        "Negative-quantity rows not marked as cancellations:",
        int((~cancelled & negative_quantity).sum())
    )

    print("\nInspection complete. Original data remains unchanged.")


if __name__ == "__main__":
    main()
