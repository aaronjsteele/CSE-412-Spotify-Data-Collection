import psycopg2

def test():
    print("hello")
    return

# Initiates connection to DB server, returns a connection
def init_db_connection():
    import website.config as config
    connection = psycopg2.connect(
        host = config.host,
        port = config.port,
        user = config.user,
        password = config.password,
        database = config.database
    )
    return connection
    """
    cursor.execute(query)
    results = cursor.fetchall()
    keys = [column.name for column in cursor.description]
    connection.close()
    return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]
    """
#is this doing anything here? Can we delete?
query = f"SELECT song_name AS title, artist_name AS artist, album_name AS album FROM song, performed_by, artist "\
        f"WHERE song.song_id = performed_by.song_id "\
        f"AND performed_by.artist_id = artist.artist_id"
'''
def search_by_artist(cursor, input_str, query_type):
    """
    An example function to perform a query where we are searching by artist.
    Note that the cursor and search term is passed in.

    NOTE: Due to psycopg2 syntax, a '%' symbol in the LIKE clause
    must be escaped with a '%'.
    """
    query = cursor.mogrify(
        """
        SELECT song_name AS title, artist_name AS artist, album_name AS album
        FROM song, performed_by, artist, album, is_in
        WHERE song.song_id = performed_by.song_id
            AND performed_by.artist_id = artist.artist_id
            AND song.song_id = is_in.song_id
            AND is_in.album_id = album.album_id
            AND artist_name ILIKE %s
        """,
        (format_like_query(input_str),)
    )
    print(query)
    cursor.execute(query)
    results = cursor.fetchall()
    keys = [column.name for column in cursor.description]
    return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]
'''
def list_all(cursor, sort_by_type):
    # function that list all the songs when the search bar is empty
    sort_by_str = sort_by_parser(sort_by_type)
    query = f"SELECT song_name AS title, artist_name AS artist "\
            f"FROM song, artist, album, performed_by, is_in "\
            f"WHERE song.song_id = performed_by.song_id "\
            f"AND performed_by.artist_id = artist.artist_id "\
            f"AND song.song_id = is_in.song_id "\
            f"AND is_in.album_id = album.album_id "\
            f"ORDER BY {sort_by_str}"
    cursor.execute(query)
    results = cursor.fetchall()
    keys = [column.name for column in cursor.description]
    return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]

def search_by(cursor, input_str, query_type, sort_by_type): 
    # function that performs a query based on the query type
    sort_by_str = sort_by_parser(sort_by_type)
    query = f"SELECT song_name AS title, artist_name AS artist "\
            f"FROM song, artist, performed_by, album, is_in "\
            f"WHERE song.song_id = performed_by.song_id "\
            f"AND performed_by.artist_id = artist.artist_id "\
            f"AND song.song_id = is_in.song_id "\
            f"AND is_in.album_id = album.album_id "\
            f"AND {query_type}_name = '{input_str}' "\
            f"ORDER BY {sort_by_str}"
    cursor.execute(query)
    results = cursor.fetchall()
    keys = [column.name for column in cursor.description]
    return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]

def sort_by_parser(sort_by_type):
    string = ""
    if sort_by_type == "title":
        string = "song_name"
    elif sort_by_type == "artist":
        string = "artist_name"
    elif sort_by_type == "album":
        string = "album_name"
    elif sort_by_type == "popularity":
        string = "popularity DESC"
    return string

def format_like_query(input_str):
    return '%' + input_str + '%'

class DotDict(dict):
	def __getattr__(self, key):
		if key not in self:
			print(f"There was an error while trying to access '{key}' from {self}")
			return "Database Error"
		else:
			return self[key]