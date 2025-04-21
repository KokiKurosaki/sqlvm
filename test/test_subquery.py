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
print(vm.execute_command("CREATE TABLE admins (id INT PRIMARY KEY, role TEXT);"))
print(vm.execute_command("INSERT INTO users VALUES (1, 'Alice');"))
print(vm.execute_command("INSERT INTO users VALUES (2, 'Bob');"))
print(vm.execute_command("INSERT INTO users VALUES (3, 'Charlie');"))
print(vm.execute_command("INSERT INTO admins VALUES (1, 'Manager');"))
print(vm.execute_command("INSERT INTO admins VALUES (3, 'Supervisor');"))

# Test subqueries
print("--- Subquery Test ---")

# Subquery 1: Simple IN condition
print(vm.execute_command("SELECT * FROM users WHERE id=2;"))

# Subquery 2: Subquery with no matching rows
print(vm.execute_command("SELECT * FROM users WHERE id IN (SELECT id FROM admins WHERE role = 'Nonexistent');"))

# Subquery 3: Subquery with all matching rows
print(vm.execute_command("SELECT * FROM users WHERE id IN (SELECT id FROM admins WHERE role IN ('Manager', 'Supervisor'));"))

# Subquery 4: Subquery with additional conditions
print(vm.execute_command("SELECT * FROM users WHERE id IN (SELECT id FROM admins WHERE role = 'Manager');"))

# Subquery 5: Nested subquery
print(vm.execute_command("SELECT * FROM users WHERE id IN (SELECT id FROM admins WHERE id IN (SELECT id FROM users));"))