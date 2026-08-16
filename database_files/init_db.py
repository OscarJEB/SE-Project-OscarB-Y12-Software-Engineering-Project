import sqlite3


def init_db():
    conn = sqlite3.connect(
        "database_files/database.db"
    )  # through python, SQL is being executed inside the database
    cursor = conn.cursor()

    # Core Films Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            media_type TEXT NOT NULL,
            format TEXT NOT NULL,
            collection_name TEXT,
            edition_notes TEXT,
            is_lent INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        ) 
    """)
    # this SQL command is labelling each column of the films table to include an id for the film, add the id for the user it belongs to, and include the title, media type, format, the name of the collection, and more notes for each film entry. It also includes a boolean that dictates whether it is lent or not.

    # Lending Log Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lent_films (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film_id INTEGER NOT NULL,
            borrower_name TEXT NOT NULL,
            date_lent DATE DEFAULT CURRENT_DATE,
            is_borrowed INTEGER DEFAULT 1,
            FOREIGN KEY (film_id) REFERENCES films (id)
        )
    """)
    # this database table includes the information for a film that is lent. it includes a new id for the lent film, the film's established film_id, the name of the borrower, date it was lent, and its current borrowed status
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
