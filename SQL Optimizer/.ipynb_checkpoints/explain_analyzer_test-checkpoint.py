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

# Tests analyze method. 
class TestAnalyzer(unittest.TestCase):

    # Sample explain plans for tests.
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
            {"detail": "SOME OPERATION USING TEMP B-TREE FOR ORDER BY"},
            {"detail": "NO ISSUE HERE"}
        ]
        self.clean_plan = [
            {"detail": "SCAN TABLE users USING INDEX user_idx"},
            {"detail": "SEARCH TABLE users USING INDEX user_idx"}
        ]

    # Tests full table scan instance.
    @patch("config.OPTIMIZATION_THRESHOLDS", {"full_table_scan": True, "missing_index": True, "using_filesort_penalty": True})
    def test_detect_full_table_scan(self):
        analyzer = ExplainAnalyzer(self.full_table_scan_plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Full Table Scan")
        self.assertIn("scan", result["issues_detected"][0]["message"].lower())

    # Tests missing index instance.
    @patch("config.OPTIMIZATION_THRESHOLDS", {"full_table_scan": False, "missing_index": True, "using_filesort_penalty": False})
    def test_detect_missing_index(self):
        analyzer = ExplainAnalyzer(self.missing_index_plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Missing Index")
        self.assertIn("no index", result["issues_detected"][0]["message"].lower())

    # Tests whether the code flags the presence of filesorts and inefficient temp data structures.
    @patch("config.OPTIMIZATION_THRESHOLDS", {"full_table_scan": False, "missing_index": False, "using_filesort_penalty": True})
    def test_detect_filesort_and_temp(self):
        analyzer = ExplainAnalyzer(self.filesort_temp_plan)
        result = analyzer.analyze()
        types = [issue["type"] for issue in result["issues_detected"]]
        self.assertIn("Using Temporary Structure", types)
        self.assertIn("Filesort", types)
        self.assertEqual(result["total_issues"], 2)

    # Tests if code handles clean queries correctly.
    @patch("config.OPTIMIZATION_THRESHOLDS", {"full_table_scan": True, "missing_index": True, "using_filesort_penalty": True})
    def test_no_issues_detected(self):
        analyzer = ExplainAnalyzer(self.clean_plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 0)
        self.assertEqual(result["issues_detected"], [])

    # Tests whether case insensitivity is handled correctly. 
    @patch("config.OPTIMIZATION_THRESHOLDS", {"full_table_scan": True})
    def test_full_table_scan_case_insensitivity(self):
        plan = [{"detail": "scan table"}]
        analyzer = ExplainAnalyzer(plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)

    # Tests the case when a table search employs an index. 
    @patch("config.OPTIMIZATION_THRESHOLDS", {"missing_index": True})
    def test_missing_index_false_positive(self):
        plan = [{"detail": "SEARCH TABLE users USING INDEX"}]
        analyzer = ExplainAnalyzer(plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 0)

    # Tests filesort presence instance. 
    @patch("config.OPTIMIZATION_THRESHOLDS", {"using_filesort_penalty": True})
    def test_filesort_detection_no_sqlite_actual(self):
        plan = [{"detail": "operation USING TEMP B-TREE FOR ORDER BY"}]
        analyzer = ExplainAnalyzer(plan)
        result = analyzer.analyze()
        self.assertEqual(result["total_issues"], 1)
        self.assertEqual(result["issues_detected"][0]["type"], "Filesort")


# Run the tests.
suite1 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFullTableScan)
unittest.TextTestRunner(verbosity = 2).run(suite1)

suite2 = unittest.TestLoader().loadTestsFromTestCase(TestCheckMissingIndex)
unittest.TextTestRunner(verbosity = 2).run(suite2)

suite3 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFilesort)
unittest.TextTestRunner(verbosity = 2).run(suite3)

suite4 = unittest.TestLoader().loadTestsFromTestCase(TestAnalyzer)
unittest.TextTestRunner(verbosity=2).run(suite4)