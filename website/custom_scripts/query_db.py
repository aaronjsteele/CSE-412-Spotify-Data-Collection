import psycopg2
import random
import string

def init_db_connection():
    """Initiates connection to DB server, returns a connection"""
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
DO NOT DELETE!!!

NOTE: A materialized table was created. In theory, we should be able
to use the materialized views for average rating and the total listens
on various songs. For reference, the query used to create the materialized
view for the avg_ratings is:

CREATE MATERIALIZED VIEW avg_ratings AS
SELECT song.song_id, ROUND(AVG(rates.rating_value),2) AS avg_rating
FROM song, rates
WHERE song.song_id = rates.song_id
GROUP BY song.song_id

This can be accessed like a normal table. This will need to be occasionally
updated (on new comment or initial connection?) through:

REFRESH MATERIALIZED VIEW avg_ratings

A similar view is created for the total listens to songs:

CREATE MATERIALIZED VIEW total_listens AS
SELECT song.song_id, COUNT(*) AS total
FROM song, listens_to
WHERE song.song_id = listens_to.song_id
GROUP BY song.song_id
"""

# This defines the 'standard' search query used in multiple searches on the
# main page.
general_search_query = (
"""
SELECT DISTINCT
    song_name AS title,
    artist_name AS artist,
    album_name AS album,
    avg_ratings.avg_rating AS average,
    total_listens.total AS num_listens,
    song.song_id AS song_id,
    artist.artist_id AS artist_id,
    popularity 
FROM
    song
    INNER JOIN performed_by ON song.song_id = performed_by.song_id
    INNER JOIN artist ON artist.artist_id = performed_by.artist_id
    INNER JOIN is_in ON song.song_id = is_in.song_id
    INNER JOIN album ON album.album_id = is_in.album_id
    INNER JOIN is_genre ON is_genre.artist_id = artist.artist_id
    INNER JOIN available_in ON available_in.song_id = song.song_id
    INNER JOIN avg_ratings ON avg_ratings.song_id = song.song_id
    INNER JOIN total_listens ON total_listens.song_id = song.song_id
"""
)

def list_all(cursor, sort_by_type):
    """
    List all songs when search bar is empty

    sort_by_type: how to sort the results, must be supported by 'sort_by_parser'
    """
    sort_by_str = sort_by_parser(sort_by_type)
    unprocessed_query = (
        general_search_query +
        f"ORDER BY {sort_by_str}"
    )
    print(unprocessed_query)
    query = cursor.mogrify(unprocessed_query)
    return execute_query_and_return(cursor, query)

def search_by(cursor, input_str, query_type, sort_by_type):
    """
    Perform a search query

    input_str: is the value to search for
    query_type: is what field to search for, must be supported by 'query_type_parser'
    sort_by_type: is what field to order by, must be supported by 'sort_by_parser'
    """
    sort_by_str = sort_by_parser(sort_by_type)
    query_type_str = query_type_parser(query_type)
    unprocessed_query = (
        general_search_query +
        f"WHERE {query_type_str} ILIKE %s\n"
        f"ORDER BY {sort_by_str}"
    )
    print(unprocessed_query)
    query = cursor.mogrify(unprocessed_query, (format_like_query(input_str),))
    return execute_query_and_return(cursor, query)

def get_artist_top_tracks(cursor, artist):
    """
    List the top tracks of an artist given the artist id
    """
    unprocessed_query = (
        """
        SELECT
            song_name AS song,
            song.song_id
        FROM artist
            INNER JOIN performed_by ON performed_by.artist_id = artist.artist_id
            INNER JOIN song ON song.song_id = performed_by.song_id
        WHERE is_top_track = true
            AND artist.artist_id = %s
        """
    )
    query = cursor.mogrify(unprocessed_query, (artist,))
    return execute_query_and_return(cursor, query)

def get_artist_genres(cursor, artist):
    """
    List all the genres associated with an artist given the artist id
    """
    unprocessed_query = (
        """
        SELECT
            genre_name AS genre
        FROM artist
            INNER JOIN is_genre ON is_genre.artist_id = artist.artist_id
        WHERE artist.artist_id = %s
        """
    )
    query = cursor.mogrify(unprocessed_query, (artist,))
    return execute_query_and_return(cursor, query)

def get_related_artists(cursor, artist):
    """
    List all the related artists given an artist id
    """
    unprocessed_query = (
        """
        SELECT
            artist_name AS artist,
            artist_id
        FROM artist
            INNER JOIN related_artists ON artist.artist_id = related_artists.artist_id_2
        WHERE related_artists.artist_id_1 = %s
        """
    )
    query = cursor.mogrify(unprocessed_query, (artist,))
    return execute_query_and_return(cursor, query)

def get_artist_albums(cursor, artist):
    """
    List all the albums the artist is apart of give an artist id
    """
    unprocessed_query = (
        """
        SELECT
            album.album_name AS album,
            album.album_id AS album_id,
            participates_in.album_group
        FROM artist
            INNER JOIN participates_in ON artist.artist_id = participates_in.artist_id
            INNER JOIN album ON album.album_id = participates_in.album_id
        WHERE artist.artist_id = %s
            AND participates_in.album_group = 'album'
        """
    )
    query = cursor.mogrify(unprocessed_query, (artist,))
    return execute_query_and_return(cursor, query)

def get_songs_in_album(cursor, album):
    """
    List all songs in an album give an album id
    """
    unprocessed_query = (
        """
        SELECT
            song.song_name AS song,
            song.song_id AS song_id
        FROM song
            INNER JOIN is_in ON song.song_id = is_in.song_id
            INNER JOIN album ON album.album_id = is_in.album_id
        WHERE album.album_id = %s
        """
    )
    query = cursor.mogrify(unprocessed_query, (album,))
    return execute_query_and_return(cursor, query)


def rate_song_page(cursor, song_id):
    """List all ratings given to a song with a certain id"""
    unprocessed_query = (
        f"SELECT song.song_name AS song_name, user_table.display_name AS username, rates.comment AS comment, rates.rating_value AS rating "\
        f"FROM song, rates, user_table "\
        f"WHERE song.song_id = rates.song_id "\
        f"    AND rates.user_id = user_table.user_id "\
        f"    AND song.song_id = %s"
    )
    unprocessed_query = (
        """
        SELECT
            song.song_name AS song_name,
            user_table.display_name AS username,
            rates.comment AS comment,
            rates.rating_value AS rating
        FROM song
            INNER JOIN rates ON song.song_id = rates.song_id
            INNER JOIN user_table ON rates.user_id = user_table.user_id
        WHERE song.song_id = %s
        """
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    return execute_query_and_return(cursor, query)

# Is done, gets song details
def get_song_info(cursor, song_id):
    unprocessed_query = (
        """
        SELECT
            song.song_name AS song_name,
            artist.artist_name AS artist_name,
            artist.artist_id AS artist_id,
            album.album_name AS album_name
        FROM song
            INNER JOIN performed_by ON song.song_id = performed_by.song_id
            INNER JOIN is_in ON song.song_id = is_in.song_id
            INNER JOIN artist ON performed_by.artist_id = artist.artist_id
            INNER JOIN album ON is_in.album_id = album.album_id
        WHERE song.song_id = %s
        """
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    return execute_query_and_return(cursor, query)

def get_countries_available(cursor, song_id):
    """Find what countries a song is available in from song_id"""
    unprocessed_query = (
        f"SELECT available_in.country_name AS country_name "\
        f"FROM song, available_in "\
        f"WHERE song.song_id = available_in.song_id "\
        f"  AND song.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    return execute_query_and_return(cursor, query)

def get_user_id(connection, username):
    """Find or create the user id for a given user

    If the user already exists, return the user_id
    If the user does not exist, create a new user and return their new user_id
    """
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
        print(f"User '{username}' does not exist! Generating new user.")
        new_user_id = get_random_alphanumeric_string(21)
        while check_if_user_id_exists(cursor, new_user_id):
            # In case the new user_id already exists
            print(f"ID '{new_user_id}' already exists, generating a new one.")
            new_user_id = get_random_alphanumeric_string(21)
        insert_new_user(connection, new_user_id, username)
        return new_user_id
    else:
        return results[0][0].strip()

def insert_new_user(connection, user_id, username):
    """Create a new entry in the user database"""
    cursor = connection.cursor()
    unprocessed_query = (
        f"INSERT INTO user_table (user_id, display_name) "\
        f"VALUES (%s, %s) "\
        f"ON CONFLICT DO NOTHING"
    )
    query = cursor.mogrify(unprocessed_query, (user_id, username))
    cursor.execute(query)
    connection.commit()

def check_if_user_id_exists(cursor, user_id):
    """Return whether the user_id is in the user_table"""
    unprocessed_query = (
        f"SELECT * "\
        f"FROM user_table "\
        f"WHERE user_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (user_id,))
    cursor.execute(query)
    return bool(cursor.fetchone())

# NOTE: FOR ANY COMMAND TO COMMIT DATA TO THE DATABASE, WE MUST
# PASS THE CONNECTION, NOT THE CURSOR
def rate(connection, user_id, song_id, rating_value, comment):
    """Creates or updates a rating on a song"""
    cursor = connection.cursor()
    # Case if user has NOT made rating on this song previously
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
    cursor.execute(query)
    print("Rate query executed! Committing now!")
    connection.commit()

def check_if_comment_made(cursor, user_id, song_id):
    """Checks if a user has made a comment on a song"""
    unprocessed_query = (
        f"SELECT * "\
        f"FROM rates "\
        f"WHERE user_id = %s AND song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (user_id, song_id))
    cursor.execute(query)
    results = cursor.fetchall()
    return bool(results)

def get_average_rating(cursor, song_id):
    """Find the average rating for a song"""
    unprocessed_query = (
        f"SELECT avg_table.avg_rating "\
        f"FROM ( "\
        f"      SELECT song.song_id AS song_id, ROUND(AVG(rates.rating_value),2) AS avg_rating "\
        f"      FROM song, rates "\
        f"      WHERE song.song_id = rates.song_id "\
        f"      GROUP BY song.song_id "\
        f"     ) AS avg_table "\
        f"WHERE avg_table.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    cursor.execute(query)
    results = cursor.fetchall()
    return results[0][0]

def get_total_listens(cursor, song_id):
    """Find the number of listens for a given song"""
    unprocessed_query = (
        f"SELECT count_table.total_listens "\
        f"FROM ( "\
        f"      SELECT song.song_id AS song_id, COUNT(listens_to.user_id) AS total_listens "\
        f"      FROM song, listens_to "\
        f"      WHERE song.song_id = listens_to.song_id "\
        f"      GROUP BY song.song_id "\
        f"     ) AS count_table "\
        f"WHERE count_table.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    cursor.execute(query)
    results = cursor.fetchall()
    return results[0][0]

def execute_query_and_return(cursor, query):
    """Execute a query and return the result as a list of dicts"""
    cursor.execute(query)
    results = cursor.fetchall()
    keys = [column.name for column in cursor.description]
    return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]

def check_if_listened(cursor, user_id, song_id):
    unprocessed_query = (
        f"SELECT * "\
        f"FROM listens_to "\
        f"WHERE listens_to.user_id = %s AND listens_to.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (user_id, song_id))
    cursor.execute(query)
    results = cursor.fetchall()
    if not results:
        return False
    else:
        return True

def add_listen(connection, user_id, song_id):
    cursor = connection.cursor()
    unprocessed_query = (
        f"INSERT INTO listens_to (user_id, song_id) "\
        f"VALUES (%s, %s) "\
        f"ON CONFLICT DO NOTHING"
    )
    query = cursor.mogrify(unprocessed_query, (user_id, song_id))
    cursor.execute(query)
    connection.commit()

# Gets details on if a song is explicit, its length,
# and the countries in which it is available.
# Is special -- returns an array with 4 elements:
#   1. Whether it is or is not explicit
#   2. Length of the song
#   3. Popularity
#   4. List of countries song is available in
def get_song_details(cursor, song_id):
    unprocessed_query = (
        f"SELECT is_explicit, duration, popularity "\
        f"FROM song "\
        f"WHERE song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    cursor.execute(query)
    results = cursor.fetchall()
    to_return = [results[0][0], convert_to_time(results[0][1]), results[0][2], get_countries(cursor, song_id)]
    return to_return

def get_countries(cursor, song_id):
    unprocessed_query = (
        f"SELECT available_in.country_name AS country_name "\
        f"FROM song, available_in "\
        f"WHERE song.song_id = available_in.song_id "\
        f"  AND song.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    cursor.execute(query)
    results = cursor.fetchall()
    output = ""
    results_len = len(results)-1
    for entry in results:
        output += entry[0].strip()
        if results.index(entry) != results_len:
            output += ", "
    return output

def convert_to_time(millis):
    seconds = (millis/1000)%60
    seconds = int(seconds)
    minutes = (millis/(1000*60))%60
    minutes = int(minutes)
    return ("%d:%d" % (minutes, seconds))

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
    elif sort_by_type == "ratings":
        string = "avg_table.avg_rating DESC"
    elif sort_by_type == "listens":
        string = "count_table.total DESC"
    return string

def query_type_parser(query_type):
    string = ""
    if query_type in {"artist", "song", "album"}:
        string = f"{query_type}.{query_type}_name"
    elif query_type == "genre":
        string = f"is_genre.genre_name"
    elif query_type == "country":
        string = f"available_in.country_name"
    return string

def format_like_query(input_str):
    return '%' + input_str + '%'

# Thanks to https://pynative.com/python-generate-random-string/
# for this code for a random string
def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str

class DotDict(dict):
    """The same as dict except you can use dot notation and it will not crash if you try to access a bad name"""
    def __getattr__(self, key):
        if key not in self:
            print(f"There was an error while trying to access '{key}' from {self}")
            return "Database Error"
        else:
            return self[key]
