from website import app
from flask import render_template, request
import os


@app.route("/", methods=["GET", "POST"])
def main():
#    if request.method == "GET":
#        return render_template("index.html", a=[1, 2, 3])
#    elif request.method == "POST":
        # logic for querying database and return data
    if request.method == "GET":
        query = f"SELECT song_name as title, artist_name as artist, song.song_id as id, rating.average_rating as rating "\
                f"FROM song, performed_by, artist, "\
                f"(SELECT song_id, avg(rating_value) as average_rating FROM rates GROUP BY song_id) as rating "\
                f"WHERE song.song_id = performed_by.song_id "\
                f"AND song.song_id = rating.song_id "\
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

	query = f"SELECT song_name as title, artist_name as artist, song.song_id as id "\
			f"FROM song, performed_by, artist "\
			f"WHERE song.song_id = performed_by.song_id "\
			f"AND performed_by.artist_id = artist.artist_id "\
			f"AND artist_name='{artist}'"

	return render_template("index.html", songs=execute_query(query))

def error_page():
	return "<h1>ERROR</h1>" # should be a template or something

class Database:
	def __init__(self):
		import website.config as config
		import psycopg2

	def __enter__(self):
		import website.config as config
		import psycopg2

		self.connection = psycopg2.connect(
			host = config.host,
			port = config.port,
			user = config.user,
			password = config.password,
			database = config.database
		)
		return self.connection.cursor()

	def __exit__(self, *args):
		self.connection.commit()
		self.connection.close()
		del self.connection

def execute_query(query):
	with Database() as cursor:
		cursor.execute(query)
		results = cursor.fetchall()
		keys = [column.name for column in cursor.description]
	return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]


@app.route("/rate", methods=["GET"])
def rate_song_page():
	if request.method != "GET":
		print(f"/rate recieved a {request.method} request when it should have recieved a 'GET' request.")
		return error_page()
	song = request.args.get("song", "")

	if not song:
		print(f"/rate needs to recieve a song-id parameter (eg. /rate?song=123)")
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
