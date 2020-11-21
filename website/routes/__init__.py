from website import app
from flask import render_template, request, g, redirect
import os
import sys
from website.custom_scripts import *

# NOTE: g is a flask global variable for the current context.
@app.route("/", methods=["GET", "POST"])
def main_page():
    if request.method == "GET":
        return render_template("index.html", prev=["", "", ""])
    elif request.method == "POST":
        # logic for querying database and return data
        search_string = request.form['inputString']
        query_type = request.form['inputQuery']
        sort_by_type = request.form['sortby']
        prev_query = [search_string, query_type, sort_by_type]
        if search_string == "":
            return render_template("index.html", prev=["", "", ""], songs=query_db.list_all(get_db().cursor(), sort_by_type))
        else:
            return render_template("index.html", prev=prev_query, songs=query_db.search_by(get_db().cursor(), search_string, query_type, sort_by_type))

@app.route("/songs-by-artist", methods=["GET"])
def songs_by_artist_page():
    if request.method != "GET":
        print(f"/songs-by-artist received a {request.method} request when it should have recieved a 'GET' request.")
        return error_page()
    artist = request.args.get("artist", "")
    if not artist:
        print(f"/songs-by-artist needs to receive an 'artist' parameter (eg. /songs-by-artist?artist=bob)")
        return error_page()
    return render_template("index.html", prev=["", " ", " "], songs=query_db.songs_by_artist(get_db().cursor(), artist))

@app.route("/rate", methods=["GET"])
def rate_song_page():
    if request.method != "GET":
        print(f"/rate recieved a {request.method} request when it should have recieved a 'GET' request.")
        return error_page()
    song = request.args.get("song", "")
    if not song:
        print(f"/rate needs to recieve a song-id parameter (eg. /rate?song=123)")
        return error_page()
    results = query_db.rate_song_page(get_db().cursor(), song)
    if not results:
        print(f"/rate was unable to find any songs with id '{song}'")
        return error_page()
    return render_template("rate.html", song=results)

@app.route("/rate/<song_id>", methods=["POST"])
def rate(song_id):
    if request.method != "POST":
        print(f"failed")
        return error_page()
    user_id = request.form['user_id']
    rating_value = int(request.form['rating'])
    comment = request.form['comment']
    if not 1 <= rating_value <= 10:
        print(f"/rate/ expected the rating to be between 1 and 10, but instead recieved {rating_value}")
        return error_page()
    query_db.rate_song_page(get_db().cursor(), user_id, song_id, rating_value, comment)		
    return redirect("/")

def error_page():
    return "FUCK" # should be a template or something

@app.errorhandler(404)
def error404(error):
    print(error)
    return error_page()

class DotDict(dict):
    def __getattr__(self, key):
        if key not in self:
            print(f"There was an error while trying to access '{key}' from {self}")
            return "Database Error"
        else:
            return self[key]

def get_db():
    """
    Opens a new connection to the DB if there is none for the current context.
    """
    if not hasattr(g, 'postgres_db'):
        g.postgres_db = query_db.init_db_connection()
    return g.postgres_db


@app.teardown_appcontext
def close_db(input):
    """
    Closes the database again at the end of the request.
    """
    if hasattr(g, 'postgres_db'):
        g.postgres_db.close()
