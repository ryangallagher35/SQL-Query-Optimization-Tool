# SQL Query Optimization Tool

_By: Ryan Gallagher_

<img width="98" height="28" alt="image" src="https://github.com/user-attachments/assets/34b3c917-7c17-4c3d-8981-ad4e5a030db5" />  <img width="85" height="28" alt="image" src="https://github.com/user-attachments/assets/70255b18-aaf6-4be7-85ad-25bca9637d22" /> <img width="85" height="28" alt="image" src="https://github.com/user-attachments/assets/48f38168-502b-4304-8446-4d2a6d35a0ff" /> <img width="85" height="28" alt="image" src="https://github.com/user-attachments/assets/a68d7f20-1709-4a4e-98f4-af9e92ec497f" />


## Overview

The **SQL Query Optimization Tool** is a Python-based web application designed to analyze and optimize SQL queries for SQLite databases. It helps developers identify performance inefficiencies by parsing queries, analyzing execution plans, and providing optimal suggestions to improve query efficiency. This tool leverages Flask for the backend, and offers a user-friendly interface built with HTML, CSS, and JavaScript. The performance of this tool has been extensively tested in the respective modules located in the "Tests" file and currently passes 113 test cases covering all components of functionality. 

## Features

- **Query Analysis:** Parses SQL queries to extract tables, columns, joins, conditions, and subqueries.
- **Explain Plan Inspection:** Retrieves and analyzes SQLite’s query execution plan to identify inefficiencies.
- **Issue Detection:** Detects common issues such as full table scans, unnecessary filesorts, missing indexes, and more!
- **Optimization Suggestions:** Offers tailored recommendations for query improvements based on detected issues.
- **Interactive UI:** Provides an easy-to-use web interface to input SQL queries and database paths and view detailed results.
- **Supports Common SQL Clauses:** Handles complex query components like WHERE, JOIN, ORDER BY, GROUP BY, HAVING, LIMIT, and subqueries.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/sql-query-optimizer.git
   cd SQL-Query-Optimization-Tool

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt

4. **Run the application:**

   ```bash
   python app.py

5. **Use the application:**

   ```bash
   Open your browser and go to http://127.0.0.1:5000

## Usage

1. Enter the **path to your SQLite database file** in the "Database Path" field.  
2. Input the **SQL query** you want to analyze.  
3. Click the **Analyze** button.  
4. View detailed output including:  
   - Query summary (tables, joins, conditions, etc.)  
   - Detected issues with the query  
   - Optimization suggestions  
   - SQLite explain plan  
   - Query results
  
