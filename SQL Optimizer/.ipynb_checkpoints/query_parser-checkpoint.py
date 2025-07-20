# Ryan Gallagher 
# SQL Query Optimization Tool 
# query_parser.py

# Resource importing and management. 
import sqlparse 
from sqlparse.sql import IdentifierList, Identifier, TokenList
from sqlparse.tokens import DML, Keyword, Whitespace, Wildcard, Punctuation, Name, Number
import re 

# Defines the query parser class and its pertainent methods. 
class QueryParser: 

    # Constructs a parsed SQL query.
    def __init__(self, query : str): 
        self.query = query 
        self.parsed = sqlparse.parse(query)[0]

    # Extracts the table names used in the SQL query. 
    def get_tables(self):
        tables = []
        expecting_table = False
    
        join_keywords = {
            "JOIN", "INNER JOIN", "LEFT JOIN", "LEFT OUTER JOIN",
            "RIGHT JOIN", "RIGHT OUTER JOIN", "FULL JOIN", "FULL OUTER JOIN",
            "CROSS JOIN", "NATURAL JOIN", "FROM"
        }
    
        parsed = self.parsed
        tokens = parsed.tokens
    
        i = 0
        while i < len(tokens):
            token = tokens[i]
    
            if token.ttype is Keyword and token.value.upper() == "FROM":
                expecting_table = True
    
            elif token.ttype is Keyword:
                combined_keyword = token.value.upper()
                j = i + 1
                while j < len(tokens) and tokens[j].ttype is Keyword:
                    combined_keyword += " " + tokens[j].value.upper()
                    j += 1
    
                if combined_keyword in join_keywords:
                    expecting_table = True
                    i = j - 1
    
            elif expecting_table:
                if isinstance(token, Identifier):
                    tables.append(token.get_real_name())
                    expecting_table = False
                elif isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        tables.append(identifier.get_real_name())
                    expecting_table = False
    
            i += 1
    
        return tables

    # Extracts the column names used in the SQL query. 
    def get_columns(self):
        columns = []
    
        select_seen = False
        for token in self.parsed.tokens:
            if token.ttype is DML and token.value.upper() == 'SELECT':
                select_seen = True
                continue
            if select_seen and token.ttype is Keyword and token.value.upper() == 'FROM':
                break
            if select_seen:
                if isinstance(token, IdentifierList):
                    for identifier in token.get_identifiers():
                        if isinstance(identifier, Identifier) and identifier.get_real_name() == '*':
                            parent = identifier.get_parent_name()
                            if parent:
                                columns.append(f"{parent}.*")
                            else:
                                columns.append('*')
                        else:
                            name = identifier.get_real_name()
                            if name:
                                columns.append(name)
                elif isinstance(token, Identifier):
                    if token.get_real_name() == '*':
                        parent = token.get_parent_name()
                        if parent:
                            columns.append(f"{parent}.*")
                        else:
                            columns.append('*')
                    else:
                        name = token.get_real_name()
                        if name:
                            columns.append(name)
                elif token.ttype is Wildcard:
                    columns.append('*')
    
        return columns


    # Extracts the joins used in the SQL query. 
    def get_joins(self):
        joins = []
        tokens = self.parsed.tokens
        idx = 0
    
        while idx < len(tokens):
            token = tokens[idx]
            if token.ttype is sqlparse.tokens.Keyword and "JOIN" in token.value.upper():
                join_clause = token.value  
                
                next_idx = idx + 1
                while next_idx < len(tokens):
                    next_token = tokens[next_idx]
                    if next_token.ttype is Whitespace:
                        next_idx += 1
                        continue
                    if isinstance(next_token, Identifier):
                        join_clause += f" {next_token.value}"
                        joins.append(join_clause.strip())
                    elif isinstance(next_token, IdentifierList):
                        for identifier in next_token.get_identifiers():
                            joins.append(f"{token.value} {identifier.value}".strip())
                    break
    
                idx = next_idx
            else:
                idx += 1
    
        return joins

 
    # Returns the conditions specified by the WHERE clause.
    def get_conditions(self):
        conditions = []
    
        for token in self.parsed.tokens:
            if isinstance(token, sqlparse.sql.Where):
                condition_tokens = token.tokens[2:]  
                current_condition = ""
                skip_next = False
                inside_between = False
                
                for i, subtoken in enumerate(condition_tokens):
                    if skip_next:
                        skip_next = False
                        continue
                    if subtoken.ttype is sqlparse.tokens.Whitespace:
                        current_condition += " "
                        continue
    
                    val = subtoken.value

                    if val.upper() == "BETWEEN":
                        inside_between = True
                        current_condition += "BETWEEN"
                        continue

                    if inside_between and val.upper() == "AND":
                        current_condition += "AND"
                        continue
                    if subtoken.ttype is Keyword and val.upper() in ("AND", "OR") and not inside_between:
                        if current_condition.strip():
                            conditions.append(current_condition.strip().rstrip(";"))
                        conditions.append(val.upper())
                        current_condition = ""
                    else:
                        current_condition += val
                        if inside_between:
                            next_tok = condition_tokens[i + 1] if i + 1 < len(condition_tokens) else None
                            if next_tok is None or (
                                next_tok.ttype is Keyword and next_tok.value.upper() not in ("AND", "OR")
                            ):
                                inside_between = False
    
                if current_condition.strip():
                    conditions.append(current_condition.strip().rstrip(";"))
                break
    
        return conditions
    

    # Extracts ORDER BY conditions, which typically denote the presence of a "filesort" operation.  
    def get_order_by(self):
        order_by_columns = []
        query_upper = self.query.upper()
        
        if "ORDER BY" not in query_upper:
            return []
    
        order_by_index = query_upper.find("ORDER BY")
        order_by_clause = self.query[order_by_index + len("ORDER BY"):]
    
        for end_keyword in ["ORDER BY", "LIMIT", "OFFSET", "FETCH", "FOR", "HAVING", ";", "WINDOW", "UNION", "INTERSECT", "EXCEPT", "RETURNING", "WHERE"]:
            end_index = order_by_clause.upper().find(end_keyword)
            if end_index != -1:
                order_by_clause = order_by_clause[:end_index]
                break
    
        columns = [col.strip() for col in order_by_clause.strip().split(",")]
    
        for col in columns:
            parts = col.split()
            if len(parts) == 0:
                continue
            column_name = parts[0]
            direction = parts[1].upper() if len(parts) > 1 and parts[1].upper() in ("ASC", "DESC") else "ASC"
            order_by_columns.append((column_name, direction))
    
        return order_by_columns

    # Extracts GROUP BY columns from the SQL query.
    def get_group_by(self):
        group_by_columns = []
        query_upper = self.query.upper()
        
        if "GROUP BY" not in query_upper:
            return []
    
        group_by_index = query_upper.find("GROUP BY")
        group_by_clause = self.query[group_by_index + len("GROUP BY"):]
    
        # Stop at the next SQL clause keyword
        for end_keyword in ["ORDER BY", "LIMIT", "OFFSET", "FETCH", "FOR", "HAVING", ";","WINDOW", "UNION", "INTERSECT", "EXCEPT", "RETURNING", "WHERE"]:
            end_index = group_by_clause.upper().find(end_keyword)
            if end_index != -1:
                group_by_clause = group_by_clause[:end_index]
                break
    
        columns = [col.strip() for col in group_by_clause.strip().split(",")]
    
        for col in columns:
            if col:
                group_by_columns.append(col)
    
        return group_by_columns

    # Returns the conditions specified by the HAVING clause.
    def get_having(self):
        having_conditions = []
        query_upper = self.query.upper()
    
        if "HAVING" not in query_upper:
            return []
    
        having_index = query_upper.find("HAVING")
        having_clause = self.query[having_index + len("HAVING"):]
    
        for end_keyword in ["ORDER BY", "LIMIT", "OFFSET", "FETCH", "FOR", ";"]:
            end_index = having_clause.upper().find(end_keyword)
            if end_index != -1:
                having_clause = having_clause[:end_index]
                break
    
        tokens = re.split(r'\s+(AND|OR)\s+', having_clause, flags=re.IGNORECASE)

        for token in tokens:
            token_strip = token.strip()
            if token_strip.upper() in ("AND", "OR"):
                having_conditions.append(token_strip.upper())
            elif token_strip:
                having_conditions.append(token_strip)
    
        return having_conditions
   

    # Returns a summary of the key components of the query.
    def summarize_query(self): 
    
        return { 
            "tables" : self.get_tables(), 
            "columns" : self.get_columns(), 
            "joins" : self.get_joins(), 
            "conditions" : self.get_conditions(), 
            "order_by" : self.get_order_by(), 
            "group_by" : self.get_group_by(), 
            "having" : self.get_having() 
        }
    
    



    
        
        
            
        