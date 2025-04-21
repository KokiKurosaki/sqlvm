import tkinter as tk
from sqlvm import SQLVM
from gui import SQLGUI

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
