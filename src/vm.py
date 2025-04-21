from .opcodes import OPCODES
from .parser import SQLParser
import os
import re

class SQLVMInterpreter:
    def __init__(self, sqlvm_instance):
        self.sqlvm = sqlvm_instance

    def execute_bytecode(self, bytecode):
        results = []
        subquery_result = None  # Store the result of the last subquery

        for instruction in bytecode:
            opcode = instruction[0]

            if opcode == "CREATE_DATABASE":
                db_name = instruction[1]
                results.append(self.sqlvm.create_database(db_name))
            elif opcode == "DROP_DATABASE":
                db_name, if_exists = instruction[1], instruction[2]
                results.append(self.sqlvm.drop_database(db_name, if_exists))
            elif opcode == "USE_DATABASE":
                db_name = instruction[1]
                results.append(self.sqlvm.use_database(db_name))
            elif opcode == "SHOW_DATABASES":
                results.append(self.sqlvm.show_databases())
            elif opcode == "CREATE_TABLE":
                table_name, columns_def = instruction[1], instruction[2]
                results.append(self.sqlvm.create_table(table_name, columns_def))
            elif opcode == "INSERT_ROW":
                if len(instruction) == 4:  # With specific columns
                    table_name, values, columns = instruction[1], instruction[2], instruction[3]
                    results.append(self.sqlvm.insert(table_name, values, columns))
                else:  # Without specific columns
                    table_name, values = instruction[1], instruction[2]
                    results.append(self.sqlvm.insert(table_name, values))
            elif opcode == "SELECT_ROWS":
                table_name = instruction[1]
                columns = instruction[2]

                # Handle WHERE clause
                if len(instruction) == 4:
                    where_clause = instruction[3]

                    # Check for nested subquery in the IN condition
                    while "IN (SELECT" in where_clause:
                        subquery = re.search(r"IN \((SELECT .+)\)", where_clause, re.I).group(1)
                        subquery_bytecode = SQLParser.parse_to_bytecode(subquery)
                        subquery_results = self.execute_bytecode(subquery_bytecode)

                        # Extract column values or handle empty subquery results
                        if not subquery_results or subquery_results[0].strip() == "" or subquery_results[0] == "None":
                            # Replace the subquery with an empty IN condition
                            where_clause = where_clause.replace(f"IN ({subquery})", "IN ()")
                        else:
                            subquery_values = self._extract_column_values(subquery_results[0])
                            where_clause = where_clause.replace(f"IN ({subquery})", f"IN ({', '.join(map(str, subquery_values))})")

                    # Execute the parent query with the updated WHERE clause
                    results.append(self.sqlvm.select(table_name, columns, where_clause))
                else:
                    results.append(self.sqlvm.select(table_name, columns))

            elif opcode == "ALTER_TABLE":
                table_name, operation, column_def = instruction[1], instruction[2], instruction[3]
                results.append(self.sqlvm.alter_table(table_name, operation, column_def))
            elif opcode == "DELETE_ROWS":
                table_name, condition = instruction[1], instruction[2]
                results.append(self.sqlvm.delete(table_name, condition))
            elif opcode == "UPDATE_ROWS":
                table_name, set_values, condition = instruction[1], instruction[2], instruction[3]
                results.append(self.sqlvm.update(table_name, set_values, condition))
            elif opcode == "INVALID_COMMAND":
                results.append(f"Error: Invalid command '{instruction[1]}'")

        return results

    def _extract_column_values(self, result):
        """
        Extract column values from a SELECT result for use in subqueries.
        Assumes the result is formatted as a table-like string.
        """
        rows = result.split("\n")[3:-1]  # Skip header and separators
        values = []
        for row in rows:
            columns = row.split("|")[1:-1]  # Extract column values
            values.append(columns[0].strip())  # Assume single-column subquery
        return values