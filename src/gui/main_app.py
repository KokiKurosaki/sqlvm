import tkinter as tk
from tkinter import ttk
import sys
import os

# Add parent directory to path to allow importing sqlvm
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.sqlvm import SQLVM

# Import GUI components using relative imports
from .db_browser import DatabaseBrowser
from .query_tab import QueryTab
from .structure_tab import StructureTab
from .data_tab import DataTab

class SQLVMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLVM Manager")
        self.root.geometry("1200x800")
        
        # Initialize SQLVM instance
        self.sqlvm = SQLVM()
        
        # Track current database and table
        self.current_db = None
        self.current_table = None
        
        # Create main layout
        self.create_layout()
        
        # Update UI with initial data
        self.browser.update_database_tree()
        
        # Update all dropdowns
        self.query_tab.refresh_all_tab_dropdowns()
    
    def create_layout(self):
        # Main paned window (left panel and right panel)
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - database browser
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=1)
        
        # Right panel - content area
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=3)
        
        # Initialize database browser
        self.browser = DatabaseBrowser(self.left_frame, self)
        
        # Create notebook for different tabs
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Set up tabs
        self.setup_tabs()
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_tabs(self):
        # SQL Query tab
        self.query_tab = QueryTab(self.notebook, self)
        self.notebook.add(self.query_tab.frame, text="SQL Query")
        
        # Structure tab
        self.structure_tab = StructureTab(self.notebook, self)
        self.notebook.add(self.structure_tab.frame, text="Structure")
        
        # Data tab
        self.data_tab = DataTab(self.notebook, self)
        self.notebook.add(self.data_tab.frame, text="Data")
    
    def select_database(self, db_name):
        result = self.sqlvm.use_database(db_name)
        self.current_db = db_name
        self.current_table = None
        self.set_status(result)
        
        # Update UI elements that depend on the current database
        self.query_tab.refresh_all_tab_dropdowns()
    
    def select_table(self, db_name, table_name):
        # Make sure we're using the correct database
        if self.current_db != db_name:
            self.sqlvm.use_database(db_name)
            self.current_db = db_name
        
        self.current_table = table_name
        self.set_status(f"Selected table {table_name}")
        
        # Update the tabs to show table information
        self.structure_tab.load_table_structure()
        self.data_tab.load_table_data()
        
        # Switch to data tab
        self.notebook.select(self.data_tab.frame)
    
    def set_status(self, message):
        self.status_bar.config(text=message)
    
    def refresh_all(self):
        """Refresh all UI components"""
        # Update database tree
        self.browser.update_database_tree()
        
        # Update dropdowns
        self.query_tab.refresh_all_tab_dropdowns()
        
        # If there's a current table, refresh its data
        if self.current_table:
            self.structure_tab.load_table_structure()
            self.data_tab.load_table_data()


def main():
    root = tk.Tk()
    app = SQLVMApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
