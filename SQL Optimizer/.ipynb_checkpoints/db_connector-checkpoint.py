# Ryan Gallagher 
# SQL Query Optimization Tool 
# db_connector.py 

# Resource importing and management. 
import sqlite3
from config import DB_CONFIG

# Initialize the DBConnector class to encapsulatee methods that connect to the SQLite database and perform common operations.
class DBConnector: 

    # Establishes a connection to the DB using credentials outlined in DB_CONFIG.
    '''
    def __init__(self): 
        self.conn = sqlite3.connect(DB_CONFIG["db_path"])
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    '''
    def __init__(self, db_path = None):
        # Use passed db_path or fall back to config
        self.db_path = db_path if db_path else DB_CONFIG["db_path"]
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    
    # Executes a regular SQL query and returns all rows from the resulting query set. 
    def execute_query(self, query : str): 
        self.cursor.execute(query) 
        rows = self.cursor.fetchall() 
        return [dict(row) for row in rows]
        

    # Returns SQLite's query plan illuminating how SQLite will execute the given query.
    def get_explain(self, query : str): 
        explain_query = f"EXPLAIN {query}" 
        self.cursor.execute(explain_query) 
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    # Closes the cursor and the DB connection. 
    def close(self): 
        self.cursor.close() 
        self.conn.close() 
