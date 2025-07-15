# Ryan Gallagher 
# SQL Query Optimization Tool 
# db_connector.py 

# Resource importing and management. 
import mysql.connector 
from .config import DB_CONFIG

# Initialize the DBConnector class to encapsulatee methods that connect to the MySQL database and perform common operations.
class DBConnector: 

    # Establishes a connection to the DB using credentials outlined in DB_CONFIG.
    def __init__(self): 
        self.conn = mysql.connector.connect(**DB_CONFIG) 
        self.cursor = self.conn.cursor(dictionary = True) 

    # Executes a regular SQL query and returns all rows from the resulting query set. 
    def execute_query(self, query : str): 
        self.cursor.execute(query) 
        return self.cursor.fetchall() 

    # Returns MySQL's query plan illuminating how MYSQL will execute the given query.
    def get_explain(self, query : str): 
        explain_query = f"EXPLAIN {query}" 
        self.cursor.execute(explain_query) 
        return self.cursor.fetchall

    # Closes the cursor and the DB connection. 
    def close(self): 
        self.cursor.close() 
        self.conn.close() 
