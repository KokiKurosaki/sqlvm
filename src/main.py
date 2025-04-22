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
    
    # Check if assets directory exists
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets')
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
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
    
    # Set app icon using the quail.ico file
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets', 'quail.ico'))
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
            # Ensure window is treated as a normal application window, not a tool window
            root.wm_attributes('-toolwindow', False)
            print(f"Loaded icon from: {icon_path}")
        except tk.TclError as e:
            print(f"Could not load icon: {e}")
    else:
        print(f"Icon file not found at: {icon_path}")
        
    # Initialize the GUI with our VM
    app = SQLGUI(root, vm)
    
    # Start the main event loop
    root.mainloop()

if __name__ == "__main__":
    main()
