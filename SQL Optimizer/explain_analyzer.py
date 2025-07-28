# Ryan Gallagher  
# SQL Query Optimization Tool  
# explain_analyzer.py

# Resource importing and management
from config import OPTIMIZATION_THRESHOLDS
from query_parser import QueryParser
import re

# Analyzes output from get_explain and flags inefficiencies based on thresholds confined in config.py.
class ExplainAnalyzer:

    # Initializes the explain output from SQLite as input.
    def __init__(self, explain_plan, raw_query = "", schema_index_info = None):
        self.explain_plan = explain_plan
        self.raw_query = raw_query.upper() 
        self.schema_index_info = schema_index_info or {}
        self.issues = []

    # Main analysis method that runs all checks based on OPTIMIZATION_THRESHOLDS from config.py
    def analyze(self):
        if OPTIMIZATION_THRESHOLDS.get("full_table_scan"):
            self._check_full_table_scan()

        if OPTIMIZATION_THRESHOLDS.get("unnecessary_filesort"):
            self._check_unnecessary_filesort() 

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

        return {
            "issues_detected": self.issues,
            "total_issues": len(self.issues)
        }

    # Detects if any part of the plan indicates a full table scan
    def _check_full_table_scan(self):
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "SCAN TABLE" in detail and "INDEX" not in detail:
                self.issues.append({
                    "type": "Full Table Scan",
                    "message": f"Query performs full scan: '{row['detail']}'"
                })
            
    # Heuristically detect potential use of filesort or temporary data structures.
    def _check_unnecessary_filesort(self):
        parser = QueryParser(self.raw_query)
        order_by_cols = parser.get_order_by_columns()
        tables = parser.get_tables()

        if not order_by_cols or not tables:
            return  

        for row in self.explain_plan:
            detail = row.get("detail", "").upper()
            if "USING TEMP B-TREE FOR ORDER BY" in detail:
        
                table_name = None
                if "TABLE" in detail:
                    parts = detail.split("TABLE")
                    if len(parts) > 1:
                        table_name = parts[1].split()[0].strip()

                if not table_name and len(tables) == 1:
                    table_name = tables[0].upper()

                if not table_name:
                    continue

                index_info = self.schema_index_info.get(table_name.upper(), {})
                if self._order_by_covered_by_index(order_by_cols, index_info):
                    self.issues.append({
                        "type": "Unnecessary Filesort",
                        "message": f"Temp B-tree used for ORDER BY on '{table_name}', but ORDER BY columns appear to be index-covered: '{row['detail']}'"
                    })

    # Checks if the columns used in an ORDER BY clause are covered by any existing index, in correct order.
    def _order_by_covered_by_index(self, order_by_cols, index_dict):
        for indexed_cols in index_dict.values():
            if [col.upper() for col in indexed_cols[:len(order_by_cols)]] == order_by_cols:
                return True
        return False

    # Detects unindexed joins in SQL statements.
    def _check_unindexed_join(self):
        join_tables = set()
        access_info = {}
        
        for row in self.explain_plan:
            detail = row.get("detail", "").upper()


            if "JOIN" in detail:
                parts = detail.split()
                for i, word in enumerate(parts):
                    if word.endswith("JOIN") and i + 1 < len(parts):
                        join_tables.add(parts[i + 1])
            
            
            if "TABLE" in detail:
                table_name = None
                if "SCAN TABLE" in detail:
                    table_name = detail.split("SCAN TABLE")[1].split()[0]
                    access_info[table_name] = "SCAN"
                elif "SEARCH TABLE" in detail:
                    table_name = detail.split("SEARCH TABLE")[1].split()[0]
                    if "USING INDEX" in detail or "USING COVERING INDEX" in detail or "USING INTEGER PRIMARY KEY" in detail:
                        access_info[table_name] = "INDEXED"
                    else:
                        access_info[table_name] = "UNINDEXED_SEARCH"
        
        for table in join_tables:
            access = access_info.get(table, "UNKNOWN")
            if access != "INDEXED":
                self.issues.append({
                    "type": "Unindexed JOIN",
                    "message": f"JOIN on table '{table}' without index (access: {access})"
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
                if ("SCAN TABLE" in detail) and ("INDEX" not in detail):
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
