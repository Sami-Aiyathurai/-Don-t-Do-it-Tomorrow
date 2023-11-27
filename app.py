import os
import sys
from datetime import datetime, date

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///taskmanager.db")
#make taskmanager database



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Greet user and list next item(s) due"""
    id = session["user_id"]
    q1 = db.execute("SELECT name FROM users WHERE id = ?", id)
    name = q1[0]["name"]
    q2 = db.execute("SELECT title, dueDate FROM projects WHERE user_id = ? LIMIT 1", id)
    q3 = db.execute("SELECT title, dueDate FROM tasks WHERE user_id = ? AND NOT status = ? LIMIT 1", id, "Completed")
    if len(q2) == 0:
        return render_template("index2.html", name = name)

    projects = q2[0]
    if len(q3) == 0:
        return render_template("index3.html", name = name, projects = projects)

    tasks = q3[0]
    return render_template("index.html", name = name, tasks = tasks, projects = projects)


@app.route("/newproject", methods=["GET", "POST"])
@login_required
def newproject():
    """Create New Project"""
    id = session["user_id"]
    if request.method == "POST":
        # Ensure project title was submitted
        if not request.form.get("title"):
            return apology("must provide title", 400)
        if not request.form.get("duedate"):
            return apology("must provide due date", 400)
        if not request.form.get("status"):
            return apology("must provide status", 400)
        rows = db.execute("SELECT * FROM projects WHERE user_id = ? AND title = ?", id, request.form.get("title"))
        # Ensure title has not been used before by user
        if len(rows) != 0:
            return apology("project title is already used", 400)
        db.execute("INSERT INTO projects (user_id, dueDate, title, description, status) VALUES(?, ?, ?, ?, ?)", id, request.form.get("duedate"), request.form.get("title"), request.form.get("description"), request.form.get("status"))
        #add project to database
        #render add_task(reaches add_task via get)
        return render_template("addTask.html", project = request.form.get("title"))

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("newProject.html")


@app.route("/addTask", methods=["GET", "POST"])
@login_required
def  addtask():
    """New task"""
    user_projs = user_projects()
    id = session["user_id"]
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("status"):
            return apology("must select status", 403)
        elif not request.form.get("title"):
            return apology("must provide task name", 403)
        elif not request.form.get("duedate"):
            return apology("must provide a due date", 403)
        project = request.form.get("project")
        query = db.execute("SELECT project_id, dueDate, status FROM projects WHERE user_id = ? AND title = ?", id, project)
        proj_id = query[0]["project_id"]
        proj_dueDate = query[0]["dueDate"]
        proj_status = query[0]["status"]
        # Query database for username
        rows = db.execute("SELECT * FROM tasks WHERE user_id = ? AND title = ?", id, request.form.get("title"))
        if len(rows) != 0:
            return apology("you have already titled a task this for this project", 400)
        if request.form.get("duedate") > proj_dueDate:
            return apology("Task due date cannot be after Project due date", 400)
        if request.form.get("status") != "Not Started":
            if proj_status == "Not Started":
                print(proj_status, file=sys.stderr)
                print("Not Started", file=sys.stderr)
                db.execute("UPDATE projects SET status = ? WHERE project_id = ?", "In Progress", proj_id)
        db.execute("INSERT INTO tasks (user_id, project_id, title, dueDate, status) VALUES(?, ?, ?, ?, ?)", id, proj_id, request.form.get("title"), request.form.get("duedate"), request.form.get("status"))
        #add project to database
        proj_details = db.execute("SELECT description, status, dueDate FROM projects WHERE project_id = ?", proj_id)
        print(proj_details, file=sys.stderr)
        task_rows = db.execute("SELECT title, status, dueDate FROM tasks WHERE user_id = ? AND project_id = ?", id, proj_id)
        return render_template("projectDetail.html", tasks = task_rows, details = proj_details, project = project)
    return render_template("addTask.html", projs = user_projs)

@app.route("/updateTask", methods=["GET", "POST"])
@login_required
def  updatetask():
    """New task"""
    id = session["user_id"]
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("status"):
            return apology("must provide status", 403)
        elif not request.form.get("duedate"):
            return apology("must provide a due date", 403)
        project = request.form.get("project")
        query = db.execute("SELECT project_id, dueDate, status FROM projects WHERE user_id = ? AND title = ?", id, project)
        proj_id = query[0]["project_id"]
        proj_dueDate = query[0]["dueDate"]
        proj_status = query[0]["status"]
        if request.form.get("duedate") > proj_dueDate:
            return apology("Task due date cannot be after Project due date", 400)
        if request.form.get("status") != "Not Started":
            if proj_status == "Not Started":
                print(proj_status, file=sys.stderr)
                print("Not Started", file=sys.stderr)
                db.execute("UPDATE projects SET status = ? WHERE project_id = ?", "In Progress", proj_id)
        db.execute("UPDATE tasks SET status = ? WHERE project_id = ? AND title = ?", request.form.get("status"), proj_id, request.form.get("title"))
        db.execute("UPDATE tasks SET dueDate = ? WHERE project_id = ? AND title = ?", request.form.get("duedate"), proj_id, request.form.get("title"))
        #add project to database
        proj_details = db.execute("SELECT description, status, dueDate FROM projects WHERE project_id = ?", proj_id)
        task_rows = db.execute("SELECT title, status, dueDate FROM tasks WHERE user_id = ? AND project_id = ?", id, proj_id)
        return render_template("projectDetail.html", tasks = task_rows, details = proj_details, project = project)

@app.route("/updateProject", methods=["GET", "POST"])
@login_required
def  updateProject():
    """New task"""
    id = session["user_id"]
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("status"):
            return apology("must provide status", 403)
        elif not request.form.get("duedate"):
            return apology("must provide a due date", 403)
        project = request.form.get("project")
        query = db.execute("SELECT project_id FROM projects WHERE user_id = ? AND title = ?", id, project)
        proj_id = query[0]["project_id"]
        if request.form.get("status") == "Completed":
            rows = db.execute("SELECT * FROM tasks WHERE project_id = ? AND NOT status = ?", proj_id, "Completed")
            if len(rows) != 0:
                return apology("Not all have tasks have been completed", 400)
        db.execute("UPDATE projects SET status = ? WHERE project_id = ? AND title = ?", request.form.get("status"), proj_id, request.form.get("title"))
        db.execute("UPDATE projects SET dueDate = ? WHERE project_id = ? AND title = ?", request.form.get("duedate"), proj_id, request.form.get("title"))
        #add project to database
        proj_details = db.execute("SELECT description, status, dueDate FROM projects WHERE project_id = ?", proj_id)
        task_rows = db.execute("SELECT title, status, dueDate FROM tasks WHERE user_id = ? AND project_id = ?", id, proj_id)
        return render_template("projectDetail.html", tasks = task_rows, details = proj_details, project = project)
    return render_template("updateProject.html", project = request.args.get('project'))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    """Display all projects"""
    user_projs = user_projects()
    id = session["user_id"]
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("project"):
            return apology("must select project", 403)
        project = request.form.get("project")
        if project == "create":
            return render_template("newProject.html")
        else:
            query = db.execute("SELECT project_id FROM projects WHERE user_id = ? AND title = ?", id, project)
            proj_id = query[0]["project_id"]
        #use project title to get project id which goes to template. template gets all relevant data
            proj_details = db.execute("SELECT description, status, dueDate FROM projects WHERE project_id = ?", proj_id)
            task_rows = db.execute("SELECT title, status, dueDate FROM tasks WHERE user_id = ? AND project_id = ?", id, proj_id)
            return render_template("projectDetail.html", tasks = task_rows, details = proj_details, project = project)
    else:
        return render_template("projects.html", projs = user_projs)

@app.route("/editProject", methods=["POST"])
@login_required
def editProject():
    """Display all projects"""
    user_projs = user_projects()
    id = session["user_id"]
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("task"):
            return apology("must select task", 403)
        task = request.form.get("task")
        project = request.form.get("project")
        if task == "create":
            return render_template("addTask.html", project = project)
        else:
            query = db.execute("SELECT dueDate FROM tasks WHERE user_id = ? AND title = ?", id, task)
            task_duedate = query[0]["dueDate"]
            return render_template("updateTask.html", task_title = task, task_duedate = task_duedate, project = project)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # Forget any user_id
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        #Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)
        #Ensure Name was given
        elif not request.form.get("name"):
            return apology("must provide a name", 400)
        #Ensure password and confirmation match
        elif (request.form.get("password") != request.form.get("confirmation")):
            return apology("password and password confirmation do not match", 400)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        # Ensure username has not been used before
        if len(rows) != 0:
            return apology("username is already used", 400)
        db.execute("INSERT INTO users (username, hash, name) VALUES(?, ?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")), request.form.get("name"))
        #log user in
        #log user in by submitting password and username to login post
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/timeline", methods=["GET", "POST"])
@login_required
def todolist():
    id = session["user_id"]
    q1 = db.execute("SELECT name FROM users WHERE id = ?", id)
    name = q1[0]["name"]
    tasks = db.execute("SELECT title, dueDate, status, project_id FROM tasks WHERE user_id = ? AND NOT status = ?", id, "Completed")
    for task in tasks:
        projectname = db.execute("SELECT title FROM projects WHERE user_id = ? AND project_id = ?", id, task["project_id"])
        task["project"] = projectname[0]["title"]
    list = sorted(tasks, key=lambda x: datetime.strptime(x['dueDate'], '%m/%d/%Y %I:%M %p'))
    return render_template("timeline.html", tasks = list)



def user_projects():
    user_id = session["user_id"]
    projs = []
    query = db.execute("SELECT title FROM projects WHERE user_id = ?", session["user_id"])
    for q in query:
        title = q["title"]
        projs.append(title)
    return projs

