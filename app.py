from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

def db():
    return sqlite3.connect("database.db")

def init():
    con = db()
    cur = con.cursor()

    # USERS TABLE
    cur.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','staff','customer'))
    )
    ''')

    # BUGS TABLE
    cur.execute('''
    CREATE TABLE IF NOT EXISTS bugs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT CHECK(priority IN ('Low','Medium','High')) DEFAULT 'Low',
        status TEXT CHECK(status IN ('Open','In Progress','Resolved')) DEFAULT 'Open',
        assigned_to TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')

    # COMMENTS TABLE
    cur.execute('''
    CREATE TABLE IF NOT EXISTS comments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bug_id INTEGER,
        user TEXT,
        comment TEXT,
        date TEXT,
        FOREIGN KEY (bug_id) REFERENCES bugs(id) ON DELETE CASCADE
    )
    ''')

    con.commit()
    con.close()
init()
# REGISTER
@app.route("/register", methods=["GET","POST"])
def register():
    error = None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        r = request.form["role"]

        con = db()
        cur = con.cursor()
        try:
            cur.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",(u,p,r))
            con.commit()
        except:
           error = "Username already exists"
        return redirect("/")
    return render_template("register.html" , error=error)

# LOGIN
@app.route("/", methods=["GET","POST"])
def login():
    error=None
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        con = db()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        user = cur.fetchone()

        if user:
            session["user"] = user[1]
            session["role"] = user[3]
            return redirect("/dashboard")
        else:
            error = "Invalid username or password"

    return render_template("login.html",error=error)

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    con = db()
    cur = con.cursor()

    search = request.args.get("search")

    if search:
        cur.execute("SELECT * FROM bugs WHERE title LIKE ?",('%'+search+'%',))
    else:
        cur.execute("SELECT * FROM bugs")

    bugs = cur.fetchall()

    # Stats
    cur.execute("SELECT COUNT(*) FROM bugs WHERE status='Open'")
    open_c = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bugs WHERE status='In Progress'")
    prog_c = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM bugs WHERE status='Resolved'")
    res_c = cur.fetchone()[0]

    return render_template("dashboard.html",
                           bugs=bugs,
                           open=open_c,
                           progress=prog_c,
                           resolved=res_c)

# ADD BUG
@app.route("/add", methods=["GET","POST"])
def add_bug():
    if "user" not in session:
        return redirect("/")

    error = None

    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("description")
        priority = request.form.get("priority")
        assigned = request.form.get("assigned")
        date = request.form.get("date")

        from datetime import datetime

        try:
            # If user gives date → use it, else current time
            if date:
                created = datetime.strptime(date, "%Y-%m-%dT%H:%M")
                created = created.strftime("%Y-%m-%d %H:%M")
            else:
                created = datetime.now().strftime("%Y-%m-%d %H:%M")

            updated = datetime.now().strftime("%Y-%m-%d %H:%M")

            con = db()
            cur = con.cursor()

            cur.execute('''
                INSERT INTO bugs(title,description,priority,status,assigned_to,created_at,updated_at)
                VALUES(?,?,?,?,?,?,?)
            ''', (title, desc, priority, "Open", assigned, created, updated))

            con.commit()
            con.close()

            return redirect("/dashboard")

        except Exception as e:
            error = str(e)

    return render_template("add_bug.html", error=error)

# EDIT BUG
@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    con = db()
    cur = con.cursor()

    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["description"]
        priority = request.form["priority"]
        assigned = request.form["assigned"]

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        cur.execute('''UPDATE bugs SET title=?,description=?,priority=?,assigned_to=?,updated_at=? WHERE id=?''',
                    (title, desc, priority, assigned, now, id))
        con.commit()

        return redirect("/dashboard")

    cur.execute("SELECT * FROM bugs WHERE id=?", (id,))
    bug = cur.fetchone()

    return render_template("edit_bug.html", bug=bug)

# DELETE BUG
@app.route("/delete/<int:id>")
def delete(id):
    con = db()
    cur = con.cursor()

    cur.execute("DELETE FROM bugs WHERE id=?", (id,))
    con.commit()

    return redirect("/dashboard")

# UPDATE STATUS
@app.route("/update/<int:id>/<status>")
def update(id, status):
    con = db()
    cur = con.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cur.execute("UPDATE bugs SET status=?, updated_at=? WHERE id=?",
                (status, now, id))
    con.commit()

    return redirect("/dashboard")

# VIEW BUG + COMMENTS
@app.route("/bug/<int:id>", methods=["GET","POST"])
def bug(id):
    con = db()
    cur = con.cursor()

    if request.method == "POST":
        comment = request.form["comment"]
        user = session["user"]
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        cur.execute("INSERT INTO comments(bug_id,user,comment,date) VALUES(?,?,?,?)",
                    (id, user, comment, date))
        con.commit()

    cur.execute("SELECT * FROM bugs WHERE id=?", (id,))
    bug = cur.fetchone()

    cur.execute("SELECT * FROM comments WHERE bug_id=?", (id,))
    comments = cur.fetchall()

    return render_template("view_bug.html", bug=bug, comments=comments)

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run()