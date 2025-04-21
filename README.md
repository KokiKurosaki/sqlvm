# SQL Virtual Machine

A Python-based SQL simulator for educational purposes.

## Features

- In-memory SQL database system
- Support for creating and managing multiple databases
- GUI with command history and syntax highlighting
- Export databases to SQL and JSON formats

## Project Structure

```
sqlvm/
├── src/             # Source code
│   ├── __init__.py  # Package initialization
│   ├── sqlvm.py     # Core SQLVM implementation
│   ├── gui.py       # GUI interface
│   └── main.py      # Main entry point for GUI application
└── test/            # Test scripts
    ├── interactive.py  # Interactive SQL shell
    └── test_sqlvm.py   # Demonstration of SQLVM features
```

## SQL Examples

Here are some examples of SQL commands you can use:

### Database Operations

```sql
-- Create a new database
CREATE DATABASE school;

-- Use a database
USE school;

-- Show all databases
SHOW DATABASES;

-- Show all tables in current database
SHOW TABLES;

-- Drop a database
DROP DATABASE school;
```

### Table Operations

```sql
-- Create a table with proper SQL syntax
CREATE TABLE students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255),
  age INT,
  gpa FLOAT
);

-- Create a table with unique constraints
CREATE TABLE courses (
  course_id INT PRIMARY KEY,
  course_name VARCHAR(100) UNIQUE,
  credits INT
);
```

### Data Operations

```sql
-- Insert data
INSERT INTO students VALUES (1, "John Smith", "john@example.com", 20, 3.5);

-- Insert with specific columns
INSERT INTO students (name, age) VALUES ("Jane Doe", 22);

-- Select all columns
SELECT * FROM students;

-- Select specific columns
SELECT name, age FROM students;

-- Update data
UPDATE students SET age=21 WHERE name="John Smith";

-- Delete data
DELETE FROM students WHERE id=1;
```

### Data Export

```sql
-- Export current database to SQL file
EXPORT DATABASE school TO SQL;

-- Export all databases to JSON
EXPORT ALL TO JSON;
```

## Important Notes

1. Always specify lengths for VARCHAR columns: `VARCHAR(255)`
2. Use PRIMARY KEY instead of just PRIMARY
3. End your commands with a semicolon (optional but recommended)

## Installation

```
git clone https://github.com/yourusername/sqlvm.git
cd sqlvm
python -m sqlvm
```

## How to Run

### Graphical User Interface (GUI)

To run the full SQLVM application with graphical interface:

```bash
python -m src.main
```

This will open a GUI window where you can:
- Type SQL commands in the input field
- View command results in the output box
- Use the command history with up/down arrow keys
- Zoom text in and out using Ctrl+ and Ctrl-

### Interactive SQL Shell

To start a command-line interactive SQL shell with a pre-configured database (`db1`) and table (`users`):

```bash
python test/interactive.py
```

This will:
1. Create a database named `db1`
2. Create a table named `users` with columns `id` (INT AUTO_INCREMENT PRIMARY) and `name` (TEXT)
3. Start an interactive prompt where you can enter SQL commands
4. Type `exit` to quit the interactive shell

Example commands to try:
```sql
SELECT * FROM users;
INSERT INTO users VALUES (NULL, "John");
INSERT INTO users (name) VALUES ("Jane");
UPDATE users SET name = "John Doe" WHERE id = 1;
DELETE FROM users WHERE id = 2;
```

### Running Tests

To run a demonstration of SQLVM's features:

```bash
python test/test_sqlvm.py
```

This test script will:
1. Create a sample database and table
2. Insert test records
3. Demonstrate PRIMARY KEY constraint enforcement
4. Show how to delete records
5. Demonstrate inserting with specific columns
6. Show updating records
7. Output the results of each operation

## Using SQLVM in Your Code

You can import and use SQLVM in your own Python code:

```python
from src.sqlvm import SQLVM

# Create a new VM instance
vm = SQLVM()

# Execute SQL commands
vm.execute_command("CREATE DATABASE mydb")
vm.execute_command("USE mydb")
vm.execute_command("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY, name VARCHAR)")

# Insert data
vm.execute_command("INSERT INTO users VALUES (NULL, \"Alice\")")

# Query data
result = vm.execute_command("SELECT * FROM users")
print(result)
```