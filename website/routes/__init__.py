from website import app
from flask import render_template, request, g
import os
from website.custom_scripts import *

# NOTE: g is a flask global variable for the current context.
@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        # logic for querying database and return data
        search_string = request.form['inputString']
        query_type = request.form['inputQuery']
        sort_by_type = request.form['sortby']
        if search_string == "":
            return render_template("index.html", songs=query_db.list_all(get_db().cursor(), sort_by_type))
        else:
            return render_template("index.html", songs=query_db.search_by(get_db().cursor(), search_string, query_type, sort_by_type))
    else:
        return "oh no", 405

@app.route("/songs-by-artist", methods=["GET"])
def songs_by_artist():
	if request.method != "GET":
		print(f"/songs-by-artist recieved a {request.method} request when it should have recieved a 'GET' request.")
		return error_page()
	artist = request.args.get("artist", "")

	if not artist:
		print(f"/songs-by-artist needs to recieve an 'artist' parameter (eg. /songs-by-artist?artist=bob)")
		return error_page()

	# Queries are moved to the 'custom_scripts' (name pending)
	# folder for organization, so we can chuck our queries or processing in another file

	query = f"SELECT song_name as title, artist_name as artist FROM song, performed_by, artist "\
			f"WHERE song.song_id = performed_by.song_id "\
			f"AND performed_by.artist_id = artist.artist_id "\
			f"AND artist_name='{artist}'"

	return render_template("index.html", songs=execute_query(query))

def error_page():
	return "" # should be a template or something

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
