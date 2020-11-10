from flask import Flask

app = Flask(__name__)

@app.route("/")
def main():
    return "Sup bitch"

app.run("0.0.0.0", 8080)