#!/usr/bin/env python3
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Run setup_assets to ensure directory exists
from setup_assets import setup_assets
setup_assets()

import tkinter as tk

# Import from the gui.main_app module
try:
    # Make sure we're importing the correct way
    from src.gui.main_app import SQLVMApp
    print("Successfully imported SQLVMApp")
except Exception as e:
    print(f"Error importing SQLVMApp: {e}")
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
    root.mainloop()

if __name__ == "__main__":
    main()
