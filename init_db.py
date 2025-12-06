import sqlite3

def init_db():
    # Ceate the database file
    connection = sqlite3.connect('finance.db')
    cursor = connection.cursor()

    # Open the schema file and execute the SQL commands
    with open('schema.sql', 'r') as f:
        schema = f.read()
        cursor.executescript(schema)

    connection.commit()
    connection.close()
    print("Success! finance.db has been created with empty tables.")

if __name__ == "__main__":
    init_db()