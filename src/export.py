import json
import os
from datetime import datetime
import re

class SQLVMExporter:
    @staticmethod
    def export_to_sql(vm, db_name=None, file_path=None):
        """
        Export database(s) to SQL format
        
        Args:
            vm: The SQLVM instance
            db_name: Specific database to export (None for all)
            file_path: Path to save the SQL file (None for auto-generated)
            
        Returns:
            Tuple of (success message, file path)
        """
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{db_name or 'all_databases'}_{timestamp}.sql"
            file_path = os.path.join(os.getcwd(), file_name)
        
        try:
            with open(file_path, 'w') as f:
                # If specific database is requested
                if db_name:
                    if db_name not in vm.databases:
                        return f"Error: Database '{db_name}' does not exist.", None
                    
                    databases = {db_name: vm.databases[db_name]}
                else:
                    databases = vm.databases
                
                # Generate SQL for each database
                for db, tables in databases.items():
                    f.write(f"-- Export of database: {db}\n")
                    f.write(f"CREATE DATABASE IF NOT EXISTS `{db}`;\n")
                    f.write(f"USE `{db}`;\n\n")
                    
                    # Create table statements
                    for table_name, table_info in tables.items():
                        columns = table_info['columns']
                        types = table_info.get('types', {})
                        auto_increment = table_info.get('auto_increment', {})
                        indexes = table_info.get('indexes', {})
                        
                        # Build column definitions with SQL-like syntax
                        col_defs = []
                        primary_keys = []
                        
                        for col in columns:
                            # Get type and convert legacy PRIMARY to PRIMARY KEY
                            col_type = types.get(col, 'TEXT')
                            index_type = indexes.get(col, '')
                            
                            # Create proper SQL column definition
                            col_def = f"`{col}` {col_type}"
                            
                            if col in auto_increment:
                                col_def += " AUTO_INCREMENT"
                                
                            # Handle primary key separately for SQL compatibility
                            if index_type == "PRIMARY" or index_type == "PRIMARY KEY":
                                primary_keys.append(col)
                                # Don't add PRIMARY KEY here - we'll add it at the end
                            elif index_type:
                                col_def += f" {index_type}"
                                
                            col_defs.append(col_def)
                        
                        # Add PRIMARY KEY clause at the end if needed
                        if primary_keys:
                            col_defs.append(f"PRIMARY KEY (`{'`, `'.join(primary_keys)}`)")
                        
                        f.write(f"CREATE TABLE `{table_name}` (\n  {',\n  '.join(col_defs)}\n);\n\n")
                        
                        # Insert statements for each row with SQL-like syntax
                        for row in table_info.get('rows', []):
                            values = []
                            for col in columns:
                                val = row.get(col)
                                if val is None:
                                    values.append("NULL")
                                elif isinstance(val, str):
                                    # Escape any quotes in string values
                                    escaped_val = val.replace("'", "''")
                                    values.append(f"'{escaped_val}'")
                                else:
                                    values.append(str(val))
                            
                            f.write(f"INSERT INTO `{table_name}` VALUES ({', '.join(values)});\n")
                        f.write("\n")
                
            return f"Successfully exported to SQL file: {file_path}", file_path
        except Exception as e:
            return f"Error exporting to SQL: {str(e)}", None
    
    @staticmethod
    def export_to_json(vm, db_name=None, file_path=None):
        """
        Export database(s) to JSON format
        
        Args:
            vm: The SQLVM instance
            db_name: Specific database to export (None for all)
            file_path: Path to save the JSON file (None for auto-generated)
            
        Returns:
            Tuple of (success message, file path)
        """
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{db_name or 'all_databases'}_{timestamp}.json"
            file_path = os.path.join(os.getcwd(), file_name)
        
        try:
            # If specific database is requested
            if db_name:
                if db_name not in vm.databases:
                    return f"Error: Database '{db_name}' does not exist.", None
                export_data = {db_name: vm.databases[db_name]}
            else:
                export_data = vm.databases
            
            # Convert to serializable format if needed
            # Some data types might need special handling for JSON serialization
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return f"Successfully exported to JSON file: {file_path}", file_path
        except Exception as e:
            return f"Error exporting to JSON: {str(e)}", None
