from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# Database connection
def get_db():
    return sqlite3.connect("database.db")

# Initialize database
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # Create users table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT)''')

    # Create bugs table
    cur.execute('''CREATE TABLE IF NOT EXISTS bugs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        status TEXT,
        created_at TEXT,
        assigned_to TEXT)''')

    # ✅ INSERT ADMIN USER (CORRECT)
    try:
        cur.execute("INSERT INTO users (username, password, role) VALUES ('admin','admin123','admin')")
        cur.execute("INSERT INTO users (username, password, role) VALUES ('jhenkar','jhenkar','jhenkar')")
        cur.execute("INSERT INTO users (username, password, role) VALUES ('staff1','staf123','staff')")
    except:
        pass

    conn.commit()
    conn.close()

init_db()

# Login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = u
            session["role"] = user[3]
            return redirect("/dashboard")

    return render_template("login.html")

# Dashboard
@app.route("/dashboard")
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    try:
        cur.execute("SELECT * FROM bugs")
        bugs = cur.fetchall()
    except:
        bugs = []

    conn.close()

    return render_template("dashboard.html", bugs=bugs)
# Create Bug
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        t = request.form["title"]
        d = request.form["description"]
        a = request.form["assigned_to"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO bugs VALUES (NULL,?,?,?, ?,?)",
                    (t, d, "Open", datetime.now(), a))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("create_bug.html")

# Resolve Bug
@app.route("/resolve/<int:id>")
def resolve(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE bugs SET status='Resolved' WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Run fast (no lag)
if __name__ == "__main__":
    app.run()