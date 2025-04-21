import sys
import os

# Add the parent directory to the Python path so we can import sqlvm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sqlvm import SQLVM

def run_test():
    """
    Test function to demonstrate SQLVM functionality with a pre-configured
    database (db1) and table (users with id INT AUTO_INCREMENT PRIMARY, name TEXT)
    """
    # Create a new SQL VM instance
    vm = SQLVM()
    
    # Set up the test environment
    print("Setting up test environment...")
    print(vm.execute_command("CREATE DATABASE db1"))
    print(vm.execute_command("USE db1"))
    print(vm.execute_command("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY, name TEXT)"))
    
    # Show initial state
    print("\n--- Initial State ---")
    print(vm.execute_command("SELECT * FROM users"))
    
    # Insert some test data
    print("\n--- Inserting Data ---")
    print(vm.execute_command("INSERT INTO users VALUES (NULL, \"Alice\")"))
    print(vm.execute_command("INSERT INTO users VALUES (NULL, \"Bob\")"))
    print(vm.execute_command("INSERT INTO users VALUES (NULL, \"Charlie\")"))
    
    # Show data after insertions
    print("\n--- After Insertions ---")
    print(vm.execute_command("SELECT * FROM users"))
    
    # Test UNIQUE/PRIMARY KEY constraint
    print("\n--- Testing PRIMARY KEY constraint ---")
    print(vm.execute_command("INSERT INTO users VALUES (2, \"Duplicate\")"))
    
    # Delete a record
    print("\n--- Deleting a Record ---")
    print(vm.execute_command("DELETE FROM users WHERE id = 2"))
    print(vm.execute_command("SELECT * FROM users"))
    
    # Insert with specific columns
    print("\n--- Insert with Specific Columns ---")
    print(vm.execute_command("INSERT INTO users (name) VALUES (\"David\")"))
    print(vm.execute_command("SELECT * FROM users"))
    
    # Update a record
    print("\n--- Updating a Record ---")
    print(vm.execute_command("UPDATE users SET name = \"Updated Charlie\" WHERE id = 3"))
    print(vm.execute_command("SELECT * FROM users"))
    
    print("\nTest completed.")

if __name__ == "__main__":
    run_test()
