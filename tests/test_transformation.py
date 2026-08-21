import unittest
from unittest.mock import patch

import pandas as pd

from src.transformation import assign_customer_ids, transform_data


class AssignCustomerIdsTests(unittest.TestCase):
    def test_preserves_known_customer_across_multiple_invoices(self):
        data = pd.DataFrame(
            {
                "InvoiceNo": ["A", "A", "B"],
                "CustomerID": [123.0, 123.0, 123.0],
            }
        )

        self.assertEqual(assign_customer_ids(data).tolist(), [123, 123, 123])

    def test_fills_missing_id_from_the_same_invoice(self):
        data = pd.DataFrame(
            {
                "InvoiceNo": ["A", "A", "B"],
                "CustomerID": [123.0, None, 456.0],
            }
        )

        self.assertEqual(assign_customer_ids(data).tolist(), [123, 123, 456])

    def test_assigns_one_non_colliding_id_per_anonymous_invoice(self):
        data = pd.DataFrame(
            {
                "InvoiceNo": ["anonymous-2", "known", "anonymous-1", "anonymous-2"],
                "CustomerID": [None, 200.0, None, None],
            }
        )

        self.assertEqual(assign_customer_ids(data).tolist(), [201, 200, 202, 201])


class HistoricalPriceTests(unittest.TestCase):
    def test_keeps_the_price_paid_on_each_invoice_item(self):
        data = pd.DataFrame(
            {
                "InvoiceNo": ["A", "A", "A"],
                "InvoiceDate": ["2026-01-01"] * 3,
                "CustomerID": [123] * 3,
                "Country": ["Finland"] * 3,
                "StockCode": ["P1"] * 3,
                "Description": ["Product"] * 3,
                "UnitPrice": [10.0, 12.0, 10.0],
                "Quantity": [1, 2, 3],
            }
        )

        with patch("src.transformation.extract_data", return_value=data):
            tables = transform_data()

        self.assertNotIn("UnitPrice", tables["products"].columns)
        self.assertEqual(
            tables["invoice_items"][["UnitPrice", "Quantity"]].values.tolist(),
            [[10.0, 4.0], [12.0, 2.0]],
        )

if __name__ == "__main__":
    unittest.main()
