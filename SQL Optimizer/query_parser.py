# Ryan Gallagher 
# SQL Query Optimization Tool 
# query_parser.py

# Resource importing and management. 
import sqlparse 
from sqlparse.sql import IdentifierList, Identifier 
from sqlparse.tokens import DML, Keyword, Whitespace, Wildcard

# Defines the query parser class and its pertainent methods. 
class QueryParser: 

    # Constructs a parsed SQL query.
    def __init__(self, query : str): 
        self.query = query 
        self.parsed = sqlparse.parse(query)[0]

    # Extracts the table names used in the SQL query. 
    def get_tables(self): 
        tables = []
        from_or_join_seen = False
        for token in self.parsed.tokens:
            if from_or_join_seen:
                if token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
                    tables.append(token.get_real_name())
                    from_or_join_seen = False
                elif isinstance(token, sqlparse.sql.IdentifierList):
                    for identifier in token.get_identifiers():
                        tables.append(identifier.get_real_name())
                    from_or_join_seen = False
            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ("FROM", "JOIN"):
                from_or_join_seen = True
        return tables

    # Extracts the colu,n names used in the SQL query. 
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

    '''
    # Extracts the joins used in the SQL query. 
    def get_joins(self): 
        joins = [] 

        join_seen = False 
        for token in self.parsed.tokens:
            if join_seen:
                if token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
                    tables.append(token.get_real_name())
                    join_seen = False
                elif isinstance(token, sqlparse.sql.IdentifierList):
                    for identifier in token.get_identifiers():
                        tables.append(identifier.get_real_name())
                    join_seen = False
            if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in ("JOIN"):
                join_seen = True
        return tables
        '''
        
            
        