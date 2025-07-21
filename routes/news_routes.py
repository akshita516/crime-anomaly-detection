# routes/news_routes.py
from flask import Blueprint, request, redirect, url_for, session, flash
from datetime import datetime
from flask import current_app as app

news_bp = Blueprint('news', __name__, url_prefix="/news")

@news_bp.route("/", methods=["POST"])
def upload_news():
    if session.get('role') != 'admin':
        flash("Only admin can post news!", "danger")
        return redirect(url_for("home"))

    title = request.form.get("title")
    location = request.form.get("location")
    content = request.form.get("content")

    if not (title and location and content):
        flash("Please fill all fields", "warning")
        return redirect(url_for("home"))

    app.mongo.db.news.insert_one({
        "title": title,
        "location": location,
        "content": content,
        "timestamp": datetime.utcnow()
    })
    flash("News posted successfully!", "success")
    return redirect(url_for("home"))
