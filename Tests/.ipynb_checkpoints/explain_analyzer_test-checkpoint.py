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

# Test suite for the _check_missing_index method.
class TestCheckMissingIndex(unittest.TestCase):

    # Verifies that the absence of "USING INDEX" is flagged as missing an index.
    def test_missing_index_detected(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SEARCH TABLE users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_missing_index()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Missing Index')
        self.assertIn('users', analyzer.issues[0]['message'])

    # Ensures that the presence of "USING INDEX" is not flagged. 
    def test_index_usage_not_flagged(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SEARCH TABLE users USING INDEX user_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_missing_index()

        self.assertEqual(len(analyzer.issues), 0)

    # Confirms "SCAN TABLE" is ignored by this method, as it is covered in _check_full_table_scan. 
    def test_non_search_operations_ignored(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE logs'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_missing_index()

        self.assertEqual(len(analyzer.issues), 0)

    # Tests multiple missing indexes in the query plan. 
    def test_multiple_missing_indexes_detected(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SEARCH TABLE users'},
            {'selectid': 0, 'order': 1, 'from': 1, 'detail': 'SEARCH TABLE orders'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_missing_index()

        self.assertEqual(len(analyzer.issues), 2)
        self.assertTrue(all(issue['type'] == 'Missing Index' for issue in analyzer.issues))

class TestCheckFilesort(unittest.TestCase):

    # Flags "USING TEMP B-TREE" as temp ysage. 
    def test_detects_using_temp_btree(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USING TEMP B-TREE'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_filesort_or_temp()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Using Temporary Structure')
        self.assertIn('TEMP B-TREE', analyzer.issues[0]['message'])

    # Flags "USING TEMP TABLE" detail
    def test_detects_using_temp_table(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USING TEMP TABLE'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_filesort_or_temp()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Using Temporary Structure')
        self.assertIn('TEMP TABLE', analyzer.issues[0]['message'])

    # Flags "USING FILESORT" detail
    def test_detects_filesort_keyword(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USING USING TEMP B-TREE FOR ORDER BY'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_filesort_or_temp()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Filesort')
        self.assertIn('USING TEMP B-TREE FOR ORDER BY', analyzer.issues[0]['message'])

    # Tests that efficient query plans don't raise any flags.
    def test_no_temp_or_filesort_detected(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE users'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_filesort_or_temp()

        self.assertEqual(len(analyzer.issues), 0)

    # Detects a conjunction of issues in a single query plan. 
    def test_multiple_temp_and_filesort(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USING TEMP B-TREE'},
            {'selectid': 0, 'order': 1, 'from': 1, 'detail': 'USING TEMP B-TREE FOR ORDER BY'},
            {'selectid': 0, 'order': 2, 'from': 2, 'detail': 'USING TEMP TABLE'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_filesort_or_temp()

        self.assertEqual(len(analyzer.issues), 3)
        types = [issue['type'] for issue in analyzer.issues]
        self.assertIn('Using Temporary Structure', types)
        self.assertIn('Filesort', types)

class TestUnindexedJoin(unittest.TestCase):

    def test_unindexed_join_detected(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE orders'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Unindexed JOIN')
        self.assertIn('orders', analyzer.issues[0]['message'])

    def test_join_with_index_not_flagged(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SCAN TABLE orders USING INDEX order_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()

        self.assertEqual(len(analyzer.issues), 0)

    def test_search_with_index_not_flagged(self):
        explain_plan = [
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'SEARCH TABLE orders USING INDEX order_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_unindexed_join()

        self.assertEqual(len(analyzer.issues), 0)


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


class TestMissingLimit(unittest.TestCase):

    def test_select_without_limit_detected(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users"
        analyzer._check_missing_limit()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Missing LIMIT')

    def test_select_with_limit_not_flagged(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users LIMIT 10"
        analyzer._check_missing_limit()

        self.assertEqual(len(analyzer.issues), 0)

    def test_non_select_query_not_flagged(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "DELETE FROM users"
        analyzer._check_missing_limit()

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


class TestOrderByWithoutIndex(unittest.TestCase):

    def test_order_by_causes_temp_usage(self):
        explain_plan = [
            {'detail': 'USING TEMP B-TREE'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users ORDER BY name"
        analyzer._check_order_by_without_index()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'ORDER BY without Index')

    def test_order_by_with_index_not_flagged(self):
        explain_plan = [
            {'detail': 'SEARCH TABLE users USING INDEX user_name_idx'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users ORDER BY name"
        analyzer._check_order_by_without_index()

        self.assertEqual(len(analyzer.issues), 0)

    def test_no_order_by_clause(self):
        explain_plan = []
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer.raw_query = "SELECT * FROM users"
        analyzer._check_order_by_without_index()

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
        "missing_index": False,
        "using_filesort_penalty": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                  
        "functions_on_indexed_columns": False,
        "order_by_without_index": False     
    })
    def test_detect_full_table_scan(self):
        analyzer = ExplainAnalyzer(self.full_table_scan_plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Full Table Scan")

    
    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "missing_index": True,
        "using_filesort_penalty": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                
        "functions_on_indexed_columns": False,
        "order_by_without_index": False     
    })
    def test_detect_missing_index(self):
        analyzer = ExplainAnalyzer(self.missing_index_plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Missing Index")

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "missing_index": False,
        "using_filesort_penalty": True, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                  
        "functions_on_indexed_columns": False,
        "order_by_without_index": False      
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
        "missing_index": True,
        "using_filesort_penalty": True, 
        "unindexed_join": True,            
        "unnecessary_subquery": True,        
        "like_without_index": True,        
        "inefficient_or_conditions": True,                
        "functions_on_indexed_columns": True,
        "order_by_without_index": True      
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
        "missing_index": False,
        "using_filesort_penalty": False, 
        "unindexed_join": True,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                 
        "functions_on_indexed_columns": False,
        "order_by_without_index": False      
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
        "missing_index": False,
        "using_filesort_penalty": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": True,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,                 
        "functions_on_indexed_columns": False,
        "order_by_without_index": False     
    })
    def test_detect_unnecessary_subquery(self):
        analyzer = ExplainAnalyzer(self.subquery_plan)
        analyzer.raw_query = "SELECT * FROM (SELECT * FROM users)"
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Unnecessary Subquery")

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "missing_index": False,
        "using_filesort_penalty": False, 
        "unindexed_join": False,            
        "unnecessary_subquery" : False,        
        "like_without_index": True,        
        "inefficient_or_conditions": False,                  
        "functions_on_indexed_columns": False,
        "order_by_without_index": False     
    })
    def test_detect_like_with_leading_wildcard(self):
        analyzer = ExplainAnalyzer(self.like_without_index_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE name LIKE '%john%'"
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "LIKE without index")

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "missing_index": False,
        "using_filesort_penalty": False, 
        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": True,   
        "missing_limit": False,                
        "functions_on_indexed_columns": False,
        "order_by_without_index": False     
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
        "missing_index": False,
        "using_filesort_penalty": False, 

        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,   
        "missing_limit": False,                
        "functions_on_indexed_columns": True,
        "order_by_without_index": False     
    })
    def test_detect_function_on_indexed_column(self):
        analyzer = ExplainAnalyzer(self.functions_on_index_plan)
        analyzer.raw_query = "SELECT * FROM users WHERE LOWER(name) = 'john'"
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Functions on Indexed Columns")

    @patch("config.OPTIMIZATION_THRESHOLDS", {
        "full_table_scan": False,
        "missing_index": False,
        "using_filesort_penalty": False, 

        "unindexed_join": False,            
        "unnecessary_subquery": False,        
        "like_without_index": False,        
        "inefficient_or_conditions": False,   
        "missing_limit": False,                
        "functions_on_indexed_columns": False,
        "order_by_without_index": True    
    })
    def test_detect_order_by_without_index(self):
        analyzer = ExplainAnalyzer(self.order_by_temp_plan)
        analyzer.raw_query = "SELECT * FROM users ORDER BY name"
        result = analyzer.analyze()
        types = [issue["type"] for issue in result["issues_detected"]]
        self.assertIn("Using Temporary Structure", types)
        self.assertIn("ORDER BY without Index", types)
        self.assertEqual(result["total_issues"], 2)


# Run the tests.
suite1 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFullTableScan)
unittest.TextTestRunner(verbosity = 2).run(suite1)

suite2 = unittest.TestLoader().loadTestsFromTestCase(TestCheckMissingIndex)
unittest.TextTestRunner(verbosity = 2).run(suite2)

suite3 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFilesort)
unittest.TextTestRunner(verbosity = 2).run(suite3)

suite4 = unittest.TestLoader().loadTestsFromTestCase(TestUnindexedJoin)
unittest.TextTestRunner(verbosity = 2).run(suite4)

suite5 = unittest.TestLoader().loadTestsFromTestCase(TestUnnecessarySubquery)
unittest.TextTestRunner(verbosity = 2).run(suite5)

suite6 = unittest.TestLoader().loadTestsFromTestCase(TestLikeWithoutIndex)
unittest.TextTestRunner(verbosity = 2).run(suite6)

suite7 = unittest.TestLoader().loadTestsFromTestCase(TestInefficientOrConditions)
unittest.TextTestRunner(verbosity = 2).run(suite7)

suite8 = unittest.TestLoader().loadTestsFromTestCase(TestMissingLimit)
unittest.TextTestRunner(verbosity = 2).run(suite8)

suite9 = unittest.TestLoader().loadTestsFromTestCase(TestFunctionsOnIndexedColumns)
unittest.TextTestRunner(verbosity = 2).run(suite9)

suite10 = unittest.TestLoader().loadTestsFromTestCase(TestFunctionsOnIndexedColumns)
unittest.TextTestRunner(verbosity = 2).run(suite10)

suite11 = unittest.TestLoader().loadTestsFromTestCase(TestAnalyzer)
unittest.TextTestRunner(verbosity=2).run(suite11)