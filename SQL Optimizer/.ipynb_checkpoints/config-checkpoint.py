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
    "using_filesort_penalty" : True
} 
