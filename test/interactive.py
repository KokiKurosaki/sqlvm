import sys
import os

# Add the parent directory to the Python path so we can import sqlvm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sqlvm import SQLVM

def main():
    """Simple interactive SQL shell"""
    vm = SQLVM()
    
    # Set up test database and table
    vm.execute_command("CREATE DATABASE db1")
    vm.execute_command("USE db1")
    vm.execute_command("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY, name TEXT)")
    print("Database db1 created with table users(id INT AUTO_INCREMENT PRIMARY, name TEXT)")
    
    print("Enter SQL commands (type 'exit' to quit):")
    while True:
        try:
            command = input("> ")
            if command.lower() == 'exit':
                break
            result = vm.execute_command(command)
            print(result)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
