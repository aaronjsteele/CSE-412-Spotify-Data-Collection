from website import app
from flask import render_template, request, g
import os
from website.custom_scripts import *

# NOTE: g is a flask global variable for the current context.
@app.route("/", methods=["GET", "POST"])
def main():
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
def songs_by_artist():
    if request.method != "GET":
        print(f"/songs-by-artist received a {request.method} request when it should have received a 'GET' request.")
        return error_page()
    artist = request.args.get("artist", "")

    if not artist:
        print(f"/songs-by-artist needs to receive an 'artist' parameter (eg. /songs-by-artist?artist=bob)")
        return error_page()

    # Queries are moved to the 'custom_scripts' (name pending)
    # folder for organization, so we can chuck our queries or processing in another file

    query = f"SELECT song_name as title, artist_name as artist FROM song, performed_by, artist "\
            f"WHERE song.song_id = performed_by.song_id "\
            f"AND performed_by.artist_id = artist.artist_id "\
            f"AND artist_name='{artist}'"

    return render_template("index.html", songs=execute_query(query))

@app.route("/selected-song", methods=["GET"])
def song_page():
    # Will need to implement method for POST (for submitting ratings/comments)
    if request.method != "GET":
        print(f"/selected-song received a {request.method} request when it should have received a 'GET' request.")
        return error_page()
    song_id = request.args.get("song_id", "")

    if not song_id:
        print(f"/selected-song needs to receive an 'song-id' parameter. How did you get here?")
        return error_page()

    # Will want to put query here that gets all comments

    # For template, want to pass in array of all comments (from query results)
    return render_template("songpage.html")

def error_page():
    return "" # should be a template or something

@app.route("/rate", methods=["GET"])
def rate_song_page():
	if request.method != "GET":
		print(f"/rate received a {request.method} request when it should have received a 'GET' request.")
		return error_page()
	song_id = request.args.get("song_id", "")

	if not song:
		print("/rate needs to receive a song-id parameter (eg. /rate?song=123)")
		return error_page()

	query = f"SELECT song_id as id, song_name as title "\
			f"FROM song "\
			f"WHERE song_id='{song}'"

	results = execute_query(query)[0]

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

	with Database() as cursor:
		cursor.execute(
			f"INSERT INTO rates (user_id, song_id, rating_value, comment) "\
			f"VALUES ('{user_id}', '{song_id}', '{rating_value}', '{comment}') "\
			f"ON CONFLICT DO NOTHING")

	return ""
#	return redirect("/")

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
