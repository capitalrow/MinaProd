from flask import Blueprint, jsonify, render_template, redirect, url_for

http_bp = Blueprint("http", __name__)

@http_bp.route("/health")
def health():
    return jsonify({"status": "ok", "version": "0.1.0"})

@http_bp.route("/")
def root():
    return redirect(url_for("pages.live"))

@http_bp.route("/live")
def live():
    return render_template("live.html")