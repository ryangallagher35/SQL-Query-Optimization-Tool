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

    # Tests the presence of an unindexed join.
    def test_unindexed_join_suggestion(self):
        issues = [{"type": "Unindexed JOIN", "message": "JOIN without index"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("join" in s.lower() and "index" in s.lower() for s in result))

    # Tests the presence of "LIKE" without an index.
    def test_like_without_index_suggestion(self):
        issues = [{"type": "LIKE without index", "message": "Leading wildcard used"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("like" in s.lower() and "wildcard" in s.lower() for s in result))

    # Tests ineffient "OR" conditions.
    def test_inefficient_or_conditions_suggestion(self):
        issues = [{"type": "Inefficient OR Conditions", "message": "OR condition found"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("or condition" in s.lower() or "union" in s.lower() for s in result))

    # Tests the presence of functions on indexed columns, negating the effectiveness of the indexed columns.
    def test_functions_on_indexed_columns_suggestion(self):
        issues = [{"type": "Functions on Indexed Columns", "message": "Function on indexed column"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("raw" in s.lower() for s in result))

 # Tests the presence of inefficient GROUP BY usage.
    def test_inefficient_group_by_suggestion(self):
        issues = [{"type": "Inefficient GROUP BY", "message": "GROUP BY uses temp B-tree"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("group by" in s.lower() and "index" in s.lower() for s in result))

    # Tests the presence of DISTINCT without supporting index.
    def test_distinct_without_index_suggestion(self):
        issues = [{"type": "DISTINCT Without Index", "message": "DISTINCT used without index"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("distinct" in s.lower() and "index" in s.lower() for s in result))

    # Fix the filesort test to match the actual issue type expected.
    def test_unnecessary_filesort_suggestion(self):
        issues = [{"type": "Unnecessary Filesort", "message": "Filesort operation detected"}]
        sugg = Suggestions(issues)
        result = sugg.generate_suggestions()
        self.assertTrue(any("filesort" in s.lower() for s in result))


# Run the tests.
unittest.TextTestRunner().run(unittest.TestLoader().loadTestsFromTestCase(TestSuggestions))