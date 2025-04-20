import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
import tkinter.font as tkFont  # Import font module for font handling

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
        Returns: (columns, types, auto_increment_cols) where columns is a list of names, 
        types is a dict {col: type}, and auto_increment_cols is a list of auto-increment column names
        """
        columns = []
        types = {}
        auto_increment_cols = []
        for coldef in columns_def.split(","):
            parts = coldef.strip().split()
            if len(parts) == 1:
                col, typ = parts[0], "TEXT"
                auto_increment = False
            else:
                col = parts[0]
                typ = parts[1].upper()
                auto_increment = "AUTO_INCREMENT" in [p.upper() for p in parts[2:]] if len(parts) > 2 else False
            
            columns.append(col)
            types[col] = typ
            if auto_increment:
                auto_increment_cols.append(col)
        
        return columns, types, auto_increment_cols

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
        columns, types, auto_increment_cols = self._parse_column_definitions(", ".join(columns_def) if isinstance(columns_def, list) else columns_def)
        self.tables[table_name] = {
            "columns": columns, 
            "types": types, 
            "rows": [],
            "auto_increment": {col: 0 for col in auto_increment_cols}
        }
        return f"Table {table_name} created with columns {[(c, types[c]) for c in columns]}."

    def insert(self, table_name, values):
        if self.current_db is None:
            return "Error: No database selected. Use USE database_name;"
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        columns = table["columns"]
        types = table.get("types", {c: "TEXT" for c in columns})
        auto_increment = table.get("auto_increment", {})
        
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
        
        # Create a list to store display values (with actual auto-increment values)
        display_values = []
        row = {}
        for col, val in zip(columns, values):
            if col in auto_increment and (val is None or val == "NULL"):
                # Handle auto-increment value
                table["auto_increment"][col] += 1
                auto_value = table["auto_increment"][col]
                row[col] = auto_value
                display_values.append(auto_value)  # Store the actual value for display
            else:
                try:
                    converted_val = self._convert_value(val, types.get(col, "TEXT"))
                    row[col] = converted_val
                    display_values.append(converted_val)  # Use converted value for display
                except Exception as e:
                    return f"Error: {e}"
        
        table["rows"].append(row)
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
            match = re.match(r"INSERT INTO (\w+) VALUES \((.+)\)", command)
            if match:
                table_name = match.group(1)
                values_str = match.group(2)
                # Improved value splitting: handles quoted strings, numbers, booleans
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

#GUI Class
class SQLGUI:
    def __init__(self, root, vm):
        self.vm = vm
        self.root = root
        self.root.title("Simple SQL VM")

        # Set the background color of the root window
        self.root.configure(bg='black')

        # Configure root layout for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)  # Output box expands
        self.root.rowconfigure(2, weight=0)  # Input field stays fixed

        # Create Menu Bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="How to Use", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Custom font
        self.custom_font = tkFont.Font(family="Arial", size=14)  # Set a larger font size

        # Custom font for the output box - use a monospace font for table alignment
        self.output_font = tkFont.Font(family="Courier New", size=14)  # Monospace font for proper alignment

        # Output Text Box (Moved to Top)
        self.output_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, height=15, bg='black', fg='lightgreen', font=self.output_font, state="disabled"
        )
        self.output_box.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Entry widget for SQL commands (with larger font size)
        self.command_entry = tk.Entry(self.root, width=50, bg='black', fg='white', insertbackground='white', font=self.custom_font)
        self.command_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Execute Button (with larger font size)
        self.execute_button = tk.Button(self.root, text="Execute", bg='lightgreen', fg='black', font=self.custom_font, command=self.execute_sql)
        self.execute_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Make widgets expand with window resizing
        self.root.columnconfigure(0, weight=1)  # Make command entry expand
        self.root.columnconfigure(1, weight=0)  # Button remains fixed size
        self.root.rowconfigure(0, weight=1)  # Output box expands

        # Command history
        self.command_history = []
        self.history_index = -1  # Track position in history

        # Bind keys for interaction
        self.command_entry.bind("<Return>", self.execute_sql)
        self.command_entry.bind("<Up>", self.show_previous_command)
        self.command_entry.bind("<Down>", self.show_next_command)

        # Bind zoom functionality
        self.root.bind("<Control-plus>", self.zoom_output_in)  # Ctrl + to zoom in
        self.root.bind("<Control-minus>", self.zoom_output_out)  # Ctrl - to zoom out

    def zoom_in(self, event=None):
        """Zoom in by increasing the font size."""
        current_size = self.custom_font.actual()["size"]
        self.custom_font.configure(size=current_size + 2)  # Increase font size

    def zoom_out(self, event=None):
        """Zoom out by decreasing the font size."""
        current_size = self.custom_font.actual()["size"]
        if current_size > 6:  # Prevent font size from becoming too small
            self.custom_font.configure(size=current_size - 2)

    def zoom_output_in(self, event=None):
        """Zoom in by increasing the font size of the output box."""
        current_size = self.output_font.actual()["size"]
        self.output_font.configure(size=current_size + 2)  # Increase font size

    def zoom_output_out(self, event=None):
        """Zoom out by decreasing the font size of the output box."""
        current_size = self.output_font.actual()["size"]
        if current_size > 6:  # Prevent font size from becoming too small
            self.output_font.configure(size=current_size - 2)

    def execute_sql(self, event=None):
        """Executes SQL command entered in the input box."""
        command = self.command_entry.get().strip()
        if command:
            self.command_history.append(command)  # Save command in history
            self.history_index = len(self.command_history)  # Reset history index
            result = self.vm.execute_command(command)
            self.output_box.config(state="normal")  # Enable editing
            self.output_box.insert(tk.END, f"> {command}\n{result}\n\n")
            self.output_box.config(state="disabled")  # Disable editing
            self.output_box.yview(tk.END)  # Auto-scroll to the latest output
            self.command_entry.delete(0, tk.END)  # Clear input box

    def show_previous_command(self, event):
        """Show the previous command in history when UP arrow is pressed."""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])

    def show_next_command(self, event):
        """Show the next command in history when DOWN arrow is pressed."""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)  # Reset if at end
            self.command_entry.delete(0, tk.END)
    def show_help(self):
        """Displays the help instructions."""
        help_text = (
            "SQLVM Help:\n"
            "- CREATE DATABASE database_name\n"
            "- DROP DATABASE [IF EXISTS] database_name\n"
            "- USE database_name\n"
            "- SHOW DATABASES\n"
            "- SHOW TABLES\n"
            "- CREATE TABLE table_name (col1 TYPE, col2 TYPE, ...)\n"
            "- INSERT INTO table_name VALUES (val1, val2, ...)\n"
            "- SELECT * FROM table_name\n"
            "- UPDATE table_name SET col=value WHERE condition\n"
            "- DELETE FROM table_name WHERE condition\n"
            "- Type 'EXIT' to quit"
        )
        messagebox.showinfo("Help", help_text)

    def show_about(self):
        """Displays information about the application."""
        about_text = (
            "SQLVM\n"
            "Version: 0.1\n"
            "Developed by:\n"
            "Group 2B\n"
            "Members:\n"
            "Cano, Kurt Daniel S.\n"
            "Caram II, Mike Rufino J.\n"
            "Dantes, Joshua Gabriel P.\n"
            "Villanueva, Jasper P.\n\n"
            "An in-memory SQL-like Virtual Machine. For educational purposes.\n"
            "Supports basic SQL commands: CREATE DATABASE, DROP DATABASE, USE, SHOW DATABASES, SHOW TABLES, CREATE, INSERT, SELECT, UPDATE, DELETE.\n"
            "Developed using Python and Tkinter for GUI.\n\n"
        )
        messagebox.showinfo("About", about_text)

# Run the Application
vm = SQLVM()
root = tk.Tk()
root.geometry("600x400")
app = SQLGUI(root, vm)
root.mainloop()
