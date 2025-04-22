#!/usr/bin/env python3
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Run setup_assets to ensure directory exists
from setup_assets import setup_assets
setup_assets()

import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk

# Import from the modules
try:
    # Make sure we're importing the correct way
    from src.gui.main_app import SQLVMApp
    print("Successfully imported SQLVMApp")
    
    # Import SQLVMExporter and SQLVMImporter
    from src.export import SQLVMExporter
    from src.importer import SQLVMImporter
    print("Successfully imported SQLVMExporter and SQLVMImporter")
except Exception as e:
    print(f"Error importing required modules: {e}")
    sys.exit(1)

def main():
    root = tk.Tk()
    root.title("SQL VM Manager")
    
    # Set app icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'quail.ico')
    try:
        root.iconbitmap(icon_path)
        # Make sure the window is treated as a normal application window
        root.wm_attributes('-toolwindow', False)
        # On Windows, ensure icon appears in taskbar
        if os.name == 'nt':
            root.wm_attributes('-topmost', False)
        print(f"Successfully loaded icon from: {icon_path}")
    except tk.TclError as e:
        print(f"Could not load icon: {e}")
    
    app = SQLVMApp(root)
    
    # Add top-level menu for export functionality
    menu_bar = tk.Menu(root)
    
    # File menu
    file_menu = tk.Menu(menu_bar, tearoff=0)
    
    # Import submenu
    import_menu = tk.Menu(file_menu, tearoff=0)
    import_menu.add_command(label="Import SQL File", 
                          command=lambda: import_file(app, "sql"))
    import_menu.add_command(label="Import JSON File", 
                          command=lambda: import_file(app, "json"))
    file_menu.add_cascade(label="Import", menu=import_menu)
    
    # Export submenu
    export_menu = tk.Menu(file_menu, tearoff=0)
    
    # Export database options
    current_db_var = lambda: app.current_db  # Function to get current DB at call time
    export_menu.add_command(label="Export Current Database to SQL", 
                          command=lambda: export_db(app, current_db_var(), "sql"))
    export_menu.add_command(label="Export Current Database to JSON", 
                          command=lambda: export_db(app, current_db_var(), "json"))
    export_menu.add_separator()
    export_menu.add_command(label="Export All Databases to SQL", 
                          command=lambda: export_db(app, None, "sql"))
    export_menu.add_command(label="Export All Databases to JSON", 
                          command=lambda: export_db(app, None, "json"))
    
    file_menu.add_cascade(label="Export", menu=export_menu)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    
    menu_bar.add_cascade(label="File", menu=file_menu)
    
    # Help menu
    help_menu = tk.Menu(menu_bar, tearoff=0)
    help_menu.add_command(label="About", command=lambda: show_about(root))
    menu_bar.add_cascade(label="Help", menu=help_menu)
    
    root.config(menu=menu_bar)
    
    root.mainloop()

def import_file(app, file_type):
    """Handle importing database from a file"""
    # Define file types for dialog
    if file_type == "sql":
        filetypes = [("SQL Files", "*.sql"), ("All Files", "*.*")]
        title = "Select SQL file to import"
    else:
        filetypes = [("JSON Files", "*.json"), ("All Files", "*.*")]
        title = "Select JSON file to import"
    
    # Get the path to the database directory
    db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'db'))
    
    # Get file path
    file_path = filedialog.askopenfilename(
        initialdir=db_dir,
        filetypes=filetypes,
        title=title
    )
    
    if not file_path:
        return
    
    # Get database options
    databases = list(app.sqlvm.databases.keys())
    
    # Create a dialog for database selection or creation
    db_dialog = tk.Toplevel(app.root)
    db_dialog.title(f"Import {file_type.upper()} File")
    db_dialog.geometry("400x200")
    db_dialog.transient(app.root)
    db_dialog.grab_set()
    
    # Try to set dialog icon
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'quail.ico')
        if os.path.exists(icon_path):
            db_dialog.iconbitmap(icon_path)
    except Exception:
        pass
    
    # Database selection options frame
    tk.Label(db_dialog, text="Select database to import into:").pack(pady=5)
    
    # Database selection variable
    db_var = tk.StringVar()
    if databases:
        db_var.set(databases[0]) 
    
    # Create New Database option
    create_new_var = tk.BooleanVar(value=False)
    
    # Function to toggle database selection
    def toggle_db_selection():
        if create_new_var.get():
            db_combo.config(state="disabled")
            new_db_entry.config(state="normal")
        else:
            db_combo.config(state="readonly")
            new_db_entry.config(state="disabled")
    
    # Database dropdown for existing databases
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
    
    # Function to handle import action
    def do_import():
        try:
            if create_new_var.get():
                # Create new database
                db_name = new_db_var.get().strip()
                if not db_name:
                    messagebox.showerror("Error", "Please enter a database name")
                    return
                
                result = app.sqlvm.create_database(db_name)
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
            
            # Import the file using our importer class
            if file_type == "sql":
                # First validate the SQL file
                validation = SQLVMImporter.validate_sql_file(file_path)
                
                if not validation["valid"]:
                    messagebox.showerror("SQL File Error", f"Invalid SQL file: {validation['error']}")
                    return
                
                # Show a message with stats about the SQL file
                if validation["stats"]["problematic"]:
                    issues_msg = "\n".join([f"• {issue}" for issue in validation["stats"]["issues"]])
                    if not messagebox.askyesno("SQL File Warning", 
                                              f"The SQL file contains commands that may not be fully supported:\n\n{issues_msg}\n\nDo you want to proceed anyway?"):
                        return
                
                # Proceed with import
                message, error_count, success_count = SQLVMImporter.import_from_sql(app.sqlvm, db_name, file_path)
                
                if error_count > 0:
                    messagebox.showwarning("Import Warnings", message)
                else:
                    messagebox.showinfo("Import Complete", message)
            else:
                message, error_count, success_count = SQLVMImporter.import_from_json(app.sqlvm, db_name, file_path)
                
                if error_count > 0:
                    messagebox.showwarning("Import Warnings", message)
                else:
                    messagebox.showinfo("Import Complete", message)
            
            # Update UI
            app.browser.update_database_tree()
            app.set_status(f"Imported {file_type.upper()} file: {os.path.basename(file_path)}")
            
            # Set the current database to the one we just imported to
            app.select_database(db_name)
            
            # Refresh all components
            app.refresh_all()
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Error during import: {str(e)}")
    
    # Import button
    ttk.Button(db_dialog, text="Import", command=do_import).pack(pady=10)

def export_db(app, db_name, format_type):
    """Handle exporting database to a file"""
    if db_name is None and app.current_db is not None:
        db_name = app.current_db
    
    if format_type == "sql" and db_name is None:
        # Exporting all databases to SQL
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*.*")],
            initialfile="all_databases.sql"
        )
        if file_path:
            try:
                message, path = SQLVMExporter.export_to_sql(app.sqlvm, None, file_path)
                app.set_status(message)
                messagebox.showinfo("Export Complete", message)
            except Exception as e:
                error_msg = f"Error exporting databases: {str(e)}"
                app.set_status(error_msg)
                messagebox.showerror("Export Error", error_msg)
    
    elif format_type == "json" and db_name is None:
        # Exporting all databases to JSON
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile="all_databases.json"
        )
        if file_path:
            try:
                message, path = SQLVMExporter.export_to_json(app.sqlvm, None, file_path)
                app.set_status(message)
                messagebox.showinfo("Export Complete", message)
            except Exception as e:
                error_msg = f"Error exporting databases: {str(e)}"
                app.set_status(error_msg)
                messagebox.showerror("Export Error", error_msg)
    
    elif db_name is not None:
        # Exporting a specific database
        extension = ".sql" if format_type == "sql" else ".json"
        ft_label = "SQL Files" if format_type == "sql" else "JSON Files"
        ft_pattern = "*.sql" if format_type == "sql" else "*.json"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=extension,
            filetypes=[(ft_label, ft_pattern), ("All Files", "*.*")],
            initialfile=f"{db_name}{extension}"
        )
        
        if file_path:
            try:
                if format_type == "sql":
                    message, path = SQLVMExporter.export_to_sql(app.sqlvm, db_name, file_path)
                else:
                    message, path = SQLVMExporter.export_to_json(app.sqlvm, db_name, file_path)
                
                app.set_status(message)
                messagebox.showinfo("Export Complete", message)
            except Exception as e:
                error_msg = f"Error exporting database: {str(e)}"
                app.set_status(error_msg)
                messagebox.showerror("Export Error", error_msg)
    else:
        messagebox.showinfo("No Database Selected", "Please select a database first.")

def show_about(root):
    """Show the about dialog"""
    messagebox.showinfo(
        "About SQL VM Manager",
        "SQL VM Manager\n\n"
        "Version: 1.0\n"
        "A simple SQL database simulator for learning SQL concepts.\n\n"
        "Developed by:\n"
        "Group 2B\n"
        "Members:\n"
        "Cano, Kurt Daniel S.\n"
        "Caram II, Mike Rufino J.\n"
        "Dantes, Joshua Gabriel P.\n"
        "Villanueva, Jasper P."
    )

if __name__ == "__main__":
    main()
