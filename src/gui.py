import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import tkinter.font as tkFont
import os

class SQLGUI:
    def __init__(self, root, vm):
        self.vm = vm
        self.root = root
        self.root.title("SQL Virtual Machine")

        # Set the background color of the root window
        self.root.configure(bg='black')

        # Configure root layout for responsiveness
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)  # Output box expands
        self.root.rowconfigure(2, weight=0)  # Input field stays fixed

        # Create Menu Bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File Menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        export_menu = tk.Menu(file_menu, tearoff=0)
        export_menu.add_command(label="Export Current DB to SQL", command=self.export_current_db_to_sql)
        export_menu.add_command(label="Export Current DB to JSON", command=self.export_current_db_to_json)
        export_menu.add_command(label="Export All DBs to SQL", command=self.export_all_dbs_to_sql)
        export_menu.add_command(label="Export All DBs to JSON", command=self.export_all_dbs_to_json)
        file_menu.add_cascade(label="Export", menu=export_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)

        # Help Menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="How to Use", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)

        # Custom font
        self.custom_font = tkFont.Font(family="Arial", size=14)

        # Custom font for the output box
        self.output_font = tkFont.Font(family="Courier New", size=14)

        # Output Text Box
        self.output_box = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, height=15, bg='black', fg='lightgreen', font=self.output_font, state="disabled"
        )
        self.output_box.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")

        # Entry widget for SQL commands
        self.command_entry = tk.Entry(self.root, width=50, bg='black', fg='white', insertbackground='white', font=self.custom_font)
        self.command_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Execute Button
        self.execute_button = tk.Button(self.root, text="Execute", bg='lightgreen', fg='black', font=self.custom_font, command=self.execute_sql)
        self.execute_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Make widgets expand with window resizing
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=0)
        self.root.rowconfigure(0, weight=1)

        # Command history
        self.command_history = []
        self.history_index = -1

        # Bind keys for interaction
        self.command_entry.bind("<Return>", self.execute_sql)
        self.command_entry.bind("<Up>", self.show_previous_command)
        self.command_entry.bind("<Down>", self.show_next_command)
        
        # Add zoom functionality
        self.root.bind("<Control-plus>", self.zoom_output_in)
        self.root.bind("<Control-minus>", self.zoom_output_out)

    def zoom_output_in(self, event=None):
        current_size = self.output_font.actual()["size"]
        self.output_font.configure(size=current_size + 2)

    def zoom_output_out(self, event=None):
        current_size = self.output_font.actual()["size"]
        if current_size > 8:  # Don't allow font to get too small
            self.output_font.configure(size=current_size - 2)

    def execute_sql(self, event=None):
        command = self.command_entry.get().strip()
        if command:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            result = self.vm.execute_command(command)
            self.output_box.config(state="normal")
            self.output_box.insert(tk.END, f"> {command}\n{result}\n\n")
            self.output_box.config(state="disabled")
            self.output_box.yview(tk.END)
            self.command_entry.delete(0, tk.END)

    def show_previous_command(self, event):
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])

    def show_next_command(self, event):
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.command_entry.delete(0, tk.END)

    def export_current_db_to_sql(self):
        if self.vm.current_db is None:
            messagebox.showerror("Error", "No database selected. Use USE database_name; first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql"), ("All files", "*.*")],
            initialfile=f"{self.vm.current_db}.sql"
        )
        if not file_path:
            return
        
        result = self.vm.export_to_sql(self.vm.current_db, file_path)
        self.output_box.config(state="normal")
        self.output_box.insert(tk.END, f"> Export current DB to SQL\n{result}\n\n")
        self.output_box.config(state="disabled")
        self.output_box.yview(tk.END)
    
    def export_current_db_to_json(self):
        if self.vm.current_db is None:
            messagebox.showerror("Error", "No database selected. Use USE database_name; first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"{self.vm.current_db}.json"
        )
        if not file_path:
            return
        
        result = self.vm.export_to_json(self.vm.current_db, file_path)
        self.output_box.config(state="normal")
        self.output_box.insert(tk.END, f"> Export current DB to JSON\n{result}\n\n")
        self.output_box.config(state="disabled")
        self.output_box.yview(tk.END)
    
    def export_all_dbs_to_sql(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[("SQL files", "*.sql"), ("All files", "*.*")],
            initialfile="all_databases.sql"
        )
        if not file_path:
            return
        
        result = self.vm.export_to_sql(None, file_path)
        self.output_box.config(state="normal")
        self.output_box.insert(tk.END, f"> Export all DBs to SQL\n{result}\n\n")
        self.output_box.config(state="disabled")
        self.output_box.yview(tk.END)
    
    def export_all_dbs_to_json(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="all_databases.json"
        )
        if not file_path:
            return
        
        result = self.vm.export_to_json(None, file_path)
        self.output_box.config(state="normal")
        self.output_box.insert(tk.END, f"> Export all DBs to JSON\n{result}\n\n")
        self.output_box.config(state="disabled")
        self.output_box.yview(tk.END)

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

    def show_about(self):
        about_text = (
            "SQLVM\n"
            "Version: 0.1\n"
            "Developed by:\n"
            "Group 2B\n"
            "Members:\n"
            "Cano, Kurt Daniel S.\n"
            "Caram II, Mike Rufino J.\n"
            "Dantes, Joshua Gabriel P.\n"
            "Villanueva, Jasper P.\n\n"
            "An in-memory SQL-like Virtual Machine. For educational purposes.\n"
            "Supports basic SQL commands: CREATE DATABASE, DROP DATABASE, USE, SHOW DATABASES, SHOW TABLES, CREATE, INSERT, SELECT, UPDATE, DELETE.\n"
            "Developed using Python and Tkinter for GUI.\n\n"
        )
        messagebox.showinfo("About", about_text)

# Add this section to make the file directly executable for testing
if __name__ == "__main__":
    from sqlvm import SQLVM
    root = tk.Tk()
    root.geometry("800x600")
    app = SQLGUI(root, SQLVM())
    root.mainloop()
