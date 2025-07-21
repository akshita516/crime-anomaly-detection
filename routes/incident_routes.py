from bson import ObjectId
from flask import Blueprint, render_template, request, redirect, session, flash, url_for, current_app, jsonify
from routes.auth_utils import login_required, admin_required
import datetime

incident_bp = Blueprint("incident", __name__, url_prefix="/incident")

# Route to report a new incident (accessible to all users)
@incident_bp.route("/report_incident", methods=["GET", "POST"])
@login_required
def report_incident():
    mongo = current_app.mongo

    if request.method == "POST":
        description = request.form.get("description")
        location = request.form.get("location")
        reporter = session.get("username", "Anonymous")

        if not description or not location:
            flash("Please provide all fields.", "warning")
            return redirect(url_for("incident.report_incident"))

        mongo.db.incidents.insert_one({
            "description": description,
            "location": location,
            "status": "reported",  # Default status
            "reporter": reporter,
            "timestamp": datetime.datetime.utcnow()
        })

        flash("Incident reported successfully!", "success")
        return redirect(url_for("home"))

    return render_template("report_incident.html")


# Admin-only route to view incidents and generate graph data
@incident_bp.route("/dashboard")
@login_required
def incident_dashboard():
    if session.get("role") != "admin":
        flash("Access denied. Admins only.", "danger")
        return redirect(url_for("home"))

    mongo = current_app.mongo
    incidents = list(mongo.db.incidents.find().sort("timestamp", -1))

    # Count splits
    reported_count = mongo.db.incidents.count_documents({"status": "reported"})
    true_count = mongo.db.incidents.count_documents({"status": "true"})

    return render_template("incident_dashboard.html", incidents=incidents,
                           reported_count=reported_count, true_count=true_count)

from bson import ObjectId
from flask import (
    Blueprint, render_template, request,
    session, jsonify, redirect, url_for, flash, current_app
)
from routes.auth_utils import login_required, admin_required
import datetime

incident_bp = Blueprint("incident", __name__, url_prefix="/incident")


@incident_bp.route("/report_incident", methods=["GET", "POST"])
@login_required
def report_incident():
    mongo = current_app.mongo

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        location = request.form.get("location")
        reporter = session.get("username", "Anonymous")

        if not title or not description or not location:
            flash("Please provide all fields.", "warning")
            return redirect(url_for("incident.report_incident"))

        mongo.db.incidents.insert_one({
            "title": title,
            "description": description,
            "location": location,
            "status": "reported",
            "reporter": reporter,
            "timestamp": datetime.datetime.utcnow()
        })

        flash("Incident reported successfully!", "success")
        return redirect(url_for("incident.view_reported"))

    return render_template("report_incident.html")


@incident_bp.route("/reported_incidents")
@login_required
@admin_required
def view_reported():
    mongo = current_app.mongo
    incidents = list(mongo.db.incidents.find().sort("timestamp", -1))
    return render_template("reported_incidents.html", incidents=incidents)


@incident_bp.route("/update_status/<id>", methods=["POST"])
@login_required
@admin_required
def update_status(id):
    mongo = current_app.mongo
    incident = mongo.db.incidents.find_one({"_id": ObjectId(id)})
    if not incident:
        return jsonify({"success": False, "message": "Incident not found"}), 404

    data = request.get_json()
    new_status = data.get("status")
    actions_taken = data.get("actions_taken", "")

    update_fields = {"status": new_status}
    if new_status == "resolved":
        update_fields["actions_taken"] = actions_taken

    mongo.db.incidents.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_fields}
    )

    return jsonify({
        "success": True,
        "new_status": new_status,
        "actions_taken": actions_taken
    })