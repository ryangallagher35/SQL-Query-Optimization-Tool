# SQL Query Optimization Tool - Main Integration Notebook

from db_connector import DBConnector
from query_parser import QueryParser
from suggestions import Suggestions
import config
import sys
import os

def analyze_query(query):
    #db = DBConnector()
    db = DBConnector(db_path = config.DB_CONFIG["db_path"])
    
    try:
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
            "explain_plan": explain_rows
        }
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        db.close()

if __name__ == "__main__":
    # Prompt user for database file path
    user_db_path = input("Please enter the path to your database file:\n").strip()
    print("Exists:", os.path.isfile(user_db_path))
    config.DB_CONFIG["db_path"] = user_db_path

    # Take user input for the SQL query
    input_query = input("Enter your SQL query to analyze:\n")
    
    # Analyze the user input query
    result = analyze_query(input_query)
    
    # Display the results
    if "error" in result:
        print(f"Error analyzing query: {result['error']}")
    else:
        print("\nQuery Summary:")
        print(result["query_summary"])
        print("\nDetected Issues:")
        for issue in result["issues"]:
            print(f"- {issue['type']}: {issue['message']}")
        print("\nSuggestions:")
        for suggestion in result["suggestions"]:
            print(f"- {suggestion}")
        print("\nExplain Plan:")
        for row in result["explain_plan"]:
            print(row)
        

