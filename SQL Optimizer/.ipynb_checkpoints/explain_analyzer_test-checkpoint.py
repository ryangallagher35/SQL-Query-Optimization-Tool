# Ryan Gallagher
# SQL Query Optimization Tool 
# explain_analyzer_test.py

# Resource importing and management. 
import unittest 
from unittest.mock import patch
from explain_analyzer import ExplainAnalyzer

# Testing suite for _check_full_tables_scan method. 
class TestCheckFullTableScan(unittest.TestCase):

    # Test to see if a full table scan without an index is correctly flagged as a performance issue. 
    def test_full_table_scan_detected(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_full_table_scan()
        
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Full Table Scan')
        self.assertIn('users', analyzer.issues[0]['message'])

    # Ensures that scans using an index are not mistakenly flagged as full table scans.
    def test_no_full_table_scan_when_index_used(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users USING INDEX user_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_full_table_scan()

        self.assertEqual(len(analyzer.issues), 0)

    # Tests that the analyzer can handle mixed query plans and only flags actual performance concern.
    def test_mixed_scan_and_search(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users'},
            {'selectid': 0, 'order': 1, 'from': 1, 'detail': 'SEARCH TABLE orders USING INDEX order_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_full_table_scan()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Full Table Scan')

    # Verifies that efficient query structures don't yield false positives.
    def test_no_scan_present(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SEARCH TABLE products USING INDEX product_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_full_table_scan()

        self.assertEqual(len(analyzer.issues), 0)


class TestCheckFilesort(unittest.TestCase):

    # Tests if an unnecessary filesort is detected.
    def test_unnecessary_filesort_detected(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users USE TEMP B-TREE FOR ORDER BY'}
        ]
        raw_query = "SELECT * FROM users ORDER BY lastname, firstname"

        schema_index_info = {
            "USERS": {
                "idx_lastname_firstname": ["LASTNAME", "FIRSTNAME"]
            }
        }

        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Unnecessary Filesort')
        self.assertIn('USERS', analyzer.issues[0]['message'].upper())

    # Test when no ORDER BY clause exists; should not raise any issues.
    def test_no_order_by_clause(self):
        explain_plan = [{'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users'}]
        raw_query = "SELECT * FROM users"
        schema_index_info = {"USERS": {"idx_lastname_firstname": ["LASTNAME", "FIRSTNAME"]}}
        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 0)

    # Test when ORDER BY is used, but no filesort appears in the explain plan; no issue expected.
    def test_order_by_but_no_filesort(self):
        explain_plan = [{'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users'}]
        raw_query = "SELECT * FROM users ORDER BY lastname, firstname"
        schema_index_info = {"USERS": {"idx_lastname_firstname": ["LASTNAME", "FIRSTNAME"]}}
        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 0)

    # Test when filesort occurs but columns are NOT covered by index; no issue should be raised.
    def test_filesort_not_covered_by_index(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users USE TEMP B-TREE FOR ORDER BY'}
        ]
        raw_query = "SELECT * FROM users ORDER BY lastname, firstname"
        schema_index_info = {"USERS": {"idx_email": ["EMAIL"]}}  # Wrong index
        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 0)

    # Test when multiple tables exist but table name cannot be inferred; should skip.
    def test_multiple_tables_unknown_target(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN users USE TEMP B-TREE FOR ORDER BY'}
        ]
        raw_query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id ORDER BY users.lastname"
        schema_index_info = {
            "USERS": {"idx_lastname": ["LASTNAME"]},
            "ORDERS": {"idx_user_id": ["USER_ID"]}
        }

        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 0)

    # Test when only one table is present and table name is missing in detail; fallback should work.
    def test_single_table_inferred_from_context(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USE TEMP B-TREE FOR ORDER BY'}
        ]
        raw_query = "SELECT * FROM users ORDER BY lastname"
        schema_index_info = {
            "USERS": {"idx_lastname": ["LASTNAME"]}
        }
        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Unnecessary Filesort')

   
class TestUnindexedJoin(unittest.TestCase):
    
    # Test that an unindexed JOIN is detected when both tables are scanned
    def test_detects_unindexed_join(self):
        explain_plan = [
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SCAN customers'}
        ]
 
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Unindexed JOIN')
        self.assertIn('customers', analyzer.issues[0]['message'].lower())
        

    # Test that JOIN using an index is NOT flagged
    def test_indexed_join_not_flagged(self):
        explain_plan = [
            {'detail': 'SCAN orders'},
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SEARCH TABLE customers USING INDEX customer_idx (customer_id=?)'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()

        self.assertEqual(len(analyzer.issues), 0)

    # Test that JOIN using INTEGER PRIMARY KEY is NOT flagged
    def test_join_using_integer_primary_key_not_flagged(self):
        explain_plan = [
            {'detail': 'SCAN orders'},
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SEARCH TABLE customers USING INTEGER PRIMARY KEY (rowid=?)'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 0)

    # Test that no JOIN results in no issues, even if SCAN is used
    def test_no_join_no_issue(self):
        explain_plan = [
            {'detail': 'SCAN orders'},
            {'detail': 'SCAN customers'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 0)

    # Test that multiple unindexed joins are both flagged
    def test_multiple_unindexed_joins_flagged(self):
        explain_plan = [
            {'detail': 'SCAN orders'},
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SCAN customers'},
            {'detail': 'LOOP JOIN products'},
            {'detail': 'SCAN products'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 2)
        messages = [issue['message'].lower() for issue in analyzer.issues]
        self.assertTrue(any('customers' in m for m in messages))
        self.assertTrue(any('products' in m for m in messages))

    # Test JOIN listed but missing table access row — should be flagged as unknown
    def test_join_with_missing_access_info(self):
        explain_plan = [
            {'detail': 'SCAN orders'},
            {'detail': 'LOOP JOIN customers'}
            # no access row for customers
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertIn('customers', analyzer.issues[0]['message'].lower())


class TestLikeWithoutIndex(unittest.TestCase):

    # Tests leading wildcard instance, should yield an issue.
    def test_leading_wildcard_like_flagged(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name LIKE '%john%'"
        analyzer._check_like_without_index()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'LIKE without index')
        self.assertIn('%john%', analyzer.issues[0]['message'])

    # Tests lack of leading wildcard instance, should not yield and issue.
    def test_no_leading_wildcard_not_flagged(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name LIKE 'john%'"
        analyzer._check_like_without_index()
        self.assertEqual(len(analyzer.issues), 0)

    # Tests instance where "LIKE" clause doesn't appear, ensures false positives do not occur.
    def test_like_clause_missing(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'john'"
        analyzer._check_like_without_index()
        self.assertEqual(len(analyzer.issues), 0)


class TestInefficientOrConditions(unittest.TestCase):

    # Tests inefficient OR instance amidst a full table scan.
    def test_or_with_full_table_scan_detected(self):
        explain_plan = [
            {'detail': 'SCAN users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR email = 'B'"
        analyzer._check_inefficient_or_conditions()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Inefficient OR Conditions')

    # Tests efficient OR instance where an index is used, should not yield any issues.
    def test_or_with_index_not_flagged(self):
        explain_plan = [
            {'detail': 'SEARCH TABLE users USING INDEX user_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR email = 'B'"
        analyzer._check_inefficient_or_conditions()
        self.assertEqual(len(analyzer.issues), 0)

    # Tests instance where no "OR" clause appears, protects against false positives.
    def test_no_or_clause(self):
        explain_plan = [
            {'detail': 'SCAN users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A'"
        analyzer._check_inefficient_or_conditions()
        self.assertEqual(len(analyzer.issues), 0)

    # Test: OR condition on same column using index should not be flagged
    def test_or_on_same_indexed_column(self):
        explain_plan = [
            {'detail': 'SEARCH TABLE users USING INDEX user_name_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR name = 'B'"
        analyzer._check_inefficient_or_conditions()
        self.assertEqual(len(analyzer.issues), 0)

    # Test: Mixed plan — one using index, one full scan — should still be flagged
    def test_or_with_partial_index_usage(self):
        explain_plan = [
            {'detail': 'SEARCH TABLE users USING INDEX user_name_idx'},
            {'detail': 'SCAN users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR email = 'B'"
        analyzer._check_inefficient_or_conditions()
        self.assertEqual(len(analyzer.issues), 1)

    # Test: Malformed query still containing OR should be flagged based on plan
    def test_or_with_malformed_query(self):
        explain_plan = [{'detail': 'SCAN users'}]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR"
        analyzer._check_inefficient_or_conditions()
        self.assertEqual(len(analyzer.issues), 1)


class TestFunctionsOnIndexedColumns(unittest.TestCase):

    # Tests a function in WHERE clause that would negate an index.
    def test_detects_function_in_where_clause(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE LOWER(name) = 'john'"
        analyzer._check_functions_on_indexed_columns()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Functions on Indexed Columns')
        self.assertIn('LOWER(name)', str(analyzer.issues[0]['message']))

    # Ensures false positives do not occur when no function occurs in WHERE clause.
    def test_no_function_in_where_clause(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'john'"
        analyzer._check_functions_on_indexed_columns()
        self.assertEqual(len(analyzer.issues), 0)

class TestExplainAnalyzer(unittest.TestCase):

    # Ensures all checks are triggered.
    def test_all_checks_triggered(self):
        explain_plan = [
            {'detail': 'SCAN users USE TEMP B-TREE FOR ORDER BY'},
            {'detail': 'SCAN users'},  
            {'detail': 'SCAN customers'},  
            {'detail': 'LOOP JOIN customers'},
        ]
        raw_query = """
            SELECT * FROM users 
            JOIN customers ON users.id = customers.user_id 
            WHERE LOWER(name) = 'john' OR email LIKE '%example.com%' 
            ORDER BY lastname, firstname
        """
        schema_index_info = {
            "USERS": {"idx_lastname_firstname": ["LASTNAME", "FIRSTNAME"]},
            "CUSTOMERS": {}
        }

        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        result = analyzer.analyze()

        issue_types = [issue['type'] for issue in result['issues_detected']]

        self.assertIn('Full Table Scan', issue_types)
        self.assertIn('Unindexed JOIN', issue_types)
        self.assertIn('Unnecessary Filesort', issue_types)
        self.assertIn('Functions on Indexed Columns', issue_types)
        self.assertIn('LIKE without index', issue_types)
        self.assertIn('Inefficient OR Conditions', issue_types)
        self.assertEqual(result['total_issues'], 8)

    # Ensures no issues are detected.
    def test_no_issues_detected(self):
        explain_plan = [
            {'detail': 'SEARCH TABLE users USING INDEX user_idx'},
            {'detail': 'SEARCH TABLE customers USING INDEX cust_idx'},
        ]
        raw_query = "SELECT * FROM users JOIN customers ON users.id = customers.user_id WHERE name = 'John' ORDER BY lastname"
        schema_index_info = {
            "USERS": {"idx_lastname": ["LASTNAME"]},
            "CUSTOMERS": {"cust_idx": ["USER_ID"]}
        }

        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        result = analyzer.analyze()

        self.assertEqual(result['total_issues'], 0)
        self.assertEqual(result['issues_detected'], [])

    # Tests whether a subset of the issues occur.
    def test_partial_issues_detected(self):
        explain_plan = [
            {'detail': 'SCAN users'},
            {'detail': 'USE TEMP B-TREE FOR ORDER BY'}
        ]
        raw_query = "SELECT * FROM users WHERE email LIKE '%gmail.com%' ORDER BY lastname"
        schema_index_info = {
            "USERS": {"idx_lastname": ["LASTNAME"]}
        }

        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        result = analyzer.analyze()

        issue_types = [issue['type'] for issue in result['issues_detected']]

        self.assertIn('Full Table Scan', issue_types)
        self.assertIn('Unnecessary Filesort', issue_types)
        self.assertIn('LIKE without index', issue_types)
        self.assertEqual(result['total_issues'], 3)


# Run the tests.
runner = unittest.TextTestRunner(verbosity = 2, buffer = False) 

suite1 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFullTableScan)
runner.run(suite1)

suite2 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFilesort)
runner.run(suite2)

suite3 = unittest.TestLoader().loadTestsFromTestCase(TestUnindexedJoin)
runner.run(suite3)

suite4 = unittest.TestLoader().loadTestsFromTestCase(TestLikeWithoutIndex)
runner.run(suite4)

suite5 = unittest.TestLoader().loadTestsFromTestCase(TestInefficientOrConditions)
runner.run(suite5)

suite6 = unittest.TestLoader().loadTestsFromTestCase(TestFunctionsOnIndexedColumns)
runner.run(suite6)

suite7 = unittest.TestLoader().loadTestsFromTestCase(TestExplainAnalyzer)
runner.run(suite7)