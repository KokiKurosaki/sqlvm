import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
from datetime import datetime

# Add the parent directory to the Python path so we can import sqlvm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sqlvm import SQLVM

class UserManagementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("User Management System")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Initialize SQL VM
        self.vm = SQLVM()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create tabs
        self.create_user_tab()
        self.create_view_tab()
        self.create_sql_tab()
        
        # Set up style
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 11))
        self.style.configure('TEntry', font=('Arial', 11))
        
        # Status bar at bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Flag to prevent recursion
        self.initializing = False
        
        # Setup database after GUI is created
        try:
            self.setup_database()
            # Load initial user data
            self.load_users()
        except Exception as e:
            self.log_sql_result("ERROR", f"Initialization error: {str(e)}")
            self.status_var.set(f"Error during initialization: {str(e)}")
        
    def setup_database(self):
        """Set up the initial database and tables"""
        try:
            # Create database
            result = self.vm.execute_command("CREATE DATABASE usersdb")
            self.log_sql_result("CREATE DATABASE usersdb", result)
            
            # Use database
            result = self.vm.execute_command("USE usersdb")
            self.log_sql_result("USE usersdb", result)
            
            # Create users table 
            create_table_cmd = """
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY,
                username VARCHAR,
                email VARCHAR,
                role VARCHAR,
                created_at VARCHAR
            )
            """
            result = self.vm.execute_command(create_table_cmd)
            self.log_sql_result(create_table_cmd, result)
            
            # Check if table was created successfully
            tables_result = self.vm.execute_command("SHOW TABLES")
            self.log_sql_result("SHOW TABLES", tables_result)
            
            if "users" in tables_result:
                # Insert some demo users
                demo_users = [
                    'INSERT INTO users VALUES (NULL, "admin", "admin@example.com", "Administrator", "2023-11-01")',
                    'INSERT INTO users VALUES (NULL, "john", "john@example.com", "User", "2023-11-02")',
                    'INSERT INTO users VALUES (NULL, "jane", "jane@example.com", "Editor", "2023-11-03")'
                ]
                
                for cmd in demo_users:
                    result = self.vm.execute_command(cmd)
                    self.log_sql_result(cmd, result)
                    
        except Exception as e:
            self.log_sql_result("ERROR", f"Exception: {str(e)}")
            messagebox.showerror("Database Error", f"Failed to set up database: {str(e)}")
    
    def log_sql_result(self, command, result):
        """Log SQL commands and their results to the SQL console tab"""
        if hasattr(self, 'sql_result'):
            self.sql_result.insert(tk.END, f"> {command}\n{result}\n\n")
            self.sql_result.see(tk.END)
    
    def create_user_tab(self):
        """Create the tab for adding users"""
        add_tab = ttk.Frame(self.notebook)
        self.notebook.add(add_tab, text="Add User")
        
        # Form for adding users
        form_frame = ttk.LabelFrame(add_tab, text="Add New User", padding="10")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.username_var, width=30).grid(row=0, column=1, pady=5, padx=5)
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_var, width=30).grid(row=1, column=1, pady=5, padx=5)
        
        # Role
        ttk.Label(form_frame, text="Role:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar()
        roles = ["User", "Editor", "Administrator"]
        ttk.Combobox(form_frame, textvariable=self.role_var, values=roles, state="readonly").grid(row=2, column=1, pady=5, padx=5)
        self.role_var.set("User")
        
        # Add User Button
        ttk.Button(form_frame, text="Add User", command=self.add_user).grid(row=3, column=1, pady=10, padx=5, sticky=tk.E)
        
        # Clear Button
        ttk.Button(form_frame, text="Clear Form", command=self.clear_form).grid(row=3, column=0, pady=10, padx=5, sticky=tk.W)
        
    def create_view_tab(self):
        """Create the tab for viewing users"""
        view_tab = ttk.Frame(self.notebook)
        self.notebook.add(view_tab, text="Manage Users")
        
        # Frame for the treeview
        tree_frame = ttk.Frame(view_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for displaying users
        self.tree = ttk.Treeview(tree_frame, columns=("ID", "Username", "Email", "Role", "Created"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Username", text="Username")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Role", text="Role")
        self.tree.heading("Created", text="Created")
        
        self.tree.column("ID", width=50)
        self.tree.column("Username", width=150)
        self.tree.column("Email", width=200)
        self.tree.column("Role", width=100)
        self.tree.column("Created", width=100)
        
        # Add scrollbar for the treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame for buttons
        button_frame = ttk.Frame(view_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Refresh button
        ttk.Button(button_frame, text="Refresh", command=self.load_users).pack(side=tk.LEFT, padx=5)
        
        # Delete button
        ttk.Button(button_frame, text="Delete Selected", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        
    def create_sql_tab(self):
        """Create the tab for direct SQL access"""
        sql_tab = ttk.Frame(self.notebook)
        self.notebook.add(sql_tab, text="SQL Console")
        
        # Text widget for SQL input
        ttk.Label(sql_tab, text="Enter SQL Command:").pack(anchor=tk.W, padx=10, pady=5)
        self.sql_input = scrolledtext.ScrolledText(sql_tab, height=5)
        self.sql_input.pack(fill=tk.X, padx=10, pady=5)
        
        # Execute button 
        ttk.Button(sql_tab, text="Execute SQL", command=self.execute_sql).pack(anchor=tk.E, padx=10, pady=5)
        
        # Result area
        ttk.Label(sql_tab, text="Results:").pack(anchor=tk.W, padx=10, pady=5)
        self.sql_result = scrolledtext.ScrolledText(sql_tab, height=15)
        self.sql_result.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
    def add_user(self):
        """Add a new user to the database"""
        username = self.username_var.get().strip()
        email = self.email_var.get().strip()
        role = self.role_var.get()
        
        # Validation
        if not username:
            messagebox.showerror("Error", "Username is required")
            return
        
        if not email:
            messagebox.showerror("Error", "Email is required")
            return
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Invalid email format")
            return
        
        # Get current date for timestamp
        created_at = datetime.now().strftime("%Y-%m-%d")
        
        # Insert into database
        result = self.vm.execute_command(f'INSERT INTO users VALUES (NULL, "{username}", "{email}", "{role}", "{created_at}")')
        
        if "Error" in result:
            messagebox.showerror("Database Error", result)
        else:
            messagebox.showinfo("Success", "User added successfully")
            self.clear_form()
            self.load_users()
            self.status_var.set(f"Added user: {username}")
            
    def clear_form(self):
        """Clear the add user form"""
        self.username_var.set("")
        self.email_var.set("")
        self.role_var.set("User")
        
    def load_users(self):
        """Load users from database into the treeview"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:    
            # Get users from database
            result = self.vm.execute_command("USE usersdb")
            result = self.vm.execute_command("SELECT * FROM users")
            self.log_sql_result("SELECT * FROM users", result)
            
            # Parse the result string into rows
            if "No tables found" not in result and "+----" in result:
                lines = result.strip().split("\n")
                # Skip header and separator lines
                data_lines = [line for line in lines if line.startswith("|") and not line.startswith("| id")]
                
                # Extract data from each line
                for line in data_lines:
                    # Skip separator lines
                    if "+" in line and "-" in line:
                        continue
                        
                    # Split by | and remove empty first and last elements
                    parts = [part.strip() for part in line.split("|")[1:-1]]
                    if len(parts) >= 5:  # Ensure we have all columns
                        self.tree.insert("", "end", values=parts)
                
                self.status_var.set(f"Loaded {len(self.tree.get_children())} users")
            else:
                self.status_var.set("No users found or table does not exist")
        except Exception as e:
            self.log_sql_result("ERROR", f"Error loading users: {str(e)}")
            self.status_var.set(f"Error loading users: {str(e)}")
    
    def delete_user(self):
        """Delete the selected user"""
        selected_item = self.tree.selection()
        
        if not selected_item:
            messagebox.showinfo("Info", "Please select a user to delete")
            return
            
        user_id = self.tree.item(selected_item, "values")[0]
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user with ID {user_id}?")
        
        if confirm:
            result = self.vm.execute_command(f"DELETE FROM users WHERE id = {user_id}")
            if "Error" in result:
                messagebox.showerror("Database Error", result)
            else:
                self.load_users()
                self.status_var.set(f"Deleted user with ID: {user_id}")
    
    def execute_sql(self):
        """Execute the SQL command from the SQL tab"""
        sql_command = self.sql_input.get("1.0", tk.END).strip()
        
        if not sql_command:
            messagebox.showinfo("Info", "Please enter an SQL command")
            return
            
        # Execute the command
        result = self.vm.execute_command(sql_command)
        
        # Display the result
        self.sql_result.delete("1.0", tk.END)
        self.sql_result.insert(tk.END, result)
        
        # Update status
        self.status_var.set(f"Executed SQL command")
        
        # If the command might have changed user data, refresh the user list
        if any(keyword in sql_command.upper() for keyword in ["INSERT", "UPDATE", "DELETE"]):
            self.load_users()


def main():
    root = tk.Tk()
    try:
        app = UserManagementApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Unhandled error: {str(e)}")
        # If GUI is available, try to show error in messagebox
        try:
            messagebox.showerror("Fatal Error", f"An unrecoverable error occurred: {str(e)}")
        except:
            pass

if __name__ == "__main__":
    main()
