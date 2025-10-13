from flask import Flask, redirect, url_for, render_template
import sqlite3
from flask_cors import CORS

DB_FILE = "toma1.db"

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/peliculas/<int:id>", methods=["GET"])
def cargar_pelicula(id):
	conn = get_db_connection()
	pelicula = conn.execute("SELECT * FROM peliculas WHERE id = ?", (id,)).fetchone()
	conn.commit()
	conn.close()
	return render_template("pelicula.html", pelicula=pelicula)
    

if __name__ == "__main__":
    app.run(debug=True)
