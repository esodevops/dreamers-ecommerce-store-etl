# Dreamers Ecommerce ETL Pipeline

This project extracts a raw ecommerce CSV file, transforms it into four related datasets, saves the processed data as CSV files, and loads the results into PostgreSQL for analytics.

## Pipeline overview

The pipeline performs the following steps:

1. Reads `dreamers_ecommerce.csv` from the source directory in `config.json`.
2. Assigns one customer ID to each invoice.
3. Converts invoice dates to a datetime format.
4. Creates customer, product, invoice, and invoice-item datasets.
5. Saves the processed datasets as CSV files.
6. Creates the configured PostgreSQL database if it does not exist.
7. Creates the `dreamers` schema and its four tables.
8. Loads the processed data into PostgreSQL.
9. Provides an Apache Airflow DAG that orchestrates the extract, transform, and load stages.

## Project structure

```text
Dreamers-Ecommerce-Store/
├── config.json
├── dataset/
│   ├── raw_data/
│   │   └── dreamers_ecommerce.csv
│   └── processed_data/
│       ├── customer.csv
│       ├── product.csv
│       ├── invoice.csv
│       └── invoice_items.csv
├── notebooks/
│   └── dreamers-etl.ipynb
├── dags/
│   └── dag-dreamers.py
├── sql/
│   └── dreamers.sql
├── src/
│   ├── dreamers-etl.py
│   ├── extraction.py
│   ├── transformation.py
│   └── loading.py
├── .env
├── requirements.txt
└── README.md
```

## Technologies

- Python
- pandas
- SQLAlchemy
- psycopg2
- PostgreSQL
- Jupyter Notebook
- Apache Airflow
- Airflow SMTP provider

## Requirements

Before running the project, install:

- Python 3
- PostgreSQL
- `psql`, if you want to run the analytics file from the terminal

PostgreSQL must be running and the configured user must be able to create databases and tables.

## Setup

### 1. Clone or download the project

Open a terminal in the project root:

```bash
git clone https://github.com/esodevops/dreamers-ecommerce-store-etl.git
cd dreamers-ecommerce-store-etl
```

All commands in this README should be run from the project root.

### 2. Create a virtual environment

```bash
python3 -m venv dreamers_ENV
source dreamers_ENV/bin/activate
```

On Windows:

```powershell
python -m venv dreamers_ENV
dreamers_ENV\Scripts\activate
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create a `.env` file in the project root:

```env
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dreamers_db
```

Do not commit `.env` because it contains database credentials.

The PostgreSQL user must already exist. The ETL creates `DB_NAME` automatically when it is missing.

### 5. Configure the data paths

`config.json` contains the source and destination directories:

```json
{
    "source": "dataset/raw_data",
    "destination": "dataset/processed_data"
}
```

The source directory must contain a file named `dreamers_ecommerce.csv`.

## Source data

The raw CSV is expected to contain these columns:

| Column | Description |
|---|---|
| `InvoiceNo` | Invoice identifier |
| `InvoiceDate` | Invoice date and time |
| `CustomerID` | Original customer identifier |
| `StockCode` | Product identifier |
| `Description` | Product description |
| `Quantity` | Number of units |
| `UnitPrice` | Price per unit |
| `Country` | Customer country |

The pipeline generates a consistent customer ID for each invoice, starting after `406829`.

## Run the ETL pipeline

With the virtual environment activated:

```bash
python src/dreamers-etl.py
```

Alternatively:

```bash
dreamers_ENV/bin/python src/dreamers-etl.py
```

A successful run prints messages similar to:

```text
Extracted 541909 rows
Prepared customer IDs and invoice dates
Created customers, products, invoices and invoice items
Loaded CSV files and PostgreSQL tables
```

> **Important:** Each run drops and recreates the four tables in the `dreamers` schema. Existing data in those tables is replaced.

## Run with Apache Airflow

The project includes `dags/dag-dreamers.py`, which defines the
`dreamers_ecommerce_dag` batch pipeline. It runs three Python tasks in this
order:

```text
extraction_layer → transformation_layer → loading_layer
```

The DAG is manually triggered (`schedule=None`), does not backfill historical
runs (`catchup=False`), retries a failed task once after one minute, and can
send an email notification when a task fails.

### 1. Set the Airflow home directory

Use a project-local directory for Airflow's metadata and logs:

```bash
export AIRFLOW_HOME="$PWD/.airflow"
```

### 2. Make the DAG available to Airflow

Point Airflow at this project's `dags` directory:

```bash
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
```

Keep the PostgreSQL variables from `.env` configured as described above. The
loading module reads the project-level `.env` file when the DAG runs.

### 3. Start Airflow

With the virtual environment activated, start the local Airflow services:

```bash
airflow standalone
```

Open the URL printed by Airflow, sign in with the generated administrator
credentials, locate `dreamers_ecommerce_dag`, enable it, and trigger a run.

You can also trigger the DAG from another terminal after Airflow has started:

```bash
airflow dags trigger dreamers_ecommerce_dag
```

### Optional failure email notifications

The DAG uses the `smtp_default` Airflow connection and reads the recipient and
sender address from `AIRFLOW_ALERT_EMAIL`. Set the email address before starting
Airflow:

```bash
export AIRFLOW_ALERT_EMAIL="you@example.com"
```

Configure an Airflow connection named `smtp_default` with the SMTP host,
credentials, port, and TLS settings required by your email provider. Without a
working SMTP connection, the ETL can still run, but Airflow cannot deliver task
failure emails.

> **Important:** The Airflow loading task uses the same replacement behavior as
> the command-line ETL: it drops and recreates the four tables in the
> `dreamers` schema.

## Processed outputs

The destination directory receives four CSV files:

| File | Contents |
|---|---|
| `customer.csv` | One row per generated customer |
| `product.csv` | One row per stock code |
| `invoice.csv` | One row per invoice |
| `invoice_items.csv` | Total quantity for each invoice and stock-code combination |

## Database model

The PostgreSQL database uses the `dreamers` schema.

### `dreamers.customers`

| Column | Type | Constraint |
|---|---|---|
| `CustomerID` | `INT` | Primary key |
| `Country` | `VARCHAR(255)` | — |

### `dreamers.products`

| Column | Type | Constraint |
|---|---|---|
| `StockCode` | `VARCHAR(255)` | Primary key |
| `Description` | `VARCHAR(255)` | — |
| `UnitPrice` | `DECIMAL(10,2)` | — |

### `dreamers.invoices`

| Column | Type | Constraint |
|---|---|---|
| `InvoiceNo` | `VARCHAR(255)` | Primary key |
| `CustomerID` | `INT` | Foreign key to `customers` |
| `InvoiceDate` | `TIMESTAMP` | — |

### `dreamers.invoice_items`

| Column | Type | Constraint |
|---|---|---|
| `InvoiceNo` | `VARCHAR(255)` | Foreign key to `invoices` |
| `StockCode` | `VARCHAR(255)` | Foreign key to `products` |
| `Quantity` | `INT` | — |

`InvoiceNo` and `StockCode` form the composite primary key.

## Run the analytics queries

The file `sql/dreamers.sql` contains ten simple analytics queries.

Use the values stored in `.env` without manually entering the password:

```bash
set -a
source .env
PGPASSWORD="$DB_PASSWORD" psql \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -f sql/dreamers.sql
```

The queries report:

- Total customers, products, invoices, and quantity sold
- Customers by country
- Average product price
- Most expensive products
- Customers with the most invoices
- Products with the highest quantity sold
- Invoices with the highest sales value

## Connect to the database manually

```bash
psql -h localhost -U dreamers_db -d dreamers_db
```

At the password prompt, enter the value of `DB_PASSWORD` from `.env`.

Inside `psql`, list the Dreamers tables with:

```sql
\dt dreamers.*
```

Run a quick check with:

```sql
SELECT COUNT(*) FROM dreamers.invoices;
```

Exit with:

```sql
\q
```

## Troubleshooting

### Password authentication failed

Make sure the username and password match `DB_USER` and `DB_PASSWORD` in `.env`. To avoid typing a different password accidentally, run `psql` with `PGPASSWORD` as shown above.

### PostgreSQL is not running

Start the PostgreSQL service and rerun the pipeline. On macOS with Homebrew, this is commonly:

```bash
brew services start postgresql
```

The exact service name can include a version number, such as `postgresql@16`.

### Database does not exist

Run the ETL pipeline first. It connects to the default `postgres` database and creates the database named by `DB_NAME`.

### Source CSV not found

Confirm that:

```text
dataset/raw_data/dreamers_ecommerce.csv
```

exists, or update the `source` value in `config.json`.

### Relation does not exist

Run the ETL pipeline before running `sql/dreamers.sql`. The pipeline creates the `dreamers` schema and tables.

### Case-sensitive column names

The database columns use names such as `"CustomerID"` and `"InvoiceNo"`. PostgreSQL queries must place these mixed-case names in double quotes.

### DAG does not appear in Airflow

Confirm that `AIRFLOW__CORE__DAGS_FOLDER` points to the absolute path of the
project's `dags` directory, then check for import errors:

```bash
airflow dags list-import-errors
```

### Failure notification cannot be sent

Confirm that `AIRFLOW_ALERT_EMAIL` is set and that the `smtp_default` Airflow
connection contains valid SMTP settings. The task logs contain the underlying
connection or authentication error.

## Main files

- `src/dreamers-etl.py` — executable ETL pipeline
- `src/extraction.py` — reusable extraction task
- `src/transformation.py` — reusable transformation task
- `src/loading.py` — CSV and PostgreSQL loading task
- `dags/dag-dreamers.py` — Apache Airflow DAG and task dependencies
- `notebooks/dreamers-etl.ipynb` — notebook version of the workflow
- `config.json` — source and destination paths
- `sql/dreamers.sql` — analytics queries
- `requirements.txt` — Python dependencies
