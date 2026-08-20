import unittest

import pandas as pd

from src.transformation import assign_customer_ids


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

if __name__ == "__main__":
    unittest.main()
