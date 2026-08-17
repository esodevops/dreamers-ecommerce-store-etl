from dotenv import load_dotenv

from loading import loading


load_dotenv()


def run_pipeline():
    """Run the complete ETL pipeline."""
    loading()


if __name__ == "__main__":
    run_pipeline()
