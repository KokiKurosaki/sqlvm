import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

class QueryTab:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Create a notebook inside the query tab for different operations
        self.query_notebook = ttk.Notebook(self.frame)
        self.query_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # SQL Query tab (raw SQL)
        self.setup_raw_sql_tab()
        
        # Import tab components with try-except to avoid circular imports
        try:
            # Setup interactive tabs - import here to avoid circular imports
            from .select_tab import SelectTab
            from .insert_tab import InsertTab
            from .update_tab import UpdateTab
            from .delete_tab import DeleteTab
            
            # Create tab instances
            self.select_tab_instance = SelectTab(self.query_notebook, self.main_app)
            self.query_notebook.add(self.select_tab_instance.frame, text="Select Data")
            
            self.insert_tab_instance = InsertTab(self.query_notebook, self.main_app)
            self.query_notebook.add(self.insert_tab_instance.frame, text="Insert Data")
            
            self.update_tab_instance = UpdateTab(self.query_notebook, self.main_app)
            self.query_notebook.add(self.update_tab_instance.frame, text="Update Data")
            
            self.delete_tab_instance = DeleteTab(self.query_notebook, self.main_app)
            self.query_notebook.add(self.delete_tab_instance.frame, text="Delete Data")
        except Exception as e:
            print(f"Error loading interactive tabs: {e}")
            # Create a placeholder frame if the tabs can't be loaded
            placeholder = ttk.Frame(self.query_notebook)
            self.query_notebook.add(placeholder, text="Query Builder")
            ttk.Label(placeholder, text="Query builder tabs could not be loaded").pack(pady=20)
    
    def setup_raw_sql_tab(self):
        # SQL Query tab (original functionality)
        self.sql_query_frame = ttk.Frame(self.query_notebook)
        self.query_notebook.add(self.sql_query_frame, text="Raw SQL")
        
        # SQL editor frame with help button
        editor_frame = ttk.Frame(self.sql_query_frame)
        editor_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(editor_frame, text="SQL Query:").pack(side=tk.LEFT, padx=5)
        ttk.Button(editor_frame, text="Help", command=self.show_help).pack(side=tk.RIGHT, padx=5)
        
        # SQL editor
        self.query_editor = scrolledtext.ScrolledText(self.sql_query_frame, height=10)
        self.query_editor.pack(fill=tk.X, padx=5, pady=5)
        
        # Execute button
        ttk.Button(self.sql_query_frame, text="Execute", command=self.execute_query).pack(anchor=tk.W, padx=5, pady=5)
        
        # Results frame
        results_frame = ttk.LabelFrame(self.sql_query_frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Results text area
        self.query_results = scrolledtext.ScrolledText(results_frame)
        self.query_results.pack(fill=tk.BOTH, expand=True)
    
    def show_help(self):
        help_text = (
            "SQLVM Help:\n\n"
            "Database Operations:\n"
            "- CREATE DATABASE database_name;\n"
            "- DROP DATABASE [IF EXISTS] database_name;\n"
            "- USE database_name;\n"
            "- SHOW DATABASES;\n"
            "- SHOW TABLES;\n\n"
            "Table Operations:\n"
            "- CREATE TABLE table_name (\n"
            "    id INT AUTO_INCREMENT PRIMARY KEY,\n"
            "    name VARCHAR(255),\n"
            "    age INT\n"
            "  );\n\n"
            "Data Operations:\n"
            "- INSERT INTO table_name VALUES (val1, val2, ...);\n"
            "- INSERT INTO table_name (col1, col2) VALUES (val1, val2);\n"
            "- SELECT * FROM table_name;\n"
            "- SELECT col1, col2 FROM table_name;\n"
            "- UPDATE table_name SET col=value WHERE condition;\n"
            "- DELETE FROM table_name WHERE condition;\n\n"
            "Export Operations:\n"
            "- EXPORT DATABASE db_name TO SQL [file_path];\n"
            "- EXPORT DATABASE db_name TO JSON [file_path];\n"
            "- EXPORT ALL TO SQL [file_path];\n"
            "- EXPORT ALL TO JSON [file_path];\n\n"
            "Note: For VARCHAR type, always specify length like VARCHAR(255)"
        )
        messagebox.showinfo("Help", help_text)
    
    def execute_query(self):
        query = self.query_editor.get("1.0", tk.END).strip()
        if not query:
            messagebox.showinfo("Info", "Query is empty")
            return
        
        result = self.sqlvm.execute_command(query)
        self.query_results.delete("1.0", tk.END)
        self.query_results.insert(tk.END, result)
        
        # Update UI after executing query
        self.main_app.refresh_all()
    
    def refresh_all_tab_dropdowns(self):
        """Update all database dropdowns in all operation tabs"""
        for tab_instance in [
            getattr(self, 'select_tab_instance', None),
            getattr(self, 'insert_tab_instance', None),
            getattr(self, 'update_tab_instance', None),
            getattr(self, 'delete_tab_instance', None)
        ]:
            if tab_instance and hasattr(tab_instance, 'update_db_dropdown'):
                try:
                    tab_instance.update_db_dropdown()
                except Exception as e:
                    print(f"Error updating dropdown in {tab_instance.__class__.__name__}: {e}")
