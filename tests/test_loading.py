import unittest
from unittest.mock import MagicMock, patch

from src.loading import write_database_tables


class StagingLoadTests(unittest.TestCase):
    @patch("src.loading.create_engine")
    def test_loads_staging_before_swapping_schemas(self, create_engine):
        connection = MagicMock()
        connection.execute.return_value.scalar.return_value = True
        create_engine.return_value.begin.return_value.__enter__.return_value = connection
        tables = {
            "customers": MagicMock(),
            "products": MagicMock(),
            "invoices": MagicMock(),
            "invoice_items": MagicMock(),
        }

        write_database_tables(tables, "dreamers_db")

        for table in tables.values():
            self.assertEqual(table.to_sql.call_args.kwargs["schema"], "dreamers_staging")

        sql = [str(call.args[0]) for call in connection.execute.call_args_list]
        self.assertIn("ALTER SCHEMA dreamers RENAME TO dreamers_previous", sql)
        self.assertEqual(sql[-1], "ALTER SCHEMA dreamers_staging RENAME TO dreamers")


if __name__ == "__main__":
    unittest.main()
