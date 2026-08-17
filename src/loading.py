import json
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

try:
    from src.transformation import transform_data
except ModuleNotFoundError:
    from transformation import transform_data


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_FOLDER, "config.json")
load_dotenv(
    os.path.join(PROJECT_FOLDER, ".env"),
    override=True,
)


def write_csv_files(tables, destination):
    """Save each transformed table as a CSV file."""
    os.makedirs(destination, exist_ok=True)
    tables["customers"].to_csv(
        os.path.join(destination, "customer.csv"), index=False
    )
    tables["products"].to_csv(
        os.path.join(destination, "product.csv"), index=False
    )
    tables["invoices"].to_csv(
        os.path.join(destination, "invoice.csv"), index=False
    )
    tables["invoice_items"].to_csv(
        os.path.join(destination, "invoice_items.csv"), index=False
    )


def create_database(database_name):
    """Create the PostgreSQL database when it does not already exist."""
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


def write_database_tables(tables, database_name):
    """Create the Dreamers tables and load the transformed data."""
    database_url = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{database_name}"
    )
    engine = create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS dreamers"))

        # Drop child tables first because they contain foreign keys.
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

        # Load parent tables before child tables to satisfy foreign keys.
        tables["customers"].to_sql(
            "customers", connection, schema="dreamers", if_exists="append", index=False
        )
        tables["products"].to_sql(
            "products", connection, schema="dreamers", if_exists="append", index=False
        )
        tables["invoices"].to_sql(
            "invoices", connection, schema="dreamers", if_exists="append", index=False
        )
        tables["invoice_items"].to_sql(
            "invoice_items",
            connection,
            schema="dreamers",
            if_exists="append",
            index=False,
        )

    engine.dispose()


def load_data():
    """Write transformed tables to CSV files and PostgreSQL."""
    with open(CONFIG_FILE, encoding="utf-8") as config_file:
        config = json.load(config_file)

    destination = os.path.join(PROJECT_FOLDER, config["destination"])
    tables = transform_data()

    write_csv_files(tables, destination)

    database_name = os.getenv("DB_NAME")
    if not database_name:
        raise ValueError("DB_NAME environment variable is required")

    create_database(database_name)
    write_database_tables(tables, database_name)
    print("Loaded CSV files and PostgreSQL tables")


def loading():
    """Run the loading step as an Airflow task."""
    load_data()


if __name__ == "__main__":
    loading()
