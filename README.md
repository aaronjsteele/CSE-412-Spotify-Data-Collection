# CSE 412 Data Collection

This repository contains some code that was used in a CSE 412 Database Project at Arizona State University.

Our project was to create a 'music library' of sorts from data on Spotify, and the code here was used to gather data from Spotify and enter it into the database. The included files (mainly `api_get.py`) is used to pull data from Spotify's API and enter it into the database. Not all entities in the database are currently covered by this code, but a majority are. The database in question is a PostgreSQL database hosted on AWS.

If you'd like to contribute, create a `config.py` file in your local repository which contains:
 - `CLIENT_ID` -- From Spotify's API
 - `CLIENT_SECRET` -- From Spotify's API
 - `host` -- the hostname of the SQL database
 - `port` -- the port of the SQL database
 - `user` -- the user of the SQL database
 - `password` -- the password for the SQL database
 - `database` -- the name of the database
 
Note that most of these values are private and will not be shared outside the group for this project.

## Included Files
The only two files of any importance in this repository at the moment are `api_get.py` and `generate_fake_data.py`. `api_get.py` pulls data from Spotify's servers to fill the database with some real data about songs, artists, albums, etc. Note that it isn't perfect right now, as it grabs the top songs for each artist then gets the album for each song. In the future it will be rewritten to grab albums for each artist _then_ the songs in each album.

`generate_fake_data.py` generates a number of fake users and ratings. In particular, it creates fake users, fake 'listened_to' and 'rates' relationships (with gibberish comments) and also creates a number of fake relationships between artists and other artists, as well as artists 'appearing on' other albums. Some of this data may be made more realistic before the end of the project.