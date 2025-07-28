# Ryan Gallagher
# SQL Query Optimization Tool
# suggestions.py


# Constructs a list of dicts describing detected query inefficiencies from ExplainAnalyzer.
class Suggestions:

    # Initializes issues_detected.
    def __init__(self, issues_detected):
        self.issues = issues_detected

    # Constructs a set of suggestions to improve the efficiency of the user's query based on the flagged issue type.
    def generate_suggestions(self):
        suggestions = []

        for issue in self.issues:
            issue_type = issue.get("type")
            message = issue.get("message", "")

            if issue_type == "Full Table Scan":
                suggestions.append(
                    "The query performs a full table scan without using any index. "
                    "Consider adding indexes on columns used in WHERE or JOIN conditions to avoid full scans."
                )

            elif issue_type == "Unnecessary Filesort":
                suggestions.append(
                    "SQLite is using a temporary B-tree for ORDER BY, even though an index might cover the sort columns. "
                    "Ensure ORDER BY columns match the leading columns of an available index in order."
                )

            elif issue_type == "Unindexed JOIN":
                suggestions.append(
                    "A JOIN operation is being executed without using an index on the joined column. "
                    "Consider adding indexes on columns used in JOIN conditions to reduce scan costs."
                )

            elif issue_type == "LIKE without index":
                suggestions.append(
                    "A LIKE clause uses a leading wildcard (e.g., '%value'), which prevents index usage. "
                    "If possible, avoid leading wildcards or use full-text search for better performance."
                )

            elif issue_type == "Inefficient OR Conditions":
                suggestions.append(
                    "OR conditions can prevent index use if not carefully structured. "
                    "Consider breaking the query into separate indexed queries combined with UNION."
                )

            elif issue_type == "Functions on Indexed Columns":
                suggestions.append(
                    "Functions are applied to columns in the WHERE clause, which disables index use. "
                    "Consider rewriting conditions to compare raw column values directly when possible."
                )

            else:
                suggestions.append(f"No specific suggestion available for issue: {message}")

        if not suggestions:
            suggestions.append("No issues detected. Query appears to be optimized based on current thresholds.")

        return suggestions