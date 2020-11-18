from website import app
from flask import render_template, request, g
import os
from website.custom_scripts import *

# NOTE: g is a flask global variable for the current context.
@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return render_template("index.html", a=[1, 2, 3])
    elif request.method == "POST":
        # logic for querying database and return data
        search_string = request.form['inputString']
        query_type = request.form['inputQuery']

        return render_template("index.html", songs=query_db.search_by_artist(get_db().cursor(), search_string))
        #return "{first_name}, bye".format(first_name=request.form.get("firstname", "???"))
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

"""
def execute_query(query):
	import website.config as config
	import psycopg2
	connection = psycopg2.connect(
		host = config.host,
		port = config.port,
		user = config.user,
		password = config.password,
		database = config.database
	)
	cursor = connection.cursor()
	cursor.execute(query)
	results = cursor.fetchall()
	keys = [column.name for column in cursor.description]
	connection.close()
	return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]
"""

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
	#Closes the database again at the end of the request.
	if hasattr(g, 'postgres_db'):
		g.postgres_db.close()
