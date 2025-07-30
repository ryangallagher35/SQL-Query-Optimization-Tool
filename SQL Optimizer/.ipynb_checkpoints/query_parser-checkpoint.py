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
    
    # Extracts the tables in the SQL query.
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
            
            if token.ttype is Keyword:
                max_lookahead = 3
                combined_keyword = token.value.upper()
                j = i + 1
                while j < len(tokens) and max_lookahead > 0:
                    next_token = tokens[j]
                    if next_token.ttype is Keyword:
                        combined_keyword += " " + next_token.value.upper()
                        j += 1
                        max_lookahead -= 1
                    else:
                        break
    
                if combined_keyword in join_keywords:
                    expecting_table = True
                    i = j - 1  
    
            elif token.ttype is Keyword and token.value.upper() == "FROM":
                expecting_table = True
    
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
        join_keywords = {
            "JOIN", "INNER JOIN", "LEFT JOIN", "LEFT OUTER JOIN", 
            "RIGHT JOIN", "RIGHT OUTER JOIN", "FULL JOIN", 
            "FULL OUTER JOIN", "CROSS JOIN", "NATURAL JOIN"
        }
    
        stop_keywords = {"WHERE", "GROUP BY", "HAVING", "ORDER BY", "LIMIT", "OFFSET", ";"}
    
        while idx < len(tokens):
            token = tokens[idx]
            
            if token.ttype is Keyword and any(keyword in token.value.upper() for keyword in join_keywords):
                join_clause = token.value  
                next_idx = idx + 1
                while next_idx < len(tokens):
                    next_token = tokens[next_idx]
    
                    if next_token.ttype is Whitespace:
                        next_idx += 1
                        continue
                    
                    if isinstance(next_token, Identifier):
                        join_clause += f" {next_token.value}"
                        next_idx += 1
    
                    elif isinstance(next_token, IdentifierList):
                        for identifier in next_token.get_identifiers():
                            join_clause += f" {identifier.value}"
                        next_idx += 1
    
                    elif next_token.ttype is Keyword and next_token.value.upper() in ["ON", "USING"]:
                        join_clause += f" {next_token.value}"
                        next_idx += 1
                        
                        while next_idx < len(tokens):
                            cond_token = tokens[next_idx]
                            token_value = cond_token.value.upper().strip() 
                            token_array = re.findall(r"[\w']+|[^\w\s]", token_value)
                            stop = False
                            
                            for i in range(len(token_array)):
                                if token_array[i] in stop_keywords: 
                                    stop = True
                                    
                            if stop or token_value in join_keywords:
                                break
                            
                            join_clause += f"{cond_token.value}"
                            next_idx += 1
                        break  
    
                    else:
                        break
    
                joins.append(join_clause.strip())
                idx = next_idx
            else:
                idx += 1
    
        joins = [join.strip().rstrip(';').rstrip(',') for join in joins]
        
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
            order_by_columns.append(f"{column_name} {direction}")
    
        return order_by_columns
    

    # Extracts GROUP BY columns from the SQL query.
    def get_group_by(self):
        group_by_columns = []
        query_upper = self.query.upper()
        
        if "GROUP BY" not in query_upper:
            return []
    
        group_by_index = query_upper.find("GROUP BY")
        group_by_clause = self.query[group_by_index + len("GROUP BY"):]
    
        for end_keyword in ["ORDER BY", "LIMIT", "OFFSET", "FETCH", "FOR", "HAVING", ";","WINDOW", "UNION", "INTERSECT", "EXCEPT", "RETURNING", "WHERE"]:
            end_index = group_by_clause.upper().find(end_keyword)
            if end_index != -1:
                group_by_clause = group_by_clause[:end_index]
                break
    
        group_by_clause = group_by_clause.split('HAVING')[0]
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
    
    # Returns any limit specifications.
    def get_limit(self):
        query = re.sub(r'--.*?(\n|$)', ' ', self.query, flags=re.IGNORECASE)
        match = re.search(r'\bLIMIT\b\s*([^\s;]+(?:\s*,\s*[^\s;]+)?(?:\s+OFFSET\s+[^\s;]+)?)', query, re.IGNORECASE)
        if not match:
            return None
        limit_clause = match.group(1).strip()
        limit_clause = limit_clause.strip('()')
    
        if ',' in limit_clause:
            parts = [p.strip() for p in limit_clause.split(',')]
            if len(parts) == 2 and all(p.isdigit() for p in parts):
                offset, count = int(parts[0]), int(parts[1])
                return (offset, count)
            else:
                return None
    
        offset_match = re.match(r'(\d+)\s+OFFSET\s+(\d+)', limit_clause, re.IGNORECASE)
        if offset_match:
            count = int(offset_match.group(1))
            offset = int(offset_match.group(2))
            return (offset, count)
    
        if limit_clause.isdigit():
            return int(limit_clause)
    
        return None
    
    # Handles parsing subqueries.
    def get_subqueries(self):
        subqueries = []
        query_str = str(self.parsed)
    
        def extract_subqueries(sql):
            subqueries_found = []
            stack = []
            start_idx = None
            length = len(sql)
    
            i = 0
            while i < length:
                char = sql[i]
    
                if char == '(':
                    if start_idx is None:
                        j = i + 1
                        while j < length and sql[j].isspace():
                            j += 1
                        if sql[j:j + 6].upper() == 'SELECT':
                            start_idx = i
                    stack.append(char)
    
                elif char == ')':
                    if stack:
                        stack.pop()
                        if not stack and start_idx is not None:
                            subquery = sql[start_idx + 1:i]
                            subqueries_found.append(subquery.strip())
                            subqueries_found.extend(extract_subqueries(subquery.strip()))
                            start_idx = None
                i += 1
    
            return subqueries_found
    
        raw_subqueries = extract_subqueries(query_str)
    
        for raw in raw_subqueries:
            subparser = QueryParser(raw)
            subqueries.append(subparser.summarize_query())
    
        return subqueries
    
       
    # Returns a summary of the key components of the query.
    def summarize_query(self): 
    
        return { 
            "Tables" : self.get_tables(), 
            "Columns" : self.get_columns(), 
            "Joins" : self.get_joins(), 
            "Conditions" : self.get_conditions(), 
            "ORDER BY clauses" : self.get_order_by(), 
            "GROUP BY clauses" : self.get_group_by(), 
            "HAVING clauses" : self.get_having(), 
            "Limit" : self.get_limit(),
            "Subqueries" : self.get_subqueries()
        }

        

    
    



    
        
        
            
        