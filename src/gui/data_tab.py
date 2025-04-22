import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

class DataTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Data frame
        self.data_frame = ttk.Frame(self.frame)
        self.data_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message when no table is selected
        self.no_data_label = ttk.Label(self.data_frame, text="Select a table to view its data.")
        self.no_data_label.pack(pady=20)
        
        # Controls for data manipulation
        self.data_controls = ttk.Frame(self.frame)
        self.data_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.data_controls, text="Insert Row", command=self.insert_row_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.data_controls, text="Refresh", command=self.refresh_data).pack(side=tk.LEFT, padx=2)
    
    def load_table_data(self):
        if not self.main_app.current_table:
            return
        
        # Clear existing widgets
        for widget in self.data_frame.winfo_children():
            widget.destroy()
        
        # Get table data using select method
        result = self.sqlvm.select(self.main_app.current_table)
        
        # Create text widget to display data
        data_display = scrolledtext.ScrolledText(self.data_frame)
        data_display.pack(fill=tk.BOTH, expand=True)
        
        # Insert formatted data
        data_display.insert(tk.END, result)
    
    def insert_row_dialog(self):
        if not self.main_app.current_table:
            messagebox.showerror("Error", "Please select a table first")
            return
        
        table = self.sqlvm.tables.get(self.main_app.current_table)
        if not table:
            messagebox.showerror("Error", f"Table {self.main_app.current_table} not found")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title(f"Insert Row into {self.main_app.current_table}")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Create a frame with scrollbar for the form
        canvas = tk.Canvas(dialog)
        scroll_frame = ttk.Frame(canvas)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Create entry fields for each column
        value_vars = {}
        row = 0
        for col_name in table["columns"]:
            ttk.Label(scroll_frame, text=f"{col_name}:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            
            # Check if column is auto_increment
            is_auto_increment = col_name in table.get("auto_increment", {})
            if is_auto_increment:
                ttk.Label(scroll_frame, text="AUTO_INCREMENT").grid(row=row, column=1, sticky="w", padx=5, pady=2)
                value_vars[col_name] = None
            else:
                var = tk.StringVar()
                entry = ttk.Entry(scroll_frame, textvariable=var)
                entry.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
                value_vars[col_name] = var
            
            row += 1
        
        # Function to handle insert
        def do_insert():
            values = []
            columns = []
            
            for col, var in value_vars.items():
                if var is not None:  # Skip auto_increment columns
                    columns.append(col)
                    values.append(var.get())
            
            result = self.sqlvm.insert(self.main_app.current_table, values, columns)
            self.main_app.set_status(result)
            self.load_table_data()  # Refresh data view
            dialog.destroy()
        
        ttk.Button(scroll_frame, text="Insert", command=do_insert).grid(row=row, column=0, columnspan=2, pady=10)
    
    def refresh_data(self):
        if self.main_app.current_table:
            self.load_table_data()
