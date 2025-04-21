import tkinter as tk
from tkinter import ttk

class StructureTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Structure frame
        self.structure_frame = ttk.Frame(self.frame)
        self.structure_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message when no table is selected
        self.no_table_label = ttk.Label(self.structure_frame, text="Select a table to view its structure.")
        self.no_table_label.pack(pady=20)
    
    def load_table_structure(self):
        if not self.main_app.current_table:
            return
        
        # Clear existing widgets
        for widget in self.structure_frame.winfo_children():
            widget.destroy()
        
        table = self.sqlvm.tables.get(self.main_app.current_table)
        if not table:
            ttk.Label(self.structure_frame, text=f"Table {self.main_app.current_table} not found").pack(pady=20)
            return
        
        # Create structure view
        columns = ["Column Name", "Type", "Indexed", "Auto Increment"]
        
        # Create treeview for structure
        tree = ttk.Treeview(self.structure_frame, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Add data
        for i, col_name in enumerate(table["columns"]):
            col_type = table.get("types", {}).get(col_name, "TEXT")
            is_indexed = "Yes" if col_name in table.get("indexes", {}) else "No"
            auto_increment = "Yes" if col_name in table.get("auto_increment", {}) else "No"
            
            tree.insert("", "end", values=(col_name, col_type, is_indexed, auto_increment))
