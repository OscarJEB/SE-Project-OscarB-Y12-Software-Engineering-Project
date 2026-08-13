import sqlite3 as sql
import time
import random
import security as secure


def insertUser(username, password, DoB, salt):
    con = sql.connect("database_files/database.db")
    cur = con.cursor()
    cur.execute(
        "INSERT INTO users (username,password,dateOfBirth,salt) VALUES (?,?,?,?)",
        (username, password, DoB, salt),
    )
    con.commit()
    con.close()


def retrieveUsers(username, password):
    con = sql.connect("database_files/database.db")
    cur = con.cursor()
    cur.execute("SELECT salt FROM users WHERE username == ?", (username,))
    salt = cur.fetchone()
    hash = secure.hashPassword(password, salt[0])
    cur.execute(
        "SELECT * FROM users WHERE username == ? AND password == ?",
        (username, hash),
    )
    if cur.fetchone() == None:
        con.close()
        return False
    else:
        # cur.execute("SELECT * FROM users WHERE password == ?", (password))
        # FIX THIS, it is looking up password matches only
        # Plain text log of visitor count as requested by Unsecure PWA management
        with open("visitor_log.txt", "r") as file:
            number = int(file.read().strip())
            number += 1
        with open("visitor_log.txt", "w") as file:
            file.write(str(number))
        # Simulate response time of heavy app for testing purposes
        time.sleep(random.randint(80, 90) / 1000)

        # if it doesn't find any users with this password
        # if cur.fetchone() == None:
        #     con.close()
        #     return False
        # else:
        con.close()
        return True


def insertFeedback(feedback):
    con = sql.connect("database_files/database.db")
    cur = con.cursor()
    cur.execute(f"INSERT INTO feedback (feedback) VALUES ('{feedback}')")  # FIX THIS
    con.commit()
    con.close()


def listFeedback():
    con = sql.connect("database_files/database.db")
    cur = con.cursor()
    data = cur.execute("SELECT * FROM feedback").fetchall()
    con.close()
    f = open("templates/partials/success_feedback.html", "w")
    for row in data:
        f.write("<p>\n")
        f.write(f"{row[1]}\n")
        f.write("</p>\n")
    f.close()
