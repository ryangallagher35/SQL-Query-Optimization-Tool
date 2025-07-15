# Ryan Gallagher 
# SQL Query Optimization Tool 
# config.py 

# DB connection details are stored here. 
DB_CONFIG = {
    "host" : "localhost", 
    "port" : 3306, 
    "user" : "your_username", 
    "password" : "your_password", 
    "database" : "your_database   
} 

# Optimization thresholds defined here. ***(may want to add more)***
OPTIMIZATION_THRESHOLDS = { 
    "using_filesort_penality" : True
} 
