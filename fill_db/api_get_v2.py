import requests
import json
import psycopg2
import sys

# Config contains the API keys and whatnot
import config

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

r = requests.get(BASE_URL + 'artists/' + '36QJpDe2go2KgaRleHCDTp' + '/albums', headers = headers, params={'country' : 'US'})
d = r.json()
print(d['items'][0])
for el in d['items']:
    print(el)

# Gather data on artists:
for a_id in artist_id_list:
    # Gets information about an artist
    r = requests.get(BASE_URL + 'artists/' + a_id, headers = headers)
    d = r.json()
    artists_to_insert.append([d['name'],a_id])
    genres_to_insert.update(d['genres'])
    is_genre_to_insert.append([d['genres'],a_id])

    # This section gets the ID's of which songs are the top songs of an artist.
    # These are used later, when the songs are grabbed.
    top_track_ids = []
    r4 = requests.get(BASE_URL + 'artists/' + a_id + '/top-tracks', headers = headers, params={'country' : 'US'})
    print(r4)
    d4 = r4.json()
    for top_song in d4['tracks']:
        top_song_id = top_song['id']
        top_track_ids.append(top_song_id)

    # Gets information about the artist's albums. Will get at most 20 albums
    r2 = requests.get(BASE_URL + 'artists/' + a_id + '/albums', headers = headers, params={'country' : 'US'})
    d2 = r2.json()
    # We now want to iterate through all the returned albums
    for album in d2['items']:
        album_id = album['id']
        album_name = album['name']
        album_group = album['album_group']
        albums_to_insert.append([album_id, album_name])
        participates_in_insert.append([album_group, a_id, album_id])

        # For each returned album, we want to iterate and get the songs.
        r3 = requests.get(BASE_URL + 'albums/' + album_id + '/tracks', headers = headers, params={'limit' : '50'})
        print(r3)
        d3 = r3.json()
        print(d3)
        for song in d3['items']:
            song_id = song['id']
            song_name = song['name']
            # We need to make an API call to the tracks object to get a song's popularity
            r5 = requests.get(BASE_URL + 'tracks/' + song_id, headers = headers)
            d5 = r5.json()
            song_pop = d5['popularity']
            if song['explicit']:
                song_explicit = 1
            else:
                song_explicit = 0
            song_duration = song['duration_ms']

            if song_id in top_track_ids:
                is_top_track = 1
            else:
                is_top_track = 0

            # Adding song information to relevant arrays
            songs_to_insert.append([song_id, song_name, song_explicit, song_pop, song_duration])
            is_in_album_to_insert.append([song_id, album_id])
            performed_by_insert.append([song_id, a_id, is_top_track])

            # Information on countries
            countries.update(song['available_markets'])
            in_countries.append([song['available_markets'], song_id])

# --------------------------------------------------------------
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

num_in_countries = len(in_countries)
i = 0
for el in in_countries:
    print(i + " of " + num_in_countries + "\n" + el)
    for g in el[0]:
        cursor.execute("""
            INSERT INTO available_in (country_name, song_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """,
            (g, el[1])
        )
    i += 1

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