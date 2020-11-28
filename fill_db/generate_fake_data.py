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
from datetime import datetime

def create_entry_list(cursor, mogrify_string, input_array):
    string_array = []
    for x in input_array:
        string_array.append(cursor.mogrify(mogrify_string, tuple(x)))
    print(string_array)
    args_str = b','.join(string_array)
    print(args_str)
    return args_str

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
cursor.execute("SELECT song.song_id FROM song INNER JOIN performed_by ON song.song_id = performed_by.song_id WHERE performed_by.artist_id = '3TVXtAsR1Inumwj472S9r4'")
rows = cursor.fetchall()
song_id_list = []
for row in rows:
    song_id_list.append(row[0].strip())

print(song_id_list)

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
Faker.seed(datetime.now())
random.seed(datetime.now())

user_list = []
for _ in range(300):
    user_id = get_random_alphanumeric_string(21)
    username = fake.simple_profile()['username']
    user_list.append([user_id, username])

# We have some users. Now they need to listen to
# some songs. Each user listens to a random number
# of songs from 10 - (# songs - 10) from the query
# earlier.
listens_to_list = []
for el in user_list:
    songs_listened_to = random.sample(song_id_list, random.randint(30, len(song_id_list) - 10))
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
    songs_rated = random.sample(song_id_list, random.randint(10, 50))
    for song_id in songs_rated:
        rates_list.append([el[0], song_id, random.randint(1,10), fake.sentence()])

# Selects a random amount of artists to be related
# to each other.
related_to_list = random.sample(artist_id_list, random.randint(3, 9))

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
cursor.execute(b"INSERT INTO user_table (user_id, display_name) VALUES "
                + create_entry_list(cursor, "(%s, %s)", user_list)
                + b" ON CONFLICT DO NOTHING;")

print("Now adding elements to \'listens_to\'")
cursor.execute(b"INSERT INTO listens_to (user_id, song_id) VALUES "
                + create_entry_list(cursor, "(%s, %s)", listens_to_list)
                + b" ON CONFLICT DO NOTHING;")

print("Now adding elements to \'rates\'")
cursor.execute(b"INSERT INTO rates (user_id, song_id, rating_value, comment) VALUES "
                + create_entry_list(cursor, "(%s, %s, %s, %s)", rates_list)
                + b" ON CONFLICT DO NOTHING;")

print("Now adding elements to \'related_artists\'")
cursor.execute(b"INSERT INTO related_artists (artist_id_1, artist_id_2) VALUES "
                + create_entry_list(cursor, "(%s, %s)", related_to_list)
                + b" ON CONFLICT DO NOTHING;")

print("Now adding elements to \'participates_in\'")
cursor.execute(b"INSERT INTO participates_in (album_group, artist_id, album_id) VALUES "
                + create_entry_list(cursor, "(%s, %s, %s)", participates_in_to_add)
                + b" ON CONFLICT DO NOTHING;")

connection.commit()

cursor.close()
connection.close()