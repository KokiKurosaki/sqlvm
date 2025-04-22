import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re

class CreateTableDialog:
    def __init__(self, parent, main_app, db_name=None):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        self.db_name = db_name or self.main_app.current_db
        
        # Create dialog
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Create New Table")
        self.dialog.geometry("750x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Make dialog resizable
        self.dialog.minsize(750, 600)
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(1, weight=1)
        
        # Setup UI components
        self.setup_table_info()
        self.setup_columns_area()
        self.setup_buttons()
        
        # Initialize with 4 empty columns by default
        self.num_columns_var.set(4)
        self.update_column_count()
    
    def setup_table_info(self):
        # Top frame for table info
        top_frame = ttk.LabelFrame(self.dialog, text="Table Information")
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Table name
        ttk.Label(top_frame, text="Table name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.table_name_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.table_name_var, width=40).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Number of columns
        ttk.Label(top_frame, text="Number of columns:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.num_columns_var = tk.IntVar(value=4)
        ttk.Spinbox(top_frame, from_=1, to=100, textvariable=self.num_columns_var, width=5, 
                   command=self.update_column_count).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        ttk.Button(top_frame, text="Go", command=self.update_column_count).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        
        # Add database info
        if self.db_name:
            ttk.Label(top_frame, text=f"Database: {self.db_name}").grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky="w")
    
    def setup_columns_area(self):
        # Create a frame for the scrollable area
        self.columns_frame = ttk.LabelFrame(self.dialog, text="Table Structure")
        self.columns_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.columns_frame.columnconfigure(0, weight=1)
        self.columns_frame.rowconfigure(0, weight=1)
        
        # Create a canvas with scrollbar
        self.canvas = tk.Canvas(self.columns_frame)
        self.scrollbar = ttk.Scrollbar(self.columns_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        # Configure scroll region when frame size changes
        self.scroll_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Header row
        header_frame = ttk.Frame(self.scroll_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # Removed "Comments" column and rebalanced column widths
        headers = ["Name", "Type", "Length/Values", "Default", "Collation", 
                  "Attributes", "Null", "Index", "A_I"]
        
        for i, header in enumerate(headers):
            ttk.Label(header_frame, text=header, font=("", 9, "bold")).grid(row=0, column=i, padx=5, pady=2)
        
        # Column frames will be added dynamically
        self.column_frames = []
    
    def setup_buttons(self):
        # Bottom buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        ttk.Button(button_frame, text="Save", command=self.create_table).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Preview SQL", command=self.preview_sql).pack(side=tk.RIGHT, padx=5)
    
    def on_frame_configure(self, event=None):
        """Update the canvas's scroll region when the scroll_frame changes size"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event=None):
        """When canvas resizes, resize the frame within it"""
        if event:
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def update_column_count(self):
        """Update the number of column frames based on the spinbox value"""
        target_count = self.num_columns_var.get()
        current_count = len(self.column_frames)
        
        # Add more column frames if needed
        if current_count < target_count:
            for i in range(current_count, target_count):
                self.add_column_frame(i + 1)
        
        # Remove excess column frames if needed
        elif current_count > target_count:
            for i in range(target_count, current_count):
                # Remove the last frame
                frame_to_remove = self.column_frames.pop()
                frame_to_remove["frame"].destroy()  # Destroy the frame widget
                # Update scroll region
        self.on_frame_configure()
    
    def add_column_frame(self, index):
        """Add a column definition frame"""
        column_frame = ttk.Frame(self.scroll_frame)
        column_frame.grid(row=index, column=0, sticky="ew", pady=2)
        
        # Apply alternating row colors for better readability
        bg_color = "#f0f0f0" if index % 2 == 0 else "#ffffff"
        column_frame.configure(style=f"Row{index}.TFrame")
        
        # Name field
        name_var = tk.StringVar(value=f"column{index}")
        name_entry = ttk.Entry(column_frame, textvariable=name_var, width=15)
        name_entry.grid(row=0, column=0, padx=2, pady=2)
        
        # Type dropdown
        type_var = tk.StringVar(value="INT")
        types = ["INT", "VARCHAR", "TEXT", "CHAR", "FLOAT", "BOOL"]
        type_dropdown = ttk.Combobox(column_frame, textvariable=type_var, values=types, width=10, state="readonly")
        type_dropdown.grid(row=0, column=1, padx=2, pady=2)
        
        # Length/Values
        length_var = tk.StringVar(value="11")
        length_entry = ttk.Entry(column_frame, textvariable=length_var, width=10)
        length_entry.grid(row=0, column=2, padx=2, pady=2)
        
        # Default value
        default_var = tk.StringVar(value="None")
        default_options = ["None", "NULL", "CURRENT_TIMESTAMP", "As defined:"]
        default_dropdown = ttk.Combobox(column_frame, textvariable=default_var, values=default_options, width=15)
        default_dropdown.grid(row=0, column=3, padx=2, pady=2)
        
        # Default value entry (only visible when "As defined:" is selected)
        default_value_var = tk.StringVar()
        default_value_entry = ttk.Entry(column_frame, textvariable=default_value_var, width=10)
        
        # Show/hide the default value entry based on dropdown selection
        def toggle_default_entry(*args):
            if default_var.get() == "As defined:":
                default_value_entry.grid(row=0, column=4, padx=2, pady=2)
            else:
                default_value_entry.grid_forget()
        
        default_var.trace("w", toggle_default_entry)
        
        # Collation dropdown (for string types)
        collation_var = tk.StringVar(value="")
        collations = ["", "utf8_general_ci", "utf8mb4_unicode_ci"]
        collation_dropdown = ttk.Combobox(column_frame, textvariable=collation_var, values=collations, width=15)
        collation_dropdown.grid(row=0, column=5, padx=2, pady=2)
        
        # Attributes dropdown
        attr_var = tk.StringVar(value="")
        attributes = ["", "UNSIGNED", "ZEROFILL"]
        attr_dropdown = ttk.Combobox(column_frame, textvariable=attr_var, values=attributes, width=10)
        attr_dropdown.grid(row=0, column=6, padx=2, pady=2)
        
        # Null checkbox
        null_var = tk.BooleanVar(value=True)
        null_check = ttk.Checkbutton(column_frame, variable=null_var)
        null_check.grid(row=0, column=7, padx=2, pady=2)
        
        # Index dropdown
        index_var = tk.StringVar(value="---")
        indexes = ["---", "PRIMARY", "UNIQUE", "INDEX", "FULLTEXT"]
        index_dropdown = ttk.Combobox(column_frame, textvariable=index_var, values=indexes, width=10)
        index_dropdown.grid(row=0, column=8, padx=2, pady=2)
        
        # Auto Increment checkbox
        ai_var = tk.BooleanVar(value=False)
        ai_check = ttk.Checkbutton(column_frame, variable=ai_var)
        ai_check.grid(row=0, column=9, padx=2, pady=2)
        
        # Store column data in a dictionary - removed comment field
        column_data = {
            "frame": column_frame,
            "name": name_var,
            "type": type_var,
            "length": length_var,
            "default": default_var,
            "default_value": default_value_var,
            "collation": collation_var,
            "attributes": attr_var,
            "null": null_var,
            "index": index_var,
            "auto_increment": ai_var
        }
        
        # Add to list of columns
        self.column_frames.append(column_data)
        
        # Type changes should update available options
        def type_changed(*args):
            selected_type = type_var.get().upper()
            
            # Update length field based on type
            if selected_type == "INT":
                length_var.set("11")
            elif selected_type == "VARCHAR":
                length_var.set("255")
            elif selected_type == "CHAR":
                length_var.set("50")
            elif selected_type in ["TEXT"]:
                length_var.set("")
            elif selected_type == "FLOAT":
                length_var.set("")
            elif selected_type == "BOOL":
                length_var.set("")
            
            # Update auto increment availability
            if selected_type in ["INT"]:
                ai_check.state(['!disabled'])
            else:
                ai_var.set(False)
                ai_check.state(['disabled'])
            
            # Update collation availability
            if selected_type in ["VARCHAR", "TEXT", "CHAR"]:
                collation_dropdown.state(['!disabled'])
            else:
                collation_var.set("")
                collation_dropdown.state(['disabled'])
            
            # Update attributes availability
            if selected_type in ["INT", "FLOAT"]:
                attr_dropdown.state(['!disabled'])
            else:
                attr_var.set("")
                attr_dropdown.state(['disabled'])
        
        type_var.trace("w", type_changed)
        
        # Auto increment changes should sync with PRIMARY KEY
        def auto_increment_changed(*args):
            if ai_var.get():
                # When auto_increment is checked, ensure this column is set as PRIMARY KEY
                index_var.set("PRIMARY")
                
                # Uncheck auto_increment on all other columns
                for other_col in self.column_frames:
                    if other_col != column_data and other_col["auto_increment"].get():
                        other_col["auto_increment"].set(False)
            
        ai_var.trace("w", auto_increment_changed)
        
        # Index changes should validate auto_increment constraints
        def index_changed(*args):
            if ai_var.get() and index_var.get() != "PRIMARY":
                messagebox.showwarning("Warning", "AUTO_INCREMENT column must be a PRIMARY KEY.\nKeeping PRIMARY KEY setting.")
                index_var.set("PRIMARY")
        
        index_var.trace("w", index_changed)
        
        # Initial update of field states
        type_changed()
        
        return column_data
    
    def create_table(self):
        """Create the table based on the form data"""
        table_name = self.table_name_var.get().strip()
        
        # Validate table name
        if not table_name:
            messagebox.showerror("Error", "Table name cannot be empty")
            return
        
        if not self.db_name:
            messagebox.showerror("Error", "No database selected")
            return
        
        # Prepare column definitions
        column_defs = []
        primary_keys = []
        unique_keys = []
        indexes = []
        auto_increment_cols = []
        
        for col in self.column_frames:
            col_name = col["name"].get().strip()
            col_type = col["type"].get()
            
            # Skip empty column names
            if not col_name:
                continue
                
            # Validate column name
            if not re.match(r'^[a-zA-Z0-9_]+$', col_name):
                messagebox.showerror("Error", f"Invalid column name: {col_name}. Use only letters, numbers and underscore.")
                return
            
            # Check for auto increment columns
            if col["auto_increment"].get():
                auto_increment_cols.append(col_name)
                
                # Validate that auto_increment column is also PRIMARY KEY
                if col["index"].get() != "PRIMARY":
                    messagebox.showerror("Error", f"AUTO_INCREMENT column '{col_name}' must be defined as PRIMARY KEY")
                    return
            
            # Build column definition
            col_def = f"{col_name} {col_type}"
            
            # Add length/values if specified
            length = col["length"].get().strip()
            if length:
                col_def += f"({length})"
            
            # Add attributes if specified
            attr = col["attributes"].get()
            if attr:
                col_def += f" {attr}"
            
            # Add NULL constraint
            if not col["null"].get():
                col_def += " NOT NULL"
            
            # Add default value if specified
            default = col["default"].get()
            if default == "NULL":
                col_def += " DEFAULT NULL"
            elif default == "CURRENT_TIMESTAMP":
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif default == "As defined:":
                default_val = col["default_value"].get()
                if default_val:
                    # Check if numeric or should be quoted
                    if default_val.isdigit() or default_val.startswith("-") and default_val[1:].isdigit():
                        col_def += f" DEFAULT {default_val}"
                    else:
                        col_def += f" DEFAULT '{default_val}'"
            
            # Add auto increment
            if col["auto_increment"].get():
                col_def += " AUTO_INCREMENT"
            
            column_defs.append(col_def)
            
            # Track keys and indexes
            index_type = col["index"].get()
            if index_type == "PRIMARY":
                primary_keys.append(col_name)
            elif index_type == "UNIQUE":
                unique_keys.append(col_name)
            elif index_type == "INDEX":
                indexes.append(col_name)
        
        # Validate auto increment columns - ensure only one exists
        if len(auto_increment_cols) > 1:
            messagebox.showerror("Error", "Incorrect table definition; there can be only one auto column and it must be defined as a key")
            return
        
        # Add primary key constraintprimary key, but it can be composite (multiple columns)
        if primary_keys:
            column_defs.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
        
        # Add unique constraints
        for uk in unique_keys:
            column_defs.append(f"UNIQUE KEY {uk}_unique ({uk})")
        
        # Add indexes
        for idx in indexes:
            column_defs.append(f"INDEX {idx}_idx ({idx})")
        
        # Generate the SQL command
        column_sql = ", ".join(column_defs)
        
        # Switch to the target database
        self.sqlvm.use_database(self.db_name)
        
        # Execute the create table command
        result = self.sqlvm.execute_command(f"CREATE TABLE {table_name} ({column_sql})")
        
        # Update UI and close dialog
        if "Error" not in result:
            messagebox.showinfo("Success", f"Table {table_name} created successfully")
            self.main_app.refresh_all()
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", result)
    
    def preview_sql(self):
        """Show the SQL command that would be executed to create the table"""
        table_name = self.table_name_var.get().strip()
        
        # Validate table name
        if not table_name:
            messagebox.showerror("Error", "Table name cannot be empty")
            return
        
        if not self.db_name:
            messagebox.showerror("Error", "No database selected")
            return
        
        # Prepare column definitions
        column_defs = []
        primary_keys = []
        unique_keys = []
        indexes = []
        auto_increment_cols = []
        
        for col in self.column_frames:
            col_name = col["name"].get().strip()
            col_type = col["type"].get()
            
            # Skip empty column names
            if not col_name:
                continue
                
            # Validate column name
            if not re.match(r'^[a-zA-Z0-9_]+$', col_name):
                messagebox.showerror("Error", f"Invalid column name: {col_name}. Use only letters, numbers and underscore.")
                return
            
            # Check for auto increment columns
            if col["auto_increment"].get():
                auto_increment_cols.append(col_name)
                
                # Validate that auto_increment column is also PRIMARY KEY
                if col["index"].get() != "PRIMARY":
                    messagebox.showerror("Error", f"AUTO_INCREMENT column '{col_name}' must be defined as PRIMARY KEY")
                    return
            
            # Build column definition
            col_def = f"{col_name} {col_type}"
            
            # Add length/values if specified
            length = col["length"].get().strip()
            if length:
                col_def += f"({length})"
            
            # Add attributes if specified
            attr = col["attributes"].get()
            if attr:
                col_def += f" {attr}"
            
            # Add NULL constraint
            if not col["null"].get():
                col_def += " NOT NULL"
            
            # Add default value if specified
            default = col["default"].get()
            if default == "NULL":
                col_def += " DEFAULT NULL"
            elif default == "CURRENT_TIMESTAMP":
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif default == "As defined:":
                default_val = col["default_value"].get()
                if default_val:
                    # Check if numeric or should be quoted
                    if default_val.isdigit() or default_val.startswith("-") and default_val[1:].isdigit():
                        col_def += f" DEFAULT {default_val}"
                    else:
                        col_def += f" DEFAULT '{default_val}'"
            
            # Add auto increment
            if col["auto_increment"].get():
                col_def += " AUTO_INCREMENT"
            
            column_defs.append(col_def)
            
            # Track keys and indexes
            index_type = col["index"].get()
            if index_type == "PRIMARY":
                primary_keys.append(col_name)
            elif index_type == "UNIQUE":
                unique_keys.append(col_name)
            elif index_type == "INDEX":
                indexes.append(col_name)
        
        # Validate auto increment columns - ensure only one exists
        if len(auto_increment_cols) > 1:
            messagebox.showerror("Error", "Incorrect table definition; there can be only one auto column and it must be defined as a key")
            return
        
        # Add primary key constraint as a composite key if multiple columns
        if primary_keys:
            column_defs.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
        
        # Add unique constraints
        for uk in unique_keys:
            column_defs.append(f"UNIQUE KEY {uk}_unique ({uk})")
        
        # Add indexes
        for idx in indexes:
            column_defs.append(f"INDEX {idx}_idx ({idx})")
        
        # Generate the SQL command with proper formatting for readability
        column_sql = ",\n  ".join(column_defs)
        sql_command = f"CREATE TABLE {table_name} (\n  {column_sql}\n);"
        
        # Create SQL preview dialog
        preview_dialog = tk.Toplevel(self.dialog)
        preview_dialog.title("SQL Preview")
        preview_dialog.geometry("650x350")
        preview_dialog.transient(self.dialog)
        preview_dialog.grab_set()
        
        # Add descriptive header
        ttk.Label(preview_dialog, text="The following SQL command will be executed:", 
                anchor="w").pack(fill="x", padx=10, pady=5)
        
        # Add SQL command in a scrollable text area
        sql_text = scrolledtext.ScrolledText(preview_dialog, wrap=tk.WORD, height=12)
        sql_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        sql_text.insert(tk.END, sql_command)
        
        # Make the text read-only
        sql_text.config(state="disabled")
        
        # Add a copy button and close button
        button_frame = ttk.Frame(preview_dialog)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        def copy_to_clipboard():
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(sql_command)
            messagebox.showinfo("Copied", "SQL command copied to clipboard")
        
        ttk.Button(button_frame, text="Copy to Clipboard", 
                command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", 
                command=preview_dialog.destroy).pack(side=tk.RIGHT, padx=5)
