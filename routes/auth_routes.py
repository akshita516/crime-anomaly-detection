from flask import Blueprint, render_template, request, redirect, session, flash, url_for, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from routes.auth_utils import login_required,admin_required
from bson.objectid import ObjectId


auth_bp = Blueprint('auth', __name__)
incident_bp = Blueprint('incident', __name__)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    mongo = current_app.mongo  # 👈 Access global mongo client

    print("\n\nfrom auth_routes",mongo,"\n\n")
    print("mongo.db",mongo.db,"\n\n")

    if request.method == "POST":
        name = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = mongo.db.users.find_one({"email": email})
        if existing_user:
            flash("User already exists!", "warning")
            return redirect(url_for("auth.signup"))

        hashed_pw = generate_password_hash(password)
        mongo.db.users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_pw,
            "role": "user"
        })

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    mongo = current_app.mongo

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["username"] = user.get("name")
            session["role"] = user.get("role", "user")
            session["email"]=user.get("email")
            session["logged_in"]=True

            flash("Login successful!", "success")
            return redirect("/home")
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route('/manage_users')
@login_required
def manage_users():
    if session.get('role') != 'admin':
        flash("Access denied: Admins only", "danger")
        return redirect(url_for('home'))

    mongo = current_app.mongo
    users = list(mongo.db.users.find({}, {'password': 0}))  # Don't fetch passwords
    return render_template("manage_users.html", users=users)

@auth_bp.route('/update_user_role', methods=['POST'])
@login_required
def update_user_role():
    if session.get('role') != 'admin':
        flash("Unauthorized", "danger")
        return redirect(url_for('home'))

    user_id = request.form.get('user_id')
    new_role = request.form.get('new_role')

    mongo = current_app.mongo
    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": new_role}}
    )

    flash("User role updated!", "success")
    return redirect(url_for('auth.manage_users'))

@incident_bp.route('/resolve/<id>', methods=['POST'])
@login_required
@admin_required
def resolve_incident(id):
    mongo = current_app.mongo
    actions = request.form.get('actions_taken')
    mongo.db.crime_anomaly.update_one(
        {'_id': ObjectId(id)},
        {'$set': {'status': 'resolved', 'actions_taken': actions}}
    )
    flash("Incident marked as resolved with actions.", "success")
    return redirect(url_for('incident.view_reported'))

@auth_bp.route("/delete_user", methods=["POST"])
@login_required
@admin_required
def delete_user():
    user_id = request.form.get("user_id")
    mongo = current_app.mongo

    # Prevent an admin from deleting themselves
    current_user = session.get("username")
    to_delete = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not to_delete:
        flash("User not found.", "warning")
        return redirect(url_for("auth.manage_users"))

    if to_delete.get("name") == current_user:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("auth.manage_users"))

    # Perform deletion
    mongo.db.users.delete_one({"_id": ObjectId(user_id)})
    flash(f"User '{to_delete.get('name')}' has been deleted.", "success")
    return redirect(url_for("auth.manage_users"))

