import sys
import os

# Add the parent directory to the Python path so we can import SQLVM
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sqlvm import SQLVM

# Initialize the SQLVM instance
vm = SQLVM()

# Test setup
print(vm.execute_command("CREATE DATABASE test_db;"))
print(vm.execute_command("USE test_db;"))
print(vm.execute_command("CREATE TABLE users (id INT PRIMARY KEY, name TEXT, age INT);"))
print(vm.execute_command("INSERT INTO users VALUES (1, 'Alice', 25);"))
print(vm.execute_command("INSERT INTO users VALUES (2, 'Bob', 30);"))
print(vm.execute_command("INSERT INTO users VALUES (3, 'Charlie', 35);"))
print(vm.execute_command("INSERT INTO users VALUES (4, 'David', 40);"))

# Test cases

# Test AND operator
print("Test AND operator:")
print(vm.execute_command("SELECT * FROM users WHERE age > 25 AND name LIKE 'C%';"))

# Test OR operator
print("Test OR operator:")
print(vm.execute_command("SELECT * FROM users WHERE age < 30 OR name = 'David';"))

# Test LIKE operator
print("Test LIKE operator:")
print(vm.execute_command("SELECT * FROM users WHERE name LIKE 'A%';"))

# Test IN operator
print("Test IN operator:")
print(vm.execute_command("SELECT * FROM users WHERE id IN (1, 3);"))

# Test parentheses in conditions
print("Test parentheses in conditions:")
print(vm.execute_command("SELECT * FROM users WHERE (age > 30 AND name LIKE 'D%') OR id = 1;"))

# Test subquery with IN
print("Test subquery with IN:")
print(vm.execute_command("SELECT * FROM users WHERE id IN (SELECT id FROM users WHERE age > 30);"))