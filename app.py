from flask import Flask, redirect, url_for, render_template, jsonify
from flask_cors import CORS
import db


app = Flask(__name__)
CORS(app)



@app.route("/")
def home():
    return render_template("index.html")

@app.route("/peliculas")
def pagina_pelicula():
    return render_template("test.html")

@app.route("/api/peliculas")
def api_peliculas():
    peliculas = db.listar_peliculas()
    return jsonify({
        "status": "success",
        "total": len(peliculas),
        "data": peliculas
    }), 200




# @app.route("/peliculas/<int:id>", methods=["GET"])
# def cargar_pelicula(id):
# 	conn = get_db_connection()
#	pelicula = conn.execute("SELECT * FROM peliculas WHERE id = ?", (id,)).fetchone()
#	conn.commit()
#	conn.close()
#	return render_template("pelicula.html", pelicula=pelicula)



if __name__ == "__main__":
    app.run(debug=True)
