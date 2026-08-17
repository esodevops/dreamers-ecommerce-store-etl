import pandas as pd

try:
    from src.extraction import extract_data
except ModuleNotFoundError:
    from extraction import extract_data


LAST_CUSTOMER_ID = 406829


def transform_data():
    """Clean the raw data and split it into four related tables."""
    # Work on a copy so the original DataFrame is not changed.
    data = extract_data()
    data = data.copy()

    # The source data have missing customer IDs. Give each invoice one customer ID.
    data["CustomerID"] = (
        data.groupby("InvoiceNo").ngroup() + LAST_CUSTOMER_ID + 1
    )

    # Convert invoice dates from text to real date and time values.
    data["InvoiceDate"] = pd.to_datetime(data["InvoiceDate"])

    # Keep one row for each customer, product, and invoice.
    customers = data[["CustomerID", "Country"]].drop_duplicates(
        subset=["CustomerID"]
    )
    products = data[
        ["StockCode", "Description", "UnitPrice"]
    ].drop_duplicates(subset=["StockCode"])
    invoices = data[
        ["InvoiceNo", "CustomerID", "InvoiceDate"]
    ].drop_duplicates(subset=["InvoiceNo"])

    # Add quantities when a product appears more than once on an invoice.
    invoice_items = data.groupby(
        ["InvoiceNo", "StockCode"], as_index=False
    )["Quantity"].sum()

    print("Created customers, products, invoices and invoice items")
    return {
        "customers": customers,
        "products": products,
        "invoices": invoices,
        "invoice_items": invoice_items,
    }


def transformation():
    """Run the transformation step as an Airflow task."""
    return transform_data()


if __name__ == "__main__":
    transformation()
