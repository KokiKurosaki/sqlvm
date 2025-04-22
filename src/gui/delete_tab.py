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
        
        # Create a frame for the table display
        self.table_frame = ttk.LabelFrame(self.frame, text="Select Rows to Delete")
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create message for when no table is selected
        self.no_table_label = ttk.Label(self.table_frame, text="Select a database and table to view data.")
        self.no_table_label.pack(pady=20)
        
        # Delete button
        self.delete_button = ttk.Button(
            self.frame, 
            text="Delete Selected Rows", 
            command=self.delete_selected_rows,
            state="disabled"
        )
        self.delete_button.pack(anchor=tk.W, padx=5, pady=10)
        
        # Result display
        self.delete_result_label = ttk.Label(self.frame, text="")
        self.delete_result_label.pack(fill=tk.X, padx=5, pady=5)
        
        # Store column names and data types for the current table
        self.column_names = []
        self.column_types = {}
        
        # Store selected rows for deletion
        self.selected_rows = set()

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
        self.delete_table_dropdown.bind("<<ComboboxSelected>>", self.load_table_data)
        
        # Refresh button
        ttk.Button(
            delete_top_frame, 
            text="Refresh Data",
            command=self.load_table_data
        ).grid(row=0, column=4, padx=5, pady=5)
    
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
                self.load_table_data()
            else:
                self.delete_table_var.set('')
                self.clear_table_display()
        else:
            self.clear_table_display()

    def clear_table_display(self):
        # Clear existing widgets
        for widget in self.table_frame.winfo_children():
            widget.destroy()
            
        # Show "no table selected" message
        self.no_table_label = ttk.Label(self.table_frame, text="Select a database and table to view data.")
        self.no_table_label.pack(pady=20)
        
        # Clear column names and types
        self.column_names = []
        self.column_types = {}
        
        # Clear selected rows
        self.selected_rows = set()
        
        # Disable delete button
        self.delete_button.config(state="disabled")
    
    def load_table_data(self, event=None):
        # Clear existing data display
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # Reset selected rows
        self.selected_rows = set()
        
        db_name = self.delete_db_var.get()
        table_name = self.delete_table_var.get()
        
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
        
        # Create treeview with a checkbox column and data columns
        columns = ["#0"] + self.column_names
        self.data_tree = ttk.Treeview(container, columns=columns[1:], show="headings")
        
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
            # Enhanced visual styling for selected rows
            self.data_tree.tag_configure('selected', background='#ff9999', foreground='black', font=('', 9, 'bold'))
            
            # Add selection count label
            self.selection_label = ttk.Label(self.table_frame, 
                text="0 rows selected for deletion")
            self.selection_label.pack(pady=5)
            
            # Bind select/deselect event
            self.data_tree.bind('<Button-1>', self.on_row_click)
            
            # Enable delete button if there's data
            if len(self.data_tree.get_children()) > 0:
                self.delete_button.config(state="normal")
            
            # Update result label and add helpful instructions
            self.delete_result_label.config(text=f"Table '{table_name}' loaded. Click on rows to select them for deletion.")
            
            # Add additional instructions label for clarity
            ttk.Label(self.table_frame, 
                text="Click on a row to select/deselect it for deletion.",
                font=('', 9, 'italic')).pack(before=self.selection_label)
            
        except Exception as e:
            ttk.Label(self.table_frame, text=f"Error parsing result: {str(e)}").pack(pady=20)
    
    def on_row_click(self, event):
        # Get the clicked row
        region = self.data_tree.identify("region", event.x, event.y)
        if region == "cell":
            row_id = self.data_tree.identify_row(event.y)
            if row_id:
                # Toggle row selection
                if row_id in self.selected_rows:
                    # Deselect: remove from selected set and restore original tag
                    self.selected_rows.remove(row_id)
                    
                    # Determine if this was an even or odd row and restore appropriate tag
                    row_index = int(row_id.split('_')[1])
                    if row_index % 2 == 0:
                        self.data_tree.item(row_id, tags=('evenrow',))
                    else:
                        self.data_tree.item(row_id, tags=('oddrow',))
                else:
                    # Select: add to selected set and apply 'selected' tag
                    self.selected_rows.add(row_id)
                    self.data_tree.item(row_id, tags=('selected',))
                
                # Update selection count with more descriptive text
                count = len(self.selected_rows)
                self.selection_label.config(
                    text=f"{count} row{'s' if count != 1 else ''} selected for deletion"
                )
    
    def delete_selected_rows(self):
        """Delete the selected rows"""
        if not self.selected_rows:
            messagebox.showinfo("No Selection", "Please select rows to delete.")
            return
        
        db_name = self.delete_db_var.get()
        table_name = self.delete_table_var.get()
        
        if not db_name or not table_name:
            messagebox.showerror("Error", "Please select a database and table first")
            return
        
        # Confirm deletion
        count = len(self.selected_rows)
        if not messagebox.askyesno("Confirm Delete", 
                                  f"Are you sure you want to delete {count} selected row{'s' if count > 1 else ''}?\n\nThis cannot be undone!"):
            return
        
        # Get the table and build the WHERE conditions for each row
        table = self.sqlvm.tables.get(table_name)
        if not table:
            messagebox.showerror("Error", f"Table {table_name} not found")
            return
        
        # Track deleted count
        deleted_count = 0
        errors = []
        
        # Process each selected row
        for row_id in self.selected_rows:
            try:
                # Get row values from the treeview
                row_values = self.data_tree.item(row_id, "values")
                
                # Build WHERE condition for this specific row
                where_conditions = []
                for i, col_name in enumerate(self.column_names):
                    if i < len(row_values):
                        value = row_values[i]
                        col_type = self.column_types.get(col_name, "TEXT").upper()
                        
                        # Format the value based on its type
                        if value.upper() == "NULL":
                            where_conditions.append(f"{col_name} IS NULL")
                        elif any(numeric_type in col_type for numeric_type in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMBER"]):
                            try:
                                float(value)  # Test if it's a number
                                where_conditions.append(f"{col_name} = {value}")
                            except ValueError:
                                where_conditions.append(f"{col_name} = '{value}'")
                        else:
                            where_conditions.append(f"{col_name} = '{value}'")
                
                # Build the complete WHERE clause
                where_clause = " AND ".join(where_conditions)
                
                # Execute DELETE for this row
                result = self.sqlvm.execute_command(f"DELETE FROM {table_name} WHERE {where_clause}")
                
                if "Error" in result:
                    errors.append(f"Error deleting row {row_id}: {result}")
                else:
                    deleted_count += 1
                    
            except Exception as e:
                errors.append(f"Error processing row {row_id}: {str(e)}")
        
        # Show results
        if errors:
            error_msg = "\n".join(errors[:3])
            if len(errors) > 3:
                error_msg += f"\n(and {len(errors) - 3} more errors)"
            messagebox.showwarning("Delete Warnings", 
                                 f"Deleted {deleted_count} of {len(self.selected_rows)} rows.\n\nErrors:\n{error_msg}")
        else:
            messagebox.showinfo("Success", f"Successfully deleted {deleted_count} rows.")
        
        # Update the UI
        self.load_table_data()
        self.delete_result_label.config(text=f"Deleted {deleted_count} rows.")
        
        # Update main app table if we're viewing the same table
        if self.main_app.current_db == db_name and self.main_app.current_table == table_name:
            self.main_app.data_tab.load_table_data()
