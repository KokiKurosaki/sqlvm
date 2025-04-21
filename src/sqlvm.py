import re

class SQLVM:
    def __init__(self):
        self.databases = {}  # { db_name: {table_name: ...} }
        self.current_db = None
        self.tables = {}  # For backward compatibility, but now always points to current db's tables

    def create_database(self, db_name):
        if db_name in self.databases:
            return f"Error: Database {db_name} already exists."
        self.databases[db_name] = {}
        return f"Database {db_name} created."

    def drop_database(self, db_name, if_exists=False):
        if db_name not in self.databases:
            if if_exists:
                return f"Database {db_name} does not exist. Skipped."
            return f"Error: Database {db_name} does not exist."
        del self.databases[db_name]
        if self.current_db == db_name:
            self.current_db = None
            self.tables = {}
        return f"Database {db_name} dropped."

    def use_database(self, db_name):
        if db_name not in self.databases:
            return f"Error: Database {db_name} does not exist."
        self.current_db = db_name
        self.tables = self.databases[db_name]
        return f"Using database {db_name}."

    def show_databases(self):
        if not self.databases:
            return "No databases found."
        dbs = sorted(self.databases.keys())
        # Format as a simple table
        maxlen = max(len("Database"), *(len(db) for db in dbs))
        header = "| " + "Database".ljust(maxlen) + " |"
        sep = "+" + "-" * (maxlen + 2) + "+"
        rows = [f"| {db.ljust(maxlen)} |" for db in dbs]
        return sep + "\n" + header + "\n" + sep + "\n" + "\n".join(rows) + "\n" + sep

    def show_tables(self):
        if self.current_db is None:
            return "Error: No database selected. Use USE database_name;"
        if not self.tables:
            return "No tables found in current database."
        tbls = sorted(self.tables.keys())
        maxlen = max(len("Table"), *(len(t) for t in tbls))
        header = "| " + "Table".ljust(maxlen) + " |"
        sep = "+" + "-" * (maxlen + 2) + "+"
        rows = [f"| {t.ljust(maxlen)} |" for t in tbls]
        return sep + "\n" + header + "\n" + sep + "\n" + "\n".join(rows) + "\n" + sep

    def _parse_column_definitions(self, columns_def):
        """
        Parse column definitions like: col1 INT, col2 TEXT, col3 FLOAT
        Returns: (columns, types, auto_increment_cols, indexes) where columns is a list of names, 
        types is a dict {col: type}, auto_increment_cols is a list of auto-increment column names,
        and indexes is a dict mapping column names to their index types
        """
        columns = []
        types = {}
        auto_increment_cols = []
        indexes = {}
        
        for coldef in columns_def.split(","):
            parts = coldef.strip().split()
            if len(parts) == 1:
                col, typ = parts[0], "TEXT"
                auto_increment = False
                index_type = None
            else:
                col = parts[0]
                typ = parts[1].upper()
                auto_increment = "AUTO_INCREMENT" in [p.upper() for p in parts[2:]] if len(parts) > 2 else False
                # Check for index types
                index_options = ["PRIMARY", "UNIQUE", "INDEX", "FULLTEXT", "SPATIAL"]
                index_type = None
                for idx_type in index_options:
                    if idx_type in [p.upper() for p in parts[2:]]:
                        index_type = idx_type
                        break
            
            columns.append(col)
            types[col] = typ
            if auto_increment:
                auto_increment_cols.append(col)
                # Make AUTO_INCREMENT columns PRIMARY KEY by default if no other index type specified
                if not index_type and typ.upper() == "INT":
                    index_type = "PRIMARY"
            if index_type:
                indexes[col] = index_type
        
        return columns, types, auto_increment_cols, indexes

    def _convert_value(self, value, typ):
        """
        Convert string value to the given SQL type.
        """
        if typ in ("TEXT", "CHAR", "VARCHAR"):
            return str(value)
        elif typ == "INT":
            try:
                return int(value)
            except Exception:
                raise ValueError(f"Invalid INT value: {value}")
        elif typ == "FLOAT":
            try:
                return float(value)
            except Exception:
                raise ValueError(f"Invalid FLOAT value: {value}")
        elif typ == "BOOL":
            if str(value).lower() in ("1", "true", "yes", "on"):
                return True
            elif str(value).lower() in ("0", "false", "no", "off"):
                return False
            else:
                raise ValueError(f"Invalid BOOL value: {value}")
        else:
            return str(value)

    def create_table(self, table_name, columns_def):
        if self.current_db is None:
            return "Error: No database selected. Use USE database_name;"
        if table_name in self.tables:
            return f"Error: Table {table_name} already exists."
        
        columns, types, auto_increment_cols, indexes = self._parse_column_definitions(", ".join(columns_def) if isinstance(columns_def, list) else columns_def)
        
        # Check that there's only one AUTO_INCREMENT column
        if len(auto_increment_cols) > 1:
            return "Error: Incorrect table definition; there can be only one auto column and it must be defined as a key"
        
        # Check that AUTO_INCREMENT column is defined as a key (PRIMARY, UNIQUE or INDEX)
        if auto_increment_cols and auto_increment_cols[0] not in indexes:
            return "Error: Incorrect table definition; there can be only one auto column and it must be defined as a key"
            
        # Validate indexes - check for multiple PRIMARY KEYs
        primary_keys = [col for col, idx_type in indexes.items() if idx_type == "PRIMARY"]
        if len(primary_keys) > 1:
            return f"Error: Multiple PRIMARY KEY definitions. A table can have only one primary key."
        
        self.tables[table_name] = {
            "columns": columns, 
            "types": types, 
            "rows": [],
            "auto_increment": {col: 0 for col in auto_increment_cols},
            "indexes": indexes
        }
        
        # Format the column definitions for display
        col_defs = []
        for col in columns:
            col_def = f"{col} {types[col]}"
            if col in auto_increment_cols:
                col_def += " AUTO_INCREMENT"
            if col in indexes:
                col_def += f" {indexes[col]}"
            col_defs.append(col_def)
            
        return f"Table {table_name} created with columns: {', '.join(col_defs)}."

    def insert(self, table_name, values, specified_columns=None):
        if self.current_db is None:
            return "Error: No database selected. Use USE database_name;"
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        columns = table["columns"]
        types = table.get("types", {c: "TEXT" for c in columns})
        auto_increment = table.get("auto_increment", {})
        indexes = table.get("indexes", {})
        
        # Handle case when columns are explicitly specified
        if specified_columns:
            # Create a mapping to match specified columns to their positions
            column_mapping = {}
            for i, col in enumerate(columns):
                column_mapping[col] = i
                
            # Create an array with None values initially
            full_values = [None] * len(columns)
            
            # Fill in the values for the specified columns
            for i, col in enumerate(specified_columns):
                if i < len(values):
                    # Check if column exists
                    if col not in column_mapping:
                        return f"Error: Unknown column '{col}' in field list"
                    full_values[column_mapping[col]] = values[i]
            
            values = full_values
        
        # Handle case when auto-increment columns are omitted
        if len(values) != len(columns) and len(values) == len([c for c in columns if c not in auto_increment]):
            # The values match the number of non-auto-increment columns
            values_with_auto = []
            value_index = 0
            for col in columns:
                if col in auto_increment:
                    values_with_auto.append(None)  # Placeholder for auto-increment
                else:
                    values_with_auto.append(values[value_index])
                    value_index += 1
            values = values_with_auto
        
        if len(values) != len(columns):
            return f"Error: Number of values doesn't match columns."
        
        # Create a dictionary to store the new row values
        new_row = {}
        display_values = []
        
        # First pass: convert values and handle auto-increment
        for col, val in zip(columns, values):
            if col in auto_increment and (val is None or val == "NULL"):
                # Handle auto-increment value
                table["auto_increment"][col] += 1
                auto_value = table["auto_increment"][col]
                new_row[col] = auto_value
                display_values.append(auto_value)
            else:
                try:
                    converted_val = self._convert_value(val, types.get(col, "TEXT"))
                    new_row[col] = converted_val
                    display_values.append(converted_val)
                except Exception as e:
                    return f"Error: {e}"
        
        # Second pass: check index constraints
        for col, index_type in indexes.items():
            if index_type in ["PRIMARY", "UNIQUE"]:
                value = new_row.get(col)
                # Check for duplicates in existing rows
                for row in table["rows"]:
                    if row.get(col) == value:
                        if index_type == "PRIMARY":
                            return f"Error: Duplicate entry '{value}' for key 'PRIMARY'"
                        else:
                            return f"Error: Duplicate entry '{value}' for key '{col}'"
        
        # All checks passed, add the row
        table["rows"].append(new_row)
        return f"Inserted {display_values} into {table_name}."

    def select(self, table_name, columns="*"):
        if self.current_db is None:
            return "Error: No database selected. Use USE database_name;"
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        if columns == "*":
            columns = table["columns"]
        else:
            columns = [col.strip() for col in columns.split(",")]
        
        # Calculate the maximum width for each column
        widths = {col: len(col) for col in columns}
        for row in table["rows"]:
            for col in columns:
                value_width = len(str(row.get(col, 'NULL')))
                if col in widths:
                    widths[col] = max(widths[col], value_width)
        
        # Format with clear column boundaries using vertical bars
        header = "| " + " | ".join(col.ljust(widths[col]) for col in columns) + " |"
        
        # Create separator with + and - to clearly mark columns
        separator = "+" + "+".join("-" * (widths[col] + 2) for col in columns) + "+"
        
        # Format the rows with vertical bars for alignment
        formatted_rows = []
        for row in table["rows"]:
            formatted_row = "| " + " | ".join(str(row.get(col, 'NULL')).ljust(widths[col]) for col in columns) + " |"
            formatted_rows.append(formatted_row)
        
        # Combine everything with clear boundaries
        result = separator + "\n" + header + "\n" + separator + "\n"
        if formatted_rows:
            result += "\n".join(formatted_rows) + "\n" + separator
        else:
            result += separator  # Bottom line for empty result set
            
        return result

    def update(self, table_name, set_values, where=None):
        if self.current_db is None:
            return "Error: No database selected. Use USE database_name;"
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        types = table.get("types", {c: "TEXT" for c in table["columns"]})
        set_dict = {}
        set_pairs = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|([^",\s]+))', set_values)
        for col, val1, val2 in set_pairs:
            value = val1 if val1 else val2
            try:
                set_dict[col] = self._convert_value(value, types.get(col, "TEXT"))
            except Exception as e:
                return f"Error: {e}"

        updated_count = 0
        for row in table["rows"]:
            if where is None or self._evaluate_condition(row, where):
                for column, value in set_dict.items():
                    if column in row:
                        row[column] = value
                updated_count += 1
        return f"Updated {updated_count} row/s in {table_name}."

    def delete(self, table_name, where=None):
        if self.current_db is None:
            return "Error: No database selected. Use USE database_name;"
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        initial_row_count = len(table["rows"])
        table["rows"] = [row for row in table["rows"] if where is None or not self._evaluate_condition(row, where)]
        deleted_count = initial_row_count - len(table["rows"])
        return f"Deleted {deleted_count} row/s from {table_name}."

    def _evaluate_condition(self, row, condition):
        col, value = condition.split("=")
        col = col.strip()
        value = value.strip().strip('"')
        typ = None
        for table in self.tables.values():
            if "types" in table and col in table["types"]:
                typ = table["types"][col]
                break
        if typ:
            try:
                value = self._convert_value(value, typ)
            except Exception:
                pass
        return row.get(col) == value

    def execute_command(self, command):
        command = command.strip().rstrip(";")  # Remove trailing semicolon if present
        parts = command.split(" ", 1)
        cmd = parts[0].upper()

        # Database commands
        if cmd == "CREATE":
            # CREATE DATABASE
            match_db = re.match(r"CREATE DATABASE (\w+)", command, re.IGNORECASE)
            if match_db:
                db_name = match_db.group(1)
                return self.create_database(db_name)
            # CREATE TABLE
            match = re.match(r"CREATE TABLE (\w+) \((.+)\)", command, re.IGNORECASE)
            if match:
                table_name = match.group(1)
                columns_def = match.group(2)
                return self.create_table(table_name, columns_def)
        elif cmd == "DROP":
            # DROP DATABASE [IF EXISTS] db_name
            match = re.match(r"DROP DATABASE(?: IF EXISTS)? (\w+)", command, re.IGNORECASE)
            if match:
                db_name = match.group(1)
                if_exists = "IF EXISTS" in command.upper()
                return self.drop_database(db_name, if_exists)
        elif cmd == "USE":
            # USE db_name
            match = re.match(r"USE (\w+)", command, re.IGNORECASE)
            if match:
                db_name = match.group(1)
                return self.use_database(db_name)
        elif cmd == "SHOW":
            # SHOW DATABASES
            if command.upper() == "SHOW DATABASES":
                return self.show_databases()
            # SHOW TABLES
            if command.upper() == "SHOW TABLES":
                return self.show_tables()
        elif cmd == "INSERT":
            # Match INSERT INTO table VALUES (...) format
            match_simple = re.match(r"INSERT INTO (\w+) VALUES \((.+)\)", command)
            if match_simple:
                table_name = match_simple.group(1)
                values_str = match_simple.group(2)
                pattern = r'''
                    "([^"]*)"           # double-quoted string
                    |                   # or
                    ([^,\s][^,]*)       # unquoted value (numbers, booleans, etc.)
                '''
                values = []
                for m in re.finditer(pattern, values_str, re.VERBOSE):
                    if m.group(1) is not None:
                        values.append(m.group(1))
                    elif m.group(2) is not None:
                        values.append(m.group(2).strip())
                return self.insert(table_name, values)
            
            # Match INSERT INTO table (col1, col2) VALUES (...) format
            match_columns = re.match(r"INSERT INTO (\w+) \((.+?)\) VALUES \((.+)\)", command, re.IGNORECASE)
            if match_columns:
                table_name = match_columns.group(1)
                columns_str = match_columns.group(2)
                values_str = match_columns.group(3)
                
                # Extract column names
                columns = [col.strip(' `\'\"') for col in columns_str.split(',')]
                
                # Extract values
                pattern = r'''
                    "([^"]*)"           # double-quoted string
                    |                   # or
                    ([^,\s][^,]*)       # unquoted value (numbers, booleans, etc.)
                '''
                values = []
                for m in re.finditer(pattern, values_str, re.VERBOSE):
                    if m.group(1) is not None:
                        values.append(m.group(1))
                    elif m.group(2) is not None:
                        values.append(m.group(2).strip())
                
                return self.insert(table_name, values, columns)
            
        elif cmd == "SELECT":
            match = re.match(r"SELECT (.+) FROM (\w+)", command)
            if match:
                columns = match.group(1)
                table_name = match.group(2)
                return self.select(table_name, columns)
        elif cmd == "UPDATE":
            match = re.match(r"UPDATE (\w+) SET (.+) WHERE (.+)", command)
            if match:
                table_name = match.group(1)
                set_values = match.group(2)
                where = match.group(3)
                return self.update(table_name, set_values, where)
        elif cmd == "DELETE":
            match = re.match(r"DELETE FROM (\w+) WHERE (.+)", command)
            if match:
                table_name = match.group(1)
                where = match.group(2)
                return self.delete(table_name, where)
        return "Error: Invalid command."