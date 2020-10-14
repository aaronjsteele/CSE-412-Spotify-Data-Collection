# This file will likely have commands to update
# the SQL server in the future

import psycopg2

import config

connection = psycopg2.connect(
    host = config.host,
    port = config.port,
    user = config.user,
    password = config.password,
    database=config.database
    )
cursor=connection.cursor()

cursor.execute("SELECT * FROM artist")
records = cursor.fetchall()
print(records)