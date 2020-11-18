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

query = f"SELECT song_name as title, artist_name as artist FROM song, performed_by, artist "\
                f"WHERE song.song_id = performed_by.song_id "\
                f"AND performed_by.artist_id = artist.artist_id"

def simple_search(cursor, input_str, query_type):
    """
    An example function to perform a query where we are searching by artist.
    Note that the cursor and search term is passed in.

    Queries get results by similar artist, album, or song title.

    NOTE: Due to psycopg2 syntax, wrap strings in the format_like_query
    function when calling an ILIKE query.
    """
    base_query = (
        f"SELECT song_name AS title, artist_name AS artist "\
        f"FROM song, performed_by, artist "\
        f"WHERE song.song_id = performed_by.song_id "\
        f"  AND performed_by.artist_id = artist.artist_id "\
        f"  AND {query_type}_name ILIKE %s"
    )
    query = cursor.mogrify(base_query, (format_like_query(input_str),))
    print(query)
    cursor.execute(query)
    results = cursor.fetchall()
    keys = [column.name for column in cursor.description]
    return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]

def format_like_query(input_str):
    return '%' + input_str + '%'

class DotDict(dict):
	def __getattr__(self, key):
		if key not in self:
			print(f"There was an error while trying to access '{key}' from {self}")
			return "Database Error"
		else:
			return self[key]