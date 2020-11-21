from flask import Flask

app = Flask(__name__)

import website.routes
import sys

if __name__ == "__main__":
    app.run("0.0.0.0", 8080)