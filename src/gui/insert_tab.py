import tkinter as tk
from tkinter import ttk, messagebox

class InsertTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Database and table selection
        self.setup_db_selection()
        
        # Form area
        self.setup_form_area()
        
        # Insert button
        self.insert_button_frame = ttk.Frame(self.frame)
        self.insert_button_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(self.insert_button_frame, text="Insert Data", 
                  command=self.execute_interactive_insert).pack(pady=10)
    
    def setup_db_selection(self):
        insert_top_frame = ttk.Frame(self.frame)
        insert_top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Database dropdown
        ttk.Label(insert_top_frame, text="Database:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.insert_db_var = tk.StringVar()
        self.insert_db_dropdown = ttk.Combobox(insert_top_frame, textvariable=self.insert_db_var, state="readonly")
        self.insert_db_dropdown.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.insert_db_dropdown.bind("<<ComboboxSelected>>", self.update_table_dropdown)
        
        # Table dropdown
        ttk.Label(insert_top_frame, text="Table:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.insert_table_var = tk.StringVar()
        self.insert_table_dropdown = ttk.Combobox(insert_top_frame, textvariable=self.insert_table_var, state="readonly")
        self.insert_table_dropdown.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.insert_table_dropdown.bind("<<ComboboxSelected>>", self.update_form)
    
    def setup_form_area(self):
        # Create a canvas with scrollbar for the form
        self.insert_canvas = tk.Canvas(self.frame)
        self.insert_scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.insert_canvas.yview)
        self.insert_form_frame = ttk.Frame(self.insert_canvas)
        
        self.insert_canvas.configure(yscrollcommand=self.insert_scrollbar.set)
        self.insert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.insert_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.insert_canvas.create_window((0, 0), window=self.insert_form_frame, anchor="nw")
        
        self.insert_form_frame.bind("<Configure>", 
                                    lambda e: self.insert_canvas.configure(scrollregion=self.insert_canvas.bbox("all")))
    
    def update_db_dropdown(self):
        db_list = list(self.sqlvm.databases.keys())
        self.insert_db_dropdown.configure(values=db_list)
        
        if db_list and self.main_app.current_db in db_list:
            self.insert_db_var.set(self.main_app.current_db)
        elif db_list:
            self.insert_db_var.set(db_list[0])
        
        # Update table dropdown
        self.update_table_dropdown()
    
    def update_table_dropdown(self, event=None):
        db_name = self.insert_db_var.get()
        if db_name in self.sqlvm.databases:
            table_list = list(self.sqlvm.databases[db_name].keys())
            self.insert_table_dropdown.configure(values=table_list)
            if table_list:
                self.insert_table_var.set(table_list[0])
            else:
                self.insert_table_var.set('')
            
            # Update form based on selected table
            self.update_form()
    
    def update_form(self, event=None):
        # Clear existing form
        for widget in self.insert_form_frame.winfo_children():
            widget.destroy()
        
        db_name = self.insert_db_var.get()
        table_name = self.insert_table_var.get()
        
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
        
        # Create entry fields for each column
        self.insert_value_vars = {}
        for i, col_name in enumerate(table["columns"]):
            ttk.Label(self.insert_form_frame, text=f"{col_name}:").grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            
            # Check if column is auto_increment
            is_auto_increment = col_name in table.get("auto_increment", {})
            if is_auto_increment:
                ttk.Label(self.insert_form_frame, text="[AUTO]").grid(row=i, column=1, sticky=tk.W, padx=5, pady=5)
                self.insert_value_vars[col_name] = None
            else:
                var = tk.StringVar()
                entry = ttk.Entry(self.insert_form_frame, textvariable=var, width=40)
                entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=5)
                self.insert_value_vars[col_name] = var
        
        # Update canvas scroll region
        self.insert_form_frame.update_idletasks()
        self.insert_canvas.configure(scrollregion=self.insert_canvas.bbox("all"))
    
    def execute_interactive_insert(self):
        db_name = self.insert_db_var.get()
        table_name = self.insert_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Switch to the selected database
        if db_name != self.main_app.current_db:
            self.sqlvm.use_database(db_name)
            self.main_app.current_db = db_name
        
        # Collect values from form
        columns = []
        values = []
        
        for col, var in self.insert_value_vars.items():
            if var is not None:  # Skip auto_increment columns
                val = var.get().strip()
                columns.append(col)
                values.append(val)
        
        if not values:
            messagebox.showerror("Error", "Please enter at least one value")
            return
        
        # Execute insert
        result = self.sqlvm.insert(table_name, values, columns)
        
        # Show result and refresh data if needed
        messagebox.showinfo("Insert Result", result)
        if table_name == self.main_app.current_table:
            self.main_app.data_tab.load_table_data()
