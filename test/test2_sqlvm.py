import os
import sys
# Add the parent directory to the Python path so we can import sqlvm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Import the SQLVM class from the src.sqlvm module      

from src.sqlvm import SQLVM

# Initialize the SQLVM
vm = SQLVM()

# Example commands to test
commands = [
    "CREATE DATABASE test_db;",
    "USE test_db;",
    "CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name TEXT, age INT);",
    "INSERT INTO users VALUES (1, 'Alice');",
    "INSERT INTO users VALUES (2, 'Bob');",
    "SELECT * FROM users;",
    "ALTER TABLE users ADD email TEXT;",
    "SELECT * FROM users;",
    "DROP DATABASE test_db;"
]

# Execute each command
for command in commands:
    print(f"Executing: {command}")
    vm.execute_command(command)
    print("-" * 50)