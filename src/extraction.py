import json
import os

import pandas as pd


PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(PROJECT_FOLDER, "config.json")
print(CONFIG_FILE)


def extract_data():
    """Read the ecommerce CSV file and return a DataFrame."""
    with open(CONFIG_FILE, encoding="utf-8") as config_file:
        config = json.load(config_file)

    source = os.path.join(PROJECT_FOLDER, config["source"])
    file_path = os.path.join(source, "dreamers_ecommerce.csv")
    data = pd.read_csv(file_path)

    print(f"Extracted {len(data)} rows")
    return data


def extraction():
    """Run the extraction step as an Airflow task."""
    return extract_data()


if __name__ == "__main__":
    extraction()
