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
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_full_table_scan()
        
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Full Table Scan')
        self.assertIn('users', analyzer.issues[0]['message'])

    # Ensures that scans using an index are not mistakenly flagged as full table scans.
    def test_no_full_table_scan_when_index_used(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users USING INDEX user_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_full_table_scan()

        self.assertEqual(len(analyzer.issues), 0)

    # Tests that the analyzer can handle mixed query plans and only flags actual performance concern.
    def test_mixed_scan_and_search(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users'},
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
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users USING TEMP B-TREE FOR ORDER BY'}
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
        explain_plan = [{'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users'}]
        raw_query = "SELECT * FROM users"
        schema_index_info = {"USERS": {"idx_lastname_firstname": ["LASTNAME", "FIRSTNAME"]}}
        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 0)

    # Test when ORDER BY is used, but no filesort appears in the explain plan; no issue expected.
    def test_order_by_but_no_filesort(self):
        explain_plan = [{'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users'}]
        raw_query = "SELECT * FROM users ORDER BY lastname, firstname"
        schema_index_info = {"USERS": {"idx_lastname_firstname": ["LASTNAME", "FIRSTNAME"]}}
        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 0)

    # Test when filesort occurs but columns are NOT covered by index; no issue should be raised.
    def test_filesort_not_covered_by_index(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users USING TEMP B-TREE FOR ORDER BY'}
        ]
        raw_query = "SELECT * FROM users ORDER BY lastname, firstname"
        schema_index_info = {"USERS": {"idx_email": ["EMAIL"]}}  # Wrong index
        analyzer = ExplainAnalyzer(explain_plan, raw_query, schema_index_info)
        analyzer._check_unnecessary_filesort()
        self.assertEqual(len(analyzer.issues), 0)

    # Test when multiple tables exist but table name cannot be inferred; should skip.
    def test_multiple_tables_unknown_target(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USING TEMP B-TREE FOR ORDER BY'}
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
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USING TEMP B-TREE FOR ORDER BY'}
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
            {'detail': 'SCAN TABLE orders'},
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SCAN TABLE customers'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Unindexed JOIN')
        self.assertIn('customers', analyzer.issues[0]['message'].lower())

    # Test that JOIN using an index is NOT flagged
    def test_indexed_join_not_flagged(self):
        explain_plan = [
            {'detail': 'SCAN TABLE orders'},
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SEARCH TABLE customers USING INDEX customer_idx (customer_id=?)'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()

        self.assertEqual(len(analyzer.issues), 0)

    # Test that JOIN using INTEGER PRIMARY KEY is NOT flagged
    def test_join_using_integer_primary_key_not_flagged(self):
        explain_plan = [
            {'detail': 'SCAN TABLE orders'},
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SEARCH TABLE customers USING INTEGER PRIMARY KEY (rowid=?)'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 0)

    # Test that no JOIN results in no issues, even if SCAN is used
    def test_no_join_no_issue(self):
        explain_plan = [
            {'detail': 'SCAN TABLE orders'},
            {'detail': 'SCAN TABLE customers'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 0)

    # Test that multiple unindexed joins are both flagged
    def test_multiple_unindexed_joins_flagged(self):
        explain_plan = [
            {'detail': 'SCAN TABLE orders'},
            {'detail': 'LOOP JOIN customers'},
            {'detail': 'SCAN TABLE customers'},
            {'detail': 'LOOP JOIN products'},
            {'detail': 'SCAN TABLE products'}
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
            {'detail': 'SCAN TABLE orders'},
            {'detail': 'LOOP JOIN customers'}
            # no access row for customers
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()
        self.assertEqual(len(analyzer.issues), 1)
        self.assertIn('customers', analyzer.issues[0]['message'].lower())


class TestUnnecessarySubquery(unittest.TestCase):

    def test_detects_nested_subquery_keyword(self):
        explain_plan = [
            {'detail': 'SUBQUERY on orders'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM (SELECT * FROM orders)"
        analyzer._check_unnecessary_subquery()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Unnecessary Subquery')

    def test_no_subquery_not_flagged(self):
        explain_plan = [
            {'detail': 'SCAN TABLE orders'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM orders"
        analyzer._check_unnecessary_subquery()

        self.assertEqual(len(analyzer.issues), 0)


class TestLikeWithoutIndex(unittest.TestCase):

    def test_leading_wildcard_like_flagged(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name LIKE '%john%'"
        analyzer._check_like_without_index()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'LIKE without index')
        self.assertIn('%john%', analyzer.issues[0]['message'])

    def test_no_leading_wildcard_not_flagged(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name LIKE 'john%'"
        analyzer._check_like_without_index()

        self.assertEqual(len(analyzer.issues), 0)

    def test_like_clause_missing(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'john'"
        analyzer._check_like_without_index()

        self.assertEqual(len(analyzer.issues), 0)


class TestInefficientOrConditions(unittest.TestCase):

    def test_or_with_full_table_scan_detected(self):
        explain_plan = [
            {'detail': 'SCAN TABLE users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR email = 'B'"
        analyzer._check_inefficient_or_conditions()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Inefficient OR Conditions')

    def test_or_with_index_not_flagged(self):
        explain_plan = [
            {'detail': 'SEARCH TABLE users USING INDEX user_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR email = 'B'"
        analyzer._check_inefficient_or_conditions()

        self.assertEqual(len(analyzer.issues), 0)

    def test_no_or_clause(self):
        explain_plan = [
            {'detail': 'SCAN TABLE users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A'"
        analyzer._check_inefficient_or_conditions()

        self.assertEqual(len(analyzer.issues), 0)

class TestFunctionsOnIndexedColumns(unittest.TestCase):

    def test_detects_function_in_where_clause(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE LOWER(name) = 'john'"
        analyzer._check_functions_on_indexed_columns()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Functions on Indexed Columns')
        self.assertIn('LOWER(name)', str(analyzer.issues[0]['message']))

    def test_no_function_in_where_clause(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'john'"
        analyzer._check_functions_on_indexed_columns()

        self.assertEqual(len(analyzer.issues), 0)


# Tests analyze method. 
class TestAnalyzer(unittest.TestCase):

    def setUp(self):
        self.full_table_scan_plan = [
            {"detail": "SCAN TABLE users"},
            {"detail": "SEARCH TABLE orders USING INDEX order_idx"}
        ]

        self.missing_index_plan = [
            {"detail": "SEARCH TABLE users"},
            {"detail": "SEARCH TABLE orders USING INDEX order_idx"}
        ]

        self.filesort_temp_plan = [
            {"detail": "USING TEMP B-TREE"},
            {"detail": "USING TEMP B-TREE FOR ORDER BY"},
            {"detail": "NO ISSUE HERE"}
        ]

        self.unindexed_join_plan = [
            {"detail": "SCAN TABLE orders"},
            {"detail": "JOIN orders to users"}
        ]

        self.subquery_plan = [
            {"detail": "SOMETHING"},  
        ]

        self.like_without_index_plan = []
        self.or_condition_plan = [
            {"detail": "SCAN TABLE users"}
        ]


        self.functions_on_index_plan = []
        self.order_by_temp_plan = [
            {"detail": "USING TEMP TABLE"}
        ]

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": True,
        "unnecessary_filesort": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                  
        "functions_on_indexed_columns": False    
    })
    def test_detect_full_table_scan(self):
        analyzer = ExplainAnalyzer(self.full_table_scan_plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Full Table Scan")

    
    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "unnecessary_filesort": True, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                  
        "functions_on_indexed_columns": False     
    })
    def test_detect_filesort_and_temp_structures(self):
        analyzer = ExplainAnalyzer(self.filesort_temp_plan)
        result = analyzer.analyze()
        types = [issue["type"] for issue in result["issues_detected"]]
        self.assertIn("Using Temporary Structure", types)
        self.assertIn("Filesort", types)
        self.assertEqual(result["total_issues"], 2)

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": True,
        "unnecessary_filesort": True, 
        "unindexed_join": True,            
        "unnecessary_subquery": True,        
        "like_without_index": True,        
        "inefficient_or_conditions": True,                
        "functions_on_indexed_columns": True  
    })
    def test_clean_plan_no_issues(self):
        clean_plan = [
            {"detail": "SCAN TABLE users USING INDEX user_idx"},
            {"detail": "SEARCH TABLE users USING INDEX user_idx"}
        ]
        analyzer = ExplainAnalyzer(clean_plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 0)


    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": True,
        "unnecessary_filesort": False, 
        "unindexed_join": True,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                 
        "functions_on_indexed_columns": False    
    })
    def test_detect_unindexed_join(self):
        analyzer = ExplainAnalyzer(self.unindexed_join_plan)
        result = analyzer.analyze()
        types = [issue["type"] for issue in result["issues_detected"]]
        self.assertIn("Full Table Scan", types)
        self.assertIn("Unindexed JOIN", types)
        self.assertEqual(result["total_issues"], 2)

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": True,
        "unnecessary_filesort": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": True,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                 
        "functions_on_indexed_columns": False   
    })
    def test_detect_unnecessary_subquery(self):
        analyzer = ExplainAnalyzer(self.subquery_plan)
        analyzer.raw_query = "SELECT * FROM (SELECT * FROM users)"
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Unnecessary Subquery")

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "unnecessary_filesort": False, 
        "unindexed_join": False,            
        "unnecessary_subquery" : False,        
        "like_without_index": True,        
        "inefficient_or_conditions": False,                  
        "functions_on_indexed_columns": False   
    })
    def test_detect_like_with_leading_wildcard(self):
        analyzer = ExplainAnalyzer(self.like_without_index_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name LIKE '%john%'"
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "LIKE without index")

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "unnecessary_filesort": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": True,                  
        "functions_on_indexed_columns": False   
    })
    def test_detect_or_condition_without_index(self):
        analyzer = ExplainAnalyzer(self.or_condition_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name = 'A' OR email = 'B'"
        result = analyzer.analyze()
        types = [issue["type"] for issue in result["issues_detected"]]
        self.assertIn("Full Table Scan", types)
        self.assertIn("Inefficient OR Conditions", types)
        self.assertEqual(result["total_issues"], 2)

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "unnecessary_filesort": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                 
        "functions_on_indexed_columns": True
    })
    def test_detect_function_on_indexed_column(self):
        analyzer = ExplainAnalyzer(self.functions_on_index_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE LOWER(name) = 'john'"
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Functions on Indexed Columns")


# Run the tests.
'''
suite1 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFullTableScan)
unittest.TextTestRunner(verbosity = 2).run(suite1)

suite2 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFilesort)
unittest.TextTestRunner(verbosity = 2).run(suite2)
'''

suite3 = unittest.TestLoader().loadTestsFromTestCase(TestUnindexedJoin)
unittest.TextTestRunner(verbosity = 2).run(suite3)

'''
suite4 = unittest.TestLoader().loadTestsFromTestCase(TestUnnecessarySubquery)
unittest.TextTestRunner(verbosity = 2).run(suite4)

suite5 = unittest.TestLoader().loadTestsFromTestCase(TestLikeWithoutIndex)
unittest.TextTestRunner(verbosity = 2).run(suite5)

suite6 = unittest.TestLoader().loadTestsFromTestCase(TestInefficientOrConditions)
unittest.TextTestRunner(verbosity = 2).run(suite6)

suite7 = unittest.TestLoader().loadTestsFromTestCase(TestFunctionsOnIndexedColumns)
unittest.TextTestRunner(verbosity = 2).run(suite7)

suite8 = unittest.TestLoader().loadTestsFromTestCase(TestAnalyzer)
unittest.TextTestRunner(verbosity=2).run(suite8)
'''