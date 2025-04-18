import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
import tkinter.font as tkFont  # Import font module for font handling

class SQLVM:
    def __init__(self):
        self.tables = {}

    def create_table(self, table_name, columns):
        if (table_name in self.tables):
            return f"Error: Table {table_name} already exists."
        self.tables[table_name] = {"columns": columns, "rows": []}
        return f"Table {table_name} created with columns {columns}."

    def insert(self, table_name, values):
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        if len(values) != len(table["columns"]):
            return f"Error: Number of values doesn't match columns."
        table["rows"].append(dict(zip(table["columns"], values)))
        return f"Inserted {values} into {table_name}."

    def select(self, table_name, columns="*"):
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
        if table_name not in self.tables:
            return f"Error: Table {table_name} does not exist."
        table = self.tables[table_name]
        set_dict = {}
        set_pairs = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|([^",\s]+))', set_values)
        for col, val1, val2 in set_pairs:
            set_dict[col] = val1 if val1 else val2  # Pick non-empty match

        updated_count = 0
        for row in table["rows"]:
            if where is None or self._evaluate_condition(row, where):
                for column, value in set_dict.items():
                    if column in row:
                        row[column] = value
                updated_count += 1
        return f"Updated {updated_count} row/s in {table_name}."

    def delete(self, table_name, where=None):
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
        return row.get(col) == value

    def execute_command(self, command):
        parts = command.split(" ", 1)
        cmd = parts[0].upper()

        if cmd == "CREATE":
            match = re.match(r"CREATE TABLE (\w+) \((.+)\)", command)
            if match:
                table_name = match.group(1)
                columns = [col.strip() for col in match.group(2).split(",")]
                return self.create_table(table_name, columns)
        elif cmd == "INSERT":
            match = re.match(r"INSERT INTO (\w+) VALUES \((.+)\)", command)
            if match:
                table_name = match.group(1)
                values = [value.strip().strip('"') for value in match.group(2).split(",")]
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
            "- CREATE TABLE table_name (col1, col2, ...)\n"
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
            "Supports basic SQL commands: CREATE, INSERT, SELECT, UPDATE, DELETE.\n"
            "Developed using Python and Tkinter for GUI.\n\n"
        )
        messagebox.showinfo("About", about_text)

# Run the Application
vm = SQLVM()
root = tk.Tk()
root.geometry("600x400")
app = SQLGUI(root, vm)
root.mainloop()
