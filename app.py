from flask import Flask, render_template, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# TMDB
API_KEY = "40de1255ef09a65984a1b8def1d8c3ce"
TMDB_URL = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=es-ES&page=1"


# ------ Rutas de páginas -------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/peliculas")
def pagina_pelicula():
    return render_template("test.html")


# ------ APIs -------
@app.route("/api/peliculas", methods=["GET"])
def api_peliculas():
    try:
        resp = requests.get(TMDB_URL)
        resp.raise_for_status()
        data = resp.json().get("results", [])

        peliculas = []
        for p in data:
            peliculas.append({
                "title": p.get("title", "Sin titulo"),
                "text": p.get("overview", "Sin descripcion."),
                "imageUrl": f"https://image.tmdb.org/t/p/w500{p['poster_path']}" if p.get("poster_path") else "https://via.placeholder.com/500x750?text=Sin+imagen",
                "updated": p.get("release_date", "Desconocido")
            })

        return jsonify({
            "status": "success",
            "total": len(peliculas),
            "data": peliculas
        }), 200

    except Exception as e:
        print("Error al obtener peliculas:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
