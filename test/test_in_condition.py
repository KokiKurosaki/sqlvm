import os
import sys
# Add the parent directory to the Python path so we can import sqlvm
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sqlvm import SQLVM

vm = SQLVM()

# Set up test environment
print(vm.execute_command("CREATE DATABASE test_db;"))
print(vm.execute_command("USE test_db;"))
print(vm.execute_command("CREATE TABLE users (id INT PRIMARY KEY, name TEXT);"))
print(vm.execute_command("INSERT INTO users VALUES (1, 'Alice');"))
print(vm.execute_command("INSERT INTO users VALUES (2, 'Bob');"))
print(vm.execute_command("INSERT INTO users VALUES (3, 'Charlie');"))

# Test IN condition
print("--- IN Condition Test ---")
print(vm.execute_command("SELECT * FROM users WHERE id IN (1, 3);"))
print(vm.execute_command("SELECT * FROM users WHERE id IN (2)"))
print(vm.execute_command("SELECT * FROM users WHERE id IN ()"))  # Empty list
print(vm.execute_command("SELECT * FROM users WHERE id IN ('Alice', 'Bob')"))  # Invalid column