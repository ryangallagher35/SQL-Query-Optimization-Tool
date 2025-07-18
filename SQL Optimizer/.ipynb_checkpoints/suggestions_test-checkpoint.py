# Ryan Gallagher
# SQL Query Optimization Tool
# suggestions.py

# Resource importing and management.
import unittest
from suggestions import Suggestions

class TestSuggestions(unittest.TestCase):

    # Tests that no issues are raised when none are present.
    def test_no_issues(self):
        sugg = Suggestions([])
        result = sugg.generate_suggestions()
        self.assertEqual(len(result), 1)
        self.assertIn("No issues detected", result[0])

    # Tests full table scan instance.
    def test_full_table_scan_suggestion(self):
        issues = [{"type": "Full Table Scan", "message": "Full scan detected"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("indexes" in s.lower() for s in result))

    # Tests missing index instance.
    def test_missing_index_suggestion(self):
        issues = [{"type": "Missing Index", "message": "No index used"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("create indexes" in s.lower() or "indexes" in s.lower() for s in result))

    # Tests the presence of an inefficient temporary structure.
    def test_using_temp_structure_suggestion(self):
        issues = [{"type": "Using Temporary Structure", "message": "Temporary table used"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("temporary tables" in s.lower() for s in result))

    # Tests the presence of filesort usage.
    def test_filesort_suggestion(self):
        issues = [{"type": "Filesort", "message": "Filesort operation detected"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("filesort" in s.lower() for s in result))

    # Tests the presence of an unknown issue.
    def test_unknown_issue_type(self):
        issues = [{"type": "Unknown Issue", "message": "Something odd happened"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("no specific suggestion" in s.lower() for s in result))

# Run the tests.
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestSuggestions))