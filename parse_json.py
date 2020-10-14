# This file intends to take API requests from Spotify and turn them into commands I can enter into SQL
# in order to fill the data_artistsbase with data_artists. This should be improved in the future, but for now
# it should be fine.

# Overall -- takes a JSON file with Albums from Spotify and prints formatted tuples
# to a file for easy entry into SQL
import json

f_artists = open("sql_artists.txt", "w")
f_genre = open("sql_genre.txt", "w")
f_is_genre = open("sql_is_genre.txt", "w")

with open('artists.json') as f:
    data_artists = json.load(f)
    
print(len(data_artists['artists']))

# Note that in the SQL data_artistsbase for this project, artists are listed
# as (artist_name, artist_id)
# So, the SQL command is INSERT INTO public.artist (artist_name, artist_id) VALUES...
f_artists.write("INSERT INTO public.artist (artist_name, artist_id)\nVALUES\n")
for i in range(len(data_artists['artists'])):
    name = data_artists['artists'][i]['name']
    artist_id = data_artists['artists'][i]['id']
    to_print = "\t(\'" + name + "\',\'" + artist_id + "\')"
    if i == len(data_artists['artists']) - 1:
        to_print += ";"
    else:
        to_print += ",\n"
    f_artists.write(to_print)

genre_list = []

f_genre.write("INSERT INTO public.genre (genre_name)\nVALUES\n")
for i in range(len(data_artists['artists'])):
    genre_list.extend(data_artists['artists'][i]['genres'])
genre_list = set(genre_list)
print(genre_list)
for e in genre_list:
    to_print = "\t(\'" + e + "\'),\n"
    f_genre.write(to_print)

f_is_genre.write("INSERT INTO public.is_genre (genre_name, artist_id)\nVALUES\n")
genre_artist = []
for i in range(len(data_artists['artists'])):
    artist_id = data_artists['artists'][i]['id']
    for g in data_artists['artists'][i]['genres']:
        genre_artist.append([artist_id, g])
for e in genre_artist:
    to_print = "\t(\'" + e[1] + "\',\'" + e[0] + "\'),\n"
    f_is_genre.write(to_print)

f_artists.close()
f_genre.close()
f_is_genre.close()