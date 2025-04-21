import tkinter as tk
from tkinter import ttk, messagebox

class UpdateTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Database and table selection
        self.setup_db_selection()
        
        # Set values section
        self.update_values_frame = ttk.LabelFrame(self.frame, text="Set Values")
        self.update_values_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Conditions section with warning
        self.setup_conditions_section()
        
        # Update button and result label
        ttk.Button(self.frame, text="Update Data", 
                  command=self.execute_interactive_update).pack(anchor=tk.W, padx=5, pady=10)
        self.update_result_label = ttk.Label(self.frame, text="")
        self.update_result_label.pack(fill=tk.X, padx=5, pady=5)
        
        # List to store conditions
        self.update_conditions_list = []
        # Dictionary to store SET field variables
        self.update_value_vars = {}
    
    def setup_db_selection(self):
        update_top_frame = ttk.Frame(self.frame)
        update_top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Database dropdown
        ttk.Label(update_top_frame, text="Database:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.update_db_var = tk.StringVar()
        self.update_db_combo = ttk.Combobox(update_top_frame, textvariable=self.update_db_var, state="readonly")  # Changed variable name
        self.update_db_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.update_db_combo.bind('<<ComboboxSelected>>', self.update_table_list)
        
        # Table dropdown
        ttk.Label(update_top_frame, text="Table:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.update_table_var = tk.StringVar()
        self.update_table_dropdown = ttk.Combobox(update_top_frame, textvariable=self.update_table_var, state="readonly")
        self.update_table_dropdown.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.update_table_dropdown.bind('<<ComboboxSelected>>', self.update_form)
    
    def setup_conditions_section(self):
        """Setup the conditions (WHERE) section with warning label"""
        self.update_where_frame = ttk.LabelFrame(self.frame, text="Where Conditions")
        self.update_where_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.update_where_frame, 
                 text="Warning: Without conditions, ALL rows will be updated!", 
                 foreground="red").pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.update_where_frame, text="Add Condition", 
                  command=self.add_condition).pack(anchor=tk.W, padx=5, pady=5)
    
    def update_db_dropdown(self):
        db_list = list(self.sqlvm.databases.keys())
        self.update_db_combo.configure(values=db_list)  # Changed to match new variable name
        
        if db_list and self.main_app.current_db in db_list:
            self.update_db_var.set(self.main_app.current_db)
        elif db_list:
            self.update_db_var.set(db_list[0])
        
        # Update table dropdown
        self.update_table_list()

    def update_table_list(self, event=None):
        db_name = self.update_db_var.get()
        if db_name in self.sqlvm.databases:
            table_list = list(self.sqlvm.databases[db_name].keys())
            self.update_table_dropdown.configure(values=table_list)
            if table_list:
                self.update_table_var.set(table_list[0])
            else:
                self.update_table_var.set('')
            self.update_form()

    def update_form(self, event=None):
        # Clear existing fields and conditions
        for widget in self.update_values_frame.winfo_children():
            widget.destroy()
        for cond in self.update_conditions_list:
            cond["frame"].destroy()
        
        self.update_conditions_list.clear()
        self.update_value_vars.clear()
        
        db_name = self.update_db_var.get()
        table_name = self.update_table_var.get()
        
        if not db_name or not table_name:
            return
        
        # Switch to the selected database
        if db_name != self.main_app.current_db:
            self.sqlvm.use_database(db_name)
            self.main_app.current_db = db_name
        
        # Get table structure
        table = self.sqlvm.tables.get(table_name)
        if not table:
            return
        
        # Create checkboxes for SET fields
        for col in table["columns"]:
            field_frame = ttk.Frame(self.update_values_frame)
            field_frame.pack(fill=tk.X, padx=5, pady=2)
            
            include_var = tk.BooleanVar()
            include_checkbox = ttk.Checkbutton(field_frame, text=col, variable=include_var)
            include_checkbox.grid(row=0, column=0, padx=2)
            
            value_var = tk.StringVar()
            value_entry = ttk.Entry(field_frame, textvariable=value_var, width=30)
            value_entry.grid(row=0, column=1, padx=2)
            
            self.update_value_vars[col] = {
                "include": include_var,
                "value": value_var
            }

    def add_condition(self):
        db_name = self.update_db_var.get()
        table_name = self.update_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Create a frame for this condition
        cond_frame = ttk.Frame(self.update_where_frame)
        cond_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Column dropdown
        col_var = tk.StringVar()
        col_dropdown = ttk.Combobox(cond_frame, textvariable=col_var, state="readonly", width=15)
        col_dropdown.configure(values=self.sqlvm.tables[table_name]["columns"])
        if self.sqlvm.tables[table_name]["columns"]:
            col_var.set(self.sqlvm.tables[table_name]["columns"][0])
        col_dropdown.grid(row=0, column=0, padx=2)
        
        # Operator dropdown
        op_var = tk.StringVar()
        op_dropdown = ttk.Combobox(cond_frame, textvariable=op_var, state="readonly", width=5)
        op_dropdown.configure(values=["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN"])
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
        self.update_conditions_list.append({
            "frame": cond_frame,
            "column": col_var,
            "operator": op_var,
            "value": val_var
        })
    
    def remove_condition(self, frame):
        for i, cond in enumerate(self.update_conditions_list):
            if cond["frame"] == frame:
                frame.destroy()
                self.update_conditions_list.pop(i)
                break
    
    def execute_interactive_update(self):
        db_name = self.update_db_var.get()
        table_name = self.update_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Collect SET values from checkboxes
        set_clauses = []
        for col, vars_dict in self.update_value_vars.items():
            if vars_dict["include"].get():
                value = vars_dict["value"].get()
                # Format value based on type
                if value.isdigit():
                    set_clauses.append(f"{col} = {value}")
                else:
                    set_clauses.append(f"{col} = '{value}'")
        
        if not set_clauses:
            messagebox.showerror("Error", "Please select at least one column to update")
            return
        
        # Build WHERE clause
        where_clauses = []
        for cond in self.update_conditions_list:
            col = cond["column"].get()
            op = cond["operator"].get()
            val = cond["value"].get()
            
            # Format value based on operator
            if op == "LIKE":
                val = f"'%{val}%'"
            elif op == "IN":
                val = f"({val})"
            elif not val.isdigit():
                val = f"'{val}'"
            
            where_clauses.append(f"{col} {op} {val}")
        
        # Build final query
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)}"
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        # Execute the update
        result = self.sqlvm.execute_command(query)
        
        # Show result and update the table view if needed
        self.update_result_label.config(text=result)
        if table_name == self.main_app.current_table:
            self.main_app.data_tab.load_table_data()
