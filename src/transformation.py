import pandas as pd

try:
    from src.extraction import extract_data
except ModuleNotFoundError:
    from extraction import extract_data


def assign_customer_ids(data):
    """Keep known IDs and create one ID for each anonymous invoice."""
    customer_ids = data.groupby("InvoiceNo")["CustomerID"].transform("first")
    next_id = int(customer_ids.max()) + 1
    missing = customer_ids.isna()
    new_ids = data.loc[missing].groupby("InvoiceNo", sort=False).ngroup() + next_id

    return customer_ids.fillna(new_ids).astype(int)


def transform_data():
    """Clean the raw data and split it into four related tables."""
    # Work on a copy so the original DataFrame is not changed.
    data = extract_data()
    data = data.copy()

    data["CustomerID"] = assign_customer_ids(data)

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
