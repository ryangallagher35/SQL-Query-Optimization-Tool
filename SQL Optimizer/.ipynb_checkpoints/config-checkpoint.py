# Ryan Gallagher 
# SQL Query Optimization Tool 
# config.py 

# DB connection details are stored here. 
DB_CONFIG = {
    "db_path" : "your_database.sqlite3"
} 

# Optimization thresholds defined here. 
OPTIMIZATION_THRESHOLDS = { 
    "full_table_scan" : True,
    "unnecessary_filesort" : True, 
    "unindexed_join": True,                    
    "like_without_index": True,          
    "inefficient_or_conditions": True,   
    "functions_on_indexed_columns": True
} 

