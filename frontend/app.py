import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/transactions")
def transactions():
    return render_template("transactions.html")

@app.route("/dividends")
def dividends():
    return render_template("dividends.html")

if __name__ == "__main__":
    # Run the frontend server on port 5050
    app.run(port=5050, debug=True)
