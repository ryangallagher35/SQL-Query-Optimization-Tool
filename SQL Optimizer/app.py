# Ryan Gallagher
# SQL Query Optimization Tool 
# app.py

# Resource importing and management. 
from flask import Flask, render_template, request, jsonify
from db_connector import DBConnector
from query_parser import QueryParser
from suggestions import Suggestions
from explain_analyzer import ExplainAnalyzer
import config
import os

app = Flask(__name__)

# Provides analysis of a SQL query given a SQLite DB. 
def analyze_query(query, db_path):
    db = DBConnector(db_path = db_path)

    try:
        query_results = db.execute_query(query)
        explain_rows = db.get_explain(query)

        analyzer = ExplainAnalyzer(explain_rows, raw_query = query)
        analysis_result = analyzer.analyze()
        issues_detected = analysis_result.get("issues_detected", [])

        parser = QueryParser(query)
        summary = parser.summarize_query()

        parser = QueryParser(query)
        summary = parser.summarize_query()

        suggester = Suggestions(issues_detected)
        suggestions = suggester.generate_suggestions()

        return {
            "query_summary": summary,
            "issues": issues_detected,
            "suggestions": suggestions,
            "explain_plan": explain_rows,
            "query_results": query_results
        }

    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()

# Renders the index.html page.
@app.route('/')
def index():
    return render_template('index.html')

# API endpoint to analyze the SQL query.
@app.route('/analyze', methods = ['POST'])
def analyze():
    data = request.get_json()
    raw_path = data.get('db_path', '').strip()
    query = data.get('query', '').strip()

    db_path = os.path.normpath(raw_path)

    if not db_path:
        return jsonify({"error": "Database path is required."}), 400
    if not os.path.exists(db_path):
        return jsonify({"error": f"Database file not found at path: {db_path}"}), 400
    if not query:
        return jsonify({"error": "SQL query is required."}), 400

    config.DB_CONFIG["db_path"] = db_path

    result = analyze_query(query, db_path)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug = True)


      

