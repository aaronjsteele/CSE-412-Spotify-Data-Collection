import requests
import json
import psycopg2

# Config contains the API keys and whatnot
import config

# Note that this only handles 'regular' arrays, not some of the nested ones
# defined in this file.
#
# This also does not work with sets

# DO NOT USE THIS!!!!
# Use the built-in psycopg2 tools instead!
"""
def insert_into_SQL_database(cursor, table_name, table_labels, data_array):
    command = "INSERT INTO " + table_name + " " + table_labels + " VALUES "
    for i in range(len(data_array)):
        el = data_array[i]
        command += '('
        for j in range(len(el)):
            command += "\'" + el[j] + "\'"
            if j != len(el)-1:
                command += ","
        command += ")"
        if i != len(data_array)-1:
            command += ","
    command += " ON CONFLICT DO NOTHING;"
    print(command)
    cursor.execute(command)
    cursor.commit()
    return command
"""

def insert_into_SQL_database(cursor, table_name, table_labels, data_array):
    for el in data_array:
        to_insert = "("
        for j in range(len(el)):
            to_insert += "\'" + el[j] + "\'"
            if j != len(el)-1:
                to_insert += ","
        to_insert += ")"

# Credit to https://stmorse.github.io/journal/spotify-api.html for guide on Spotify API access

AUTH_URL = 'https://accounts.spotify.com/api/token'

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': config.CLIENT_ID,
    'client_secret': config.CLIENT_SECRET,
})

# convert the response to JSON
auth_response_data = auth_response.json()
# save the access token
access_token = auth_response_data['access_token']

headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}

# --------------------------------------------------------------
# Connect to Database
connection = psycopg2.connect(
    host = config.host,
    port = config.port,
    user = config.user,
    password = config.password,
    database = config.database
    )
cursor=connection.cursor()

# --------------------------------------------------------------
# Now we have an access token for access
BASE_URL = 'https://api.spotify.com/v1/'

artist_id_list = ['36QJpDe2go2KgaRleHCDTp']

artists_to_insert = []
genres_to_insert = set()
is_genre_to_insert = []

songs_to_insert = []
is_in_album_to_insert = []
albums_to_insert = []

performed_by_insert = []
participates_in_insert = []

countries = set()
in_countries = []

r = requests.get(BASE_URL + 'artists/' + '36QJpDe2go2KgaRleHCDTp' + "/top-tracks", headers = headers, params={'country' : 'US'})
d = r.json()
print(d['tracks'][0]['duration_ms'])

# Gather data on artists
for a_id in artist_id_list:
    r = requests.get(BASE_URL + 'artists/' + a_id, headers = headers)
    d = r.json()
    artists_to_insert.append([d['name'],a_id])
    genres_to_insert.update(d['genres'])
    is_genre_to_insert.append([d['genres'],a_id])

    # Now, we get the top tracks for an artist and use those as the tracks for our
    # sample data set. From this we can also get the albums we want
    r2 = requests.get(BASE_URL + 'artists/' + a_id + "/top-tracks", headers = headers, params={'country' : 'US'})
    d2 = r2.json()
    # First, get data on the song (note that the table has song_id, song_name, is_explicit, popularity, duration)
    for i in range(10):
        song_id = d2['tracks'][i]['id']
        song_name = d2['tracks'][i]['name']
        song_pop = d2['tracks'][i]['popularity']
        if d2['tracks'][i]['explicit']:
            song_explicit = 1
        else:
            song_explicit = 0
        song_duration = d2['tracks'][i]['duration_ms']
        songs_to_insert.append([song_id,song_name,song_explicit,song_pop,song_duration])
        print([song_id,song_name,song_explicit,song_pop,song_duration])

        # Now that we have data on a song, we should get which album it's in
        album_id = d2['tracks'][i]['album']['id']
        album_name = d2['tracks'][i]['album']['name']
        albums_to_insert.append([album_id, album_name])
        print([album_id, album_name])

        is_in_album_to_insert.append([song_id, album_id])

        # NOTE: Since for now we're simplifying things by using the top tracks of an
        # artist to GET the tracks,  the 'is_top_track' is 'random' right now (i odd is 1, i even is 0)
        performed_by_insert.append([song_id, a_id, i%2])
        
        # Now, we get the album from the album_id and pull out the album_group (needed for 
        # participates relation) and the countries (needed for its table and the relation with
        # the tracks)
        r3 = requests.get(BASE_URL + 'albums/' + album_id, headers = headers)
        d3 = r3.json()

        countries.update(d3['available_markets'])
        print(d3['available_markets'])

        in_countries.append([d3['available_markets'], song_id])

        # For now, participates_in will have dummy data (this method of filling
        # albums only gets artists who made the albums)
        participates_in_insert.append(['album', a_id, album_id])

for el in genres_to_insert:
    print(el)

print(albums_to_insert)
print(is_in_album_to_insert)
# In theory, now we have a boatload of data for everything except our users. We will fill that later.
# Now, we update the SQL server
for el in artists_to_insert:
    cursor.execute("""
        INSERT INTO artist (artist_name, artist_id)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1])
    )

for el in genres_to_insert:
    cursor.execute("""
        INSERT INTO genre (genre_name)
        VALUES (%s) ON CONFLICT DO NOTHING;
        """,
        (el,)
    )

for el in is_genre_to_insert:
    for g in el[0]:
        cursor.execute("""
            INSERT INTO is_genre (genre_name, artist_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """,
            (g, el[1])
        )

for el in songs_to_insert:
    cursor.execute("""
        INSERT INTO song (song_id, song_name, is_explicit, popularity, duration)
        VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1], bool(el[2]), el[3], el[4])
    )

for el in albums_to_insert:
    cursor.execute("""
        INSERT INTO album (album_id, album_name)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1])
    )

for el in is_in_album_to_insert:
    cursor.execute("""
        INSERT INTO is_in (song_id, album_id)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1])
    )

for el in performed_by_insert:
    cursor.execute("""
        INSERT INTO performed_by (song_id, artist_id, is_top_track)
        VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1], bool(el[2]))
    )

for el in countries:
    cursor.execute("""
        INSERT INTO countries (country_name)
        VALUES (%s) ON CONFLICT DO NOTHING;
        """,
        (el,)
    )

print("now working on in_countries")

for el in in_countries:
    print(el)
    for g in el[0]:
        cursor.execute("""
            INSERT INTO available_in (country_name, song_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """,
            (g, el[1])
        )

for el in participates_in_insert:
    cursor.execute("""
        INSERT INTO participates_in (album_group, artist_id, album_id)
        VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1], el[2])
    )

connection.commit()

cursor.close()
connection.close()