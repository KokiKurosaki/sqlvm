import tkinter as tk
from tkinter import ttk, messagebox

class DeleteTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Database and table selection
        self.setup_db_selection()
        
        # Warning label
        ttk.Label(self.frame, text="Warning: Delete operations cannot be undone!", 
                 foreground="red").pack(fill=tk.X, padx=5, pady=5)
        
        # Delete all records checkbox
        self.setup_delete_options()
        
        # Delete button
        ttk.Button(self.frame, text="Delete Data", 
                 command=self.execute_interactive_delete).pack(anchor=tk.W, padx=5, pady=10)
        
        # Result display
        self.delete_result_label = ttk.Label(self.frame, text="")
        self.delete_result_label.pack(fill=tk.X, padx=5, pady=5)
        
        # List to store conditions
        self.delete_conditions_list = []

    def setup_db_selection(self):
        delete_top_frame = ttk.Frame(self.frame)
        delete_top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Database dropdown
        ttk.Label(delete_top_frame, text="Database:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.delete_db_var = tk.StringVar()
        self.delete_db_dropdown = ttk.Combobox(delete_top_frame, textvariable=self.delete_db_var, state="readonly")
        self.delete_db_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.delete_db_dropdown.bind("<<ComboboxSelected>>", self.update_table_dropdown)
        
        # Table dropdown
        ttk.Label(delete_top_frame, text="Table:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.delete_table_var = tk.StringVar()
        self.delete_table_dropdown = ttk.Combobox(delete_top_frame, textvariable=self.delete_table_var, state="readonly")
        self.delete_table_dropdown.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.delete_table_dropdown.bind("<<ComboboxSelected>>", self.update_form)

    def setup_delete_options(self):
        # Delete all records checkbox
        self.delete_all_var = tk.BooleanVar(value=False)
        self.delete_all_check = ttk.Checkbutton(self.frame, text="Delete ALL records", 
                                              variable=self.delete_all_var,
                                              command=self.toggle_delete_conditions)
        self.delete_all_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # Conditions frame
        self.delete_where_frame = ttk.LabelFrame(self.frame, text="Where Conditions")
        self.delete_where_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add condition button
        ttk.Button(self.delete_where_frame, text="Add Condition", 
                  command=self.add_condition).pack(anchor=tk.W, padx=5, pady=5)
    
    def update_db_dropdown(self):
        db_list = list(self.sqlvm.databases.keys())
        if not db_list:
            return
            
        self.delete_db_dropdown.configure(values=db_list)
        if self.main_app.current_db in db_list:
            self.delete_db_var.set(self.main_app.current_db)
        else:
            self.delete_db_var.set(db_list[0])
        self.update_table_dropdown()
    
    def update_table_dropdown(self, event=None):
        db_name = self.delete_db_var.get()
        if db_name in self.sqlvm.databases:
            table_list = list(self.sqlvm.databases[db_name].keys())
            self.delete_table_dropdown.configure(values=table_list)
            if table_list:
                self.delete_table_var.set(table_list[0])
            else:
                self.delete_table_var.set('')
            self.update_form()

    def update_form(self, event=None):
        # Clear existing conditions
        for widget in self.delete_where_frame.winfo_children():
            if widget.winfo_class() != 'TButton':  # Keep the "Add Condition" button
                widget.destroy()
        
        # Initialize condition list
        self.delete_conditions_list = []
        
        # Update UI based on delete all checkbox
        self.toggle_delete_conditions()
    
    def toggle_delete_conditions(self):
        # Enable/disable the conditions section based on "Delete All" checkbox
        if self.delete_all_var.get():
            self.delete_where_frame.pack_forget()
        else:
            self.delete_where_frame.pack(fill=tk.X, padx=5, pady=5)
    
    def add_condition(self):
        db_name = self.delete_db_var.get()
        table_name = self.delete_table_var.get()
        
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
        cond_frame = ttk.Frame(self.delete_where_frame)
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
        self.delete_conditions_list.append({
            "frame": cond_frame,
            "column": col_var,
            "operator": op_var,
            "value": val_var
        })
    
    def remove_condition(self, frame):
        # Find and remove the condition from the list
        for i, cond in enumerate(self.delete_conditions_list):
            if cond["frame"] == frame:
                frame.destroy()
                self.delete_conditions_list.pop(i)
                break
    
    def execute_interactive_delete(self):
        db_name = self.delete_db_var.get()
        table_name = self.delete_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Switch to the selected database
        if db_name != self.main_app.current_db:
            self.sqlvm.use_database(db_name)
            self.main_app.current_db = db_name
        
        # Build WHERE conditions
        where_clauses = []
        if not self.delete_all_var.get():
            for cond in self.delete_conditions_list:
                col = cond["column"].get()
                op = cond["operator"].get()
                val = cond["value"].get()
                
                # Format value based on operator and type
                if op == "LIKE":
                    val = f"'%{val}%'"
                elif op == "IN":
                    val = f"({val})"
                elif not val.isdigit():
                    val = f"'{val}'"
                
                where_clauses.append(f"{col} {op} {val}")
        
        # Build and execute SQL query
        query = f"DELETE FROM {table_name}"
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        # Confirm before executing
        if not where_clauses:
            confirm = messagebox.askyesno("Warning", 
                                         "This will delete ALL rows from the table. Are you sure?")
            if not confirm:
                return
        
        # Execute delete
        result = self.sqlvm.execute_command(query)
        
        # Show result and refresh if needed
        self.delete_result_label.config(text=result)
        if table_name == self.main_app.current_table:
            self.main_app.data_tab.load_table_data()
