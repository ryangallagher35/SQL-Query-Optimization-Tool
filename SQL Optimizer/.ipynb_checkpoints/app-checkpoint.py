# Ryan Gallagher
# SQL Query Optimization Tool 
# main.py

# Resource importing and management. 
from flask import Flask, render_template, request, jsonify
from db_connector import DBConnector
from query_parser import QueryParser
from suggestions import Suggestions
import config
import os
import sys

app = Flask(__name__)

def analyze_query(query, db_path):
    db = DBConnector(db_path=db_path)

    try:
        query_results = db.execute_query(query)
        explain_rows = db.get_explain(query)

        issues_detected = []
        for row in explain_rows:
            detail = row.get('detail', '').lower() if 'detail' in row else ''
            if 'scan' in detail and 'index' not in detail:
                issues_detected.append({"type": "Full Table Scan", "message": detail})
            if 'using filesort' in detail:
                issues_detected.append({"type": "Filesort", "message": detail})
            if 'temporary' in detail:
                issues_detected.append({"type": "Using Temporary Structure", "message": detail})

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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    raw_path = data.get('db_path', '').strip()
    query = data.get('query', '').strip()

    # Normalize and validate database path
    db_path = os.path.normpath(raw_path)

    if not db_path:
        return jsonify({"error": "Database path is required."}), 400
    if not os.path.exists(db_path):
        return jsonify({"error": f"Database file not found at path: {db_path}"}), 400
    if not query:
        return jsonify({"error": "SQL query is required."}), 400

    # Update global config path (if needed by db_connector)
    config.DB_CONFIG["db_path"] = db_path

    result = analyze_query(query, db_path)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)


      

