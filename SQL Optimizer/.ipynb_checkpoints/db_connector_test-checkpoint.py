# Ryan Gallagher 
# SQL Query Optimization Tool 
# db_connector_test.py 

import os
import sqlite3

## Create a sample test SQLite DB file and add sample data.

DB_PATH = "your_database.sqlite3"

# Delete the file if it exists to start fresh each run
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


# Create a simple table 'users' with sample data
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL
)
''')

cursor.executemany('INSERT INTO users (name, age) VALUES (?, ?)', [
    ('Alice', 30),
    ('Bob', 25),
    ('Charlie', 35)
])

conn.commit()
conn.close()


## Update the DB_CONFIG for testing.

from config import DB_CONFIG
DB_CONFIG['db_path'] = DB_PATH

# Import and test DBConnector.
from db_connector import DBConnector

db = DBConnector()

# Test: Fetch all users
users = db.execute_query("SELECT * FROM users")
print("Users in DB:")
for user in users:
    print(user)


# Test: Get explain plan of a simple query
explain = db.get_explain("SELECT * FROM users WHERE age > 25")
print("\nExplain plan for 'SELECT * FROM users WHERE age > 25':")
for row in explain:
    print(row)

db.close()