from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import db

app = Flask(__name__)
CORS(app)



# --- Configuración TMDB ---
API_KEY = "40de1255ef09a65984a1b8def1d8c3ce"
TMDB_URL = "https://api.themoviedb.org/3"


# -------- RUTAS DE PÁGINAS --------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/peliculas-popular")
def pagina_peliculas_populares():
    return render_template("test.html")

@app.route("/peliculas/<int:movie_id>")
def pagina_pelicula(movie_id):
    return render_template("pelicula.html", movie_id=movie_id)


# -------- API REST --------
@app.route("/api/peliculas-popular", methods=["GET"])
def api_peliculas():
    """Devuelve lista de películas populares"""
    try:
        resp = requests.get(f"{TMDB_URL}/movie/popular", params={
            "api_key": API_KEY,
            "language": "es-ES"
        })
        resp.raise_for_status()
        data = resp.json().get("results", [])

        peliculas = []
        for p in data:
            peliculas.append({
                "id": p.get("id"),
                "title": p.get("title", "Sin título"),
                "text": p.get("overview", "Sin descripción."),
                "imageUrl": f"https://image.tmdb.org/t/p/w500{p['poster_path']}" if p.get("poster_path") else "https://via.placeholder.com/500x750?text=Sin+imagen",
                "updated": p.get("release_date", "Desconocido")
            })

        return jsonify({
            "status": "success",
            "total": len(peliculas),
            "data": peliculas
        }), 200

    except Exception as e:
        print("Error al obtener películas:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/peliculas/<int:movie_id>", methods=["GET"])
def api_pelicula(movie_id):
    """Devuelve detalles de una película específica por ID"""
    try:
        resp = requests.get(f"{TMDB_URL}/movie/{movie_id}", params={
            "api_key": API_KEY,
            "language": "es-ES"
        })
        resp.raise_for_status()
        data = resp.json()

        pelicula = {
            "id": data.get("id"),
            "title": data.get("title", "Sin título"),
            "overview": data.get("overview", "Sin descripción disponible."),
            "imageUrl": f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get("poster_path") else "https://via.placeholder.com/500x750?text=Sin+imagen",
            "release_date": data.get("release_date", "Desconocido"),
            "runtime": data.get("runtime", "N/D"),
            "genres": [g["name"] for g in data.get("genres", [])],
            "vote_average": data.get("vote_average", "N/D")
        }

        return jsonify({
            "status": "success",
            "data": pelicula
        }), 200

    except Exception as e:
        print("Error al obtener película:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/api/mi-lista/<int:pelicula_id>/", methods=["POST"])
def agregar_pelicula_lista(pelicula_id):
    data = request.json or {}
    id_usuario = data.get("user_id", 1)  # por ahora usuario fijo para pruebas
    titulo = data.get("titulo")
    poster = data.get("poster_url")

    db.agregar_a_lista(id_usuario, pelicula_id, titulo, poster)
    return jsonify({"status": "success", "message": "Película agregada a tu lista"}), 201


@app.route("/api/mi-lista/<int:pelicula_id>/", methods=["DELETE"])
def eliminar_pelicula_lista(pelicula_id):
    id_usuario = request.args.get("user_id", 1)  # también por ahora fijo
    db.eliminar_de_lista(id_usuario, pelicula_id)
    return jsonify({"status": "success", "message": "Película eliminada de tu lista"}), 200


@app.route("/api/mi-lista/<int:user_id>/", methods=["GET"])
def obtener_lista(user_id):
    lista = db.obtener_lista_usuario(user_id)
    return jsonify({
        "status": "success",
        "total": len(lista),
        "data": lista
    }), 200


if __name__ == "__main__":
    app.run(debug=True)
