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

    # Test a basic single condition.
    def test_single_condition(self):
        query = "SELECT * FROM users WHERE age > 30;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["age > 30"])

    # Test multiple conditions with AND.
    def test_multiple_conditions_and(self):
        query = "SELECT * FROM users WHERE age > 30 AND status = 'active';"
        qp = QueryParser(query)
        self.assertEqual(
            qp.get_conditions(),
            ["age > 30", "AND", "status = 'active'"]
        )

    # Test multiple conditions with OR.
    def test_multiple_conditions_or(self):
        query = "SELECT * FROM users WHERE city = 'New York' OR city = 'Chicago';"
        qp = QueryParser(query)
        self.assertEqual(
            qp.get_conditions(),
            ["city = 'New York'", "OR", "city = 'Chicago'"]
        )

    # Test parentheses and nested conditions.
    def test_nested_conditions(self):
        query = "SELECT * FROM users WHERE (age > 30 AND status = 'active') OR role = 'admin';"
        qp = QueryParser(query)
        self.assertEqual(
            qp.get_conditions(),
            ["(age > 30 AND status = 'active')", "OR", "role = 'admin'"]
        )

    # Test condition with LIKE operator.
    def test_like_condition(self):
        query = "SELECT * FROM users WHERE name LIKE 'R%';"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["name LIKE 'R%'"])

    # Test case insensitivity in WHERE clause.
    def test_case_insensitive_where(self):
        query = "SELECT * FROM users wHeRe age = 25;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["age = 25"])

    # Test query with no WHERE clause.
    def test_no_where_clause(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), [])

    # Test WHERE clause using BETWEEN.
    def test_between_condition(self):
        query = "SELECT * FROM orders WHERE amount BETWEEN 100 AND 500;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["amount BETWEEN 100 AND 500"])

    # Test WHERE clause using IN.
    def test_in_condition(self):
        query = "SELECT * FROM customers WHERE region IN ('North', 'East');"
        qp = QueryParser(query)
        self.assertEqual(qp.get_conditions(), ["region IN ('North', 'East')"])

# Testing suite for get_order_by method.
class TestGetOrderBy(unittest.TestCase):

    # Tests ORDER BY functionality when a single column is employed with ASC.
    def test_single_column_asc(self):
        query = "SELECT * FROM users ORDER BY name ASC;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_order_by(), [("name", "ASC")])

    # Tests ORDER BY functionality when a single column is employed with DESC.
    def test_single_column_desc(self):
        query = "SELECT * FROM users ORDER BY age DESC;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_order_by(), [("age", "DESC")])

    # Tests ORDER BY functionality when multiple columns are given.
    def test_multiple_columns(self):
        query = "SELECT * FROM users ORDER BY last_name ASC, first_name DESC;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_order_by(), [("last_name", "ASC"), ("first_name", "DESC")])

    # Tests if the empty set is returned when no "ORDER BY" clause is given,
    def test_no_order_by(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_order_by(), [])

    # Tests ORDER BY functionality when aliases are employed.
    def test_order_by_with_alias(self):
        query = "SELECT u.id, u.name FROM users u ORDER BY u.name DESC;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_order_by(), [("u.name", "DESC")])

# Testing suite for the get_group_by method.
class TestGetGroupBy(unittest.TestCase):

    # Test single GROUP BY column.
    def test_single_group_by(self):
        query = "SELECT department, COUNT(*) FROM employees GROUP BY department;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_group_by(), ["department"])

    # Test multiple GROUP BY columns.
    def test_multiple_group_by(self):
        query = "SELECT department, role, COUNT(*) FROM employees GROUP BY department, role;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_group_by(), ["department", "role"])

    # Test GROUP BY with aliases.
    def test_group_by_with_alias(self):
        query = "SELECT e.department, COUNT(*) FROM employees e GROUP BY e.department;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_group_by(), ["e.department"])

    # Test GROUP BY followed by ORDER BY.
    def test_group_by_with_order_by(self):
        query = "SELECT category, SUM(price) FROM products GROUP BY category ORDER BY category ASC;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_group_by(), ["category"])

    # Test GROUP BY followed by LIMIT.
    def test_group_by_with_limit(self):
        query = "SELECT city, COUNT(*) FROM customers GROUP BY city LIMIT 5;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_group_by(), ["city"])

    # Test GROUP BY with spacing and case variation.
    def test_group_by_case_insensitivity(self):
        query = "select region, sum(sales) from sales_data gRoUp By region;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_group_by(), ["region"])

    # Test query without GROUP BY should return empty list.
    def test_no_group_by(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_group_by(), [])

# Testing suite for get_having method.
class TestGetHaving(unittest.TestCase):

    # Tests a simple single HAVING condition.
    def test_single_having_condition(self):
        query = "SELECT department, COUNT(*) FROM employees GROUP BY department HAVING COUNT(*) > 5;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_having(), ["COUNT(*) > 5"])

    # Tests multiple HAVING conditions combined with AND.
    def test_multiple_having_conditions_and(self):
        query = """
        SELECT department, AVG(salary) 
        FROM employees 
        GROUP BY department 
        HAVING AVG(salary) > 50000 AND COUNT(*) > 10;
        """
        qp = QueryParser(query)
        self.assertEqual(qp.get_having(), ["AVG(salary) > 50000", "AND", "COUNT(*) > 10"])

    # Tests multiple HAVING conditions combined with OR.
    def test_multiple_having_conditions_or(self):
        query = """
        SELECT department, SUM(bonus) 
        FROM employees 
        GROUP BY department 
        HAVING SUM(bonus) > 10000 OR COUNT(*) < 5;
        """
        qp = QueryParser(query)
        self.assertEqual(qp.get_having(), ["SUM(bonus) > 10000", "OR", "COUNT(*) < 5"])

    # Tests HAVING clause with complex expressions and parentheses.
    def test_complex_having_conditions(self):
        query = """
        SELECT department, COUNT(*)
        FROM employees
        GROUP BY department
        HAVING (COUNT(*) > 5 AND AVG(salary) < 70000) OR MAX(bonus) > 10000;
        """
        qp = QueryParser(query)
        self.assertEqual(qp.get_having(), ["(COUNT(*) > 5", "AND", "AVG(salary) < 70000)", "OR", "MAX(bonus) > 10000"])

    # Tests HAVING clause case insensitivity.
    def test_case_insensitive_having(self):
        query = """
        SELECT category, SUM(sales)
        FROM orders
        GROUP BY category
        haVinG SUM(sales) > 1000;
        """
        qp = QueryParser(query)
        self.assertEqual(qp.get_having(), ["SUM(sales) > 1000"])

    # Tests no HAVING clause returns empty list.
    def test_no_having_clause(self):
        query = "SELECT category FROM orders GROUP BY category;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_having(), [])

# Test suite for get_limit method.
class TestGetLimit(unittest.TestCase):

    # Test simple LIMIT with a single numeric value
    def test_simple_limit(self):
        query = "SELECT * FROM users LIMIT 10;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), 10)

    # Test LIMIT with no number (invalid SQL, should handle gracefully)
    def test_limit_no_number(self):
        query = "SELECT * FROM users LIMIT ;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), None)  # Assuming None if invalid or no limit

    # Test no LIMIT clause
    def test_no_limit(self):
        query = "SELECT * FROM users;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), None)

    # Test LIMIT with zero
    def test_limit_zero(self):
        query = "SELECT * FROM products LIMIT 0;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), 0)

    # Test LIMIT with large numbers
    def test_large_limit(self):
        query = "SELECT * FROM logs LIMIT 1000000;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), 1000000)

    # Test LIMIT with whitespace and mixed case keywords
    def test_limit_case_and_whitespace(self):
        query = "SELECT * FROM users LiMiT    15 ;"
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), 15)

    # Test LIMIT with comments inside query
    def test_limit_with_comment(self):
        query = """
        SELECT * FROM users
        -- Limit the number of results
        LIMIT 50;
        """
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), 50)

    # Test LIMIT with parentheses.
    def test_limit_with_parentheses(self):
        query = "SELECT * FROM users LIMIT (10);"
        qp = QueryParser(query)
        self.assertEqual(qp.get_limit(), (10))

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

    # Test summary with BETWEEN and alias
    def test_summary_with_between(self):
        query = "SELECT o.* FROM orders o WHERE o.date BETWEEN '2024-01-01' AND '2024-12-31';"
        qp = QueryParser(query)
        summary = qp.summarize_query()
        self.assertEqual(summary["tables"], ["orders"])
        self.assertEqual(summary["columns"], ["o.*"])
        self.assertEqual(summary["joins"], [])
        self.assertEqual(summary["conditions"], ["o.date BETWEEN '2024-01-01' AND '2024-12-31'"])

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
        self.assertEqual(set(summary["tables"]), {"Sales", "Regions"})
        self.assertEqual(summary["columns"], ["*"])
        self.assertEqual(summary["joins"], ["LeFt JoIn Regions r"])
        self.assertEqual(summary["conditions"], ["r.name = 'East'"])

# Runs the tests. 
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetTables))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetColumns))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetJoins))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetConditions))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetOrderBy))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetGroupBy))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetHaving))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestGetLimit))
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestSummarizeQuery))