from .opcodes import OPCODES
import os

class SQLVMInterpreter:
    def __init__(self, sqlvm_instance):
        self.sqlvm = sqlvm_instance

    def execute_bytecode(self, bytecode):
        results = []
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
                table_name, columns = instruction[1], instruction[2]
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