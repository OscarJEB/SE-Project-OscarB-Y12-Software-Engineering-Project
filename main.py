from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from flask_cors import CORS
import sqlite3
from datetime import datetime
import csv

app = Flask(__name__)
CORS(app)
app.secret_key = "media_tracker"


# connects to sqlite db and lets us grab columns by name
def get_db_connection():
    conn = sqlite3.connect("database_files/database.db")
    conn.row_factory = sqlite3.Row  # access columns by name in jinja templates
    return conn


# landing page / profile chooser
@app.route("/index.html", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
@app.route("/")
def home():
    # redirect straight to collection if already logged in
    if "user_id" in session:
        return redirect("/collection")

    conn = get_db_connection()
    users = conn.execute("SELECT id, username FROM users").fetchall()
    conn.close()

    error = request.args.get("error")
    return render_template("index.html", users=users, error=error)


# logs user in with 4-digit pin
@app.route("/login", methods=["POST"])
def login():
    user_id = request.form.get("user_id")
    pin = request.form.get("pin", "").strip()

    if not user_id or not pin:
        return redirect("/?error=missing_info")

    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()

    if user:
        user_dict = dict(user)
        # check pin or fallback to password column
        user_pin = user_dict.get("pin") or user_dict.get("password")

        if user_pin and str(user_pin).strip() == pin:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/collection")

    return redirect("/?error=invalid_pin")


# displays user collection and handles search
@app.route("/collection")
def collection():
    if "user_id" not in session:
        return redirect("/")

    search_query = request.args.get("q", "").strip()
    conn = get_db_connection()

    # filter films if user typed something in search
    if search_query:
        query_str = "%" + search_query + "%"
        films_raw = conn.execute(
            """
            SELECT f.*, f.lent_to_name AS borrower_name 
            FROM films f
            WHERE f.user_id = ? AND (
                f.title LIKE ? OR 
                f.format LIKE ? OR 
                f.collection_name LIKE ? OR 
                f.notes LIKE ?
            )
            """,
            (session["user_id"], query_str, query_str, query_str, query_str),
        ).fetchall()
    else:
        # grab all films owned by logged in user
        films_raw = conn.execute(
            """
            SELECT f.*, f.lent_to_name AS borrower_name 
            FROM films f
            WHERE f.user_id = ?
            """,
            (session["user_id"],),
        ).fetchall()

    films = [dict(film) for film in films_raw]
    conn.close()

    error = request.args.get("error")
    return render_template(
        "collection.html",
        films=films,
        username=session.get("username"),
        search_query=search_query,
        error=error,
    )


# adds a single film manually
@app.route("/add_film", methods=["POST"])
def add_film():
    if "user_id" not in session:
        return redirect("/")

    title = request.form["title"]
    format_type = request.form["format"]
    collection_name = request.form.get("collection_name", "")
    notes = request.form.get("edition_notes", "")

    # automatically tag as digital or physical based on format
    digital_formats = ["Apple TV", "Prime Video", "YouTube", "Google Play"]
    media_type = "Digital" if format_type in digital_formats else "Physical"

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO films (user_id, title, media_type, format, collection_name, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (session["user_id"], title, media_type, format_type, collection_name, notes),
    )
    conn.commit()
    conn.close()
    return redirect("/collection")


# rearranges the date to day, month, year
@app.template_filter("format_date")
def format_date(value):
    if not value:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%d %b %Y"):
        try:
            dt = datetime.strptime(str(value).strip(), fmt)
            return dt.strftime("%d %b %Y")
        except ValueError:
            pass
    return value


# shows page to lend a film
@app.route("/lend/<int:film_id>")
def lend_page(film_id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    film = conn.execute(
        "SELECT * FROM films WHERE id = ? AND user_id = ?",
        (film_id, session["user_id"]),
    ).fetchone()
    conn.close()

    if not film:
        return redirect("/collection")

    return render_template("lend.html", film=film)


# process lending out a film
@app.route("/lend_film/<int:film_id>", methods=["POST"])
def lend_film(film_id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()

    film = conn.execute(
        "SELECT media_type FROM films WHERE id = ? AND user_id = ?",
        (film_id, session["user_id"]),
    ).fetchone()

    # block digital copies from being lent
    if film and film["media_type"] == "Digital":
        conn.close()
        return redirect("/collection?error=digital_cannot_be_lent")

    borrower_name = request.form.get("borrower_name", "").strip()
    date_lent = datetime.now().strftime("%d %b %Y")

    conn.execute(
        """
        UPDATE films 
        SET is_lent = 1, 
            lent_to_name = ?,
            date_lent = ? 
        WHERE id = ? AND user_id = ?
        """,
        (borrower_name, date_lent, film_id, session["user_id"]),
    )
    conn.commit()
    conn.close()

    return redirect("/collection")


# marks a lent film as returned
@app.route("/return_film/<int:film_id>", methods=["POST"])
def return_film(film_id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    conn.execute(
        """
        UPDATE films 
        SET is_lent = 0, lent_to_name = NULL, date_lent = NULL 
        WHERE id = ? AND user_id = ?
        """,
        (film_id, session["user_id"]),
    )
    conn.commit()
    conn.close()

    return redirect("/collection")


# logs user out
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# handles uploaded csv files
@app.route("/import", methods=["GET", "POST"])
def import_csv():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "GET":
        return render_template("import.html")

    file = request.files.get("file")
    media_type = request.form.get("media_type", "Physical")

    if not file or not file.filename.endswith(".csv"):
        return render_template("import.html", error="Please select a valid CSV file.")

    # decode with utf-8-sig to automatically strip byte-order marks (\ufeff)
    raw_content = file.stream.read().decode("utf-8-sig")
    lines = [line for line in raw_content.splitlines() if line.strip()]

    if len(lines) < 2:
        return render_template(
            "import.html", error="CSV file is missing data or formatted incorrectly."
        )

    # skip header line and parse rows
    reader = csv.DictReader(lines[1:])
    imported_films = []

    for row in reader:
        # handle different possible column names
        name = row.get("Name") or row.get("Title") or row.get("Film")
        notes = row.get("Description") or row.get("Notes") or ""

        if name and name.strip():
            imported_films.append({"title": name.strip(), "notes": notes.strip()})

    if not imported_films:
        return render_template("import.html", error="No valid films found in CSV.")

    # stash import list in session for review loop
    session["import_queue"] = imported_films
    session["import_media_type"] = media_type
    session["import_index"] = 0

    return redirect("/import/review")


# steps through imported movies one by one
@app.route("/import/review")
def import_review():
    if "user_id" not in session or "import_queue" not in session:
        return redirect("/collection")

    queue = session["import_queue"]
    idx = session.get("import_index", 0)

    # clean up session when done reviewing
    if idx >= len(queue):
        session.pop("import_queue", None)
        session.pop("import_media_type", None)
        session.pop("import_index", None)
        return redirect("/collection")

    return render_template(
        "import_review.html",
        film=queue[idx],
        current_index=idx,
        total=len(queue),
        media_type=session.get("import_media_type", "Physical"),
    )


# saves current reviewed film from csv queue
@app.route("/import/save", methods=["POST"])
def import_save():
    if "user_id" not in session or "import_queue" not in session:
        return redirect("/collection")

    title = request.form["title"]
    format_type = request.form["format"]
    collection_name = request.form.get("collection_name", "")
    notes = request.form.get("notes", "")
    media_type = session.get("import_media_type", "Physical")

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO films (user_id, title, media_type, format, collection_name, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (session["user_id"], title, media_type, format_type, collection_name, notes),
    )
    conn.commit()
    conn.close()

    # increment queue index
    session["import_index"] = session.get("import_index", 0) + 1
    return redirect("/import/review")


# permanently removes film
@app.route("/delete_film/<int:film_id>")
def delete_film(film_id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM films WHERE id = ? AND user_id = ?", (film_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect("/collection")


# creates a new user profile
@app.route("/create_profile", methods=["POST"])
def create_profile():
    username = request.form.get("username", "").strip()
    pin = request.form.get("pin", "").strip()

    if not username or not pin or len(pin) != 4:
        return redirect("/?error=invalid_profile")

    conn = get_db_connection()

    # check if username already exists
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    if existing:
        conn.close()
        return redirect("/?error=username_taken")

    conn.execute("INSERT INTO users (username, pin) VALUES (?, ?)", (username, pin))
    conn.commit()
    conn.close()

    return redirect("/")


# manages adding friends and viewing friends list
@app.route("/friends", methods=["GET", "POST"])
def friends():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()

    if request.method == "POST":
        friend_username = request.form.get("username", "").strip()
        friend = conn.execute(
            "SELECT id FROM users WHERE username = ?", (friend_username,)
        ).fetchone()

        if friend and friend["id"] != session["user_id"]:
            existing = conn.execute(
                "SELECT id FROM friends WHERE user_id = ? AND friend_id = ?",
                (session["user_id"], friend["id"]),
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO friends (user_id, friend_id) VALUES (?, ?)",
                    (session["user_id"], friend["id"]),
                )
                conn.commit()

    friends_list = conn.execute(
        """
        SELECT u.id, u.username FROM users u
        JOIN friends f ON u.id = f.friend_id
        WHERE f.user_id = ?
    """,
        (session["user_id"],),
    ).fetchall()

    conn.close()
    return render_template("friends.html", friends=friends_list)


# view a friend's collection
@app.route("/friends/<int:friend_id>")
def view_friend_collection(friend_id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    friend = conn.execute(
        "SELECT username FROM users WHERE id = ?", (friend_id,)
    ).fetchone()
    films = conn.execute(
        "SELECT * FROM films WHERE user_id = ?", (friend_id,)
    ).fetchall()
    conn.close()

    return render_template("friend_collection.html", friend=friend, films=films)


# watchlist with friend media availability checks
@app.route("/watchlist", methods=["GET", "POST"])
def watchlist():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            conn.execute(
                "INSERT INTO watchlist (user_id, title) VALUES (?, ?)",
                (session["user_id"], title),
            )
            conn.commit()

    watchlist_items = conn.execute(
        "SELECT * FROM watchlist WHERE user_id = ?", (session["user_id"],)
    ).fetchall()

    enhanced_watchlist = []
    for item in watchlist_items:
        # check if any friend owns an available physical copy
        friend_owner = conn.execute(
            """
            SELECT u.username, f.format FROM films f
            JOIN users u ON f.user_id = u.id
            JOIN friends fr ON fr.friend_id = u.id
            WHERE fr.user_id = ? AND LOWER(f.title) = LOWER(?) AND f.media_type = 'Physical' AND f.is_lent = 0
        """,
            (session["user_id"], item["title"]),
        ).fetchone()

        enhanced_watchlist.append(
            {
                "id": item["id"],
                "title": item["title"],
                "borrowable_from": friend_owner["username"] if friend_owner else None,
                "format": friend_owner["format"] if friend_owner else None,
            }
        )

    conn.close()
    return render_template("watchlist.html", watchlist=enhanced_watchlist)


# edit existing film details
@app.route("/edit_film/<int:film_id>", methods=["GET", "POST"])
def edit_film(film_id):
    if "user_id" not in session:
        return redirect("/")

    conn = get_db_connection()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        format_type = request.form.get("format", "").strip()
        collection_name = request.form.get("collection_name", "").strip()
        notes = request.form.get("notes", "").strip()
        lent_to_name = request.form.get("lent_to_name", "").strip()

        digital_formats = ["Apple TV", "Prime Video", "YouTube", "Google Play"]
        media_type = "Digital" if format_type in digital_formats else "Physical"

        # toggle lending flags depending on whether borrower name exists
        is_lent = 1 if lent_to_name else 0
        date_lent = datetime.now().strftime("%d %b %Y") if lent_to_name else None

        conn.execute(
            """
            UPDATE films
            SET title = ?,
                format = ?,
                media_type = ?,
                collection_name = ?,
                notes = ?,
                is_lent = ?,
                lent_to_name = ?,
                date_lent = COALESCE(date_lent, ?)
            WHERE id = ? AND user_id = ?
            """,
            (
                title,
                format_type,
                media_type,
                collection_name,
                notes,
                is_lent,
                lent_to_name if lent_to_name else None,
                date_lent,
                film_id,
                session["user_id"],
            ),
        )
        conn.commit()
        conn.close()
        return redirect("/collection")

    film = conn.execute(
        """
        SELECT f.*, f.lent_to_name AS borrower_name 
        FROM films f
        WHERE f.id = ? AND f.user_id = ?
        """,
        (film_id, session["user_id"]),
    ).fetchone()
    conn.close()

    if not film:
        return redirect("/collection")

    return render_template("edit_film.html", film=film)


if __name__ == "__main__":
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.run(debug=True, host="0.0.0.0", port=5000)
