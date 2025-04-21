import tkinter as tk
import sys
import os

# Add proper import handling depending on how the script is run
if __name__ == "__main__":
    # When run directly, use absolute imports
    # Add parent directory to path so we can import the src package
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.sqlvm import SQLVM
    from src.gui import SQLGUI
else:
    # When imported as part of the package, use relative imports
    from .sqlvm import SQLVM
    from .gui import SQLGUI

def main():
    # Create an instance of the SQL Virtual Machine
    vm = SQLVM()
    
    # Create the root Tkinter window
    root = tk.Tk()
    root.title("SQL Virtual Machine - Interactive SQL Environment")
    root.geometry("1000x700")
    root.minsize(800, 600)
    
    # Set app icon if available
    try:
        root.iconbitmap("sql_icon.ico")
    except tk.TclError:
        pass
        
    # Initialize the GUI with our VM
    app = SQLGUI(root, vm)
    
    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()
