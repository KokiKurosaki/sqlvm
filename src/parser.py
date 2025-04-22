import re
from .opcodes import OPCODES
import os

class SQLParser:
    @staticmethod
    def parse_to_bytecode(command):
        # Preserve the original command for values but normalize keywords
        original_command = command.strip()
        command = original_command.upper()

        if command.startswith("SELECT"):
            # Match SELECT queries with nested subqueries in the IN condition
            match_nested_subquery = re.match(r"SELECT (.+) FROM (\w+) WHERE (.+) IN \((SELECT .+ IN \(.+\))\)", original_command, re.I)
            if match_nested_subquery:
                columns = match_nested_subquery.group(1)
                table_name = match_nested_subquery.group(2)
                condition_column = match_nested_subquery.group(3)
                nested_subquery = match_nested_subquery.group(4)
                return [("SELECT_ROWS", table_name, columns, f"{condition_column} IN ({nested_subquery})")]

            # Match SELECT queries with single-level subqueries in the IN condition
            match_where_in = re.match(r"SELECT (.+) FROM (\w+) WHERE (.+) IN \((SELECT .+)\)", original_command, re.I)
            if match_where_in:
                columns = match_where_in.group(1)
                table_name = match_where_in.group(2)
                condition_column = match_where_in.group(3)
                subquery = match_where_in.group(4)
                return [("SELECT_ROWS", table_name, columns, f"{condition_column} IN ({subquery})")]
            
            # Match SELECT queries with a WHERE clause
            match_where = re.match(r"SELECT (.+) FROM (\w+) WHERE (.+)", original_command, re.I)
            if match_where:
                columns = match_where.group(1)
                table_name = match_where.group(2)
                where_clause = match_where.group(3)
                return [("SELECT_ROWS", table_name, columns, where_clause)]

            # Match SELECT queries with static IN values
            match_where_in_static = re.match(r"SELECT (.+) FROM (\w+) WHERE (.+) IN \((.*)\)", original_command, re.I)
            if match_where_in_static:
                columns = match_where_in_static.group(1)
                table_name = match_where_in_static.group(2)
                condition_column = match_where_in_static.group(3)
                in_values = match_where_in_static.group(4).strip()

                # Handle empty IN condition
                if not in_values:
                    return [("SELECT_ROWS", table_name, columns, f"{condition_column} IN ()")]

                return [("SELECT_ROWS", table_name, columns, f"{condition_column} IN ({in_values})")]

            # Match simple SELECT queries
            match = re.match(r"SELECT (.+) FROM (\w+)", original_command, re.I)
            if match:
                columns = match.group(1)
                table_name = match.group(2)
                return [("SELECT_ROWS", table_name, columns)]

        # Handle other commands (existing logic)
        if command.startswith("CREATE DATABASE"):
            match = re.match(r"CREATE DATABASE (\w+)", original_command, re.I)
            if match:
                db_name = match.group(1)
                return [("CREATE_DATABASE", db_name)]
        elif command.startswith("DROP DATABASE"):
            match = re.match(r"DROP DATABASE(?: IF EXISTS)? (\w+)", original_command, re.I)
            if match:
                db_name = match.group(1)
                if_exists = "IF EXISTS" in command
                return [("DROP_DATABASE", db_name, if_exists)]
        elif command.startswith("USE"):
            match = re.match(r"USE (\w+)", original_command, re.I)
            if match:
                db_name = match.group(1)
                return [("USE_DATABASE", db_name)]
        elif command.startswith("SHOW DATABASES"):
            return [("SHOW_DATABASES",)]
        elif command.startswith("CREATE TABLE"):
            match = re.match(r"CREATE TABLE (\w+) \((.+)\)", original_command, re.I)
            if match:
                table_name = match.group(1)
                columns_def = match.group(2)
                return [("CREATE_TABLE", table_name, columns_def)]
        elif command.startswith("INSERT INTO"):
            # Match INSERT INTO table VALUES (...)
            match = re.match(r"INSERT INTO (\w+) VALUES \((.+)\)", original_command, re.I)
            if match:
                table_name = match.group(1)
                values = [v.strip().strip('"').strip("'") for v in match.group(2).split(",")]
                return [("INSERT_ROW", table_name, values)]
            # Match INSERT INTO table (columns) VALUES (...)
            match = re.match(r"INSERT INTO (\w+) \((.+)\) VALUES \((.+)\)", original_command, re.I)
            if match:
                table_name = match.group(1)
                columns = [col.strip() for col in match.group(2).split(",")]
                values = [v.strip().strip('"').strip("'") for v in match.group(3).split(",")]
                return [("INSERT_ROW", table_name, values, columns)]
        elif command.startswith("ALTER TABLE"):
            match_add = re.match(r"ALTER TABLE (\w+) ADD (.+)", original_command, re.I)
            if match_add:
                table_name = match_add.group(1)
                column_def = match_add.group(2)
                return [("ALTER_TABLE", table_name, "ADD", column_def)]
            match_drop = re.match(r"ALTER TABLE (\w+) DROP (\w+)", original_command, re.I)
            if match_drop:
                table_name = match_drop.group(1)
                column_name = match_drop.group(2)
                return [("ALTER_TABLE", table_name, "DROP", column_name)]
            match_modify = re.match(r"ALTER TABLE (\w+) MODIFY (.+)", original_command, re.I)
            if match_modify:
                table_name = match_modify.group(1)
                column_def = match_modify.group(2)
                return [("ALTER_TABLE", table_name, "MODIFY", column_def)]
        elif command.startswith("DELETE"):
            match = re.match(r"DELETE FROM (\w+) WHERE (.+)", original_command, re.I)
            if match:
                table_name = match.group(1)
                condition = match.group(2)
                return [("DELETE_ROWS", table_name, condition)]
        elif command.startswith("UPDATE"):
            match = re.match(r"UPDATE (\w+) SET (.+) WHERE (.+)", original_command, re.I)
            if match:
                table_name = match.group(1)
                set_values = match.group(2)
                condition = match.group(3)
                return [("UPDATE_ROWS", table_name, set_values, condition)]
        return [("INVALID_COMMAND", original_command)]