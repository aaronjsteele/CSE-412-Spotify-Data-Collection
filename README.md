# CSE 412 Group Project

This repository contains some code that was used in a CSE 412 Database Project at Arizona State University.

Our project was to create a 'music library' of sorts from data on Spotify, and the code here was used to gather data from Spotify and enter it into the database. The included files (mainly `api_get.py`) is used to pull data from Spotify's API and enter it into the database. Not all entities in the database are currently covered by this code, but a majority are. The database in question is a PostgreSQL database hosted on AWS.

If you'd like to contribute or host the website locally, create a `config.py` file in your local repository which contains:
 - `CLIENT_ID` -- From Spotify's API
 - `CLIENT_SECRET` -- From Spotify's API
 - `host` -- the hostname of the SQL database
 - `port` -- the port of the SQL database
 - `user` -- the user of the SQL database
 - `password` -- the password for the SQL database
 - `database` -- the name of the database
 
Note that this data is _private_ and will not be shared outside of the class due to potential security concerns! If a grader comes across this, note that all this information is included in the report submitted for the project.

---

## Data Collection

The first part of the database is the `fill_db` folder, which contains the files used to fill the database with information. A fair bit of information in the project is real and pulled from Spotify's API

## Included Files
The only two files of any importance in this repository at the moment are `api_get.py` and `generate_fake_data.py`. `api_get.py` pulls data from Spotify's servers to fill the database with some real data about songs, artists, albums, etc. Note that it isn't perfect right now, as it grabs the top songs for each artist then gets the album for each song. In the future it will be rewritten to grab albums for each artist _then_ the songs in each album.

`generate_fake_data.py` generates a number of fake users and ratings. In particular, it creates fake users, fake 'listened_to' and 'rates' relationships (with gibberish comments) and also creates a number of fake relationships between artists and other artists, as well as artists 'appearing on' other albums. Some of this data may be made more realistic before the end of the project.

---

## Hosting the Website

If you would like to run the website locally, navigate so that you are in the `website` directory and make sure that a `config.py` file is placed inside, as described above. To run the server, first set the environment variable `FLASK_APP` to `__init__.py`. How you do this will vary depending on if you are using Windows or Linux, but once this is set you can type `flask run` in the console to launch the website locally on port `5000`. Assuming you have installed all necessary packages and are running a modern version of Python, the website is yours to run!

For data to fill a locally-hosted version of the database, please look in the `db_dump` folder of the project, which contains the exported data of all tables in our project. To download a zip of the data, please visit this [link](https://drive.google.com/file/d/1pl704g8YnwuMO9Vvh2_Dyj4G0Hfjaq_j/view?usp=sharing).

If you are having issues getting the website to run, please contact the group responsible for this project.
