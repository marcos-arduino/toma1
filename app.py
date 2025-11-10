from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import db
import os
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Conjunto para llevar la cuenta de clientes conectados
connected_clients = set()


# --- Configuración TMDB ---
API_KEY = "40de1255ef09a65984a1b8def1d8c3ce"
TMDB_URL = "https://api.themoviedb.org/3"


# -------- RUTAS DE PÁGINAS --------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/peliculas/<string:tipo>")
def ver_peliculas(tipo):
    return render_template("grid-peliculas.html", tipo=tipo)

@app.route("/peliculas/<int:movie_id>")
def pagina_pelicula(movie_id):
    return render_template("pelicula.html", movie_id=movie_id)

@app.route("/buscar")
def pagina_busqueda():
    """Página que muestra los resultados de búsqueda."""
    return render_template("buscar.html")

@app.route("/perfil")
def pagina_perfil():
    return render_template("perfil.html")


# -------- API REST --------
@app.route("/api/peliculas/<categoria>", methods=["GET"])
def api_peliculas_categoria(categoria):
    try:
        match categoria:
            case "popular":
                endpoint = "movie/popular"
            case "top_rated":
                endpoint = "movie/top_rated"
            case "upcoming":
                endpoint = "movie/upcoming"
            case "now_playing":
                endpoint = "movie/now_playing"
            case _:
                return jsonify({"status": "error", "message": "Categoría no válida"}), 400

        resp = requests.get(f"{TMDB_URL}/{endpoint}", params={
            "api_key": API_KEY,
            "language": "es-ES"
        })
        resp.raise_for_status()
        data = resp.json().get("results", [])

        peliculas = [{
            "id": p.get("id"),
            "title": p.get("title", "Sin título"),
            "text": p.get("overview", "Sin descripción."),
            "imageUrl": f"https://image.tmdb.org/t/p/w500{p['poster_path']}" if p.get("poster_path") else "https://via.placeholder.com/500x750?text=Sin+imagen",
            "updated": p.get("release_date", "Desconocido"),
            "vote_average": p.get("vote_average")
        } for p in data]

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



# -------- REVIEWS --------
@app.route("/api/reviews/<int:movie_id>", methods=["GET"])
def listar_reviews(movie_id):
    try:
        items = db.listar_reviews_por_pelicula(movie_id)
        return jsonify({
            "status": "success",
            "total": len(items),
            "data": items,
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/users/<int:user_id>/reviews", methods=["GET"])
def listar_reviews_usuario(user_id):
    try:
        items = db.listar_reviews_por_usuario(user_id)
        return jsonify({
            "status": "success",
            "total": len(items),
            "data": items,
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/reviews/<int:movie_id>", methods=["POST"])
def crear_review(movie_id):
    try:
        data = request.json or {}
        id_usuario = data.get("user_id", 1)
        rating = float(data.get("rating"))
        titulo = (data.get("titulo") or "").strip()
        comentario = (data.get("comentario") or "").strip()

        if not (1.0 <= rating <= 10.0):
            return jsonify({"status": "error", "message": "Rating inválido"}), 400
        # Ensure pelicula exists locally to satisfy FK
        try:
            resp = requests.get(f"{TMDB_URL}/movie/{movie_id}", params={
                "api_key": API_KEY,
                "language": "es-ES"
            })
            resp.raise_for_status()
            m = resp.json()
            titulo_min = m.get("title") or m.get("original_title") or f"TMDB {movie_id}"
            anio_min = None
            if m.get("release_date"):
                anio_min = int(m["release_date"].split("-")[0])
            db.upsert_pelicula_minima(movie_id, titulo_min, anio_min)
        except Exception:
            # As a last resort, insert with fallback title
            db.upsert_pelicula_minima(movie_id, f"TMDB {movie_id}")

        review_id = db.crear_review(id_usuario, movie_id, rating, titulo, comentario)
        return jsonify({
            "status": "success",
            "id": review_id,
        }), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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

@socketio.on("connect")
def handle_connect(auth=None):
    print("Cliente conectado")
    connected_clients.add(request.sid)
    socketio.emit("online_count", {"count": len(connected_clients)})

@socketio.on("disconnect")
def handle_disconnect():
    print("Cliente desconectado")
    connected_clients.discard(request.sid)
    socketio.emit("online_count", {"count": len(connected_clients)})

@socketio.on("ping")
def handle_ping(data):
    emit("pong", {"message": "pong"})

@socketio.on("chat_message")
def handle_chat_message(data):
    # Reemite el mensaje a todos los clientes conectados
    emit("chat_message", {"from": request.sid, "text": data.get("text")}, broadcast=True)

@app.route("/api/broadcast-test", methods=["GET"])
def broadcast_test():
    # Emite un mensaje de prueba a todos los clientes conectados
    socketio.emit("chat_message", {"from": "server", "text": "Hola a todos"})
    return jsonify({"status": "ok"}), 200

@app.route("/api/mi-lista/<int:pelicula_id>/", methods=["POST"])
def agregar_pelicula_lista(pelicula_id):
    data = request.get_json(silent=True)
    print("📩 Datos recibidos:", data)  # 👀 imprimí esto

    if not data:
        return jsonify({"status": "error", "message": "No se recibió JSON"}), 400

    id_usuario = data.get("user_id", 1)
    titulo = data.get("titulo")
    poster = data.get("poster_url")

    if not titulo:
        return jsonify({"status": "error", "message": "Falta el título"}), 400

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


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    nombre = data.get("nombre")
    email = data.get("email")
    contrasena = data.get("contrasena")

    if not nombre or not email or not contrasena:
        return jsonify({"status": "error", "message": "Faltan campos"}), 400

    # Verificar si ya existe el email
    if db.buscar_usuario_por_email(email):
        return jsonify({"status": "error", "message": "El usuario ya existe"}), 400

    user_id = db.registrar_usuario(nombre, email, contrasena)
    return jsonify({
        "status": "success",
        "message": "Usuario registrado correctamente",
        "user_id": user_id
    }), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    contrasena = data.get("contrasena")

    if not email or not contrasena:
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    usuario = db.buscar_usuario_por_email(email)
    if not usuario:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    if not bcrypt.check_password_hash(usuario["contrasena_hash"], contrasena):
        return jsonify({"status": "error", "message": "Contraseña incorrecta"}), 401

    return jsonify({
        "status": "success",
        "message": "Inicio de sesión exitoso",
        "user": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"]
        }
    }), 200

@app.route("/api/buscar", methods=["GET"])
def buscar_peliculas():
    """Busca películas por texto en TMDB"""
    from flask import request

    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "status": "error",
            "message": "Debe ingresar un texto de búsqueda."
        }), 400

    try:
        resp = requests.get(f"{TMDB_URL}/search/movie", params={
            "api_key": API_KEY,
            "language": "es-ES",
            "query": query
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
                "updated": p.get("release_date", "Desconocido"),
                "vote_average": p.get("vote_average")
            })

        return jsonify({
            "status": "success",
            "total": len(peliculas),
            "data": peliculas
        }), 200

    except Exception as e:
        print("Error al buscar películas:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



if __name__ == "__main__":
    socketio.run(app, debug=True)
