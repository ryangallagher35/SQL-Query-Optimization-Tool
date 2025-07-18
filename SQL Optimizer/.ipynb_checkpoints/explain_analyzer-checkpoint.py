# Ryan Gallagher  
# SQL Query Optimization Tool  
# explain_analyzer.py

# Resource importing and management
from config import OPTIMIZATION_THRESHOLDS

# Analyzes output from get_explain and flags inefficiencies based on thresholds confined in config.py.
class ExplainAnalyzer:

    # Initializes the explain output from SQLite as input.
    def __init__(self, explain_plan):
        self.explain_plan = explain_plan
        self.issues = []

    # Main analysis method that runs all checks based on OPTIMIZATION_THRESHOLDS from config.py
    def analyze(self):
        if OPTIMIZATION_THRESHOLDS.get("full_table_scan"):
            self._check_full_table_scan()

        if OPTIMIZATION_THRESHOLDS.get("missing_index"):
            self._check_missing_index()

        if OPTIMIZATION_THRESHOLDS.get("using_filesort_penalty"):
            self._check_filesort_or_temp()

        return {
            "issues_detected": self.issues,
            "total_issues": len(self.issues)
        }

    # Detects if any part of the plan indicates a full table scan
    def _check_full_table_scan(self):
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "SCAN" in detail and "INDEX" not in detail:
                self.issues.append({
                    "type": "Full Table Scan",
                    "message": f"Query performs full scan: '{row['detail']}'"
                })
            

    # Detects if an index was not used where expected
    def _check_missing_index(self):
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "SEARCH" in detail and "INDEX" not in detail:
                self.issues.append({
                    "type": "Missing Index",
                    "message": f"No index used in search: '{row['detail']}'"
                })

    # Heuristically detect potential use of filesort or temp ops
    def _check_filesort_or_temp(self):
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "USING TEMP B-TREE" in detail or "USING TEMP TABLE" in detail:
                self.issues.append({
                    "type": "Using Temporary Structure",
                    "message": f"Temporary structure used: '{row['detail']}'"
                })
            elif "USING FILESORT" in detail:  # SQLite won't actually say this
                self.issues.append({
                    "type": "Filesort",
                    "message": f"Filesort operation detected: '{row['detail']}'"
                })



     


