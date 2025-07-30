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

        if OPTIMIZATION_THRESHOLDS.get("unnecessary_filesort"):
            self._check_unnecessary_filesort() 

        if OPTIMIZATION_THRESHOLDS.get("inefficient GROUP BY"):
            self._check_inefficient_group_by() 

        if OPTIMIZATION_THRESHOLDS.get("like_without_index"):
            self._check_like_without_index()

        if OPTIMIZATION_THRESHOLDS.get("inefficient_or_conditions"):
            self._check_inefficient_or_conditions()

        if OPTIMIZATION_THRESHOLDS.get("functions_on_indexed_columns"):
            self._check_functions_on_indexed_columns()

        if OPTIMIZATION_THRESHOLDS.get("distinct_without_index"):
            self._check_distinct_without_index()

        return {
            "issues_detected": self.issues,
            "total_issues": len(self.issues)
        }

    # Detects if any part of the plan indicates a full table scan
    def _check_full_table_scan(self):
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "SCAN" in detail and "USING INDEX" not in detail:
                self.issues.append({
                    "type": "Full Table Scan",
                    "message": f"Query performs full table scan: '{row['detail']}'"
                })
            
    # Heuristically detect potential use of filesort.
    def _check_unnecessary_filesort(self):
        index_seen = False
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "USING INDEX" in detail:
                index_seen = True
            if "USE TEMP B-TREE FOR ORDER BY" in detail and not index_seen:
                self.issues.append({
                    "type": "Unnecessary Filesort",
                    "message": f"Query may be using an unnecessary filesort: '{row['detail']}'"
                })

    # Detects inefficient GROUP BY statements that yield temporary B-Trees.
    def _check_inefficient_group_by(self):
        index_seen = False
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "USING INDEX" in detail:
                index_seen = True
            if "USE TEMP B-TREE FOR GROUP BY" in detail and not index_seen:
                self.issues.append({
                    "type": "Inefficient GROUP BY",
                    "message": f"Query may be using a temporary B-Tree for the GROUP BY Clause: '{row['detail']}'"
                })

    
    # Detects inefficiencies surrounding the "LIKE" clause.
    def _check_like_without_index(self):
        like_patterns = re.findall(r"LIKE\s+['\"](.*?)['\"]", self.raw_query, flags=re.IGNORECASE)
        
        for pattern in like_patterns:
            if pattern.startswith('%'):
                self.issues.append({
                    "type": "LIKE without index",
                    "message": f"LIKE pattern starts with wildcard '{pattern}', index likely not used."
                })


    # Checks for inefficiencies pertaining to "OR" conditions.
    def _check_inefficient_or_conditions(self):
        if re.search(r'\bOR\b', self.raw_query, re.IGNORECASE):
            for row in self.explain_plan:
                detail = row.get("detail", "").upper()
                if ("SCAN" in detail) and ("INDEX" not in detail):
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
        func_calls = re.findall(r"\b[A-Z]+\s*\([^)]*\)", where_clause, re.IGNORECASE)
        if func_calls:
            self.issues.append({
                "type": "Functions on Indexed Columns",
                "message": f"Functions used in WHERE clause may disable index usage: {func_calls}"
            })

    # Detects if DISTINCT is used without an index, which can lead to inefficient execution
    def _check_distinct_without_index(self):
        if "DISTINCT" in self.raw_query:
            index_used = any(
                "INDEX" in row.get("detail", "").upper() or
                "USING" in row.get("detail", "").upper()
                for row in self.explain_plan
            )
            if not index_used:
                self.issues.append({
                    "type": "DISTINCT Without Index",
                    "message": "DISTINCT clause is used but no index was detected in the query plan."
                })
