from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask_cors import CORS
import user_management as dbHandler
import security as secure
import bcrypt
import sqlite3

# Code snippet for logging a message
# app.logger.critical("message")

app = Flask(__name__)
# Enable CORS to allow cross-origin requests (needed for CSRF demo in Codespaces)
CORS(app)


@app.route("/success.html", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
def addFeedback():
    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url", "")
        return redirect(url, code=302)
    if request.method == "POST":
        feedback = request.form["feedback"]
        dbHandler.insertFeedback(feedback)
        dbHandler.listFeedback()
        return render_template("/success.html", state=True, value="Back")
    else:
        dbHandler.listFeedback()
        return render_template("/success.html", state=True, value="Back")


@app.route("/signup.html", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
def signup():
    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url", "")
        return redirect(url, code=302)
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        DoB = request.form["dob"]
        salt = secure.getSalt()
        password = secure.hashPassword(password, salt)
        dbHandler.insertUser(username, password, DoB, salt)
        return render_template("/index.html")
    else:
        return render_template("/signup.html")


# signup page from Unsecure PWA, includes hashing and salting passwords


@app.route("/index.html", methods=["POST", "GET", "PUT", "PATCH", "DELETE"])
@app.route("/", methods=["POST", "GET"])
def home():
    # Simple Dynamic menu
    if request.method == "GET" and request.args.get("url"):
        url = request.args.get("url", "")
        return redirect(url, code=302)
    # Pass message to front end
    elif request.method == "GET":
        msg = request.args.get("msg", "")
        return render_template("/index.html", msg=msg)
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        isLoggedIn = dbHandler.retrieveUsers(username, password)
        if isLoggedIn:
            dbHandler.listFeedback()
            return render_template("/success.html", value=username, state=isLoggedIn)
        else:
            return render_template("/index.html")
    else:
        return render_template("/index.html")


# defining homepage, taken from unsecure pwa which checks if the user is logged in


def get_db_connection():
    conn = sqlite3.connect("database_files/database.db")
    conn.row_factory = sqlite3.Row  # Access columns by name in Jinja templates
    return conn


@app.route("/collection")
def collection():
    conn = get_db_connection()
    films = conn.execute("SELECT * FROM films").fetchall()
    conn.close()
    return render_template("collection.html", films=films)


# defining the page where the collection is found, which accesses everything in the 'films' database, and renders it.


# add film page, with different fields to fill in film information \/
@app.route("/add_film", methods=["POST"])
def add_film():
    title = request.form["title"]
    format_type = request.form["format"]
    collection_name = request.form.get("collection_name", "")
    notes = request.form.get("edition_notes", "")

    # Automatically set media_type based on chosen format
    digital_formats = ["Apple TV", "Prime Video", "YouTube", "Google Play"]
    media_type = "Digital" if format_type in digital_formats else "Physical"

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO films (user_id, title, media_type, format, collection_name, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (1, title, media_type, format_type, collection_name, notes),
    )
    conn.commit()
    conn.close()
    return redirect("/collection")


# eg: 1, Scott Pilgrim vs. the World, digital, Amazon Prime
# default user id, the title, that it is found digitally, where you can find it, and no entries for the last two because it is not in a collection, and no other notes, but you could add if it was just a rental or if it was a director's cut.
# only title and format_type will actually display though.
# submitting the film entry into the database, then returning to the collection so you can see it there.


@app.route("/lend/<int:film_id>")
def lend_page(film_id):
    conn = get_db_connection()
    film = conn.execute("SELECT * FROM films WHERE id = ?", (film_id,)).fetchone()
    conn.close()
    return render_template("lend.html", film=film)


@app.route("/lend_film/<int:film_id>", methods=["POST"])
def lend_film(film_id):
    borrower_name = request.form["borrower_name"]

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO lent_films (film_id, borrower_name)
        VALUES (?, ?)
    """,
        (film_id, borrower_name),
    )

    conn.execute("UPDATE films SET is_lent = 1 WHERE id = ?", (film_id,))
    conn.commit()
    conn.close()

    return redirect("/collection")


if __name__ == "__main__":
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.run(debug=True, host="0.0.0.0", port=5000)
