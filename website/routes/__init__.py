from website import app
from flask import render_template, request
import os


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return render_template("index.html", a=[1, 2, 3])
    elif request.method == "POST":
        # logic for querying database and return data
        dummy_data = [
            {"title": "Call Me Maybe", "artist": "Someone i forgot the name"},
            {"title": "WAP", "artist": "Cardi B"}
        ]
        return render_template("index.html", songs=dummy_data)
        #return "{first_name}, fuck off".format(first_name=request.form.get("firstname", "???"))
    else:
        return "fuck yourself", 405
