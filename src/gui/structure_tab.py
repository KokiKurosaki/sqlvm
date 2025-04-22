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
        
        # Find columns that are part of primary key
        primary_keys = table.get("primary_key", [])
        if not primary_keys and "indexes" in table:
            # For backward compatibility - extract primary keys from indexes
            primary_keys = [col for col, idx_type in table.get("indexes", {}).items() if idx_type == "PRIMARY KEY"]
        
        # Add data with alternating row colors for better readability
        for i, col_name in enumerate(table["columns"]):
            col_type = table.get("types", {}).get(col_name, "TEXT")
            
            # Determine index type with special handling for primary keys
            is_indexed = "No"
            if "indexes" in table and col_name in table["indexes"]:
                if table["indexes"][col_name] == "PRIMARY KEY":
                    is_indexed = "PRIMARY KEY"
                else:
                    is_indexed = table["indexes"][col_name]
            elif col_name in primary_keys:
                is_indexed = "PRIMARY KEY"
            
            auto_increment = "Yes" if col_name in table.get("auto_increment", {}) else "No"
            
            # Add alternating row tag
            tag = "even" if i % 2 == 0 else "odd"
            # Add primary key tag if applicable
            if col_name in primary_keys:
                tag = "primary"
                
            tree.insert("", "end", values=(col_name, col_type, is_indexed, auto_increment), tags=(tag,))
        
        # Add alternating row colors and primary key highlighting
        tree.tag_configure("odd", background="#f0f0f0")
        tree.tag_configure("even", background="white")
        tree.tag_configure("primary", background="#ffffcc", foreground="#000000")  # Light yellow for primary keys
        
        # Add table info section
        info_frame = ttk.LabelFrame(self.structure_frame, text="Table Information")
        info_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        # Display table details
        ttk.Label(info_frame, text=f"Table: {self.main_app.current_table}").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Database: {self.main_app.current_db}").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        ttk.Label(info_frame, text=f"Total columns: {len(table['columns'])}").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        
        # Add primary key information
        if primary_keys:
            pk_type = "Composite Primary Key" if len(primary_keys) > 1 else "Primary Key"
            pk_columns = ", ".join(primary_keys)
            ttk.Label(info_frame, text=f"{pk_type}: {pk_columns}", font=("", 9, "bold")).grid(
                row=3, column=0, sticky='w', padx=5, pady=2)
        else:
            ttk.Label(info_frame, text="No Primary Key defined").grid(
                row=3, column=0, sticky='w', padx=5, pady=2)
        
        # Add indexes section
        if "indexes" in table and table["indexes"]:
            indexes_frame = ttk.LabelFrame(self.structure_frame, text="Indexes")
            indexes_frame.grid(row=3, column=0, columnspan=2, sticky='ew', pady=5, padx=5)
            
            # Create a simple treeview for indexes
            idx_tree = ttk.Treeview(indexes_frame, columns=["Keyname", "Type", "Unique", "Columns"], 
                                    show="headings", height=min(5, len(table["indexes"])))
            
            # Configure columns
            idx_tree.heading("Keyname", text="Keyname", anchor=tk.W)
            idx_tree.heading("Type", text="Type", anchor=tk.W)
            idx_tree.heading("Unique", text="Unique", anchor=tk.CENTER)
            idx_tree.heading("Columns", text="Columns", anchor=tk.W)
            
            idx_tree.column("Keyname", width=120, stretch=True)
            idx_tree.column("Type", width=80, stretch=False)
            idx_tree.column("Unique", width=60, stretch=False)
            idx_tree.column("Columns", width=220, stretch=True)
            
            # Group columns by index type
            index_groups = {}
            for col, idx_type in table["indexes"].items():
                if idx_type not in index_groups:
                    index_groups[idx_type] = []
                index_groups[idx_type].append(col)
            
            # Add rows for each index type
            for i, (idx_type, cols) in enumerate(index_groups.items()):
                is_unique = "Yes" if "UNIQUE" in idx_type or "PRIMARY" in idx_type else "No"
                idx_name = "PRIMARY" if "PRIMARY" in idx_type else f"idx_{i}"
                columns_str = ", ".join(cols)
                
                idx_tree.insert("", "end", values=(idx_name, idx_type, is_unique, columns_str))
                
            idx_tree.pack(fill=tk.X, padx=5, pady=5)
