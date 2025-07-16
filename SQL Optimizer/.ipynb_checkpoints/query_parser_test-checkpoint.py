# Ryan Gallagher
# SQL Query Optimization Tool 
# query_parser_test.py 

# Library importing and management. 
import unittest
from query_parser import QueryParser  

# Testing suite for the get_tables method. 
class TestGetTables(unittest.TestCase):

    # Tests get_tables for a single table instance.
    def test_single_table(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_tables(), ["users"])

    # Test get_tables for an instance of multiple tables.
    def test_multiple_tables_with_joins(self):
        query = "SELECT u.id, o.amount FROM users u JOIN orders o ON u.id = o.user_id;"
        qp = QueryParser(query)
        self.assertEqual(set(qp.get_tables()), set(["users", "orders"]))

    # Tests get_tables with alias handling.
    def test_alias_handling(self):
        query = "SELECT a.name FROM accounts a;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_tables(), ["accounts"])

    # Tests get_tables to see if it can handle a conjunction of comma-separated lists and aliases.
    def test_identifier_list(self):
        query = "SELECT * FROM users u, accounts a WHERE u.id = a.user_id;"
        qp = QueryParser(query)
        self.assertEqual(set(qp.get_tables()), set(["users", "accounts"]))

    # Ensures that the method works even when improper querying syntax is employed
    def test_case_insensitivity(self):
        query = "SeLeCt * FrOm Customers;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_tables(), ["Customers"])

# Testing suite for get_columns method.
class TestGetColumns(unittest.TestCase):

    # Tests a single column instance.
    def test_single_column(self):
        query = "SELECT id FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_columns(), ["id"])

    # Tests multiple column instance.
    def test_multiple_columns(self):
        query = "SELECT id, name, email FROM users;"
        qp = QueryParser(query)
        self.assertEqual(set(qp.get_columns()), set(["id", "name", "email"]))

    # Tests instance where an alias precedes the wildcard character.
    def test_table_prefixed_star(self):
        query = "SELECT u.* FROM users u;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_columns(), ["u.*"])

    # Tests the wildcard instance.
    def test_wildcard_star(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_columns(), ["*"])

    # Tests a hybrid query comprising of column aliases and wildcards. 
    def test_mixed_columns_and_star(self):
        query = "SELECT u.id, u.*, o.amount FROM users u JOIN orders o ON u.id = o.user_id;"
        qp = QueryParser(query)
        self.assertEqual(set(qp.get_columns()), set(["id", "u.*", "amount"]))

    # Tests alias handling in column extraction. 
    def test_alias_handling(self):
        query = "SELECT a.name, a.email FROM accounts a;"
        qp = QueryParser(query)
        self.assertEqual(set(qp.get_columns()), set(["name", "email"]))

    # Tests the instance where no columns appear.
    def test_no_columns(self):
        query = "SELECT FROM users;"  # Invalid, but should return empty or []
        qp = QueryParser(query)
        self.assertEqual(qp.get_columns(), [])

# Runs the tests. 
print("Test results for get_tables: ")
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetTables))
print(" ")

print("Test results for get_columns: ")
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetColumns))
print("") 