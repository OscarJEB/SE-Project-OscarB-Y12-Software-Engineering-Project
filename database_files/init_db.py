import sqlite3


def init_db():
    conn = sqlite3.connect("database_files/database.db")
    # through python, SQL is being executed inside the database
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            pin TEXT NOT NULL
        )
    """)

    # Finds how many users there are and creates two if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO users (username, pin) VALUES (?, ?)
        """,
            [("Oscar", "7777"), ("Steve", "1234")],
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
