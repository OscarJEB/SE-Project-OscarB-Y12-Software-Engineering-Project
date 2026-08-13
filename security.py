# this module handles the secure functions for this app
import bcrypt


def getSalt():
    salt = bcrypt.gensalt()
    return salt


def hashPassword(password, salt):
    bytes = password.encode("utf-8")
    password = bcrypt.hashpw(bytes, salt)
    return password
