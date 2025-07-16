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

    # Test case insensitivity. 
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

# Testing suite for the get_joins method.
class TestGetJoins(unittest.TestCase):

    # Test single INNER JOIN instance.
    def test_inner_join(self):
        query = "SELECT u.id, p.name FROM users u INNER JOIN profiles p ON u.id = p.user_id;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_joins(), ["INNER JOIN profiles p"])

    # Test multiple JOIN instances (i.e. INNER, LEFT OUTER). 
    def test_multiple_joins(self):
        query = """
        SELECT u.id, p.name, l.time 
        FROM users u 
        INNER JOIN profiles p ON u.id = p.user_id 
        LEFT OUTER JOIN logins l ON p.id = l.profile_id;
        """
        qp = QueryParser(query)
        self.assertEqual(
            qp.get_joins(), 
            ["INNER JOIN profiles p", "LEFT OUTER JOIN logins l"]
        )

    # Test mere JOIN instance (no qualifier such INNER/LEFT, etc.). 
    def test_plain_join(self):
        query = "SELECT * FROM a JOIN b ON a.id = b.a_id;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_joins(), ["JOIN b"])

    # Test alias handling in JOIN clauses. 
    def test_join_with_alias(self):
        query = "SELECT * FROM customer c JOIN orders o ON c.id = o.customer_id;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_joins(), ["JOIN orders o"])

    # Test case insensitivity.
    def test_case_insensitive_join(self):
        query = "SELECT * FROM users u LeFt JoIn orders o ON u.id = o.user_id;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_joins(), ["LeFt JoIn orders o"])

    # Test instance where no join appears in query. 
    def test_no_joins(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_joins(), [])

# Testing suite for get_conditions method.
class TestGetConditions(unittest.TestCase):

    # Test a basic single condition
    def test_single_condition(self):
        query = "SELECT * FROM users WHERE age > 30;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["age > 30"])

    # Test multiple conditions with AND
    def test_multiple_conditions_and(self):
        query = "SELECT * FROM users WHERE age > 30 AND status = 'active';"
        qp = QueryParser(query)
        self.assertEqual(
            qp.get_conditions(),
            ["age > 30", "AND", "status = 'active'"]
        )

    # Test multiple conditions with OR
    def test_multiple_conditions_or(self):
        query = "SELECT * FROM users WHERE city = 'New York' OR city = 'Chicago';"
        qp = QueryParser(query)
        self.assertEqual(
            qp.get_conditions(),
            ["city = 'New York'", "OR", "city = 'Chicago'"]
        )

    # Test parentheses and nested conditions
    def test_nested_conditions(self):
        query = "SELECT * FROM users WHERE (age > 30 AND status = 'active') OR role = 'admin';"
        qp = QueryParser(query)
        self.assertEqual(
            qp.get_conditions(),
            ["(age > 30 AND status = 'active')", "OR", "role = 'admin'"]
        )

    # Test condition with LIKE operator
    def test_like_condition(self):
        query = "SELECT * FROM users WHERE name LIKE 'R%';"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["name LIKE 'R%'"])

    # Test case insensitivity in WHERE clause
    def test_case_insensitive_where(self):
        query = "SELECT * FROM users wHeRe age = 25;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["age = 25"])

    # Test query with no WHERE clause
    def test_no_where_clause(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), [])

    # Test WHERE clause using BETWEEN
    def test_between_condition(self):
        query = "SELECT * FROM orders WHERE amount BETWEEN 100 AND 500;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["amount  BETWEEN 100  AND 500"])

    # Test WHERE clause using IN
    def test_in_condition(self):
        query = "SELECT * FROM customers WHERE region IN ('North', 'East');"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["region IN ('North', 'East')"])

# Testing suite for the summarize_query method.
class TestSummarizeQuery(unittest.TestCase):

    # Test summary with all components
    def test_full_summary(self):
        query = """
        SELECT u.id, u.name, o.amount 
        FROM users u 
        INNER JOIN orders o ON u.id = o.user_id 
        WHERE o.amount > 100 AND u.status = 'active';
        """
        qp = QueryParser(query)
        summary = qp.summarize_query()
        print(summary["tables"])
        self.assertEqual(set(summary["tables"]), {"users", "orders"})
        self.assertEqual(set(summary["columns"]), {"id", "name", "amount"})
        self.assertEqual(summary["joins"], ["INNER JOIN orders o"])
        self.assertEqual(
            summary["conditions"], 
            ["o.amount > 100", "AND", "u.status = 'active'"]
        )

    # Test summary with wildcard column
    def test_summary_with_star(self):
        query = "SELECT * FROM customers;"
        qp = QueryParser(query)
        summary = qp.summarize_query()
        self.assertEqual(summary["tables"], ["customers"])
        self.assertEqual(summary["columns"], ["*"])
        self.assertEqual(summary["joins"], [])
        self.assertEqual(summary["conditions"], [])

    '''
    # Test summary with BETWEEN and alias
    def test_summary_with_between(self):
        query = "SELECT o.* FROM orders o WHERE o.date BETWEEN '2024-01-01' AND '2024-12-31';"
        qp = QueryParser(query)
        summary = qp.summarize_query()
        self.assertEqual(summary["tables"], ["orders"])
        self.assertEqual(summary["columns"], ["o.*"])
        self.assertEqual(summary["joins"], [])
        self.assertEqual(summary["conditions"], ["o.date  BETWEEN '2024-01-01'  AND '2024-12-31'"])
    '''

    # Test summary for query without WHERE or JOIN
    def test_summary_minimal(self):
        query = "SELECT name FROM employees;"
        qp = QueryParser(query)
        summary = qp.summarize_query()
        self.assertEqual(summary["tables"], ["employees"])
        self.assertEqual(summary["columns"], ["name"])
        self.assertEqual(summary["joins"], [])
        self.assertEqual(summary["conditions"], [])

    # Test case insensitivity across all elements
    def test_case_insensitivity_summary(self):
        query = "SeLeCt * FrOm Sales s LeFt JoIn Regions r On s.region_id = r.id WhErE r.name = 'East';"
        qp = QueryParser(query)
        summary = qp.summarize_query()
        print(summary["tables"])
        self.assertEqual(set(summary["tables"]), {"Sales", "Regions"})
        self.assertEqual(summary["columns"], ["*"])
        self.assertEqual(summary["joins"], ["LeFt JoIn Regions r"])
        self.assertEqual(summary["conditions"], ["r.name = 'East'"])


# Runs the tests. 
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetTables))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetColumns))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetJoins))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetConditions))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestSummarizeQuery))