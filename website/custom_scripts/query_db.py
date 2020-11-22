import psycopg2
import random
import string

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

def list_all(cursor, sort_by_type):
    # function that list all the songs when the search bar is empty
    sort_by_str = sort_by_parser(sort_by_type)
    unprocessed_query = (
        f"SELECT song_name AS title, artist_name AS artist, album_name AS album, avg_table.avg_rating AS average, count_table.total AS num_listens, song.song_id AS song_id "\
        f"FROM song, artist, performed_by, album, is_in, "\
        f"    ( "\
        f"        SELECT song.song_id, ROUND(AVG(rates.rating_value),2) AS avg_rating "\
        f"        FROM song, rates "\
        f"        WHERE song.song_id = rates.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS avg_table, "\
        f"    ( "\
        f"        SELECT song.song_id, COUNT(*) AS total "\
        f"        FROM song, listens_to "\
        f"        WHERE song.song_id = listens_to.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS count_table "\
        f"WHERE song.song_id = performed_by.song_id  "\
        f"    AND performed_by.artist_id = artist.artist_id  "\
        f"    AND song.song_id = is_in.song_id  "\
        f"    AND is_in.album_id = album.album_id  "\
        f"    AND avg_table.song_id = song.song_id "\
        f"    AND count_table.song_id = song.song_id "\
        f"ORDER BY {sort_by_str}"
    )
    query = cursor.mogrify(unprocessed_query)
    return execute_query_and_return(cursor, query)

def search_by(cursor, input_str, query_type, sort_by_type): 
    # function that performs a query based on the query type
    sort_by_str = sort_by_parser(sort_by_type)
    unprocessed_query = (
        f"SELECT song_name AS title, artist_name AS artist, album_name AS album, avg_table.avg_rating AS average, count_table.total AS num_listens, song.song_id AS song_id "\
        f"FROM song, artist, performed_by, album, is_in, "\
        f"    ( "\
        f"        SELECT song.song_id, ROUND(AVG(rates.rating_value),2) AS avg_rating "\
        f"        FROM song, rates "\
        f"        WHERE song.song_id = rates.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS avg_table, "\
        f"    ( "\
        f"        SELECT song.song_id, COUNT(*) AS total "\
        f"        FROM song, listens_to "\
        f"        WHERE song.song_id = listens_to.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS count_table "\
        f"WHERE song.song_id = performed_by.song_id  "\
        f"    AND performed_by.artist_id = artist.artist_id  "\
        f"    AND song.song_id = is_in.song_id  "\
        f"    AND is_in.album_id = album.album_id  "\
        f"    AND avg_table.song_id = song.song_id "\
        f"    AND count_table.song_id = song.song_id "\
        f"    AND {query_type}.{query_type}_name ILIKE %s "\
        f"ORDER BY {sort_by_str}"
    )
    query = cursor.mogrify(unprocessed_query, (format_like_query(input_str),))
    return execute_query_and_return(cursor, query)

def songs_by_artist(cursor, artist):
    unprocessed_query = (
        f"SELECT song_name as title, artist_name as artist FROM song, performed_by, artist "\
        f"WHERE song.song_id = performed_by.song_id "\
        f"AND performed_by.artist_id = artist.artist_id "\
        f"AND artist_name='{artist}'"
    )
    query = cursor.mogrify(unprocessed_query)
    return execute_query_and_return(cursor, query)


def rate_song_page(cursor, song_id):
    unprocessed_query = (
        f"SELECT song.song_name AS song_name, user_table.display_name AS username, rates.comment AS comment, rates.rating_value AS rating "\
        f"FROM song, rates, user_table "\
        f"WHERE song.song_id = rates.song_id "\
        f"    AND rates.user_id = user_table.user_id "\
        f"    AND song.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    return execute_query_and_return(cursor, query)

# Is done, gets song details
def get_song_info(cursor, song_id):
    unprocessed_query = (
        f"SELECT song.song_name AS song_name, artist.artist_name AS artist_name, album.album_name AS album_name "\
        f"FROM song, album, artist, is_in, performed_by "\
        f"WHERE song.song_id = performed_by.song_id "\
        f"  AND performed_by.artist_id = artist.artist_id "\
        f"  AND song.song_id = is_in.song_id "\
        f"  AND is_in.album_id = album.album_id "\
        f"  AND song.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    return execute_query_and_return(cursor, query)

def get_countries_available(cursor, song_id):
    unprocessed_query = (
        f"SELECT available_in.country_name AS country_name "\
        f"FROM song, available_in "\
        f"WHERE song.song_id = available_in.song_id "\
        f"  AND song.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    return execute_query_and_return(cursor, query)

# Gets ID of user posting a comment. If the user does not exist,
# a new ID is created and entered into the database.
def get_user_id(connection, username):
    cursor = connection.cursor()
    unprocessed_query = (
        f"SELECT user_id "\
        f"FROM user_table "\
        f"WHERE display_name = %s"
    )
    query = cursor.mogrify(unprocessed_query, (username,))
    cursor.execute(query)
    results = cursor.fetchall()

    # Case if user does not exist
    if not results:
        print("User does not exist! Generating new user.")
        new_user_id = get_random_alphanumeric_string(21)
        insert_new_user(connection, new_user_id, username)
        return new_user_id
    else:
        return results[0][0].strip()

def insert_new_user(connection, user_id, username):
    cursor = connection.cursor()
    unprocessed_query = (
        f"INSERT INTO user_table (user_id, display_name) "\
        f"VALUES (%s, %s) "\
        f"ON CONFLICT DO NOTHING"
    )
    query = cursor.mogrify(unprocessed_query, (user_id, username))
    cursor.execute(query)
    connection.commit()

# NOTE: FOR ANY COMMAND TO COMMIT DATA TO THE DATABASE, WE MUST
# PASS THE CONNECTION, NOT THE CURSOR
#
# Creates a rating on a song. Either enters a new entry or updates an existing
# entry depending if one has been made previously.
def rate(connection, user_id, song_id, rating_value, comment):
    cursor = connection.cursor()
    # Case if user has NOT made rating on song previously
    if not check_if_comment_made(cursor, user_id, song_id):
        unprocessed_query = (
            f"INSERT INTO rates (user_id, song_id, rating_value, comment) "\
            f"VALUES (%s, %s, %s, %s) "\
            f"ON CONFLICT DO NOTHING"
        )
        query = cursor.mogrify(unprocessed_query, (user_id, song_id, rating_value, comment))
    else:
        unprocessed_query = (
            f"UPDATE rates "\
            f"SET comment = %s, rating_value = %s "\
            f"WHERE user_id = %s AND song_id = %s"
        )
        query = cursor.mogrify(unprocessed_query, (comment, rating_value, user_id, song_id))
    print(query)
    cursor.execute(query)
    print("Rate query executed! Committing now!")
    connection.commit()

# Checks if a user has made a comment on a song
def check_if_comment_made(cursor, user_id, song_id):
    unprocessed_query = (
        f"SELECT * "\
        f"FROM rates "\
        f"WHERE user_id=%s AND song_id=%s"
    )
    query = cursor.mogrify(unprocessed_query, (user_id, song_id))
    cursor.execute(query)
    results = cursor.fetchall()
    if not results:
        return False
    else:
        return True

def get_average_rating(cursor, song_id):
    unprocessed_query = (
        f"SELECT avg_table.avg_rating "\
        f"FROM ( "\
        f"      SELECT song.song_id AS song_id, ROUND(AVG(rates.rating_value),2) AS avg_rating "\
        f"      FROM song, rates "\
        f"      GROUP BY song.song_id "\
        f"     ) AS avg_table "\
        f"WHERE avg_table.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    cursor.execute(query)
    results = cursor.fetchall()
    print(results[0][0])
    return results[0][0]

def get_total_listens(cursor, song_id):
    unprocessed_query = (
        f"SELECT count_table.total_listens "\
        f"FROM ( "\
        f"      SELECT song.song_id AS song_id, COUNT(listens_to.user_id) AS total_listens "\
        f"      FROM song, listens_to "\
        f"      GROUP BY song.song_id "\
        f"     ) AS count_table "\
        f"WHERE count_table.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    cursor.execute(query)
    results = cursor.fetchall()
    print(results[0][0])
    return results[0][0]

def execute_query_and_return(cursor, query):
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
"""
def get_song_details(cursor, song_id):
    unprocessed_query = 
"""

# Thanks to https://pynative.com/python-generate-random-string/
# for this code for a random string
def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str

class DotDict(dict):
    def __getattr__(self, key):
        if key not in self:
            print(f"There was an error while trying to access '{key}' from {self}")
            return "Database Error"
        else:
            return self[key]