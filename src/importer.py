import os
import json
import re
from datetime import datetime

class SQLVMImporter:
    @staticmethod
    def import_from_sql(vm, db_name, file_path):
        """
        Import SQL file into a specified database
        
        Args:
            vm: The SQLVM instance
            db_name: Target database name
            file_path: Path to the SQL file to import
            
        Returns:
            Tuple of (success message, error_count, success_count)
        """
        try:
            # Check if database exists and use it
            if db_name not in vm.databases:
                return f"Error: Database '{db_name}' does not exist.", 0, 0
            
            result = vm.use_database(db_name)
            if "Error" in result:
                return f"Error: Could not use database '{db_name}': {result}", 0, 0
                
            # Read SQL file
            with open(file_path, 'r') as sql_file:
                sql_content = sql_file.read()
            
            print(f"Processing SQL file: {file_path}")
            
            # Pre-process the SQL content
            # 1. Remove comments
            sql_content = re.sub(r'--.*?$', '', sql_content, flags=re.MULTILINE)  # Single line comments
            sql_content = re.sub(r'/\*[\s\S]*?\*/', '', sql_content)  # Multi-line comments
            
            # 2. Normalize line endings
            sql_content = sql_content.replace('\r\n', '\n').replace('\r', '\n')
            
            # 3. Split commands more intelligently
            commands = SQLVMImporter._parse_sql_commands(sql_content)
            
            print(f"Found {len(commands)} commands in SQL file")
            
            # Process commands for SQLVM compatibility
            processed_commands = []
            for i, cmd in enumerate(commands):
                # Skip empty commands
                if not cmd.strip():
                    continue
                
                # Skip certain statements
                # 1. Skip USE statements
                if re.match(r'^\s*USE\s+', cmd, re.IGNORECASE):
                    print(f"Skipping USE statement: {cmd}")
                    continue
                
                # 2. Skip CREATE DATABASE for the current DB
                if re.match(r'^\s*CREATE\s+DATABASE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?' + db_name + r'[`"\']?', cmd, re.IGNORECASE):
                    print(f"Skipping CREATE DATABASE statement: {cmd}")
                    continue
                
                # 3. Skip SET statements
                if re.match(r'^\s*SET\s+', cmd, re.IGNORECASE):
                    print(f"Skipping SET statement: {cmd}")
                    continue
                
                # Standardize SQL syntax for SQLVM compatibility
                standardized_cmd = SQLVMImporter._standardize_identifiers(cmd)
                processed_commands.append(standardized_cmd)
                print(f"Command {i+1}: {standardized_cmd[:75]}..." if len(standardized_cmd) > 75 else standardized_cmd)
            
            # Execute each processed command
            success_count = 0
            errors = []
            
            for i, cmd in enumerate(processed_commands):
                try:
                    print(f"Executing command {i+1}/{len(processed_commands)}")
                    result = vm.execute_command(cmd)
                    
                    if "Error" in result:
                        detailed_error = SQLVMImporter._get_detailed_error(cmd, result)
                        errors.append(detailed_error)
                        print(f"Error in command {i+1}: {detailed_error[:100]}...")
                    else:
                        success_count += 1
                        print(f"Command {i+1} executed successfully")
                except Exception as e:
                    error_msg = f"Exception executing: {cmd[:50]}{'...' if len(cmd) > 50 else ''}\n{str(e)}"
                    errors.append(error_msg)
                    print(f"Exception in command {i+1}: {error_msg}")
            
            # Generate result message
            if errors:
                error_message = f"Imported with {len(errors)} errors. {success_count} commands succeeded."
                if len(errors) <= 3:
                    error_message += "\n\nErrors:\n" + "\n".join(errors)
                return error_message, len(errors), success_count
            else:
                success_message = f"Successfully imported {success_count} SQL commands into {db_name}."
                return success_message, 0, success_count
                
        except Exception as e:
            return f"Error importing SQL file: {str(e)}", 1, 0

    @staticmethod
    def _standardize_identifiers(cmd):
        """
        Standardize SQL identifiers to work better with SQLVM:
        - Replace quoted identifiers with unquoted versions
        - Handle other quoting issues
        - Normalize syntax to be compatible with SQLVM
        """
        result = cmd
        
        # Handle CREATE TABLE statements with composite primary keys
        if re.match(r'^\s*CREATE\s+TABLE\s+', result, re.IGNORECASE):
            # First handle quoted table names
            patterns = [
                (r"CREATE\s+TABLE\s+'([^']+)'", r"CREATE TABLE \1"),
                (r'CREATE\s+TABLE\s+"([^"]+)"', r"CREATE TABLE \1"),
                (r"CREATE\s+TABLE\s+`([^`]+)`", r"CREATE TABLE \1")
            ]
            
            for pattern, replacement in patterns:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            
            # Extract and preserve composite primary key definition
            composite_pk_match = re.search(r'PRIMARY\s+KEY\s+\(\s*(`[^`]+`|"[^"]+"|\'[^\']+\'|\w+)(?:\s*,\s*(`[^`]+`|"[^"]+"|\'[^\']+\'|\w+))+\s*\)', result, re.IGNORECASE)
            composite_pk = None
            
            if composite_pk_match:
                composite_pk = composite_pk_match.group(0)
                # Extract the column names from the PRIMARY KEY definition
                # This regex matches: quoted or unquoted column names inside the PRIMARY KEY parentheses
                pk_columns = re.findall(r'`([^`]+)`|"([^"]+)"|\'([^\']+)\'|(\w+)', composite_pk_match.group(0))
                # Flatten the list of tuples and filter out None values
                pk_column_names = [next(filter(None, col)) for col in pk_columns]
                
                # Create a properly formatted PRIMARY KEY clause
                composite_pk = f"PRIMARY KEY ({', '.join(pk_column_names)})"
            
            # Process column definitions
            if "(" in result and ")" in result:
                match = re.search(r'CREATE\s+TABLE\s+\w+\s*\((.*)\)', result, re.IGNORECASE | re.DOTALL)
                
                if match:
                    column_defs = match.group(1)
                    
                    # Clean up column definitions one by one
                    cleaned_cols = []
                    for col_def in SQLVMImporter._split_column_definitions(column_defs):
                        # If this is the PRIMARY KEY definition and we already extracted a composite key, skip it
                        if composite_pk and col_def.strip().upper().startswith("PRIMARY KEY"):
                            continue
                            
                        # Remove quotes from column names and normalize data types
                        col_def = re.sub(r"^'([^']+)'", r"\1", col_def)
                        col_def = re.sub(r'^"([^"]+)"', r"\1", col_def)
                        col_def = re.sub(r"^`([^`]+)`", r"\1", col_def)
                        
                        # Normalize data types
                        col_def = re.sub(r"int\s*\(\d+\)", "INT", col_def, flags=re.IGNORECASE)
                        col_def = re.sub(r"varchar\s*\(\d+\)", "VARCHAR", col_def, flags=re.IGNORECASE)
                        col_def = re.sub(r"char\s*\(\d+\)", "CHAR", col_def, flags=re.IGNORECASE)
                        
                        # Remove unsupported features
                        col_def = re.sub(r"CHARACTER\s+SET\s+\w+", "", col_def, flags=re.IGNORECASE)
                        col_def = re.sub(r"COLLATE\s+\w+", "", col_def, flags=re.IGNORECASE)
                        col_def = re.sub(r"COMMENT\s+'[^']*'", "", col_def, flags=re.IGNORECASE)
                        
                        # Add to cleaned columns list if not empty
                        cleaned_cols.append(col_def.strip())
                    
                    # Add back the composite primary key if we found one
                    if composite_pk:
                        cleaned_cols.append(composite_pk)
                    
                    # Rebuild the CREATE TABLE statement
                    table_name_match = re.match(r'CREATE\s+TABLE\s+(\w+)', result, re.IGNORECASE)
                    if table_name_match:
                        table_name = table_name_match.group(1)
                        result = f"CREATE TABLE {table_name} ({', '.join(cleaned_cols)})"
        
        # Handle quoted table names in INSERT statements
        elif re.match(r'^\s*INSERT\s+INTO\s+', result, re.IGNORECASE):
            # Handle INSERT INTO commands with quoted table names
            # Match patterns like: INSERT INTO `table` or INSERT INTO 'table' or INSERT INTO "table"
            patterns = [
                (r"INSERT\s+INTO\s+`([^`]+)`", r"INSERT INTO \1"),
                (r"INSERT\s+INTO\s+'([^']+)'", r"INSERT INTO \1"),
                (r'INSERT\s+INTO\s+"([^"]+)"', r"INSERT INTO \1")
            ]
            
            for pattern, replacement in patterns:
                result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            
            # Standardize values in INSERT statements
            # First, extract everything after VALUES to handle the values part separately
            values_match = re.search(r'(VALUES\s*\()(.+)(\))', result, re.IGNORECASE)
            if values_match:
                prefix = values_match.group(1)
                values_content = values_match.group(2)
                suffix = values_match.group(3)
                
                # Process values: standardize quotes for string values
                processed_values = []
                # Split by comma, but respect quotes
                value_parts = SQLVMImporter._split_by_comma_respecting_quotes(values_content)
                
                for value in value_parts:
                    value = value.strip()
                    # Convert 'string' or `string` to "string" for consistency
                    if (value.startswith("'") and value.endswith("'")) or (value.startswith("`") and value.endswith("`")):
                        inner_value = value[1:-1].replace('"', '\\"')  # Escape any double quotes
                        processed_value = f'"{inner_value}"'
                        processed_values.append(processed_value)
                    else:
                        processed_values.append(value)
                
                # Reconstruct the INSERT statement
                result = result.replace(values_match.group(0), f"{prefix}{', '.join(processed_values)}{suffix}")
        
        # Handle generic UPDATE, SELECT, and DELETE operations with quoted table names
        cmd_patterns = [
            (r"UPDATE\s+`([^`]+)`", r"UPDATE \1"),
            (r"UPDATE\s+'([^']+)'", r"UPDATE \1"),
            (r'UPDATE\s+"([^"]+)"', r"UPDATE \1"),
            
            (r"FROM\s+`([^`]+)`", r"FROM \1"),
            (r"FROM\s+'([^']+)'", r"FROM \1"),
            (r'FROM\s+"([^"]+)"', r"FROM \1"),
            
            (r"DELETE\s+FROM\s+`([^`]+)`", r"DELETE FROM \1"),
            (r"DELETE\s+FROM\s+'([^']+)'", r"DELETE FROM \1"),
            (r'DELETE\s+FROM\s+"([^"]+)"', r"DELETE FROM \1"),
        ]
        
        for pattern, replacement in cmd_patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Always remove unsupported clauses from statements, regardless of statement type
        clauses_to_remove = [
            r"ENGINE\s*=\s*\w+",
            r"DEFAULT\s+CHARACTER\s+SET\s*=?\s*\w+",
            r"COLLATE\s+\w+",
            r"AUTO_INCREMENT\s*=\s*\d+",
            r"ROW_FORMAT\s*=\s*\w+",
            r"CHARACTER\s+SET\s+\w+",
            r"DEFAULT\s+COLLATE\s*=?\s*\w+"
        ]
        
        for clause in clauses_to_remove:
            result = re.sub(clause, "", result, flags=re.IGNORECASE)
        
        # Clean up extra spaces and commas that might be left
        result = re.sub(r',\s*\)', ')', result)  # Remove trailing commas before closing parenthesis
        result = re.sub(r'\s+', ' ', result)     # Normalize whitespace
        result = result.strip()
        
        return result

    @staticmethod
    def _split_by_comma_respecting_quotes(text):
        """
        Split a string by commas, but respect quoted content
        For example: "hello", 'world', 42 -> ["hello", 'world', 42]
        """
        result = []
        current_part = ""
        in_quotes = False
        quote_char = None
        paren_level = 0
        
        for char in text:
            if char in ["'", '"', '`'] and (not in_quotes or quote_char == char):
                in_quotes = not in_quotes
                if in_quotes:
                    quote_char = char
                else:
                    quote_char = None
                current_part += char
            elif char == '(' and not in_quotes:
                paren_level += 1
                current_part += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_part += char
            elif char == ',' and not in_quotes and paren_level == 0:
                result.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        # Add the last part if it exists
        if current_part.strip():
            result.append(current_part.strip())
        
        return result

    @staticmethod
    def _split_column_definitions(column_defs):
        """
        Split column definitions intelligently, handling commas within parentheses
        For example: col1 INT, col2 VARCHAR(255), PRIMARY KEY (id)
        """
        result = []
        current_def = ""
        paren_level = 0
        quote_char = None
        
        for char in column_defs:
            if char in ("'", '"', '`') and (quote_char is None or char == quote_char):
                if quote_char is None:
                    quote_char = char
                else:
                    quote_char = None
                current_def += char
            elif char == '(' and quote_char is None:
                paren_level += 1
                current_def += char
            elif char == ')' and quote_char is None:
                paren_level -= 1
                current_def += char
            elif char == ',' and paren_level == 0 and quote_char is None:
                result.append(current_def.strip())
                current_def = ""
            else:
                current_def += char
        
        if current_def.strip():
            result.append(current_def.strip())
        
        return result

    @staticmethod
    def _parse_sql_commands(sql_content):
        """
        More intelligent parsing of SQL commands, handling different quoting styles
        and respecting statement boundaries.
        """
        commands = []
        current_cmd = ""
        in_quotes = False
        quote_char = None
        paren_level = 0
        comment_mode = None  # None, 'line', or 'block'
        i = 0
        
        while i < len(sql_content):
            char = sql_content[i]
            next_char = sql_content[i+1] if i < len(sql_content) - 1 else None
            
            # Handle comments
            if comment_mode == 'line' and char == '\n':
                # End of line comment
                comment_mode = None
                i += 1
                continue
            elif comment_mode == 'block' and char == '*' and next_char == '/':
                # End of block comment
                comment_mode = None
                i += 2
                continue
            elif comment_mode:
                # Inside a comment, continue to next character
                i += 1
                continue
            elif char == '-' and next_char == '-':
                # Start of line comment
                comment_mode = 'line'
                i += 2
                continue
            elif char == '/' and next_char == '*':
                # Start of block comment
                comment_mode = 'block'
                i += 2
                continue
            
            # Handle quotes and special characters
            if char in ["'", '"', '`'] and (not in_quotes or quote_char == char):
                in_quotes = not in_quotes
                if in_quotes:
                    quote_char = char
                else:
                    quote_char = None
                current_cmd += char
            elif char == '(' and not in_quotes:
                paren_level += 1
                current_cmd += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_cmd += char
            elif char == ';' and not in_quotes and paren_level == 0:
                # End of command
                if current_cmd.strip():
                    commands.append(current_cmd.strip())
                current_cmd = ""
            else:
                current_cmd += char
            
            i += 1
        
        # Add the last command if it exists
        if current_cmd.strip():
            commands.append(current_cmd.strip())
        
        return commands

    @staticmethod
    def _get_detailed_error(cmd, error_msg):
        """
        Generate a more detailed error message based on common issues
        """
        # Extract the first line of the command for context
        cmd_first_line = cmd.split('\n')[0] + ("..." if '\n' in cmd else "")
        
        # Check for common issues and provide more helpful messages
        if "Error: Invalid command." in error_msg or "syntax error" in error_msg.lower():
            # Check for INSERT statement issues
            if cmd.upper().startswith("INSERT INTO"):
                # Check for quoted table names
                quoted_table_pattern = r"INSERT\s+INTO\s+['\"`]([^'\"`]+)['\"`]"
                quoted_table_match = re.search(quoted_table_pattern, cmd, re.IGNORECASE)
                
                if quoted_table_match:
                    return (
                        f"Error executing: {cmd_first_line}\n"
                        f"SQLVM doesn't properly support quoted table names in INSERT statements. "
                        f"Try removing quotes around the table name: INSERT INTO {quoted_table_match.group(1)} ..."
                    )
                
                # Check for value format issues
                if "VALUES" in cmd.upper():
                    return (
                        f"Error executing: {cmd_first_line}\n"
                        f"Possible issue with VALUES format. Make sure string values are quoted properly "
                        f"and numeric values are not quoted."
                    )
            
            # Check for CREATE TABLE syntax issues
            elif "CREATE TABLE" in cmd.upper():
                # Look for quoted identifiers
                quoted_identifiers = re.findall(r"'([^']+)'|\"([^\"]+)\"|`([^`]+)`", cmd)
                if quoted_identifiers:
                    return (
                        f"Error executing: {cmd_first_line}\n"
                        "SQLVM doesn't fully support quoted identifiers. "
                        "Try using plain identifiers without quotes."
                    )
                
                # Check for complex constraints or features
                complex_features = ["FOREIGN KEY", "CONSTRAINT", "DEFAULT", "CHECK", "REFERENCES", "UNIQUE"]
                for feature in complex_features:
                    if feature in cmd.upper():
                        return (
                            f"Error executing: {cmd_first_line}\n"
                            f"SQLVM doesn't support {feature} syntax. Try simplifying your SQL statement."
                        )
            
            # Look for complex JOIN syntax
            elif "JOIN" in cmd.upper() and "SELECT" in cmd.upper():
                return (
                    f"Error executing: {cmd_first_line}\n"
                    "SQLVM may not support complex JOIN syntax. Try using simpler queries."
                )
        
        # Default to original error with command context
        return f"Error executing: {cmd_first_line}\n{error_msg}"

    @staticmethod
    def import_from_json(vm, db_name, file_path):
        """
        Import JSON file into a specified database
        
        Args:
            vm: The SQLVM instance
            db_name: Target database name
            file_path: Path to the JSON file to import
            
        Returns:
            Tuple of (success message, error_count, success_count)
        """
        try:
            # Check if database exists and use it
            if db_name not in vm.databases:
                return f"Error: Database '{db_name}' does not exist.", 0, 0
            
            result = vm.use_database(db_name)
            if "Error" in result:
                return f"Error: Could not use database '{db_name}': {result}", 0, 0
                
            # Read JSON file
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                
            # Handle different JSON formats
            success_count = 0
            errors = []
            
            # Case 1: Direct database format from export (dict with tables)
            if isinstance(data, dict):
                # Check if this JSON contains the target database
                if db_name in data:
                    # Extract just this database's tables
                    tables_data = data[db_name]
                    result, error_count, success_count = SQLVMImporter._import_tables_dict(vm, tables_data)
                    return result, error_count, success_count
                
                # Check if this is a direct tables dictionary
                elif all(isinstance(val, dict) for val in data.values()):
                    result, error_count, success_count = SQLVMImporter._import_tables_dict(vm, data)
                    return result, error_count, success_count
                
                # Check if this is a single table definition
                elif "table" in data and "columns" in data:
                    result, error_count, success_count = SQLVMImporter._import_single_table(vm, data)
                    return result, error_count, success_count
                
                else:
                    return "Error: Unrecognized JSON format. Expected database or table structure.", 1, 0
                    
            # Case 2: Array of records
            elif isinstance(data, list) and len(data) > 0:
                if all(isinstance(item, dict) for item in data):
                    # This is a list of records for a single table
                    result, error_count, success_count = SQLVMImporter._import_records_list(vm, data, None)
                    return result, error_count, success_count
                else:
                    return "Error: Expected list of record objects.", 1, 0
            
            else:
                return "Error: Unsupported JSON format.", 1, 0
                
        except Exception as e:
            return f"Error importing JSON file: {str(e)}", 1, 0
    
    @staticmethod
    def _import_tables_dict(vm, tables_data):
        """Import tables from a dictionary of table definitions"""
        success_tables = 0
        success_records = 0
        errors = []
        
        # Process each table
        for table_name, table_info in tables_data.items():
            try:
                # Create the table if it doesn't exist
                if "columns" not in table_info:
                    errors.append(f"Table {table_name} is missing columns definition")
                    continue
                
                columns = table_info.get('columns', [])
                types = table_info.get('types', {})
                
                # Build column definitions
                col_defs = []
                for col in columns:
                    col_type = types.get(col, "TEXT")
                    col_defs.append(f"{col} {col_type}")
                
                create_cmd = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
                result = vm.execute_command(create_cmd)
                
                if "Error" in result and "already exists" not in result:
                    errors.append(f"Error creating table {table_name}: {result}")
                    continue
                
                success_tables += 1
                
                # Insert rows if present
                if "rows" in table_info:
                    for row in table_info["rows"]:
                        values = []
                        for col in columns:
                            val = row.get(col)
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, str):
                                values.append(f'"{val.replace('"', '""')}"')
                            else:
                                values.append(str(val))
                        
                        insert_cmd = f"INSERT INTO {table_name} VALUES ({', '.join(values)})"
                        result = vm.execute_command(insert_cmd)
                        
                        if "Error" in result:
                            errors.append(f"Error inserting into {table_name}: {result}")
                        else:
                            success_records += 1
                
            except Exception as e:
                errors.append(f"Error processing table {table_name}: {str(e)}")
        
        # Generate result message
        if errors:
            error_message = f"Imported {success_tables} tables with {success_records} records. {len(errors)} errors occurred."
            return error_message, len(errors), success_records
        else:
            success_message = f"Successfully imported {success_tables} tables with {success_records} records."
            return success_message, 0, success_records
    
    @staticmethod
    def _import_single_table(vm, table_data):
        """Import a single table definition"""
        table_name = table_data.get("table")
        if not table_name:
            return "Error: Missing table name in JSON", 1, 0
        
        columns = table_data.get("columns", [])
        if not columns:
            return f"Error: No columns defined for table {table_name}", 1, 0
        
        # Extract column definitions
        col_defs = []
        col_names = []
        
        for col in columns:
            if isinstance(col, dict):
                col_name = col.get("name")
                col_type = col.get("type", "VARCHAR")
                constraints = " ".join(col.get("constraints", []))
                
                col_defs.append(f"{col_name} {col_type} {constraints}".strip())
                col_names.append(col_name)
            else:
                # Simple column name
                col_defs.append(f"{col} VARCHAR")
                col_names.append(col)
        
        # Create table
        create_cmd = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
        result = vm.execute_command(create_cmd)
        
        if "Error" in result and "already exists" not in result:
            return f"Error creating table: {result}", 1, 0
        
        # Insert records
        success_count = 0
        errors = []
        records = table_data.get("records", [])
        
        for record in records:
            try:
                if isinstance(record, list):
                    # Format values
                    values = []
                    for val in record:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            values.append(f'"{val.replace('"', '""')}"')
                        else:
                            values.append(str(val))
                    
                    insert_cmd = f"INSERT INTO {table_name} VALUES ({', '.join(values)})"
                else:
                    # Record is a dictionary, use column names
                    columns = []
                    values = []
                    for col_name, val in record.items():
                        columns.append(col_name)
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            values.append(f'"{val.replace('"', '""')}"')
                        else:
                            values.append(str(val))
                    
                    insert_cmd = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)})"
                
                result = vm.execute_command(insert_cmd)
                if "Error" in result:
                    errors.append(f"Error inserting record: {result}")
                else:
                    success_count += 1
                    
            except Exception as e:
                errors.append(f"Error inserting record: {str(e)}")
        
        # Generate result message
        if errors:
            error_message = f"Imported table {table_name} with {success_count}/{len(records)} records. {len(errors)} errors."
            return error_message, len(errors), success_count
        else:
            success_message = f"Successfully imported table {table_name} with {success_count} records."
            return success_message, 0, success_count
    
    @staticmethod
    def _import_records_list(vm, records, table_name):
        """Import a list of records into a table"""
        # If no table name specified, use a default or return an error
        if not table_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            table_name = f"imported_table_{timestamp}"
        
        success_count = 0
        errors = []
        
        # Create table if it doesn't exist
        if len(records) > 0:
            # Infer columns from first record
            first_record = records[0]
            if not isinstance(first_record, dict):
                return "Error: Expected records as dictionaries", 1, 0
            
            columns = list(first_record.keys())
            
            # Create table
            col_defs = [f"{col} VARCHAR" for col in columns]
            create_cmd = f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
            
            result = vm.execute_command(create_cmd)
            if "Error" in result and "already exists" not in result:
                return f"Error creating table: {result}", 1, 0
        
        # Insert records
        for record in records:
            try:
                if isinstance(record, dict):
                    # Record is a dictionary, use column names
                    columns = list(record.keys())
                    values = []
                    for val in record.values():
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            values.append(f'"{val.replace('"', '""')}"')
                        else:
                            values.append(str(val))
                    
                    insert_cmd = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)})"
                    
                    result = vm.execute_command(insert_cmd)
                    if "Error" in result:
                        errors.append(f"Error inserting record: {result}")
                    else:
                        success_count += 1
                else:
                    errors.append(f"Skipped non-dictionary record: {record}")
                    
            except Exception as e:
                errors.append(f"Error inserting record: {str(e)}")
        
        # Generate result message
        if errors:
            error_message = f"Imported {success_count}/{len(records)} records into {table_name}. {len(errors)} errors."
            return error_message, len(errors), success_count
        else:
            success_message = f"Successfully imported {success_count} records into {table_name}."
            return success_message, 0, success_count