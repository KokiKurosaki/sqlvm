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
        
        # Add import button
        self.import_button = ttk.Button(toolbar, text="Import", command=self.show_import_menu)
        self.import_button.pack(side=tk.LEFT, padx=2)
        
        # Export button
        self.export_button = ttk.Button(toolbar, text="Export", command=self.show_export_menu)
        self.export_button.pack(side=tk.LEFT, padx=2)
        
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
            
            # Display the menu
            context_menu.tk_popup(event.x_root, event.y_root)
    
    def create_database_dialog(self):
        # Create dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Create Database")
        dialog.geometry("300x120")
        dialog.transient(self.parent)
        dialog.grab_set()
        
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
    
    def drop_database(self, db_name):
        if messagebox.askyesno("Confirm", f"Are you sure you want to drop database '{db_name}'?"):
            result = self.sqlvm.drop_database(db_name)
            self.main_app.set_status(result)
            
            if self.main_app.current_db == db_name:
                self.main_app.current_db = None
                self.main_app.current_table = None
            
            self.update_database_tree()
            # Database is automatically saved by the monkey-patched drop_database method
    
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
    
    def show_export_menu(self):
        if not self.main_app.current_db:
            messagebox.showerror("Error", "Please select a database first")
            return
        
        # Create popup menu
        export_menu = tk.Menu(self.parent, tearoff=0)
        export_menu.add_command(label=f"Export {self.main_app.current_db} to SQL", 
                               command=lambda: self.export_database(self.main_app.current_db, "sql"))
        export_menu.add_command(label=f"Export {self.main_app.current_db} to JSON", 
                               command=lambda: self.export_database(self.main_app.current_db, "json"))
        export_menu.add_separator()
        export_menu.add_command(label="Export All to SQL", 
                               command=lambda: self.export_database(None, "sql"))
        export_menu.add_command(label="Export All to JSON", 
                               command=lambda: self.export_database(None, "json"))
        
        # Get position of export button
        x = self.export_button.winfo_rootx()
        y = self.export_button.winfo_rooty() + self.export_button.winfo_height()
        
        # Show menu
        export_menu.tk_popup(x, y)
    
    def export_database(self, db_name, format_type):
        # Get file path
        filetypes = [("SQL Files", "*.sql")] if format_type == "sql" else [("JSON Files", "*.json")]
        file_path = filedialog.asksaveasfilename(defaultextension=f".{format_type}", filetypes=filetypes)
        
        if not file_path:
            return
        
        if format_type == "sql":
            result = self.sqlvm.export_to_sql(db_name, file_path)
        else:
            result = self.sqlvm.export_to_json(db_name, file_path)
        
        self.main_app.set_status(result)
    
    def show_import_menu(self):
        """Show import menu options"""
        # Create popup menu
        import_menu = tk.Menu(self.parent, tearoff=0)
        import_menu.add_command(label="Import SQL file", 
                               command=lambda: self.import_file("sql"))
        import_menu.add_command(label="Import JSON file", 
                               command=lambda: self.import_file("json"))
        import_menu.add_separator()
        import_menu.add_command(label="Open DB Directory", 
                               command=self.open_db_directory)
        
        # Get position of import button
        x = self.import_button.winfo_rootx()
        y = self.import_button.winfo_rooty() + self.import_button.winfo_height()
        
        # Show menu
        import_menu.tk_popup(x, y)
    
    def import_file(self, file_type):
        """Import SQL or JSON file"""
        # Define file types for dialog
        if file_type == "sql":
            filetypes = [("SQL Files", "*.sql"), ("All Files", "*.*")]
        else:
            filetypes = [("JSON Files", "*.json"), ("All Files", "*.*")]
            
        # Get file path
        file_path = filedialog.askopenfilename(
            initialdir=DB_DIR,
            filetypes=filetypes,
            title=f"Select {file_type.upper()} file to import"
        )
        
        if not file_path:
            return
            
        # Ask which database to use
        db_dialog = tk.Toplevel(self.parent)
        db_dialog.title(f"Import {file_type.upper()} file")
        db_dialog.geometry("400x150")
        db_dialog.transient(self.parent)
        db_dialog.grab_set()
        
        # Database selection
        ttk.Label(db_dialog, text="Select database to import into:").pack(pady=5)
        
        # Get list of databases
        databases = list(self.sqlvm.databases.keys())
        db_var = tk.StringVar()
        if databases:
            db_var.set(databases[0])  # Default to first db
        
        # Add option to create new database
        create_new_var = tk.BooleanVar()
        create_new_var.set(False)
        
        def toggle_db_selection():
            if create_new_var.get():
                db_combo.config(state="disabled")
                new_db_entry.config(state="normal")
            else:
                db_combo.config(state="readonly")
                new_db_entry.config(state="disabled")
        
        # Database dropdown
        db_combo = ttk.Combobox(db_dialog, textvariable=db_var, values=databases, state="readonly")
        db_combo.pack(fill=tk.X, padx=20, pady=5)
        
        # Option to create new database
        ttk.Checkbutton(
            db_dialog, 
            text="Create new database", 
            variable=create_new_var,
            command=toggle_db_selection
        ).pack(anchor=tk.W, padx=20, pady=2)
        
        # Entry for new database name
        new_db_var = tk.StringVar()
        new_db_entry = ttk.Entry(db_dialog, textvariable=new_db_var, state="disabled")
        new_db_entry.pack(fill=tk.X, padx=20, pady=5)
        
        def do_import():
            if create_new_var.get():
                # Create new database first
                db_name = new_db_var.get().strip()
                if not db_name:
                    messagebox.showerror("Error", "Please enter a database name")
                    return
                    
                # Create the database
                result = self.sqlvm.create_database(db_name)
                if "Error" in result:
                    messagebox.showerror("Error", f"Failed to create database: {result}")
                    return
            else:
                # Use selected database
                if not databases:
                    messagebox.showerror("Error", "No databases available")
                    return
                    
                db_name = db_var.get()
            
            # Close dialog
            db_dialog.destroy()
            
            # Now perform the import
            if file_type == "sql":
                self.import_sql_file(file_path, db_name)
            else:
                self.import_json_file(file_path, db_name)
                
            # Update tree
            self.update_database_tree()
            
            # Select the database we just imported to
            self.main_app.select_database(db_name)
        
        # Import button
        ttk.Button(db_dialog, text="Import", command=do_import).pack(pady=10)
    
    def import_sql_file(self, file_path, db_name):
        """Import SQL file into the specified database"""
        try:
            # Switch to the target database
            result = self.sqlvm.use_database(db_name)
            if "Error" in result:
                raise Exception(f"Failed to use database '{db_name}': {result}")
                
            # Read SQL file
            with open(file_path, 'r') as sql_file:
                sql_content = sql_file.read()
                
            # Split into commands (simple split by semicolon)
            commands = [cmd.strip() for cmd in sql_content.split(";") if cmd.strip()]
            
            # Execute each command
            success_count = 0
            errors = []
            
            for cmd in commands:
                result = self.sqlvm.execute_command(cmd)
                if "Error" in result:
                    errors.append(f"Error executing: {cmd}\n{result}")
                else:
                    success_count += 1
            
            # Show results
            if errors:
                error_message = "\n\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_message += f"\n\n(and {len(errors) - 5} more errors)"
                
                messagebox.showwarning("Import Warnings", 
                    f"Imported with {len(errors)} errors. {success_count} commands succeeded.\n\n{error_message}")
            else:
                messagebox.showinfo("Import Complete", 
                    f"Successfully imported {success_count} SQL commands")
            
            self.main_app.set_status(f"Imported SQL file: {os.path.basename(file_path)}")
            
            # Database is automatically saved by the monkey-patched execute_command method
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing SQL file: {str(e)}")
            self.main_app.set_status(f"Error importing SQL file: {str(e)}")
    
    def import_json_file(self, file_path, db_name):
        """Import JSON file into the specified database"""
        try:
            # Switch to the target database
            result = self.sqlvm.use_database(db_name)
            if "Error" in result:
                raise Exception(f"Failed to use database '{db_name}': {result}")
                
            # Read JSON file
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                
            # Check JSON structure
            if isinstance(data, dict):
                if "tables" in data:
                    # Database export format
                    self.import_database_json(data, db_name)
                elif "table" in data and "records" in data:
                    # Single table format
                    self.import_table_json(data)
                else:
                    raise Exception("Unrecognized JSON format. Expected 'tables' or 'table' key.")
            elif isinstance(data, list):
                # Assume it's a list of records for a single table
                self.import_records_json(data, db_name)
            else:
                raise Exception("Invalid JSON format. Expected object or array.")
                
            self.main_app.set_status(f"Imported JSON file: {os.path.basename(file_path)}")
            
            # Database is automatically saved by the monkey-patched execute_command method
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing JSON file: {str(e)}")
            self.main_app.set_status(f"Error importing JSON file: {str(e)}")
    
    def import_database_json(self, data, db_name):
        """Import a full database structure from JSON"""
        try:
            success_tables = 0
            success_records = 0
            errors = []
            
            # Process each table
            for table_data in data.get("tables", []):
                table_name = table_data.get("name")
                if not table_name:
                    errors.append("Table missing name")
                    continue
                    
                # Get columns
                columns = table_data.get("columns", [])
                if not columns:
                    errors.append(f"Table {table_name} has no columns")
                    continue
                
                # Create the table
                try:
                    # Generate CREATE TABLE command
                    create_cmd = f"CREATE TABLE {table_name} ("
                    col_defs = []
                    
                    for col in columns:
                        if isinstance(col, dict):
                            col_name = col.get("name")
                            col_type = col.get("type", "VARCHAR")
                            constraints = " ".join(col.get("constraints", []))
                            
                            col_defs.append(f"{col_name} {col_type} {constraints}".strip())
                        else:
                            # Simple column name
                            col_defs.append(f"{col} VARCHAR")
                    
                    create_cmd += ", ".join(col_defs) + ")"
                    
                    # Execute create command
                    result = self.sqlvm.execute_command(create_cmd)
                    if "Error" in result:
                        errors.append(f"Error creating table {table_name}: {result}")
                        continue
                        
                    success_tables += 1
                    
                    # Import records if present
                    records = table_data.get("records", [])
                    if records:
                        # Get column names
                        col_names = [c.get("name") if isinstance(c, dict) else c for c in columns]
                        
                        # Insert each record
                        for record in records:
                            if len(record) != len(col_names):
                                errors.append(f"Record length mismatch in {table_name}")
                                continue
                                
                            # Format values
                            values = []
                            for val in record:
                                if val is None:
                                    values.append("NULL")
                                elif isinstance(val, str):
                                    values.append(f'"{val.replace('"', '""')}"')
                                else:
                                    values.append(str(val))
                            
                            # Insert command
                            insert_cmd = f"INSERT INTO {table_name} VALUES ({', '.join(values)})"
                            result = self.sqlvm.execute_command(insert_cmd)
                            
                            if "Error" in result:
                                errors.append(f"Error inserting into {table_name}: {result}")
                            else:
                                success_records += 1
                except Exception as e:
                    errors.append(f"Error processing table {table_name}: {str(e)}")
            
            # Show results
            if errors:
                error_message = "\n".join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_message += f"\n\n(and {len(errors) - 5} more errors)"
                
                messagebox.showwarning("Import Warnings", 
                    f"Created {success_tables} tables with {success_records} records.\n{len(errors)} errors occurred.\n\n{error_message}")
            else:
                messagebox.showinfo("Import Complete", 
                    f"Successfully imported {success_tables} tables with {success_records} records")
                
        except Exception as e:
            raise Exception(f"Failed to import database structure: {str(e)}")
    
    def import_table_json(self, data):
        """Import a single table from JSON"""
        table_name = data.get("table")
        columns = data.get("columns", [])
        records = data.get("records", [])
        
        if not table_name:
            raise Exception("Missing table name in JSON")
            
        if not columns:
            raise Exception("Missing columns in JSON")
            
        # Create table
        create_cmd = f"CREATE TABLE {table_name} ("
        col_defs = []
        
        for col in columns:
            if isinstance(col, dict):
                col_name = col.get("name")
                col_type = col.get("type", "VARCHAR")
                constraints = " ".join(col.get("constraints", []))
                
                col_defs.append(f"{col_name} {col_type} {constraints}".strip())
            else:
                # Simple column name
                col_defs.append(f"{col} VARCHAR")
        
        create_cmd += ", ".join(col_defs) + ")"
        
        # Execute create command
        result = self.sqlvm.execute_command(create_cmd)
        if "Error" in result:
            raise Exception(f"Error creating table: {result}")
            
        # Insert records
        success_count = 0
        errors = []
        
        # Get column names
        col_names = [c.get("name") if isinstance(c, dict) else c for c in columns]
        
        # Insert each record
        for record in records:
            if len(record) != len(col_names):
                errors.append("Record length mismatch")
                continue
                
            # Format values
            values = []
            for val in record:
                if val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    values.append(f'"{val.replace('"', '""')}"')
                else:
                    values.append(str(val))
            
            # Insert command
            insert_cmd = f"INSERT INTO {table_name} VALUES ({', '.join(values)})"
            result = self.sqlvm.execute_command(insert_cmd)
            
            if "Error" in result:
                errors.append(f"Error inserting: {result}")
            else:
                success_count += 1
        
        # Show results
        if errors:
            error_message = "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_message += f"\n\n(and {len(errors) - 5} more errors)"
            
            messagebox.showwarning("Import Warnings", 
                f"Imported table '{table_name}' with {success_count}/{len(records)} records.\n{len(errors)} errors occurred.\n\n{error_message}")
        else:
            messagebox.showinfo("Import Complete", 
                f"Successfully imported table '{table_name}' with {success_count} records")
    
    def import_records_json(self, data, db_name):
        """Import records from a JSON array"""
        if not data:
            raise Exception("Empty records array")
            
        # Ask for table name
        table_dialog = tk.Toplevel(self.parent)
        table_dialog.title("Import Records")
        table_dialog.geometry("400x200")
        table_dialog.transient(self.parent)
        table_dialog.grab_set()
        
        ttk.Label(table_dialog, text="Enter table name:").pack(pady=5)
        table_var = tk.StringVar()
        ttk.Entry(table_dialog, textvariable=table_var).pack(fill=tk.X, padx=20, pady=5)
        
        # Create new table or use existing
        create_table_var = tk.BooleanVar()
        create_table_var.set(True)
        ttk.Radiobutton(
            table_dialog, 
            text="Create new table", 
            variable=create_table_var, 
            value=True
        ).pack(anchor=tk.W, padx=20, pady=2)
        
        ttk.Radiobutton(
            table_dialog, 
            text="Insert into existing table", 
            variable=create_table_var, 
            value=False
        ).pack(anchor=tk.W, padx=20, pady=2)
        
        def do_import_records():
            table_name = table_var.get().strip()
            if not table_name:
                messagebox.showerror("Error", "Please enter a table name")
                return
                
            # Close dialog
            table_dialog.destroy()
            
            try:
                # Check if we need to create the table
                if create_table_var.get():
                    # Infer columns from first record
                    if not data[0] or not isinstance(data[0], dict):
                        raise Exception("First record must be an object to infer table structure")
                        
                    # Get column names from first record
                    columns = list(data[0].keys())
                    
                    # Create table
                    create_cmd = f"CREATE TABLE {table_name} ("
                    col_defs = [f"{col} VARCHAR" for col in columns]
                    create_cmd += ", ".join(col_defs) + ")"
                    
                    result = self.sqlvm.execute_command(create_cmd)
                    if "Error" in result:
                        raise Exception(f"Error creating table: {result}")
                
                # Insert records
                success_count = 0
                errors = []
                
                for record in data:
                    if isinstance(record, dict):
                        # Format values
                        columns = list(record.keys())
                        values = []
                        for val in record.values():
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, str):
                                values.append(f'"{val.replace('"', '""')}"')
                            else:
                                values.append(str(val))
                        
                        # Insert command with column names
                        insert_cmd = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)})"
                    elif isinstance(record, list):
                        # Format values
                        values = []
                        for val in record:
                            if val is None:
                                values.append("NULL")
                            elif isinstance(val, str):
                                values.append(f'"{val.replace('"', '""')}"')
                            else:
                                values.append(str(val))
                        
                        # Insert command without column names
                        insert_cmd = f"INSERT INTO {table_name} VALUES ({', '.join(values)})"
                    else:
                        errors.append("Record must be object or array")
                        continue
                    
                    result = self.sqlvm.execute_command(insert_cmd)
                    
                    if "Error" in result:
                        errors.append(f"Error inserting: {result}")
                    else:
                        success_count += 1
                
                # Show results
                if errors:
                    error_message = "\n".join(errors[:5])
                    if len(errors) > 5:
                        error_message += f"\n\n(and {len(errors) - 5} more errors)"
                    
                    messagebox.showwarning("Import Warnings", 
                        f"Imported {success_count}/{len(data)} records into '{table_name}'.\n{len(errors)} errors occurred.\n\n{error_message}")
                else:
                    messagebox.showinfo("Import Complete", 
                        f"Successfully imported {success_count} records into '{table_name}'")
                    
                # Update database tree
                self.update_database_tree()
                    
                # Database is automatically saved by the monkey-patched execute_command method
                    
            except Exception as e:
                messagebox.showerror("Import Error", f"Error importing records: {str(e)}")
        
        # Import button
        ttk.Button(table_dialog, text="Import", command=do_import_records).pack(pady=10)
    
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
