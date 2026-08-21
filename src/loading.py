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
    """Load staging tables, then atomically promote them to production."""
    database_url = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{database_name}"
    )
    engine = create_engine(database_url)

    with engine.begin() as connection:
        # Build the new version without changing the live tables.
        connection.execute(text("DROP SCHEMA IF EXISTS dreamers_staging CASCADE"))
        connection.execute(text("CREATE SCHEMA dreamers_staging"))

        connection.execute(text('''
                CREATE TABLE dreamers_staging.customers (
                    "CustomerID" INT PRIMARY KEY,
                    "Country" VARCHAR(255)
                )
            '''))
        connection.execute(text('''
                CREATE TABLE dreamers_staging.products (
                    "StockCode" VARCHAR(255) PRIMARY KEY,
                    "Description" VARCHAR(255)
                )
            '''))
        connection.execute(text('''
                CREATE TABLE dreamers_staging.invoices (
                    "InvoiceNo" VARCHAR(255) PRIMARY KEY,
                    "CustomerID" INT REFERENCES dreamers_staging.customers("CustomerID"),
                    "InvoiceDate" TIMESTAMP
                )
            '''))
        connection.execute(text('''
                CREATE TABLE dreamers_staging.invoice_items (
                    "InvoiceNo" VARCHAR(255) REFERENCES dreamers_staging.invoices("InvoiceNo"),
                    "StockCode" VARCHAR(255) REFERENCES dreamers_staging.products("StockCode"),
                    "UnitPrice" DECIMAL(10, 2),
                    "Quantity" INT,
                    PRIMARY KEY ("InvoiceNo", "StockCode", "UnitPrice")
                )
            '''))

        # Load parent tables before child tables to satisfy foreign keys.
        tables["customers"].to_sql(
            "customers", connection, schema="dreamers_staging", if_exists="append", index=False
        )
        tables["products"].to_sql(
            "products", connection, schema="dreamers_staging", if_exists="append", index=False
        )
        tables["invoices"].to_sql(
            "invoices", connection, schema="dreamers_staging", if_exists="append", index=False
        )
        tables["invoice_items"].to_sql(
            "invoice_items",
            connection,
            schema="dreamers_staging",
            if_exists="append",
            index=False,
        )

        # Keep the last successful version, then publish the new one at once.
        live_schema_exists = connection.execute(
            text("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'dreamers'")
        ).scalar()
        connection.execute(text("DROP SCHEMA IF EXISTS dreamers_previous CASCADE"))
        if live_schema_exists:
            connection.execute(text("ALTER SCHEMA dreamers RENAME TO dreamers_previous"))
        connection.execute(text("ALTER SCHEMA dreamers_staging RENAME TO dreamers"))

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
