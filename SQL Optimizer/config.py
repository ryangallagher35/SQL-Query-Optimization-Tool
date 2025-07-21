# Ryan Gallagher 
# SQL Query Optimization Tool 
# config.py 

# DB connection details are stored here. 
DB_CONFIG = {
    "db_path" : "your_database.sqlite3"
} 

# Optimization thresholds defined here. ***(may want to add more)***
OPTIMIZATION_THRESHOLDS = { 
    "full_table_scan" : True,
    "missing_index" : True,
    "using_filesort_penalty" : True, 

    # New features.
    "unindexed_join": True,              # Detect JOINs on columns without indexes
    "unnecessary_subquery": True,        # Detect unnecessary/nested subqueries
    "like_without_index": True,          # Detect LIKE queries that cannot use index
    "inefficient_or_conditions": True,   # Detect OR conditions that disable indexes
    "functions_on_indexed_columns": True,# Detect functions applied on indexed columns in WHERE
    "order_by_without_index": True     # Detect ORDER BY without index
} 
