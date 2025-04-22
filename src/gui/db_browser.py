import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import sys
import pickle
import atexit

# Define database directory constant - will be created if it doesn't exist
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'db'))
# Define default database file path
DEFAULT_DB_FILE = os.path.join(DB_DIR, 'sqlvm_database.db')

class DatabaseBrowser:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.sqlvm = main_app.sqlvm
        
        # Create database directory if it doesn't exist
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        
        # Load database from file if exists
        self.load_database()
        
        # Register save function to be called when program exits
        atexit.register(self.save_database)
        
        # Also register with parent window close event
        if isinstance(parent.winfo_toplevel(), tk.Tk):
            parent.winfo_toplevel().protocol("WM_DELETE_WINDOW", self.on_close)
            
        # Monkey patch SQLVM methods to add auto-save
        self._setup_auto_save()
        
        # Try to set the icon for any dialogs we create
        self.icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'quail.ico'))
            
        self.setup_tree()
        self.setup_toolbar()
    
    def _setup_auto_save(self):
        """
        Monkey patch SQLVM methods to add auto-save functionality
        This will automatically save the database after any modification
        """
        # Store original methods
        original_execute = self.sqlvm.execute_command
        original_create_db = self.sqlvm.create_database
        original_drop_db = self.sqlvm.drop_database
        
        # Override execute_command with auto-save functionality
        def execute_with_autosave(command, *args, **kwargs):
            result = original_execute(command, *args, **kwargs)
            
            # Check if this is a data-modifying command
            command_upper = command.strip().upper()
            if any(cmd in command_upper for cmd in ["CREATE", "INSERT", "UPDATE", "DELETE", "DROP", "ALTER"]):
                self.save_database()
                
            return result
        
        # Override create_database with auto-save functionality
        def create_db_with_autosave(db_name):
            result = original_create_db(db_name)
            self.save_database()
            return result
        
        # Override drop_database with auto-save functionality
        def drop_db_with_autosave(db_name):
            result = original_drop_db(db_name)
            self.save_database()
            return result
        
        # Replace the methods
        self.sqlvm.execute_command = execute_with_autosave
        self.sqlvm.create_database = create_db_with_autosave
        self.sqlvm.drop_database = drop_db_with_autosave
    
    def on_close(self):
        """Called when the application window is closed"""
        try:
            self.save_database()
            self.parent.winfo_toplevel().destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error while closing: {str(e)}")
            # Destroy anyway to prevent hanging
            self.parent.winfo_toplevel().destroy()
    
    def save_database(self):
        """Save the database schema and data to a file"""
        try:
            # Create a backup of the previous database file if it exists
            if os.path.exists(DEFAULT_DB_FILE):
                backup_file = f"{DEFAULT_DB_FILE}.bak"
                try:
                    if os.path.exists(backup_file):
                        os.remove(backup_file)
                    os.rename(DEFAULT_DB_FILE, backup_file)
                except Exception as e:
                    print(f"Warning: Could not create backup: {str(e)}")
            
            # Get database dictionary from sqlvm
            databases = self.sqlvm.databases
            
            # Save to file using pickle (for complex objects)
            with open(DEFAULT_DB_FILE, 'wb') as db_file:
                pickle.dump(databases, db_file)
                
            print(f"Database automatically saved to {DEFAULT_DB_FILE}")
            return True
            
        except Exception as e:
            print(f"Error saving database: {str(e)}")
            return False
    
    def load_database(self):
        """Load the database schema and data from a file"""
        try:
            # Check if the database file exists
            if not os.path.exists(DEFAULT_DB_FILE):
                print(f"No database file found at {DEFAULT_DB_FILE}")
                return False
            
            # Load from file using pickle
            with open(DEFAULT_DB_FILE, 'rb') as db_file:
                databases = pickle.load(db_file)
            
            # Update sqlvm databases
            self.sqlvm.databases = databases
            
            print(f"Database loaded from {DEFAULT_DB_FILE}")
            return True
            
        except Exception as e:
            print(f"Error loading database: {str(e)}")
            # If there was an error, try to load from backup
            try:
                backup_file = f"{DEFAULT_DB_FILE}.bak"
                if os.path.exists(backup_file):
                    print("Attempting to load from backup...")
                    with open(backup_file, 'rb') as db_file:
                        databases = pickle.load(db_file)
                    self.sqlvm.databases = databases
                    print(f"Database loaded from backup: {backup_file}")
                    return True
            except Exception as backup_error:
                print(f"Error loading backup: {str(backup_error)}")
            
            return False
    
    def setup_tree(self):
        # Tree frame with label
        tree_frame = ttk.LabelFrame(self.parent, text="Databases & Tables")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview
        self.db_tree = ttk.Treeview(tree_frame)
        self.db_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        tree_scrollbar = ttk.Scrollbar(self.db_tree, orient="vertical", command=self.db_tree.yview)
        self.db_tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure tree
        self.db_tree.heading('#0', text='Databases/Tables')
        
        # Bind events
        self.db_tree.bind('<Double-1>', self.on_tree_double_click)
        self.db_tree.bind('<Button-3>', self.on_tree_right_click)
    
    def setup_toolbar(self):
        # Toolbar frame
        toolbar = ttk.Frame(self.parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Create buttons
        ttk.Button(toolbar, text="New DB", command=self.create_database_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="New Table", command=self.create_table_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.update_database_tree).pack(side=tk.LEFT, padx=2)
        
        # Remove the export button since we now have export in the File menu
        
        # Add DB directory button
        ttk.Button(toolbar, text="DB Directory", command=self.open_db_directory).pack(side=tk.RIGHT, padx=2)
    
    def update_database_tree(self):
        # Clear existing items
        self.db_tree.delete(*self.db_tree.get_children())
        
        # Add root databases
        for db_name in self.sqlvm.databases:
            db_node = self.db_tree.insert("", "end", text=db_name, values=("database",))
            
            # Add tables as children
            for table_name in self.sqlvm.databases[db_name]:
                self.db_tree.insert(db_node, "end", text=table_name, values=("table",))
    
    def on_tree_double_click(self, event):
        item = self.db_tree.selection()[0]
        item_type = self.db_tree.item(item, "values")[0] if self.db_tree.item(item, "values") else None
        
        if item_type == "database":
            # Switch to database
            db_name = self.db_tree.item(item, "text")
            self.main_app.select_database(db_name)
        
        elif item_type == "table":
            # Get parent database and select table
            parent = self.db_tree.parent(item)
            db_name = self.db_tree.item(parent, "text")
            table_name = self.db_tree.item(item, "text")
            
            self.main_app.select_table(db_name, table_name)
    
    def on_tree_right_click(self, event):
        # Select the item under cursor
        item = self.db_tree.identify_row(event.y)
        if item:
            self.db_tree.selection_set(item)
            
            # Create context menu
            context_menu = tk.Menu(self.parent, tearoff=0)
            item_type = self.db_tree.item(item, "values")[0] if self.db_tree.item(item, "values") else None
            
            if item_type == "database":
                db_name = self.db_tree.item(item, "text")
                context_menu.add_command(label=f"Use Database '{db_name}'", 
                                         command=lambda: self.main_app.select_database(db_name))
                context_menu.add_command(label="New Table", command=self.create_table_dialog)
                context_menu.add_separator()
                context_menu.add_command(label=f"Drop Database '{db_name}'", 
                                         command=lambda: self.drop_database(db_name))
            
            elif item_type == "table":
                parent = self.db_tree.parent(item)
                db_name = self.db_tree.item(parent, "text")
                table_name = self.db_tree.item(item, "text")
                
                context_menu.add_command(label=f"View Data", 
                                         command=lambda: self.main_app.select_table(db_name, table_name))
                context_menu.add_command(label=f"View Structure", 
                                         command=lambda: self.view_table_structure(db_name, table_name))
                context_menu.add_separator()
                context_menu.add_command(label="Insert Row", 
                                         command=lambda: self.prepare_insert_row(db_name, table_name))
                context_menu.add_separator()
                context_menu.add_command(label=f"Drop Table '{table_name}'", 
                                         command=lambda: self.drop_table(db_name, table_name),
                                         foreground="red")
            
            # Display the menu
            context_menu.tk_popup(event.x_root, event.y_root)
    
    def drop_database(self, db_name):
        if messagebox.askyesno("Confirm", f"Are you sure you want to drop database '{db_name}'?"):
            result = self.sqlvm.drop_database(db_name)
            self.main_app.set_status(result)
            
            if self.main_app.current_db == db_name:
                self.main_app.current_db = None
                self.main_app.current_table = None
            
            self.update_database_tree()
            # Database is automatically saved by the monkey-patched drop_database method
    
    def drop_table(self, db_name, table_name):
        """Drop a table after confirmation"""
        if messagebox.askyesno("Confirm", f"Are you sure you want to drop table '{table_name}'?\nThis action cannot be undone!"):
            try:
                # Switch to the database if needed
                if self.main_app.current_db != db_name:
                    print(f"Switching from current database '{self.main_app.current_db}' to '{db_name}'")
                    result = self.sqlvm.use_database(db_name)
                    print(f"Database switch result: {result}")
                    self.main_app.current_db = db_name
                    
                # Print the current tables in the database before deletion
                print(f"Current tables in database '{db_name}': {list(self.sqlvm.databases.get(db_name, {}).keys())}")
                
                # Check if the table exists
                if table_name not in self.sqlvm.databases.get(db_name, {}):
                    messagebox.showerror("Error", f"Table '{table_name}' does not exist in database '{db_name}'")
                    return
                    
                # Since SQLVM doesn't properly support DROP TABLE, use direct deletion
                try:
                    # First try the SQL command for future compatibility
                    drop_command = f"DROP TABLE {table_name}"
                    print(f"Executing command: {drop_command}")
                    result = self.sqlvm.execute_command(drop_command)
                    print(f"Drop result: {result}")
                    
                    # Regardless of SQL result, manually remove the table
                    if table_name in self.sqlvm.databases.get(db_name, {}):
                        print(f"Manual removal of table '{table_name}'")
                        # Direct modification of the database structure
                        del self.sqlvm.databases[db_name][table_name]
                        print(f"Table '{table_name}' manually removed from database '{db_name}'")
                        # Force save after direct modification
                        self.save_database()
                    
                    # Clear references to the dropped table
                    if self.main_app.current_table == table_name:
                        self.main_app.current_table = None
                        # Clear the structure and data tabs
                        if hasattr(self.main_app, 'structure_tab') and self.main_app.structure_tab:
                            for widget in self.main_app.structure_tab.structure_frame.winfo_children():
                                widget.destroy()
                            self.main_app.structure_tab.no_table_label = ttk.Label(
                                self.main_app.structure_tab.structure_frame, 
                                text="Select a table to view its structure."
                            )
                            self.main_app.structure_tab.no_table_label.pack(pady=20)
                            
                        if hasattr(self.main_app, 'data_tab') and self.main_app.data_tab:
                            for widget in self.main_app.data_tab.data_frame.winfo_children():
                                widget.destroy()
                            self.main_app.data_tab.no_data_label = ttk.Label(
                                self.main_app.data_tab.data_frame, 
                                text="Select a table to view its data."
                            )
                            self.main_app.data_tab.no_data_label.pack(pady=20)
                    
                    # Success message regardless of SQL command result
                    self.main_app.set_status(f"Table '{table_name}' dropped successfully")
                    
                    # Refresh the database tree view
                    self.update_database_tree()
                    
                    # Also refresh any database dropdown menus
                    self.main_app.refresh_all()
                    
                except Exception as e:
                    print(f"Error during table drop: {e}")
                    messagebox.showerror("Error", f"Failed to drop table: {str(e)}")
                    
            except Exception as e:
                print(f"Exception in drop_table: {str(e)}")
                messagebox.showerror("Error", f"An error occurred while dropping the table: {str(e)}")
    
    def create_database_dialog(self):
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create Database")
        dialog.geometry("300x120")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Try to set the icon for the dialog
        if os.path.exists(self.icon_path):
            try:
                dialog.iconbitmap(self.icon_path)
                dialog.wm_attributes('-toolwindow', False)
            except tk.TclError as e:
                print(f"Could not set dialog icon: {e}")
        
        ttk.Label(dialog, text="Database Name:").pack(pady=5)
        db_name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=db_name_var).pack(fill=tk.X, padx=20, pady=5)
        
        def create_db():
            db_name = db_name_var.get().strip()
            if db_name:
                result = self.sqlvm.create_database(db_name)
                self.main_app.set_status(result)
                self.update_database_tree()
                dialog.destroy()
                # Database is automatically saved by the monkey-patched create_database method
            else:
                messagebox.showerror("Error", "Database name cannot be empty")
        
        ttk.Button(dialog, text="Create", command=create_db).pack(pady=10)
    
    def create_table_dialog(self):
        if not self.main_app.current_db:
            messagebox.showerror("Error", "Please select a database first")
            return
        
        # Import the CreateTableDialog class
        from .create_table_dialog import CreateTableDialog
        
        # Create the dialog
        table_dialog = CreateTableDialog(self.parent, self.main_app)
        
        # The dialog will update the database tree when a table is created
    
    def view_table_structure(self, db_name, table_name):
        # Switch to database if needed
        if self.main_app.current_db != db_name:
            self.main_app.select_database(db_name)
        
        self.main_app.current_table = table_name
        self.main_app.structure_tab.load_table_structure()
        self.main_app.notebook.select(self.main_app.structure_tab.frame)
    
    def prepare_insert_row(self, db_name, table_name):
        # Switch to database if needed
        if self.main_app.current_db != db_name:
            self.main_app.select_database(db_name)
        
        self.main_app.current_table = table_name
        self.main_app.data_tab.insert_row_dialog()
    
    def open_db_directory(self):
        """Open the database directory in file explorer"""
        try:
            if os.path.exists(DB_DIR):
                if os.name == 'nt':  # Windows
                    os.startfile(DB_DIR)
                elif os.name == 'posix':  # macOS or Linux
                    import subprocess
                    subprocess.call(['open' if sys.platform == 'darwin' else 'xdg-open', DB_DIR])
                
                self.main_app.set_status(f"Opened database directory: {DB_DIR}")
            else:
                messagebox.showinfo("Info", "Database directory does not exist")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory: {str(e)}")
