#!/usr/bin/env python3
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import tkinter as tk

# Import directly from the gui module
try:
    from src.gui import SQLVMApp
    print("Successfully imported SQLVMApp")
except Exception as e:
    print(f"Error importing SQLVMApp: {e}")

def main():
    root = tk.Tk()
    app = SQLVMApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
