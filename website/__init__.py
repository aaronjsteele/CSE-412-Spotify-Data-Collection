from flask import Flask

app = Flask(__name__)

import website.routes

if __name__ == "__main__":
    app.run("0.0.0.0", 8080)