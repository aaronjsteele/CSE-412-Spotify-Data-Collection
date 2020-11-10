from website import app
from flask import render_template, request
import os


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "GET":
        return render_template("index.html", a=[1, 2, 3])
    elif request.method == "POST":
        # logic for querying database and return data
        query = f"SELECT song_name as title, artist_name as artist FROM song, performed_by, artist "\
                f"WHERE song.song_id = performed_by.song_id "\
                f"AND performed_by.artist_id = artist.artist_id"

        return render_template("index.html", songs=execute_query(query))
        #return "{first_name}, fuck off".format(first_name=request.form.get("firstname", "???"))
    else:
        return "fuck yourself", 405

@app.route("/songs-by-artist", methods=["GET"])
def songs_by_artist():
	if request.method != "GET":
		print(f"/songs-by-artist recieved a {request.method} request when it should have recieved a 'GET' request.")
		return error_page()
	artist = request.args.get("artist", "")

	if not artist:
		print(f"/songs-by-artist needs to recieve an 'artist' parameter (eg. /songs-by-artist?artist=bob)")
		return error_page()

	query = f"SELECT song_name as title, artist_name as artist FROM song, performed_by, artist "\
			f"WHERE song.song_id = performed_by.song_id "\
			f"AND performed_by.artist_id = artist.artist_id "\
			f"AND artist_name='{artist}'"

	return render_template("index.html", songs=execute_query(query))

def error_page():
	return "" # should be a template or something

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
	return [{key: data for key, data in zip(keys, row)} for row in results]
