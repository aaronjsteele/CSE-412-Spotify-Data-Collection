# --------------------------------------------------------
# This file generates a number of fake usernames and
# comments to place into the SQL server, as we do not
# have real users. Some SQL queries are used to get the
# necessary parameters (so we can pair up a fake user
# with some song in the database, for example).
# --------------------------------------------------------

import psycopg2
import random
import string
from faker import Faker
import config
import sys

# Thanks to https://pynative.com/python-generate-random-string/
# for this code for a random string
def get_random_alphanumeric_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    result_str = ''.join((random.choice(letters_and_digits) for i in range(length)))
    return result_str

# --------------------------------------------------------
# Connect to Database
connection = psycopg2.connect(
    host = config.host,
    port = config.port,
    user = config.user,
    password = config.password,
    database = config.database
    )
cursor=connection.cursor()
# --------------------------------------------------------
# First, we want to select all song_id values, so we can
# choose some.
cursor.execute("SELECT song.song_id FROM song INNER JOIN performed_by ON song.song_id = performed_by.song_id WHERE performed_by.artist_id = '36QJpDe2go2KgaRleHCDTp'")
rows = cursor.fetchall()
song_id_list = []
for row in rows:
    song_id_list.append(row[0].strip())

# For artist relationships, we create all tuples that
# are not artists related to themselves. We will then
# add a random selection of these.
cursor.execute("""
    SELECT a1.artist_id, a2.artist_id
    FROM artist AS a1, artist AS a2
    WHERE a1.artist_id != a2.artist_id;
""")
rows = cursor.fetchall()
artist_id_list = []
for row in rows:
    artist_id_list.append([row[0].strip(), row[1].strip()])

# Finally, we select all tuples of artist_id and album_id
# That DO NOT already have a relationship in
# participates_in, so we can add one.
# NOTE: In Spotify valid album_group values are "album",
#       "single", "compilation", "appears_on". We will
#       add "appears_on" (wrongly) to some of these
cursor.execute("""
    (SELECT artist_id, album_id FROM artist, album)
    EXCEPT
    (SELECT artist_id, album_id FROM participates_in)
""")
rows = cursor.fetchall()
participates_in_list = []
for row in rows:
    participates_in_list.append([row[0].strip(), row[1].strip()])
# --------------------------------------------------------
# Now, let's generate some fake users to enter into our
# database.
fake = Faker()
Faker.seed(1337)
random.seed(10000)

user_list = []
for _ in range(100):
    user_id = get_random_alphanumeric_string(21)
    username = fake.simple_profile()['username']
    user_list.append([user_id, username])

# We have some users. Now they need to listen to
# some songs. Each user listens to a random number
# of songs from 10 - (# songs - 10) from the query
# earlier.
listens_to_list = []
for el in user_list:
    songs_listened_to = random.sample(song_id_list, random.randint(10, 100))
    print(len(songs_listened_to))
    for song_id in songs_listened_to:
        listens_to_list.append([el[0], song_id])

print(listens_to_list)

# A similar approach is given to construct the
# data for the 'rates' table, except additional
# data is added for the rating_value (an integer
# from 1 to 10) and a comment
rates_list = []
for el in user_list:
    songs_rated = random.sample(song_id_list, random.randint(10, 30))
    for song_id in songs_rated:
        rates_list.append([el[0], song_id, random.randint(1,10), fake.sentence()])

# Selects a random amount of artists to be related
# to each other.
related_to_list = random.sample(artist_id_list, random.randint(30, 50))

# Finally, we add some random elements to the
# participates_in relationship with an album_group
# of "appears_on"
participates_in_to_add = []
temp = random.sample(participates_in_list, 100)
for row in temp:
    participates_in_to_add.append(["appears_on" ,row[0], row[1]])

# --------------------------------------------------------
# Finally, we add our data to the Database

print("Now adding elements to \'user_table\'")
for el in user_list:
    print("adding ", el)
    cursor.execute("""
        INSERT INTO user_table (user_id, display_name)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1])
    )

print("Now adding elements to \'listens_to\'")
for el in listens_to_list:
    print("adding ", el)
    cursor.execute("""
        INSERT INTO listens_to (user_id, song_id)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1])
    )

print("Now adding elements to \'rates\'")
for el in rates_list:
    print("adding ", el)
    cursor.execute("""
        INSERT INTO rates (user_id, song_id, rating_value, comment)
        VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1], el[2], el[3])
    )

print("Now adding elements to \'related_artists\'")
for el in related_to_list:
    print("adding ", el)
    cursor.execute("""
        INSERT INTO related_artists (artist_id_1, artist_id_2)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1])
    )

print("Now adding elements to \'participates_in\'")
for el in participates_in_to_add:
    print("adding ", el)
    cursor.execute("""
        INSERT INTO participates_in (album_group, artist_id, album_id)
        VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;
        """,
        (el[0], el[1], el[2])
    )

connection.commit()

cursor.close()
connection.close()