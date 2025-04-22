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
        
        # Create treeview for structure with fixed column widths and better styling
        tree = ttk.Treeview(self.structure_frame, columns=columns, show="headings", height=20)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self.structure_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(self.structure_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for better alignment
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        # Make the treeview expandable
        self.structure_frame.grid_rowconfigure(0, weight=1)
        self.structure_frame.grid_columnconfigure(0, weight=1)
        
        # Configure column headings
        tree.heading("Column Name", text="Column Name", anchor=tk.W)
        tree.heading("Type", text="Type", anchor=tk.W)
        tree.heading("Indexed", text="Indexed", anchor=tk.CENTER)
        tree.heading("Auto Increment", text="Auto Increment", anchor=tk.CENTER)
        
        # Set column widths and alignment
        tree.column("Column Name", width=180, stretch=True, anchor=tk.W)
        tree.column("Type", width=120, stretch=True, anchor=tk.W)
        tree.column("Indexed", width=80, stretch=False, anchor=tk.CENTER)
        tree.column("Auto Increment", width=120, stretch=False, anchor=tk.CENTER)
        
        # Add data with alternating row colors for better readability
        for i, col_name in enumerate(table["columns"]):
            col_type = table.get("types", {}).get(col_name, "TEXT")
            is_indexed = "Yes" if col_name in table.get("indexes", {}) else "No"
            auto_increment = "Yes" if col_name in table.get("auto_increment", {}) else "No"
            
            # Add alternating row tag
            tag = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=(col_name, col_type, is_indexed, auto_increment), tags=(tag,))
        
        # Add alternating row colors
        tree.tag_configure("odd", background="#f0f0f0")
        tree.tag_configure("even", background="white")
        
        # Add table info section
        info_frame = ttk.LabelFrame(self.structure_frame, text="Table Information")
        info_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Display table details
        ttk.Label(info_frame, text=f"Table: {self.main_app.current_table}").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Database: {self.main_app.current_db}").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Total columns: {len(table['columns'])}").grid(row=2, column=0, sticky='w', padx=5, pady=2)
