import re
import time  # Import the time module
from .parser import SQLParser
from .vm import SQLVMInterpreter
import ast

class SQLVM:
    def __init__(self):
        self.databases = {}  # { db_name: {table_name: ...} }
        self.current_db = None
        self.tables = {}  # For backward compatibility, but now always points to current db's tables
        self.vm = SQLVMInterpreter(self)

    def create_database(self, db_name):
        if (db_name in self.databases):
            return f"Error: Database {db_name} already exists."
        self.databases[db_name] = {}
        return f"Database {db_name} created."

    def drop_database(self, db_name, if_exists=False):
        if (db_name not in self.databases):
            if (if_exists):
                return f"Database {db_name} does not exist. Skipped."
            return f"Error: Database {db_name} does not exist."
        del self.databases[db_name]
        if (self.current_db == db_name):
            self.current_db = None
            self.tables = {}
        return f"Database {db_name} dropped."

    def use_database(self, db_name):
        if (db_name not in self.databases):
            return f"Error: Database {db_name} does not exist."
        self.current_db = db_name
        self.tables = self.databases[db_name]
        return f"Using database {db_name}."

    def show_databases(self):
        if (not self.databases):
            return "No databases found."
        dbs = sorted(self.databases.keys())
        # Format as a simple table
        maxlen = max(len("Database"), *(len(db) for db in dbs))
        header = "| " + "Database".ljust(maxlen) + " |"
        sep = "+" + "-" * (maxlen + 2) + "+"
        rows = [f"| {db.ljust(maxlen)} |" for db in dbs]
        return sep + "\n" + header + "\n" + sep + "\n" + "\n".join(rows) + "\n" + sep

    def show_tables(self):
        if (self.current_db is None):
            return "Error: No database selected. Use USE database_name;"
        if (not self.tables):
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
        
        # First, check for standalone PRIMARY KEY definition
        primary_key_match = re.search(r'PRIMARY\s+KEY\s*\(([^)]+)\)', columns_def, re.I)
        primary_key_columns = []
        if primary_key_match:
            # Get the columns in the PRIMARY KEY constraint
            pk_cols_str = primary_key_match.group(1)
            primary_key_columns = [col.strip() for col in pk_cols_str.split(',')]
            
            # Remove the PRIMARY KEY constraint from the column definitions
            columns_def = columns_def.replace(primary_key_match.group(0), '')
        
        # Split columns, handling commas inside parentheses (for PRIMARY KEY definitions)
        depth = 0
        start = 0
        col_defs = []
        
        for i, char in enumerate(columns_def):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                col_defs.append(columns_def[start:i].strip())
                start = i + 1
        
        # Add the last column definition
        if start < len(columns_def):
            col_defs.append(columns_def[start:].strip())
        
        # Process each column definition
        for coldef in col_defs:
            if not coldef.strip():
                continue
                
            # Check if this is a standalone PRIMARY KEY definition
            if coldef.strip().upper().startswith('PRIMARY KEY'):
                continue  # Skip, already handled above
                
            # Parse column definition with regex to handle VARCHAR(n) and other types with parameters
            col_match = re.match(r'(\w+)\s+(\w+)(?:\((\d+)\))?(.*)$', coldef.strip(), re.I)
            
            if (not col_match):
                # Handle the simplest case where only column name is provided
                col = coldef.strip()
                typ = "TEXT"
                auto_increment = False
                index_type = None
            else:
                # Extract from regex match
                col = col_match.group(1)
                base_type = col_match.group(2).upper()
                type_param = col_match.group(3)  # Size parameter (e.g. VARCHAR(255))
                modifiers = col_match.group(4).upper() if col_match.group(4) else ""
                
                # Build the full type with parameters
                if (type_param):
                    typ = f"{base_type}({type_param})"
                else:
                    typ = base_type
                
                # Check for AUTO_INCREMENT in modifiers
                auto_increment = "AUTO_INCREMENT" in modifiers
                
                # Check for index types - converting PRIMARY to PRIMARY KEY for SQL compliance
                index_options = {"PRIMARY KEY": "PRIMARY KEY", "UNIQUE KEY": "UNIQUE KEY", 
                                "UNIQUE": "UNIQUE", "INDEX": "INDEX", "KEY": "KEY", 
                                "FULLTEXT": "FULLTEXT", "SPATIAL": "SPATIAL"}
                index_type = None
                
                # Also check for the legacy "PRIMARY" keyword and convert to "PRIMARY KEY"
                if ("PRIMARY" in modifiers and "PRIMARY KEY" not in modifiers):
                    index_type = "PRIMARY KEY"
                else:
                    for idx_name, idx_value in index_options.items():
                        if (idx_name in modifiers):
                            index_type = idx_value
                            break
            
            columns.append(col)
            types[col] = typ
            if (auto_increment):
                auto_increment_cols.append(col)
                # Make AUTO_INCREMENT columns PRIMARY KEY by default if no other index type specified
                if (not index_type and typ.upper().startswith("INT")):
                    index_type = "PRIMARY KEY"
            if (index_type):
                indexes[col] = index_type
        
        # Apply the standalone PRIMARY KEY constraint to the columns
        for col in primary_key_columns:
            if col in columns:
                indexes[col] = "PRIMARY KEY"
        
        return columns, types, auto_increment_cols, indexes

    def _convert_value(self, value, typ):
        """
        Convert string value to the given SQL type.
        """
        # Extract base type without size parameter
        base_type = re.match(r'(\w+)(?:\(\d+\))?', typ).group(1).upper()
        
        if (base_type in ("TEXT", "CHAR", "VARCHAR")):
            return str(value)
        elif (base_type == "INT"):
            try:
                return int(value)
            except Exception:
                raise ValueError(f"Invalid INT value: {value}")
        elif (base_type == "FLOAT"):
            try:
                return float(value)
            except Exception:
                raise ValueError(f"Invalid FLOAT value: {value}")
        elif (base_type == "BOOL"):
            if (str(value).lower() in ("1", "true", "yes", "on")):
                return True
            elif (str(value).lower() in ("0", "false", "no", "off")):
                return False
            else:
                raise ValueError(f"Invalid BOOL value: {value}")
        else:
            return str(value)

    def create_table(self, table_name, columns_def):
        if (self.current_db is None):
            return "Error: No database selected. Use USE database_name;"
        if (table_name in self.tables):
            return f"Error: Table {table_name} already exists."
        
        columns, types, auto_increment_cols, indexes = self._parse_column_definitions(", ".join(columns_def) if isinstance(columns_def, list) else columns_def)
        
        # Check that there's only one AUTO_INCREMENT column
        if (len(auto_increment_cols) > 1):
            return "Error: Incorrect table definition; there can be only one auto column and it must be defined as a key"
        
        # Check that AUTO_INCREMENT column is defined as a key (PRIMARY KEY, UNIQUE or INDEX)
        if (auto_increment_cols and auto_increment_cols[0] not in indexes):
            return "Error: Incorrect table definition; there can be only one auto column and it must be defined as a key"
            
        # Validate indexes - A table can have only one primary key, but it can be a composite key
        primary_keys = [col for col, idx_type in indexes.items() if idx_type == "PRIMARY KEY"]
        if (len(primary_keys) > 1):
            return f"Error: Multiple PRIMARY KEY definitions. A table can have only one primary key."
        
        self.tables[table_name] = {
            "columns": columns, 
            "types": types, 
            "rows": [],
            "auto_increment": {col: 0 for col in auto_increment_cols},
            "indexes": indexes,
            "primary_key": primary_keys if primary_keys else None
        }
        
        # Format the column definitions for display
        col_defs = []
        for col in columns:
            col_def = f"{col} {types[col]}"
            if (col in auto_increment_cols):
                col_def += " AUTO_INCREMENT"
            if col in indexes and indexes[col] != "PRIMARY KEY":
                # Don't add PRIMARY KEY here as we'll display it separately for clarity
                col_def += f" {indexes[col]}"
            col_defs.append(col_def)

        # If we have primary keys, display them as a composite key if multiple
        if primary_keys:
            if len(primary_keys) > 1:
                pk_def = f"PRIMARY KEY ({', '.join(primary_keys)})"
            else:
                pk_def = f"PRIMARY KEY ({primary_keys[0]})"
            col_defs.append(pk_def)
            
        return f"Table {table_name} created with columns: {', '.join(col_defs)}."

    def insert(self, table_name, values, specified_columns=None):
        if (self.current_db is None):
            return "Error: No database selected. Use USE database_name;"
        if (table_name not in self.tables):
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        columns = table["columns"]
        types = table.get("types", {c: "TEXT" for c in columns})
        auto_increment = table.get("auto_increment", {})
        indexes = table.get("indexes", {})
        
        # Handle case when columns are explicitly specified
        if (specified_columns):
            # Create a mapping to match specified columns to their positions
            column_mapping = {}
            for i, col in enumerate(columns):
                column_mapping[col] = i
                
            # Create an array with None values initially
            full_values = [None] * len(columns)
            
            # Fill in the values for the specified columns
            for i, col in enumerate(specified_columns):
                if (i < len(values)):
                    # Check if column exists
                    if (col not in column_mapping):
                        return f"Error: Unknown column '{col}' in field list"
                    full_values[column_mapping[col]] = values[i]
            
            values = full_values
        
        # Handle case when auto-increment columns are omitted
        if (len(values) != len(columns) and len(values) == len([c for c in columns if c not in auto_increment])):
            # The values match the number of non-auto-increment columns
            values_with_auto = []
            value_index = 0
            for col in columns:
                if (col in auto_increment):
                    values_with_auto.append(None)  # Placeholder for auto-increment
                else:
                    values_with_auto.append(values[value_index])
                    value_index += 1
            values = values_with_auto
        
        if (len(values) != len(columns)):
            return f"Error: Number of values doesn't match columns."
        
        # Create a dictionary to store the new row values
        new_row = {}
        display_values = []
        
        # First pass: convert values and handle auto-increment
        for col, val in zip(columns, values):
            if (col in auto_increment and (val is None or val == "NULL")):
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
            if (index_type in ["PRIMARY KEY", "UNIQUE"]):
                value = new_row.get(col)
                # Check for duplicates in existing rows
                for row in table["rows"]:
                    if (row.get(col) == value):
                        if (index_type == "PRIMARY KEY"):
                            return f"Error: Duplicate entry '{value}' for key 'PRIMARY KEY'"
                        else:
                            return f"Error: Duplicate entry '{value}' for key '{col}'"
        
        # All checks passed, add the row
        table["rows"].append(new_row)
        return f"Inserted {display_values} into {table_name}."

    def select(self, table_name, columns="*", where=None):
        print(f"DEBUG: select called with table_name={table_name}, columns={columns}, where={where}")
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
        filtered_rows = table["rows"]

        # Handle WHERE clause
        if where:
            print(f"DEBUG: WHERE clause detected: {where}")
            if "IN" in where.upper():
                # Split the condition into column and values
                col, values_str = where.split("IN", 1)
                col = col.strip()
                values_str = values_str.strip().rstrip(";")  # Remove trailing semicolon

                # Check if it's a subquery
                if values_str.startswith("(") and values_str.endswith(")"):
                    subquery = values_str[1:-1].strip()
                    if (subquery.upper().startswith("SELECT")):
                        # Execute the subquery and get the result
                        subquery_result = self.execute_command(subquery)
                        print(f"DEBUG: Subquery result: {subquery_result}")
                        # Extract the values from the subquery result
                        values = [row.split("|")[1].strip() for row in subquery_result.split("\n")[3:-2]]
                        # Convert numeric values to integers where applicable
                        values = [int(v) if v.isdigit() else v for v in values]
                    else:
                        # Parse the values directly
                        values_str = values_str[1:-1].strip()
                        values = [v.strip().strip("'").strip('"') for v in values_str.split(",") if v.strip()]
                        values = [int(v) if v.isdigit() else v for v in values]
                else:
                    return f"Error: Invalid IN condition format '{values_str}'."

                # Debug: Print the parsed column and values
                print(f"DEBUG: Parsed column: {col}, Parsed values: {values}")

                # Use the in_condition method
                try:
                    filtered_rows = self.in_condition(table_name, col, values)
                except ValueError as e:
                    return str(e)
            else:
                # Handle other conditions
                filtered_rows = [row for row in table["rows"] if self._evaluate_condition(row, where)]

        # Adjust column widths based on the filtered rows
        for row in filtered_rows:
            for col in columns:
                value_width = len(str(row.get(col, 'NULL')))
                if col in widths:
                    widths[col] = max(widths[col], value_width)

        # Format with clear column boundaries using vertical bars
        header = "| " + " | ".join(col.ljust(widths[col]) for col in columns) + " |"
        separator = "+" + "+".join("-" * (widths[col] + 2) for col in columns) + "+"
        formatted_rows = []
        for row in filtered_rows:
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
        if (self.current_db is None):
            return "Error: No database selected. Use USE database_name;"
        if (table_name not in self.tables):
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
            if (where is None or self._evaluate_condition(row, where)):
                for column, value in set_dict.items():
                    if (column in row):
                        row[column] = value
                updated_count += 1
        return f"Updated {updated_count} row/s in {table_name}."

    def delete(self, table_name, where=None):
        if (self.current_db is None):
            return "Error: No database selected. Use USE database_name;"
        if (table_name not in self.tables):
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        initial_row_count = len(table["rows"])
        table["rows"] = [row for row in table["rows"] if (where is None or not self._evaluate_condition(row, where))]
        deleted_count = initial_row_count - len(table["rows"])
        return f"Deleted {deleted_count} row/s from {table_name}."

    def _evaluate_condition(self, row, condition):
        """
        Evaluate a WHERE condition against a row.
        Now supports complex conditions with AND/OR operators and nested parentheses.
        """
        # Strip any trailing semicolons
        condition = condition.strip(";").strip()
        print(f"DEBUG: Evaluating condition: {condition}")

        # Handle parenthesized expressions first
        while "(" in condition and ")" in condition:
            # Find the innermost parentheses
            start = condition.rfind("(")
            end = condition.find(")", start)
            if start == -1 or end == -1:
                raise ValueError("Unbalanced parentheses in condition.")

            # Extract the inner condition
            inner_condition = condition[start + 1:end]
            print(f"DEBUG: Found inner condition: {inner_condition}")

            # Evaluate the inner condition
            inner_result = self._evaluate_condition(row, inner_condition)
            print(f"DEBUG: Result of inner condition '{inner_condition}': {inner_result}")

            # Replace the parenthesized expression with its boolean result
            condition = condition[:start] + str(inner_result) + condition[end + 1:]
            print(f"DEBUG: Updated condition after resolving parentheses: {condition}")

        # Handle complex conditions with AND
        if " AND " in condition.upper():
            parts = condition.split(" AND ", 1)  # Split at first AND
            left_result = self._evaluate_condition(row, parts[0].strip())
            right_result = self._evaluate_condition(row, parts[1].strip())
            print(f"DEBUG: AND condition - Left: {parts[0].strip()} = {left_result}, Right: {parts[1].strip()} = {right_result}")
            return left_result and right_result

        # Handle complex conditions with OR
        if " OR " in condition.upper():
            parts = condition.split(" OR ", 1)  # Split at first OR
            left_result = self._evaluate_condition(row, parts[0].strip())
            right_result = self._evaluate_condition(row, parts[1].strip())
            print(f"DEBUG: OR condition - Left: {parts[0].strip()} = {left_result}, Right: {parts[1].strip()} = {right_result}")
            return left_result or right_result

        # Handle standard comparison operators
        for operator in ["!=", "<=", ">=", "=", "<", ">"]:
            if operator in condition:
                parts = condition.split(operator, 1)
                col = parts[0].strip()
                value_str = parts[1].strip()

                # Remove quotes from string literals
                if value_str.startswith("'") and value_str.endswith("'"):
                    value_str = value_str[1:-1]
                elif value_str.startswith('"') and value_str.endswith('"'):
                    value_str = value_str[1:-1]

                # Get column type and convert value accordingly
                value = value_str
                typ = None
                for table in self.tables.values():
                    if "types" in table and col in table["types"]:
                        typ = table["types"][col]
                        break

                if typ:
                    try:
                        value = self._convert_value(value_str, typ)
                    except Exception:
                        pass

                # Get row value
                row_value = row.get(col)
                print(f"DEBUG: Comparing column '{col}' with value '{value}' using operator '{operator}'. Row value: {row_value}")

                # Handle None values
                if row_value is None:
                    return False

                # Compare based on operator
                if operator == "=":
                    return row_value == value
                elif operator == "!=":
                    return row_value != value
                elif operator == "<":
                    return row_value < value
                elif operator == ">":
                    return row_value > value
                elif operator == "<=":
                    return row_value <= value
                elif operator == ">=":
                    return row_value >= value

        # Handle LIKE operator
        if " LIKE " in condition.upper():
            parts = condition.split(" LIKE ", 1)
            col = parts[0].strip()
            pattern = parts[1].strip()

            # Remove quotes from pattern
            if pattern.startswith("'") and pattern.endswith("'"):
                pattern = pattern[1:-1]
            elif pattern.startswith('"') and pattern.endswith('"'):
                pattern = pattern[1:-1]

            # Convert SQL LIKE pattern to regex pattern
            try:
                pattern = pattern.replace("%", ".*").replace("_", ".")
                pattern = f"^{pattern}$"
                row_value = str(row.get(col, ""))
                if row_value is None:
                    return False
                match_result = bool(re.match(pattern, row_value, re.IGNORECASE))
                print(f"DEBUG: LIKE operator - column: {col}, pattern: {pattern}, row_value: {row_value}, match_result: {match_result}")
                return match_result
            except re.error as e:
                print(f"DEBUG: Invalid regex pattern '{pattern}' - {e}")
                return False

        # Handle IN operator
        if " IN " in condition.upper():
            parts = condition.split(" IN ", 1)
            col = parts[0].strip()
            values_str = parts[1].strip()

            # Parse values in parentheses
            if values_str.startswith("(") and values_str.endswith(")"):
                values_str = values_str[1:-1]

                # Split by comma and handle quoted values
                values = []
                for val in re.findall(r'(?:[^,"]|"(?:\\.|[^"])*")+', values_str):
                    val = val.strip()
                    if val.startswith("'") and val.endswith("'"):
                        val = val[1:-1]
                    elif val.startswith('"') and val.endswith('"'):
                        val = val[1:-1]
                    values.append(val)

                row_value = row.get(col)
                print(f"DEBUG: IN operator - column: {col}, values: {values}, row_value: {row_value}")
                return row_value in values

        # Fallback to simple equality check for backward compatibility
        if "=" in condition:
            col, value = condition.split("=", 1)
            col = col.strip()
            value = value.strip().strip('"').strip("'")
            print(f"DEBUG: Fallback equality check - column: {col}, value: {value}, row_value: {row.get(col)}")
            return row.get(col) == value

        return False

    def export_to_sql(self, db_name=None, file_path=None):
        """
        Export database(s) to SQL format
        
        Args:
            db_name: Specific database to export (None for all)
            file_path: Path to save the SQL file (None for auto-generated)
            
        Returns:
            Success message
        """
        from .export import SQLVMExporter
        message, _ = SQLVMExporter.export_to_sql(self, db_name, file_path)
        return message
    
    def export_to_json(self, db_name=None, file_path=None):
        """
        Export database(s) to JSON format
        
        Args:
            db_name: Specific database to export (None for all)
            file_path: Path to save the JSON file (None for auto-generated)
            
        Returns:
            Success message
        """
        from .export import SQLVMExporter
        message, _ = SQLVMExporter.export_to_json(self, db_name, file_path)
        return message

    def import_from_sql(self, db_name, file_path):
        """
        Import SQL file into a database
        
        Args:
            db_name: Target database to import into
            file_path: Path to the SQL file
            
        Returns:
            Success message
        """
        from .importer import SQLVMImporter
        message, _, _ = SQLVMImporter.import_from_sql(self, db_name, file_path)
        return message

    def import_from_json(self, db_name, file_path):
        """
        Import JSON file into a database
        
        Args:
            db_name: Target database to import into
            file_path: Path to the JSON file
            
        Returns:
            Success message
        """
        from .importer import SQLVMImporter
        message, _, _ = SQLVMImporter.import_from_json(self, db_name, file_path)
        return message

    def execute_command(self, command):
        command = command.strip()
        
        # Handle DROP TABLE command
        if command.upper().startswith("DROP TABLE "):
            try:
                # Extract table name
                table_name = command[len("DROP TABLE "):].strip().split()[0].strip(';').strip()
                
                # Check if the table exists
                if table_name not in self.tables:
                    return f"Error: Table '{table_name}' does not exist"
                
                # Remove the table from the current database
                current_db = self.current_db
                if current_db not in self.databases:
                    return f"Error: No database selected"
                
                # Remove the table from the database structure
                if table_name in self.databases[current_db]:
                    del self.databases[current_db][table_name]
                    # Also remove from the tables dictionary
                    if table_name in self.tables:
                        del self.tables[table_name]
                    return f"Table '{table_name}' dropped"
                else:
                    return f"Error: Table '{table_name}' not found in database '{current_db}'"
            except Exception as e:
                return f"Error dropping table: {str(e)}"
        
        # Clean up the command - remove extra whitespace, newlines, and trailing semicolon
        command = re.sub(r'\s+', ' ', command.strip().rstrip(";"))
        
        parts = command.split(" ", 1)
        cmd = parts[0].upper()

        # Database commands
        if cmd == "CREATE":
            # CREATE DATABASE
            match_db = re.match(r"CREATE DATABASE (\w+)", command, re.I)
            if match_db:
                db_name = match_db.group(1)
                return self.create_database(db_name)
            # CREATE TABLE
            match = re.match(r"CREATE TABLE (\w+) \((.+)\)", command, re.I)
            if match:
                table_name = match.group(1)
                columns_def = match.group(2)
                return self.create_table(table_name, columns_def)
        elif cmd == "DROP":
            # DROP DATABASE [IF EXISTS] db_name
            match = re.match(r"DROP DATABASE(?: IF EXISTS)? (\w+)", command, re.I)
            if match:
                db_name = match.group(1)
                if_exists = "IF EXISTS" in command.upper()
                return self.drop_database(db_name, if_exists)
        elif cmd == "USE":
            # USE db_name
            match = re.match(r"USE (\w+)", command, re.I)
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
            # Updated to handle WHERE clause with complex conditions
            match = re.match(r"SELECT (.+) FROM (\w+)(?:\s+WHERE\s+(.+))?", command, re.I)
            if match:
                columns = match.group(1)
                table_name = match.group(2)
                where = match.group(3)
                return self.select(table_name, columns, where)
        elif cmd == "UPDATE":
            # Allow complex WHERE clauses with AND/OR
            match = re.match(r"UPDATE (\w+) SET (.+) WHERE (.+)", command)
            if match:
                table_name = match.group(1)
                set_values = match.group(2)
                where = match.group(3)
                return self.update(table_name, set_values, where)
        elif cmd == "DELETE":
            # Allow complex WHERE clauses with AND/OR
            match = re.match(r"DELETE FROM (\w+) WHERE (.+)", command)
            if match:
                table_name = match.group(1)
                where = match.group(2)
                return self.delete(table_name, where)
        elif cmd == "EXPORT":
            # EXPORT DATABASE db_name TO SQL file_path
            match_export_sql = re.match(r"EXPORT DATABASE (\w+) TO SQL(?:\s+(.+))?", command, re.I)
            if match_export_sql:
                db_name = match_export_sql.group(1)
                file_path = match_export_sql.group(2).strip() if match_export_sql.group(2) else None
                return self.export_to_sql(db_name, file_path)
                
            # EXPORT ALL TO SQL file_path
            match_export_all_sql = re.match(r"EXPORT ALL TO SQL(?:\s+(.+))?", command, re.I)
            if match_export_all_sql:
                file_path = match_export_all_sql.group(1).strip() if match_export_all_sql.group(1) else None
                return self.export_to_sql(None, file_path)
                
            # EXPORT DATABASE db_name TO JSON file_path
            match_export_json = re.match(r"EXPORT DATABASE (\w+) TO JSON(?:\s+(.+))?", command, re.I)
            if match_export_json:
                db_name = match_export_json.group(1)
                file_path = match_export_json.group(2).strip() if match_export_json.group(2) else None
                return self.export_to_json(db_name, file_path)
                
            # EXPORT ALL TO JSON file_path
            match_export_all_json = re.match(r"EXPORT ALL TO JSON(?:\s+(.+))?", command, re.I)
            if match_export_all_json:
                file_path = match_export_all_json.group(1).strip() if match_export_all_json.group(1) else None
                return self.export_to_json(None, file_path)
                
        elif cmd == "IMPORT":
            # IMPORT DATABASE db_name FROM SQL file_path
            match_import_sql = re.match(r"IMPORT DATABASE (\w+) FROM SQL(?:\s+(.+))?", command, re.I)
            if match_import_sql:
                db_name = match_import_sql.group(1)
                file_path = match_import_sql.group(2).strip() if match_import_sql.group(2) else None
                return self.import_from_sql(db_name, file_path)
                
            # IMPORT DATABASE db_name FROM JSON file_path
            match_import_json = re.match(r"IMPORT DATABASE (\w+) FROM JSON(?:\s+(.+))?", command, re.I)
            if match_import_json:
                db_name = match_import_json.group(1)
                file_path = match_import_json.group(2).strip() if match_import_json.group(2) else None
                return self.import_from_json(db_name, file_path)
                
        return "Error: Invalid command."
    def alter_table(self, table_name, operation, column_def=None):
        if (self.current_db is None):
            return "Error: No database selected. Use USE database_name;"
        if (table_name not in self.tables):
            return f"Error: Table {table_name} does not exist."
        
        table = self.tables[table_name]

        if (operation.upper() == "ADD"):
            # Parse the column definition
            col_match = re.match(r'(\w+)\s+(\w+)(?:\((\d+)\))?(.*)$', column_def.strip(), re.I)
            if (not col_match):
                return f"Error: Invalid column definition '{column_def}'."
            
            col_name = col_match.group(1)
            col_type = col_match.group(2).upper()
            col_size = col_match.group(3)
            modifiers = col_match.group(4).upper() if col_match.group(4) else ""

            # Check if the column already exists
            if (col_name in table["columns"]):
                return f"Error: Column '{col_name}' already exists in table '{table_name}'."

            # Add the column to the table
            full_type = f"{col_type}({col_size})" if col_size else col_type
            table["columns"].append(col_name)
            table["types"][col_name] = full_type

            # Handle AUTO_INCREMENT
            if ("AUTO_INCREMENT" in modifiers):
                if (any("AUTO_INCREMENT" in table["types"][col] for col in table["auto_increment"])):
                    return "Error: Only one AUTO_INCREMENT column is allowed per table."
                table["auto_increment"][col_name] = 0

            # Add default values for the new column in existing rows
            for row in table["rows"]:
                row[col_name] = None

            return f"Column '{col_name}' added to table '{table_name}'."

        elif (operation.upper() == "DROP"):
            # Check if the column exists
            if (column_def not in table["columns"]):
                return f"Error: Column '{column_def}' does not exist in table '{table_name}'."

            # Remove the column from the table
            table["columns"].remove(column_def)
            table["types"].pop(column_def, None)
            table["auto_increment"].pop(column_def, None)
            table["indexes"].pop(column_def, None)

            # Remove the column from all rows
            for row in table["rows"]:
                row.pop(column_def, None)

            return f"Column '{column_def}' dropped from table '{table_name}'."

        elif (operation.upper() == "MODIFY"):
            # Parse the column definition
            col_match = re.match(r'(\w+)\s+(\w+)(?:\((\d+)\))?(.*)$', column_def.strip(), re.I)
            if (not col_match):
                return f"Error: Invalid column definition '{column_def}'."
            
            col_name = col_match.group(1)
            col_type = col_match.group(2).upper()
            col_size = col_match.group(3)
            modifiers = col_match.group(4).upper() if col_match.group(4) else ""

            # Check if the column exists
            if (col_name not in table["columns"]):
                return f"Error: Column '{col_name}' does not exist in table '{table_name}'."

            # Update the column type
            full_type = f"{col_type}({col_size})" if col_size else col_type
            table["types"][col_name] = full_type

            return f"Column '{col_name}' modified in table '{table_name}'."

        else:
            return f"Error: Unsupported ALTER TABLE operation '{operation}'."

    def in_condition(self, table_name, column, values):
        print(f"DEBUG: in_condition called with table_name={table_name}, column={column}, values={values}")
        if self.current_db is None:
            raise ValueError("Error: No database selected. Use USE database_name;")
        if table_name not in self.tables:
            raise ValueError(f"Error: Table {table_name} does not exist.")
        table = self.tables[table_name]

        # Ensure the column exists in the table
        if column not in table["columns"]:
            raise ValueError(f"Error: Column '{column}' does not exist in table '{table_name}'.")

        # Ensure values is a list
        if not isinstance(values, list):
            raise ValueError(f"Error: IN condition values must be a list. Got '{type(values).__name__}' instead.")

        # If values is empty, return no rows
        if not values:
            return []

        # Get the column type
        column_type = table["types"].get(column, "TEXT")

        # Convert values to the column type
        try:
            converted_values = [self._convert_value(value, column_type) for value in values]
        except ValueError as e:
            raise ValueError(f"Error: {e}. Ensure the values in the IN condition match the column type '{column_type}'.")

        # Debug: Print the converted values
        print(f"DEBUG: Converted values for IN condition: {converted_values}")

        # Filter rows based on the IN condition
        filtered_rows = [row for row in table["rows"] if row.get(column) in converted_values]

        # Debug: Print the filtered rows
        print(f"DEBUG: Filtered rows: {filtered_rows}")

        return filtered_rows

    def execute_command(self, command):
        print(f"DEBUG: execute_command called with command={command}")
        import time  # Ensure the time module is imported
        start_time = time.time()  # Record the start time

        bytecode = SQLParser.parse_to_bytecode(command)
        print(f"DEBUG: Parsed bytecode: {bytecode}")
        results = self.vm.execute_bytecode(bytecode)
        result_output = "\n".join(results)

        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate elapsed time

        # Append execution time to the result
        result_output += f"\n(Execution time: {elapsed_time:.4f} seconds)"
        return result_output

