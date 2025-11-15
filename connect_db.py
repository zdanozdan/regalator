import pyodbc

# --- Database Connection Details ---
# Replace the placeholder values with your actual connection information.
server = 'your_server_name.database.windows.net'  # or just 'localhost' for a local instance
database = 'your_database_name'
username = 'your_username'
password = 'your_password'

# --- Connection String ---
# Note: The 'DRIVER' value may vary. Common drivers include:
# - '{ODBC Driver 17 for SQL Server}'
# - '{SQL Server}'
# - '{ODBC Driver 18 for SQL Server}'
# - '{SQL Server Native Client 11.0}'

cnxn_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password}"
)

try:
    # --- Establish the Connection ---
    cnxn = pyodbc.connect(cnxn_string)
    cursor = cnxn.cursor()
    print("Connection to the database was successful!")

    # --- Execute a Sample Query ---
    # Replace 'your_table' with the name of a table in your database.
    cursor.execute("SELECT TOP 5 * FROM your_table")
    
    # --- Fetch and Print the Results ---
    rows = cursor.fetchall()
    for row in rows:
        print(row)

except pyodbc.Error as ex:
    # --- Handle Connection Errors ---
    sqlstate = ex.args[0]
    print(f"Connection failed! Error: {ex}")
    print(f"SQLSTATE: {sqlstate}")
    
finally:
    # --- Close the Connection ---
    if 'cnxn' in locals() and cnxn:
        cnxn.close()
        print("Database connection closed.")
