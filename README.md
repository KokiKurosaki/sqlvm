# SQLVM

SQLVM is a lightweight SQL database virtual machine implemented in Python. It provides a simple in-memory SQL database system that supports many common SQL operations.

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

## Features

- Multiple database support
- Tables with various data types (INT, TEXT, VARCHAR, FLOAT, BOOL)
- Primary key and unique constraints
- AUTO_INCREMENT column support
- Basic SQL commands: CREATE, INSERT, SELECT, UPDATE, DELETE
- Graphical user interface with command history

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