import json
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


class DreamersEtlPipeline:
    def __init__(self, source, destination):
        self.source = source
        self.destination = destination

    def raw_data_ingestion(self):
        file_path = os.path.join(self.source, "dreamers_ecommerce.csv")
        self.data = pd.read_csv(file_path)
        print(f"Extracted {len(self.data)} rows")

    def data_extraction(self):
        # Give every invoice one customer ID.
        last_customer_id = 406829
        self.data["CustomerID"] = (
            self.data.groupby("InvoiceNo").ngroup() + last_customer_id + 1
        )
        self.data["InvoiceDate"] = pd.to_datetime(self.data["InvoiceDate"])
        print("Prepared customer IDs and invoice dates")

    def data_tranformation(self):
        self.customers = self.data[["CustomerID", "Country"]].drop_duplicates(
            subset=["CustomerID"]
        )

        self.products = self.data[
            ["StockCode", "Description", "UnitPrice"]
        ].drop_duplicates(subset=["StockCode"])

        self.invoices = self.data[
            ["InvoiceNo", "CustomerID", "InvoiceDate"]
        ].drop_duplicates(subset=["InvoiceNo"])

        self.invoice_items = self.data.groupby(
            ["InvoiceNo", "StockCode"], as_index=False
        )["Quantity"].sum()

        print("Created customers, products, invoices and invoice items")

    def load_data(self):
        os.makedirs(self.destination, exist_ok=True)

        self.customers.to_csv(
            os.path.join(self.destination, "customer.csv"), index=False
        )
        self.products.to_csv(
            os.path.join(self.destination, "product.csv"), index=False
        )
        self.invoices.to_csv(
            os.path.join(self.destination, "invoice.csv"), index=False
        )
        self.invoice_items.to_csv(
            os.path.join(self.destination, "invoice_items.csv"), index=False
        )

        database_name = os.getenv("DB_NAME")
        admin_url = (
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/postgres"
        )

        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as connection:
            database_exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": database_name},
            ).scalar()

            if not database_exists:
                connection.execute(text(f'CREATE DATABASE "{database_name}"'))

        admin_engine.dispose()

        database_url = (
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
            f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{database_name}"
        )
        engine = create_engine(database_url)

        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS dreamers"))
            connection.execute(text("DROP TABLE IF EXISTS dreamers.invoice_items"))
            connection.execute(text("DROP TABLE IF EXISTS dreamers.invoices"))
            connection.execute(text("DROP TABLE IF EXISTS dreamers.products"))
            connection.execute(text("DROP TABLE IF EXISTS dreamers.customers"))

            connection.execute(text('''
                CREATE TABLE dreamers.customers (
                    "CustomerID" INT PRIMARY KEY,
                    "Country" VARCHAR(255)
                )
            '''))
            connection.execute(text('''
                CREATE TABLE dreamers.products (
                    "StockCode" VARCHAR(255) PRIMARY KEY,
                    "Description" VARCHAR(255),
                    "UnitPrice" DECIMAL(10, 2)
                )
            '''))
            connection.execute(text('''
                CREATE TABLE dreamers.invoices (
                    "InvoiceNo" VARCHAR(255) PRIMARY KEY,
                    "CustomerID" INT REFERENCES dreamers.customers("CustomerID"),
                    "InvoiceDate" TIMESTAMP
                )
            '''))
            connection.execute(text('''
                CREATE TABLE dreamers.invoice_items (
                    "InvoiceNo" VARCHAR(255) REFERENCES dreamers.invoices("InvoiceNo"),
                    "StockCode" VARCHAR(255) REFERENCES dreamers.products("StockCode"),
                    "Quantity" INT,
                    PRIMARY KEY ("InvoiceNo", "StockCode")
                )
            '''))

            self.customers.to_sql(
                "customers", connection, schema="dreamers", if_exists="append", index=False
            )
            self.products.to_sql(
                "products", connection, schema="dreamers", if_exists="append", index=False
            )
            self.invoices.to_sql(
                "invoices", connection, schema="dreamers", if_exists="append", index=False
            )
            self.invoice_items.to_sql(
                "invoice_items", connection, schema="dreamers", if_exists="append", index=False
            )

        engine.dispose()
        print("Loaded CSV files and PostgreSQL tables")

    def run_pipeline(self):
        self.raw_data_ingestion()
        self.data_extraction()
        self.data_tranformation()
        self.load_data()


if __name__ == "__main__":
    with open("config.json") as config_file:
        config = json.load(config_file)

    pipeline = DreamersEtlPipeline(
        source=config["source"],
        destination=config["destination"],
    )
    pipeline.run_pipeline()
