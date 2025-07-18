# Ryan Gallagher
# SQL Query Optimization Tool 
# explain_analyzer_test.py

# Resource importing and management. 
import unittest 
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
            {'selectid': 0, 'order': 0, 'from': 0, 'detail': 'USING FILESORT'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_filesort_or_temp()

        self.assertEqual(len(analyzer.issues), 1)
        self.assertEqual(analyzer.issues[0]['type'], 'Filesort')
        self.assertIn('FILESORT', analyzer.issues[0]['message'])

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
            {'selectid': 0, 'order': 1, 'from': 1, 'detail': 'USING FILESORT'},
            {'selectid': 0, 'order': 2, 'from': 2, 'detail': 'USING TEMP TABLE'}
        ]
        analyzer = ExplainAnalyzer(explain_plan)
        analyzer._check_filesort_or_temp()

        self.assertEqual(len(analyzer.issues), 3)
        types = [issue['type'] for issue in analyzer.issues]
        self.assertIn('Using Temporary Structure', types)
        self.assertIn('Filesort', types)

# Run the tests.
suite = unittest.TestLoader().loadTestsFromTestCase(TestCheckFullTableScan)
unittest.TextTestRunner(verbosity = 2).run(suite)

suite2 = unittest.TestLoader().loadTestsFromTestCase(TestCheckMissingIndex)
unittest.TextTestRunner(verbosity = 2).run(suite2)

suite3 = unittest.TestLoader().loadTestsFromTestCase(TestCheckFilesort)
unittest.TextTestRunner(verbosity = 2).run(suite3)