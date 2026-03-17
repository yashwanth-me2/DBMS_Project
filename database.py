import sqlite3

def connect_db():
    conn = sqlite3.connect("hospital.db")
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER
    )
    """)

    conn.commit()
    conn.close()

def insert_patient(name, age):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO patients (name, age) VALUES (?, ?)", (name, age))

    conn.commit()
    conn.close()