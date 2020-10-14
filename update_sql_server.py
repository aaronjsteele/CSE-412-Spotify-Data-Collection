import psycopg2
connection = psycopg2.connect(
    host = '***REMOVED***',
    port = ***REMOVED***,
    user = '***REMOVED***',
    password = '***REMOVED***',
    database='***REMOVED***'
    )
cursor=connection.cursor()

cursor.execute("SELECT * FROM artist")
records = cursor.fetchall()
print(records)