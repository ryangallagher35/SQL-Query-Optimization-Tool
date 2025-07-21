# Ryan Gallagher
# SQL Query Optimization Tool
# suggestions.py

 # Constructs a list of dicts describing detected query inefficiencies from ExplainAnalyzer.
class Suggestions:

    def __init__(self, issues_detected):
        self.issues = issues_detected

    def generate_suggestions(self):
        suggestions = []

        for issue in self.issues:
            issue_type = issue.get("type")
            message = issue.get("message", "")

            if issue_type == "Full Table Scan":
                suggestions.append(
                    "Consider adding appropriate indexes on columns used in WHERE or JOIN clauses "
                    "to avoid full table scans."
                )

            elif issue_type == "Missing Index":
                suggestions.append(
                    "Create indexes on columns involved in search conditions to speed up data retrieval."
                )

            elif issue_type == "Using Temporary Structure":
                suggestions.append(
                    "Optimize query to reduce the need for temporary tables or sorting operations; "
                    "consider rewriting joins or adding indexes."
                )

            elif issue_type == "Filesort":
                suggestions.append(
                    "Avoid ORDER BY operations that require filesort; "
                    "index columns involved in sorting or limit sorting where possible."
                )

                        elif issue_type == "Unindexed JOIN":
                suggestions.append(
                    "Add indexes to columns used in JOIN conditions to improve performance and reduce scan costs."
                )

            elif issue_type == "Unnecessary Subquery":
                suggestions.append(
                    "Consider flattening nested subqueries or using JOINs where applicable to simplify and speed up the query."
                )

            elif issue_type == "LIKE without index":
                suggestions.append(
                    "Avoid using leading wildcards (e.g., '%value') in LIKE patterns; consider full-text search or redesigning the query."
                )

            elif issue_type == "Inefficient OR Conditions":
                suggestions.append(
                    "Rewrite OR conditions using UNION or ensure each condition benefits from an index to maintain performance."
                )

            elif issue_type == "Functions on Indexed Columns":
                suggestions.append(
                    "Avoid wrapping indexed columns in functions in the WHERE clause; refactor the query to allow index usage."
                )

            elif issue_type == "ORDER BY without Index":
                suggestions.append(
                    "Add indexes to columns used in ORDER BY to avoid temporary table usage and improve sort performance."
                )

            else:
                suggestions.append(f"No specific suggestion available for issue: {message}")

        if not suggestions:
            suggestions.append("No issues detected. Query is optimized based on current thresholds.")

        return suggestions