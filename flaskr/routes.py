from flask import render_template

from flaskr import app


@app.route("/")
@app.route("/index")
def index():
    user = {"username": "Frost"}
    return render_template("index.html", title="Home", user=user)
