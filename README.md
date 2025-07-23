# SQL Query Optimization Tool

## Overview

The **SQL Query Optimization Tool** is a Python-based web application designed to analyze and optimize SQL queries for SQLite databases. It helps developers identify performance bottlenecks by parsing queries, analyzing execution plans, and providing actionable suggestions to improve query efficiency. This tool leverages Flask for the backend, and offers a user-friendly interface built with HTML, CSS, and JavaScript.

## Features

- **Query Analysis:** Parses SQL queries to extract tables, columns, joins, conditions, and subqueries.
- **Explain Plan Inspection:** Retrieves and analyzes SQLite’s query execution plan to identify inefficiencies.
- **Issue Detection:** Detects common issues such as full table scans, missing indexes, filesorts, unindexed joins, and unnecessary subqueries.
- **Optimization Suggestions:** Offers tailored recommendations for query improvements based on detected issues.
- **Interactive UI:** Provides an easy-to-use web interface to input SQL queries and database paths and view detailed results.
- **Supports Common SQL Clauses:** Handles complex query components like WHERE, JOIN, ORDER BY, GROUP BY, HAVING, LIMIT, and subqueries.

## Installation

1. **Clone the repository:**

   git clone https://github.com/yourusername/sql-query-optimizer.git
   cd sql-query-optimizer

2. ** Install dependencies: **

   pip install -r requirements.txt

3. Run the application:

   python app.py

4. Open your browser and go to http://127.0.0.1:5000

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
