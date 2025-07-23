# Ryan Gallagher  
# SQL Query Optimization Tool  
# explain_analyzer.py

# Resource importing and management
from config import OPTIMIZATION_THRESHOLDS
import re

# Analyzes output from get_explain and flags inefficiencies based on thresholds confined in config.py.
class ExplainAnalyzer:

    # Initializes the explain output from SQLite as input.
    def __init__(self, explain_plan, raw_query = ""):
        self.explain_plan = explain_plan
        self.raw_query = raw_query.upper() 
        self.issues = []

    # Main analysis method that runs all checks based on OPTIMIZATION_THRESHOLDS from config.py
    def analyze(self):
        if OPTIMIZATION_THRESHOLDS.get("full_table_scan"):
            self._check_full_table_scan()

        if OPTIMIZATION_THRESHOLDS.get("missing_index"):
            self._check_missing_index()

        if OPTIMIZATION_THRESHOLDS.get("using_filesort_penalty"):
            self._check_filesort_or_temp()

        # New features.
        if OPTIMIZATION_THRESHOLDS.get("unindexed_join"):
            self._check_unindexed_join()

        if OPTIMIZATION_THRESHOLDS.get("unnecessary_subquery"):
            self._check_unnecessary_subquery()

        if OPTIMIZATION_THRESHOLDS.get("like_without_index"):
            self._check_like_without_index()

        if OPTIMIZATION_THRESHOLDS.get("inefficient_or_conditions"):
            self._check_inefficient_or_conditions()

        if OPTIMIZATION_THRESHOLDS.get("functions_on_indexed_columns"):
            self._check_functions_on_indexed_columns()

        if OPTIMIZATION_THRESHOLDS.get("order_by_without_index"):
            self._check_order_by_without_index()

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

    # Heuristically detect potential use of filesort or temporary data structures.
    def _check_filesort_or_temp(self):
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "USING TEMP B-TREE FOR ORDER BY" in detail:  
                self.issues.append({
                    "type": "Filesort",
                    "message": f"Filesort operation detected: '{row['detail']}'"
                })
            elif "USING TEMP B-TREE" in detail or "USING TEMP TABLE" in detail:
                self.issues.append({
                    "type": "Using Temporary Structure",
                    "message": f"Temporary structure used: '{row['detail']}'"
                })

    # Detects unindexed JOIN in detail.
    def _check_unindexed_join(self):
            for row in self.explain_plan:
                detail = row.get("detail", "").upper()
                if "JOIN" in detail and "INDEX" not in detail:
                    self.issues.append({
                        "type": "Unindexed JOIN",
                        "message": f"JOIN or table scan without index: '{row['detail']}'"
                    })
                    
    # Detects possible unecessary subqeuries in SELECT statements.
    def _check_unnecessary_subquery(self):
        if "SUBQUERY" in " ".join(r.get("detail", "").upper() for r in self.explain_plan) or \
           "SELECT" in self.raw_query and "SELECT" in self.raw_query[self.raw_query.find("SELECT") + 1:]:
            self.issues.append({
                "type": "Unnecessary Subquery",
                "message": "Query contains nested subqueries which may be optimized."
            })

    # Detects if raw_query has LIKE with leading % and no index used.
    def _check_like_without_index(self):
        if "LIKE" in self.raw_query:
            like_patterns = re.findall(r"LIKE\s+'(.*?)'", self.raw_query)
            for pattern in like_patterns:
                if pattern.startswith("%"):
                    self.issues.append({
                        "type": "LIKE without index",
                        "message": f"LIKE pattern starts with wildcard '{pattern}', index not used."
                    })

    # Checks if raw_query contains OR and explain indicates no index usage.
    def _check_inefficient_or_conditions(self):
        if " OR " in self.raw_query:
            for row in self.explain_plan:
                detail = row.get("detail", "").upper()
                if "SCAN" in detail and "INDEX" not in detail:
                    self.issues.append({
                        "type": "Inefficient OR Conditions",
                        "message": "OR condition detected that may prevent index usage."
                    })
                    break

    # Checks for function usage in WHERE clauses that disable indexes.
    def _check_functions_on_indexed_columns(self):
        where_clause = ""
        if "WHERE" in self.raw_query:
            where_clause = self.raw_query.split("WHERE")[1]
        func_calls = re.findall(r"\b[A-Z]+\s*\([^)]*\)", where_clause)
        if func_calls:
            self.issues.append({
                "type": "Functions on Indexed Columns",
                "message": f"Functions used in WHERE clause may disable index usage: {func_calls}"
            })

    # Checks if ORDER BY is present but plan shows temp table or no index usage.
    def _check_order_by_without_index(self):
        if "ORDER BY" in self.raw_query:
            temp_usage = any("USING TEMP" in r.get("detail", "").upper() for r in self.explain_plan)
            if temp_usage:
                self.issues.append({
                    "type": "ORDER BY without Index",
                    "message": "ORDER BY causes temporary table usage, index might be missing."
                })

     


