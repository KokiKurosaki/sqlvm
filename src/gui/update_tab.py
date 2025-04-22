import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class UpdateTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Database and table selection
        self.setup_db_selection()
        
        # Create a frame for the table display
        self.table_frame = ttk.LabelFrame(self.frame, text="Table Data (Double-click a row to edit)")
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create message for when no table is selected
        self.no_table_label = ttk.Label(self.table_frame, text="Select a database and table to view data.")
        self.no_table_label.pack(pady=20)
        
        # Status display
        self.status_frame = ttk.Frame(self.frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        self.status_label = ttk.Label(self.status_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Refresh button
        ttk.Button(
            self.status_frame, 
            text="Refresh Data",
            command=self.refresh_data
        ).pack(side=tk.RIGHT, padx=5)
        
        # Store column names and data types for the current table
        self.column_names = []
        self.column_types = {}
    
    def setup_db_selection(self):
        update_top_frame = ttk.Frame(self.frame)
        update_top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Database dropdown
        ttk.Label(update_top_frame, text="Database:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.update_db_var = tk.StringVar()
        self.update_db_combo = ttk.Combobox(update_top_frame, textvariable=self.update_db_var, state="readonly")
        self.update_db_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        self.update_db_combo.bind('<<ComboboxSelected>>', self.update_table_list)
        
        # Table dropdown
        ttk.Label(update_top_frame, text="Table:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.update_table_var = tk.StringVar()
        self.update_table_dropdown = ttk.Combobox(update_top_frame, textvariable=self.update_table_var, state="readonly")
        self.update_table_dropdown.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        self.update_table_dropdown.bind('<<ComboboxSelected>>', self.load_table_data)
    
    def update_db_dropdown(self):
        db_list = list(self.sqlvm.databases.keys())
        self.update_db_combo.configure(values=db_list)
        
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
                self.load_table_data()
            else:
                self.update_table_var.set('')
                self.clear_table_display()
        else:
            self.clear_table_display()
    
    def clear_table_display(self):
        # Clear the table display area
        for widget in self.table_frame.winfo_children():
            widget.destroy()
            
        # Show "no table selected" message
        self.no_table_label = ttk.Label(self.table_frame, text="Select a database and table to view data.")
        self.no_table_label.pack(pady=20)
        
        # Clear column names and types
        self.column_names = []
        self.column_types = {}
    
    def load_table_data(self, event=None):
        # Clear existing data display
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        db_name = self.update_db_var.get()
        table_name = self.update_table_var.get()
        
        if not db_name or not table_name:
            self.clear_table_display()
            return
        
        # Switch to the selected database
        if db_name != self.main_app.current_db:
            self.sqlvm.use_database(db_name)
            self.main_app.current_db = db_name
        
        # Get table structure
        table = self.sqlvm.tables.get(table_name)
        if not table:
            ttk.Label(self.table_frame, text=f"Table {table_name} not found").pack(pady=20)
            return
        
        # Store column names and data types
        self.column_names = table["columns"]
        self.column_types = table.get("types", {})
        
        # Execute a SELECT query to get table data
        result = self.sqlvm.select(table_name)
        
        # Create treeview for data display with scrollbars
        container = ttk.Frame(self.table_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with columns from the table
        self.data_tree = ttk.Treeview(container, columns=self.column_names, show="headings")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(container, orient="vertical", command=self.data_tree.yview)
        hsb = ttk.Scrollbar(container, orient="horizontal", command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for treeview and scrollbars
        self.data_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # Configure column headings
        for col in self.column_names:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100)
        
        # Parse the result into rows
        try:
            # Skip the first two lines (header and separator)
            lines = result.strip().split('\n')
            if len(lines) < 3:
                ttk.Label(self.table_frame, text="No data in table").pack(pady=20)
                return
            
            # Process each data row
            for line_idx, line in enumerate(lines[2:]):
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
                
                # Insert into tree
                if values and len(values) > 0:
                    # Add identifier to the row
                    row_id = f"row_{line_idx}"
                    
                    # If values and columns don't match, try to pad or truncate
                    if len(values) != len(self.column_names):
                        if len(values) < len(self.column_names):
                            values.extend([''] * (len(self.column_names) - len(values)))
                        else:
                            values = values[:len(self.column_names)]
                    
                    self.data_tree.insert("", "end", iid=row_id, values=values)
                    
                    # Apply alternating row colors
                    if line_idx % 2 == 0:
                        self.data_tree.item(row_id, tags=('evenrow',))
                    else:
                        self.data_tree.item(row_id, tags=('oddrow',))
            
            # Apply tag configurations for row colors
            self.data_tree.tag_configure('oddrow', background='#f0f0f0')
            self.data_tree.tag_configure('evenrow', background='white')
            
            # Bind double-click to edit row
            self.data_tree.bind("<Double-1>", self.edit_selected_row)
            
            # Update status
            self.status_label.config(text=f"Table '{table_name}' loaded. Double-click a row to edit it.")
        
        except Exception as e:
            ttk.Label(self.table_frame, text=f"Error parsing result: {str(e)}").pack(pady=20)
    
    def edit_selected_row(self, event):
        # Get the selected item
        selected_item = self.data_tree.selection()
        if not selected_item:
            return
            
        # Get the values of the selected row
        row_values = self.data_tree.item(selected_item[0], "values")
        
        # Create the edit dialog
        self.create_edit_dialog(selected_item[0], row_values)
    
    def create_edit_dialog(self, row_id, row_values):
        db_name = self.update_db_var.get()
        table_name = self.update_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Edit Row - {table_name}")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create a canvas with scrollbar for the form
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Add a description
        ttk.Label(
            scroll_frame,
            text="Edit the values below and click 'Update' to save changes.",
            font=("", 9, "italic")
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=5, pady=10)
        
        # Create fields for each column
        value_vars = {}
        original_values = {}
        primary_key_values = {}
        
        # Determine which columns are primary keys
        table = self.sqlvm.tables.get(table_name)
        primary_keys = []
        
        # Fix for the index structure
        if table and "indexes" in table:
            indexes = table["indexes"]
            if isinstance(indexes, dict):
                for col_name, index_info in indexes.items():
                    if isinstance(index_info, dict) and index_info.get("type") == "PRIMARY":
                        primary_keys.append(col_name)
                    elif isinstance(index_info, str) and index_info == "PRIMARY":
                        primary_keys.append(col_name)
            elif isinstance(indexes, list):
                for index in indexes:
                    if isinstance(index, dict) and index.get("type") == "PRIMARY" and "column" in index:
                        primary_keys.append(index["column"])
        
        # If no primary keys defined, warn the user
        if not primary_keys:
            ttk.Label(
                scroll_frame,
                text="Warning: No primary key defined. Updates may affect multiple rows!",
                foreground="red"
            ).grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        
        for i, col_name in enumerate(self.column_names):
            row = i + 2  # Start after the header rows
            
            # Column name with type display
            col_type = self.column_types.get(col_name, "TEXT")
            col_header = f"{col_name} ({col_type})"
            
            # Is this a primary key?
            if col_name in primary_keys:
                col_header += " [PRIMARY KEY]"
                ttk.Label(scroll_frame, text=col_header, font=("", 9, "bold")).grid(
                    row=row, column=0, sticky="w", padx=5, pady=5)
                
                # For primary keys, show the value but don't allow editing
                ttk.Label(scroll_frame, text=row_values[i]).grid(
                    row=row, column=1, sticky="w", padx=5, pady=5)
                
                # Store primary key for the WHERE clause
                primary_key_values[col_name] = row_values[i]
            else:
                # Regular editable field
                ttk.Label(scroll_frame, text=col_header).grid(
                    row=row, column=0, sticky="w", padx=5, pady=5)
                
                # Create variable and entry field
                var = tk.StringVar(value=row_values[i])
                entry = ttk.Entry(scroll_frame, textvariable=var, width=30)
                entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
                
                value_vars[col_name] = var
            
            # Store original value for comparison
            original_values[col_name] = row_values[i]
        
        # Buttons
        button_frame = ttk.Frame(scroll_frame)
        button_frame.grid(row=len(self.column_names) + 2, column=0, columnspan=2, pady=10)
        
        def update_row():
            # Build SET clause - only include changed values
            set_clauses = []
            for col_name, var in value_vars.items():
                new_value = var.get()
                old_value = original_values[col_name]
                
                if new_value != old_value:
                    # Format based on column type
                    col_type = self.column_types.get(col_name, "TEXT").upper()
                    if new_value.upper() == "NULL":
                        set_clauses.append(f"{col_name} = NULL")
                    elif any(numeric_type in col_type for numeric_type in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMBER"]):
                        try:
                            if "." in new_value or "FLOAT" in col_type or "DOUBLE" in col_type or "DECIMAL" in col_type:
                                float(new_value)
                            else:
                                int(new_value)
                            set_clauses.append(f"{col_name} = {new_value}")
                        except ValueError:
                            set_clauses.append(f"{col_name} = '{new_value}'")
                    else:
                        set_clauses.append(f"{col_name} = '{new_value}'")
            
            # Build WHERE clause from primary keys
            where_clauses = []
            if primary_key_values:
                for col_name, value in primary_key_values.items():
                    col_type = self.column_types.get(col_name, "TEXT").upper()
                    if any(numeric_type in col_type for numeric_type in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMBER"]):
                        try:
                            if "." in value or "FLOAT" in col_type or "DOUBLE" in col_type or "DECIMAL" in col_type:
                                float(value)
                            else:
                                int(value)
                            where_clauses.append(f"{col_name} = {value}")
                        except ValueError:
                            where_clauses.append(f"{col_name} = '{value}'")
                    else:
                        where_clauses.append(f"{col_name} = '{value}'")
            else:
                for col_name, orig_value in original_values.items():
                    col_type = self.column_types.get(col_name, "TEXT").upper()
                    if orig_value.upper() == "NULL":
                        where_clauses.append(f"{col_name} IS NULL")
                    elif any(numeric_type in col_type for numeric_type in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMBER"]):
                        try:
                            if "." in orig_value or "FLOAT" in col_type or "DOUBLE" in col_type or "DECIMAL" in col_type:
                                float(orig_value)
                            else:
                                int(orig_value)
                            where_clauses.append(f"{col_name} = {orig_value}")
                        except ValueError:
                            where_clauses.append(f"{col_name} = '{orig_value}'")
                    else:
                        where_clauses.append(f"{col_name} = '{orig_value}'")
            
            # Build the UPDATE query
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)}"
            if where_clauses:
                query += f" WHERE {' AND '.join(where_clauses)}"
            
            # Execute the query
            result = self.sqlvm.execute_command(query)
            
            if "Error" in result:
                messagebox.showerror("Update Error", result)
            else:
                messagebox.showinfo("Success", "Row updated successfully!")
                
                new_values = list(row_values)
                for i, col_name in enumerate(self.column_names):
                    if col_name in value_vars and value_vars[col_name] is not None:
                        new_values[i] = value_vars[col_name].get()
                
                self.data_tree.item(row_id, values=new_values)
                dialog.destroy()
        
        def preview_sql():
            set_clauses = []
            for col_name, var in value_vars.items():
                new_value = var.get()
                old_value = original_values[col_name]
                
                if new_value != old_value:
                    col_type = self.column_types.get(col_name, "TEXT").upper()
                    if new_value.upper() == "NULL":
                        set_clauses.append(f"{col_name} = NULL")
                    elif any(numeric_type in col_type for numeric_type in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMBER"]):
                        try:
                            if "." in new_value or "FLOAT" in col_type or "DOUBLE" in col_type or "DECIMAL" in col_type:
                                float(new_value)
                            else:
                                int(new_value)
                            set_clauses.append(f"{col_name} = {new_value}")
                        except ValueError:
                            set_clauses.append(f"{col_name} = '{new_value}'")
                    else:
                        set_clauses.append(f"{col_name} = '{new_value}'")
            
            where_clauses = []
            if primary_key_values:
                for col_name, value in primary_key_values.items():
                    col_type = self.column_types.get(col_name, "TEXT").upper()
                    if any(numeric_type in col_type for numeric_type in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMBER"]):
                        try:
                            if "." in value or "FLOAT" in col_type or "DOUBLE" in col_type or "DECIMAL" in col_type:
                                float(value)
                            else:
                                int(value)
                            where_clauses.append(f"{col_name} = {value}")
                        except ValueError:
                            where_clauses.append(f"{col_name} = '{value}'")
                    else:
                        where_clauses.append(f"{col_name} = '{value}'")
            else:
                for col_name, orig_value in original_values.items():
                    col_type = self.column_types.get(col_name, "TEXT").upper()
                    if orig_value.upper() == "NULL":
                        where_clauses.append(f"{col_name} IS NULL")
                    elif any(numeric_type in col_type for numeric_type in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMBER"]):
                        try:
                            if "." in orig_value or "FLOAT" in col_type or "DOUBLE" in col_type or "DECIMAL" in col_type:
                                float(orig_value)
                            else:
                                int(orig_value)
                            where_clauses.append(f"{col_name} = {orig_value}")
                        except ValueError:
                            where_clauses.append(f"{col_name} = '{orig_value}'")
                    else:
                        where_clauses.append(f"{col_name} = '{orig_value}'")
            
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)}"
            if where_clauses:
                query += f" WHERE {' AND '.join(where_clauses)}"
            
            sql_dialog = tk.Toplevel(dialog)
            sql_dialog.title("SQL Preview")
            sql_dialog.geometry("600x300")
            sql_dialog.transient(dialog)
            sql_dialog.grab_set()
            
            sql_display = scrolledtext.ScrolledText(sql_dialog, wrap=tk.WORD, height=10)
            sql_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            sql_display.insert(tk.END, query)
            
            ttk.Button(
                sql_dialog, 
                text="Close",
                command=sql_dialog.destroy
            ).pack(padx=10, pady=10)
        
        ttk.Button(button_frame, text="Update", command=update_row).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Preview SQL", command=preview_sql).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def refresh_data(self):
        """Refresh the current table data"""
        self.load_table_data()
        self.status_label.config(text="Data refreshed.")
