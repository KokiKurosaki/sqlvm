import tkinter as tk
from tkinter import ttk, messagebox

class SelectTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Database and table selection
        self.setup_db_selection()
        
        # Columns selection
        self.setup_columns_selection()
        
        # Conditions section
        self.setup_conditions()
        
        # Button to execute select
        ttk.Button(self.frame, text="Run Query", 
                  command=self.execute_interactive_select).pack(anchor=tk.W, padx=5, pady=10)
        
        # Results section
        self.setup_results()
        
        # List to track conditions
        self.select_conditions_list = []
    
    def setup_db_selection(self):
        select_top_frame = ttk.Frame(self.frame)
        select_top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Database dropdown
        ttk.Label(select_top_frame, text="Database:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.select_db_var = tk.StringVar()
        self.select_db_dropdown = ttk.Combobox(select_top_frame, textvariable=self.select_db_var, state="readonly")
        self.select_db_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.select_db_dropdown.bind("<<ComboboxSelected>>", self.update_table_dropdown)
        
        # Table dropdown
        ttk.Label(select_top_frame, text="Table:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.select_table_var = tk.StringVar()
        self.select_table_dropdown = ttk.Combobox(select_top_frame, textvariable=self.select_table_var, state="readonly")
        self.select_table_dropdown.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.select_table_dropdown.bind("<<ComboboxSelected>>", self.update_columns)
    
    def setup_columns_selection(self):
        # Columns frame
        self.select_columns_frame = ttk.LabelFrame(self.frame, text="Select Columns")
        self.select_columns_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Select all checkbox
        self.select_all_var = tk.BooleanVar(value=True)
        self.select_all_check = ttk.Checkbutton(self.select_columns_frame, text="Select All Columns", 
                                               variable=self.select_all_var, 
                                               command=self.toggle_select_all_columns)
        self.select_all_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # Column checkboxes will be dynamically created
        self.select_column_vars = {}
        self.select_column_frame = ttk.Frame(self.select_columns_frame)
        self.select_column_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def setup_conditions(self):
        # Conditions frame
        self.select_conditions_frame = ttk.LabelFrame(self.frame, text="Conditions (WHERE)")
        self.select_conditions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add condition button
        ttk.Button(self.select_conditions_frame, text="Add Condition", 
                  command=self.add_condition).pack(anchor=tk.W, padx=5, pady=5)
    
    def setup_results(self):
        # Results frame
        self.select_results_frame = ttk.LabelFrame(self.frame, text="Results")
        self.select_results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initially show a message when no results are available
        self.no_results_label = ttk.Label(self.select_results_frame, text="Run a query to see results.")
        self.no_results_label.pack(pady=20)
    
    def update_db_dropdown(self):
        db_list = list(self.sqlvm.databases.keys())
        self.select_db_dropdown.configure(values=db_list)
        
        if db_list and self.main_app.current_db in db_list:
            self.select_db_var.set(self.main_app.current_db)
        elif db_list:
            self.select_db_var.set(db_list[0])
        
        # Update table dropdown
        self.update_table_dropdown()
    
    def update_table_dropdown(self, event=None):
        db_name = self.select_db_var.get()
        if db_name in self.sqlvm.databases:
            table_list = list(self.sqlvm.databases[db_name].keys())
            self.select_table_dropdown.configure(values=table_list)
            if table_list:
                self.select_table_var.set(table_list[0])
            else:
                self.select_table_var.set('')
            
            # Update columns based on selected table
            self.update_columns()
    
    def update_columns(self, event=None):
        # Clear existing column checkboxes
        for widget in self.select_column_frame.winfo_children():
            widget.destroy()
        
        self.select_column_vars.clear()
        
        db_name = self.select_db_var.get()
        table_name = self.select_table_var.get()
        
        if not db_name or not table_name:
            return
        
        # Switch to the selected database
        current_db = self.main_app.current_db
        if db_name != current_db:
            self.sqlvm.use_database(db_name)
            self.main_app.current_db = db_name
        
        # Get table structure
        table = self.sqlvm.tables.get(table_name)
        if not table:
            return
        
        # Create a checkbox for each column
        for i, col_name in enumerate(table["columns"]):
            var = tk.BooleanVar(value=self.select_all_var.get())
            cb = ttk.Checkbutton(self.select_column_frame, text=col_name, variable=var)
            cb.grid(row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)
            self.select_column_vars[col_name] = var
    
    def toggle_select_all_columns(self):
        # Set all column checkboxes based on "Select All" checkbox
        all_selected = self.select_all_var.get()
        for var in self.select_column_vars.values():
            var.set(all_selected)
    
    def add_condition(self):
        db_name = self.select_db_var.get()
        table_name = self.select_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Switch to the selected database
        if db_name != self.main_app.current_db:
            self.sqlvm.use_database(db_name)
            self.main_app.current_db = db_name
        
        # Get table structure
        table = self.sqlvm.tables.get(table_name)
        if not table:
            return
        
        # Create a frame for this condition
        cond_frame = ttk.Frame(self.select_conditions_frame)
        cond_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Column dropdown
        col_var = tk.StringVar()
        col_dropdown = ttk.Combobox(cond_frame, textvariable=col_var, state="readonly", width=15)
        col_dropdown['values'] = table["columns"]
        if table["columns"]:
            col_var.set(table["columns"][0])
        col_dropdown.grid(row=0, column=0, padx=2)
        
        # Operator dropdown
        op_var = tk.StringVar()
        op_dropdown = ttk.Combobox(cond_frame, textvariable=op_var, state="readonly", width=5)
        op_dropdown['values'] = ["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"]
        op_var.set("=")
        op_dropdown.grid(row=0, column=1, padx=2)
        
        # Value entry
        val_var = tk.StringVar()
        val_entry = ttk.Entry(cond_frame, textvariable=val_var, width=20)
        val_entry.grid(row=0, column=2, padx=2)
        
        # Remove button
        remove_btn = ttk.Button(cond_frame, text="X", width=2,
                              command=lambda f=cond_frame: self.remove_condition(f))
        remove_btn.grid(row=0, column=3, padx=2)
        
        # Add to conditions list
        self.select_conditions_list.append({
            "frame": cond_frame,
            "column": col_var,
            "operator": op_var,
            "value": val_var
        })
    
    def remove_condition(self, frame):
        # Find and remove the condition from the list
        for i, cond in enumerate(self.select_conditions_list):
            if cond["frame"] == frame:
                frame.destroy()
                self.select_conditions_list.pop(i)
                break
    
    def execute_interactive_select(self):
        db_name = self.select_db_var.get()
        table_name = self.select_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Switch to the selected database
        if db_name != self.main_app.current_db:
            self.sqlvm.use_database(db_name)
            self.main_app.current_db = db_name
        
        # Build the query
        selected_columns = []
        for col, var in self.select_column_vars.items():
            if var.get():
                selected_columns.append(col)
        
        if not selected_columns:
            messagebox.showerror("Error", "Please select at least one column")
            return
        
        # Start building the query
        query = f"SELECT {', '.join(selected_columns)} FROM {table_name}"
        
        # Add WHERE conditions if any
        if self.select_conditions_list:
            conditions = []
            for cond in self.select_conditions_list:
                col = cond["column"].get()
                op = cond["operator"].get()
                val = cond["value"].get()
                
                # Format the value based on operator and data type
                if op == "LIKE":
                    val = f"'%{val}%'"
                elif op == "IN":
                    # Format IN clause values properly
                    val_items = [item.strip() for item in val.split(',')]
                    formatted_items = []
                    for item in val_items:
                        if item.replace('.', '', 1).replace('-', '', 1).isdigit():
                            formatted_items.append(item)  # Numeric value
                        else:
                            formatted_items.append(f"'{item}'")  # String value
                    val = f"({', '.join(formatted_items)})"
                else:
                    # Better check for numeric values (including negatives and decimals)
                    try:
                        float(val)  # Test if value can be converted to number
                        val = val
                    except ValueError:
                        val = f"'{val}'"  # Not a number, quote it
                
                conditions.append(f"{col} {op} {val}")
            
            query += f" WHERE {' AND '.join(conditions)}"
        
        # Debug: Print the query
        print(f"Executing SQL query: {query}")
        
        # Execute the query
        result = self.sqlvm.execute_command(query)
        
        # Display results in the treeview
        self.display_results(result, query, selected_columns)
    
    def display_results(self, result_text, query=None, selected_columns=None):
        # Clear existing widgets
        for widget in self.select_results_frame.winfo_children():
            widget.destroy()
        
        # Debug info
        print(f"Raw result: {result_text}")
        
        # Parse the result into a table
        lines = result_text.strip().split('\n')
        if len(lines) < 3:  # Need at least header, separator, and one data row
            self.no_results_label = ttk.Label(self.select_results_frame, text="No results found.")
            self.no_results_label.pack(pady=20)
            
            # Show the query that was executed for debugging
            if query:
                ttk.Label(self.select_results_frame, 
                         text=f"Query executed: {query}", 
                         wraplength=600).pack(pady=5)
            return
        
        # Create a container frame for results
        container = ttk.Frame(self.select_results_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Use the selected_columns passed from execute_interactive_select
        if not selected_columns:
            selected_columns = []
            for col, var in self.select_column_vars.items():
                if var.get():
                    selected_columns.append(col)
        
        # Create treeview with selected columns
        tree = ttk.Treeview(container, columns=selected_columns, show="headings")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for treeview and scrollbars
        tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # Configure column headings
        for col in selected_columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Improved parsing of data rows
        # First, determine if we have a result with data
        if len(lines) < 3:
            # No data
            return
        
        # Parse data rows more carefully
        for line_idx, line in enumerate(lines[2:]):  # Skip header and separator lines
            if not line or '|' not in line:
                continue
                
            # Split the line by | character and extract values
            raw_values = line.split('|')
            # Remove first and last elements (they're usually empty)
            if raw_values and not raw_values[0].strip():
                raw_values = raw_values[1:]
            if raw_values and not raw_values[-1].strip():
                raw_values = raw_values[:-1]
                
            values = [v.strip() for v in raw_values]
            
            # Debug the extracted values
            print(f"Row {line_idx}: Extracted values: {values}")
            
            # Insert into tree if we have values
            if values and len(values) > 0:
                # If values and columns don't match, try to pad or truncate
                if len(values) != len(selected_columns):
                    print(f"Warning: Values count ({len(values)}) doesn't match columns count ({len(selected_columns)})")
                    if len(values) < len(selected_columns):
                        values.extend([''] * (len(selected_columns) - len(values)))
                    else:
                        values = values[:len(selected_columns)]
                
                tree.insert("", "end", values=values)
        
        # Store reference to tree
        self.results_tree = tree
