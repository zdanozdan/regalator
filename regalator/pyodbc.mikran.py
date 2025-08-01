import pyodbc

connection_string = (
    'DRIVER={/usr/local/lib/libmsodbcsql.17.dylib};'
    'SERVER=192.168.0.140,1433;'
    'DATABASE=MIKRAN;'
    'UID=sa;'
    'PWD=zdanozdan123;'
    'Encrypt=No;'
    'TrustServerCertificate=Yes'
)

try:
    conn = pyodbc.connect(connection_string)
    print("Successfully connected to SQL Server with pyodbc!")
    conn.close()
except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"Failed to connect with pyodbc. Error: {ex}")
    print(f"SQLSTATE: {sqlstate}")
