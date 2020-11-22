from website import app
from flask import render_template, request, g, redirect, make_response
import os
import sys
from website.custom_scripts import *

# NOTE: g is a flask global variable for the current context.
@app.route("/", methods=["GET", "POST"])
def main_page():
    if request.method == "GET":
        return render_template("homepage.html", prev=["", "", ""])
    elif request.method == "POST":
        # logic for querying database and return data
        search_string = request.form['inputString']
        query_type = request.form['inputQuery']
        sort_by_type = request.form['sortby']
        prev_query = [search_string, query_type, sort_by_type]
        if search_string == "":
            return render_template(
                "index.html",
                prev=["", "", ""],
                songs=query_db.list_all(get_db().cursor(), sort_by_type)
            )
        else:
            return render_template(
                "index.html",
                prev=prev_query,
                songs=query_db.search_by(get_db().cursor(), search_string, query_type, sort_by_type)
            )

@app.route("/artist", methods=["GET"])
def artist_page():
    artist = request.args.get("artist", "")
    if not artist:
        print(f"/songs-by-artist needs to receive an 'artist' parameter (eg. /songs-by-artist?artist=bob)")
        return error_page()
    return render_template("artist.html", artist_name=artist)

@app.route("/rate", methods=["GET", "POST"])
def rate_song_page():
    if request.method == "GET":
        user_id = request.cookies.get('user_id')
        username = request.cookies.get('username')
        if not user_id or not username:
            print(f"You need to log in before rating any songs")
            return redirect("/sign-in")
        song_id = request.args.get("song_id", "")
        if not song_id:
            print("/rate needs to receive a song_id parameter (eg. /rate?song=123)")
            return error_page()
        results = query_db.rate_song_page(get_db().cursor(), song_id)

        listened_to = request.args.get("listened_to", "")
        print(listened_to)
        if listened_to == '1':
            print("entered if")
            # Logic for ADDING the listened_to relationship
            query_db.add_listen(get_db(), user_id, song_id)

        print(results[0].song_name)
        if not results:
            print(f"/rate was unable to find any songs with id '{song_id}'")
            return error_page()
        return render_template("rate.html",
                                song_id=song_id,
                                avg_rating=query_db.get_average_rating(get_db().cursor(), song_id),
                                total_listens=query_db.get_total_listens(get_db().cursor(), song_id),
                                song=query_db.get_song_info(get_db().cursor(), song_id)[0],
                                listened_to_song=query_db.check_if_listened(get_db().cursor(), user_id, song_id),
                                other_details=query_db.get_other_song_details(get_db().cursor(), song_id),
                                results=results)

    elif request.method == "POST":
        user_id = request.cookies.get('user_id')
        username = request.cookies.get('username')
        if not user_id or not username:
            print(f"You need to log in before rating any songs")
            return redirect("/sign-in")
        comment = request.form["comment"]
        rating = request.form["rating"]

        song_id = request.args.get("song_id", "")
        if not song_id:
            print("/rate needs to receive a song_id parameter (eg. /rate?song=123)")
            return error_page()

        if not rating.isdigit():
            print(f"/rate/ expected the rating to be an integer, but instead received '{rating}'")
            return error_page()
        rating = int(rating)
        if not 1 <= rating <= 10:
            print(f"/rate/ expected the rating to be between 1 and 10, but instead received '{rating}'")
            return error_page()

        # Logic to enter new comment into database
        query_db.rate(get_db(), user_id, song_id, rating, comment)
        results = query_db.rate_song_page(get_db().cursor(), song_id)

        if not results:
            print(f"/rate was unable to find any songs with id '{song_id}'")
            return error_page()
        return render_template("rate.html",
                                song_id=song_id,
                                avg_rating=query_db.get_average_rating(get_db().cursor(), song_id),
                                total_listens=query_db.get_total_listens(get_db().cursor(), song_id),
                                song=query_db.get_song_info(get_db().cursor(), song_id)[0],
                                listened_to_song=query_db.check_if_listened(get_db().cursor(), user_id, song_id),
                                other_details=query_db.get_other_song_details(get_db().cursor(), song_id),
                                results=results)
    else:
        print(f"/rate received a {request.method} request when it should have received a 'GET' or 'POST' request.")
        return error_page()

#TODO store passwords in user_table
@app.route("/sign-in", methods=["GET", "POST"])
def log_in():
    if request.method == "GET":
        return render_template("sign-in.html")
    else:
        username = request.form['username']
        password = request.form['password']
        print("We currently are not actually using password information.")
        user_id = query_db.get_user_id(get_db(), username)
        page = make_response(redirect("/"))
        # FUCK
        page.set_cookie('user_id', user_id)
        page.set_cookie('username', username)
        return page

@app.route("/sign-out", methods=["GET"])
def log_out():
    """Deletes the cookies storing user info and returns them to the previous page"""
    page = redirect(request.referrer)
    page.set_cookie('user_id', "")
    page.set_cookie('username', "")
    return page

def error_page():
    return "FUCK" # should be a template or something

@app.errorhandler(404)
def error404(error):
    print(error)
    return error_page()

def get_db():
    """Opens a new connection to the DB if there is none for the current context."""
    if not hasattr(g, 'postgres_db'):
        g.postgres_db = query_db.init_db_connection()
    return g.postgres_db

@app.teardown_appcontext
def close_db(input):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'postgres_db'):
        g.postgres_db.close()
