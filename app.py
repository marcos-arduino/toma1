from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
import db
import audit_log
import os
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Conjunto para llevar la cuenta de clientes conectados
connected_clients = set()

# Helper para obtener IP del cliente
def get_client_ip():
    """Obtiene la dirección IP del cliente."""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.environ.get('REMOTE_ADDR', 'unknown')


# Cargar variables de entorno desde .env si existe
load_dotenv()

# --- Configuración TMDB ---
API_KEY = os.getenv("TMDB_API_KEY", "40de1255ef09a65984a1b8def1d8c3ce")
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
    ip_address = get_client_ip()
    try:
        data = request.json or {}
        id_usuario = data.get("user_id", 1)
        rating = float(data.get("rating"))
        titulo = (data.get("titulo") or "").strip()
        comentario = (data.get("comentario") or "").strip()

        if not (1.0 <= rating <= 10.0):
            audit_log.log_audit_event(
                event_type='DATA_VALIDATION_ERROR',
                action_description=f"Intento de crear review con rating inválido: {rating}",
                severity='WARNING',
                user_id=id_usuario,
                ip_address=ip_address,
                entity_type='review',
                result='FAILED',
                error_message='Rating inválido',
                metadata={'movie_id': movie_id, 'rating': rating}
            )
            return jsonify({"status": "error", "message": "Rating inválido"}), 400
        
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
        
        # Emitir evento en tiempo real a los clientes conectados
        try:
            usuario = db.buscar_usuario_por_id(id_usuario)
            socketio.emit("nueva_review", {
                "movie_id": movie_id,
                "id": review_id,
                "rating": rating,
                "titulo": titulo,
                "comentario": comentario,
                "usuario": usuario["nombre"] if usuario else "Anónimo",
            })
        except Exception as socket_err:
            # No romper la creación de la review si falla el broadcast
            print("Error emitiendo nueva_review:", socket_err)

        audit_log.log_audit_event(
            event_type='REVIEW_CREATE',
            action_description=f"Review creada para película {movie_id}",
            severity='INFO',
            user_id=id_usuario,
            ip_address=ip_address,
            entity_type='review',
            entity_id=review_id,
            new_value={'movie_id': movie_id, 'rating': rating, 'titulo': titulo},
            result='SUCCESS'
        )
        
        return jsonify({
            "status": "success",
            "id": review_id,
        }), 201
    except Exception as e:
        audit_log.log_audit_event(
            event_type='REVIEW_CREATE',
            action_description=f"Error al crear review para película {movie_id}",
            severity='ERROR',
            user_id=id_usuario if 'id_usuario' in locals() else None,
            ip_address=ip_address,
            entity_type='review',
            result='FAILED',
            error_message=str(e),
            metadata={'movie_id': movie_id}
        )
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

        cast_names = []
        try:
            credits = requests.get(
                f"{TMDB_URL}/movie/{movie_id}/credits",
                params={"api_key": API_KEY, "language": "es-ES"}
            )
            credits.raise_for_status()
            cjson = credits.json() or {}
            cast = cjson.get("cast", [])
            cast_names = [c.get("name") for c in cast if c.get("name")] [:3]
        except Exception:
            cast_names = []

        pelicula = {
            "id": data.get("id"),
            "title": data.get("title", "Sin título"),
            "overview": data.get("overview", "Sin descripción disponible."),
            "imageUrl": f"https://image.tmdb.org/t/p/w500{data['poster_path']}" if data.get("poster_path") else "https://via.placeholder.com/500x750?text=Sin+imagen",
            "backdropUrl": f"https://image.tmdb.org/t/p/w1280{data['backdrop_path']}" if data.get("backdrop_path") else None,
            "release_date": data.get("release_date", "Desconocido"),
            "runtime": data.get("runtime", "N/D"),
            "genres": [g["name"] for g in data.get("genres", [])],
            "vote_average": data.get("vote_average", "N/D"),
            "cast": cast_names
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
    ip_address = get_client_ip()
    data = request.get_json(silent=True)
    print("Datos recibidos:", data)  #imprimí esto

    if not data:
        audit_log.log_audit_event(
            event_type='DATA_VALIDATION_ERROR',
            action_description=f"Intento de agregar película {pelicula_id} sin datos JSON",
            severity='WARNING',
            ip_address=ip_address,
            entity_type='lista_usuario',
            result='FAILED',
            error_message='No se recibió JSON'
        )
        return jsonify({"status": "error", "message": "No se recibió JSON"}), 400

    id_usuario = data.get("user_id", 1)
    titulo = data.get("titulo")
    poster = data.get("poster_url")

    if not titulo:
        audit_log.log_audit_event(
            event_type='DATA_VALIDATION_ERROR',
            action_description=f"Intento de agregar película {pelicula_id} sin título",
            severity='WARNING',
            user_id=id_usuario,
            ip_address=ip_address,
            entity_type='lista_usuario',
            result='FAILED',
            error_message='Falta el título'
        )
        return jsonify({"status": "error", "message": "Falta el título"}), 400

    try:
        db.agregar_a_lista(id_usuario, pelicula_id, titulo, poster)
        
        audit_log.log_audit_event(
            event_type='LIST_ADD',
            action_description=f"Película {pelicula_id} agregada a lista del usuario {id_usuario}",
            severity='INFO',
            user_id=id_usuario,
            ip_address=ip_address,
            entity_type='lista_usuario',
            new_value={'pelicula_id': pelicula_id, 'titulo': titulo},
            result='SUCCESS'
        )
        
        return jsonify({"status": "success", "message": "Película agregada a tu lista"}), 201
    except Exception as e:
        audit_log.log_audit_event(
            event_type='LIST_ADD',
            action_description=f"Error al agregar película {pelicula_id} a lista",
            severity='ERROR',
            user_id=id_usuario,
            ip_address=ip_address,
            entity_type='lista_usuario',
            result='FAILED',
            error_message=str(e)
        )
        return jsonify({"status": "error", "message": "Error al agregar película"}), 500


@app.route("/api/mi-lista/<int:pelicula_id>/", methods=["DELETE"])
def eliminar_pelicula_lista(pelicula_id):
    ip_address = get_client_ip()
    id_usuario = request.args.get("user_id", 1)  # también por ahora fijo
    
    try:
        db.eliminar_de_lista(id_usuario, pelicula_id)
        
        audit_log.log_audit_event(
            event_type='LIST_REMOVE',
            action_description=f"Película {pelicula_id} eliminada de lista del usuario {id_usuario}",
            severity='INFO',
            user_id=id_usuario,
            ip_address=ip_address,
            entity_type='lista_usuario',
            old_value={'pelicula_id': pelicula_id},
            result='SUCCESS'
        )
        
        return jsonify({"status": "success", "message": "Película eliminada de tu lista"}), 200
    except Exception as e:
        audit_log.log_audit_event(
            event_type='LIST_REMOVE',
            action_description=f"Error al eliminar película {pelicula_id} de lista",
            severity='ERROR',
            user_id=id_usuario,
            ip_address=ip_address,
            entity_type='lista_usuario',
            result='FAILED',
            error_message=str(e)
        )
        return jsonify({"status": "error", "message": "Error al eliminar película"}), 500


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
    ip_address = get_client_ip()

    if not nombre or not email or not contrasena:
        audit_log.log_audit_event(
            event_type='REGISTER',
            action_description=f"Intento de registro con campos faltantes",
            severity='WARNING',
            user_email=email,
            ip_address=ip_address,
            result='FAILED',
            error_message='Faltan campos requeridos'
        )
        return jsonify({"status": "error", "message": "Faltan campos"}), 400

    # Verificar si ya existe el email
    if db.buscar_usuario_por_email(email):
        audit_log.log_audit_event(
            event_type='REGISTER',
            action_description=f"Intento de registro con email duplicado: {email}",
            severity='WARNING',
            user_email=email,
            ip_address=ip_address,
            result='FAILED',
            error_message='El usuario ya existe'
        )
        return jsonify({"status": "error", "message": "El usuario ya existe"}), 400

    try:
        user_id = db.registrar_usuario(nombre, email, contrasena)
        
        audit_log.log_audit_event(
            event_type='REGISTER',
            action_description=f"Usuario registrado exitosamente: {email}",
            severity='INFO',
            user_id=user_id,
            user_email=email,
            ip_address=ip_address,
            entity_type='usuario',
            entity_id=user_id,
            new_value={'nombre': nombre, 'email': email},
            result='SUCCESS'
        )
        
        return jsonify({
            "status": "success",
            "message": "Usuario registrado correctamente",
            "user_id": user_id
        }), 201
    except Exception as e:
        audit_log.log_audit_event(
            event_type='REGISTER',
            action_description=f"Error al registrar usuario: {email}",
            severity='ERROR',
            user_email=email,
            ip_address=ip_address,
            result='FAILED',
            error_message=str(e)
        )
        return jsonify({"status": "error", "message": "Error al registrar usuario"}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email")
    contrasena = data.get("contrasena")
    ip_address = get_client_ip()

    if not email or not contrasena:
        audit_log.log_audit_event(
            event_type='LOGIN_FAILED',
            action_description=f"Intento de login con campos faltantes",
            severity='WARNING',
            user_email=email,
            ip_address=ip_address,
            result='FAILED',
            error_message='Faltan datos'
        )
        return jsonify({"status": "error", "message": "Faltan datos"}), 400

    usuario = db.buscar_usuario_por_email(email)
    if not usuario:
        audit_log.log_audit_event(
            event_type='LOGIN_FAILED',
            action_description=f"Intento de login con usuario inexistente: {email}",
            severity='WARNING',
            user_email=email,
            ip_address=ip_address,
            result='FAILED',
            error_message='Usuario no encontrado'
        )
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    # Bloquear login si el usuario está dado de baja
    if not usuario.get("activo", True):
        return jsonify({"status": "error", "message": "Usuario desactivado. Contacte al administrador."}), 403

    if not bcrypt.check_password_hash(usuario["contrasena_hash"], contrasena):
        audit_log.log_audit_event(
            event_type='LOGIN_FAILED',
            action_description=f"Intento de login con contraseña incorrecta: {email}",
            severity='CRITICAL',
            user_id=usuario["id"],
            user_email=email,
            ip_address=ip_address,
            entity_type='usuario',
            entity_id=usuario["id"],
            result='FAILED',
            error_message='Contraseña incorrecta',
            metadata={'attempt_type': 'wrong_password'}
        )
        return jsonify({"status": "error", "message": "Contraseña incorrecta"}), 401

    # Login exitoso
    audit_log.log_audit_event(
        event_type='LOGIN_SUCCESS',
        action_description=f"Inicio de sesión exitoso: {email}",
        severity='INFO',
        user_id=usuario["id"],
        user_email=email,
        ip_address=ip_address,
        entity_type='usuario',
        entity_id=usuario["id"],
        result='SUCCESS'
    )

    return jsonify({
        "status": "success",
        "message": "Inicio de sesión exitoso",
        "user": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "es_admin": usuario.get("es_admin", False),
            "activo": usuario.get("activo", True)
        }
    }), 200


@app.route("/api/admin/usuarios", methods=["GET"])
def admin_listar_usuarios():
    """Lista todos los usuarios. Requiere un admin_id válido y administrador."""
    admin_id = request.args.get("admin_id", type=int)
    if not admin_id:
        return jsonify({"status": "error", "message": "admin_id requerido"}), 400

    admin = db.buscar_usuario_por_id(admin_id)
    if not admin or not admin.get("es_admin", False):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    usuarios = db.listar_usuarios()
    return jsonify({
        "status": "success",
        "total": len(usuarios),
        "data": usuarios
    }), 200


@app.route("/api/admin/usuarios/<int:user_id>/desactivar", methods=["POST"])
def admin_desactivar_usuario(user_id):
    """Da de baja lógica a un usuario (activo = FALSE). Requiere admin_id admin."""
    data = request.json or {}
    admin_id = data.get("admin_id")
    if not admin_id:
        return jsonify({"status": "error", "message": "admin_id requerido"}), 400

    admin = db.buscar_usuario_por_id(int(admin_id))
    if not admin or not admin.get("es_admin", False):
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    if int(admin_id) == int(user_id):
        return jsonify({"status": "error", "message": "Un admin no puede desactivarse a sí mismo"}), 400

    usuario = db.buscar_usuario_por_id(user_id)
    if not usuario:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

    db.desactivar_usuario(user_id)
    return jsonify({"status": "success", "message": "Usuario desactivado"}), 200

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

# -------- AUDIT LOG API --------
@app.route("/api/audit/logs", methods=["GET"])
def get_audit_logs_api():
    """Obtiene registros de auditoría con filtros opcionales."""
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
        user_id = request.args.get("user_id", type=int)
        event_type = request.args.get("event_type")
        severity = request.args.get("severity")
        
        logs = audit_log.get_audit_logs(
            limit=limit,
            offset=offset,
            user_id=user_id,
            event_type=event_type,
            severity=severity
        )
        
        return jsonify({
            "status": "success",
            "total": len(logs),
            "data": logs
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/audit/alerts", methods=["GET"])
def get_critical_alerts_api():
    """Obtiene alertas críticas."""
    try:
        limit = int(request.args.get("limit", 50))
        unresolved_only = request.args.get("unresolved_only", "true").lower() == "true"
        unnotified_only = request.args.get("unnotified_only", "false").lower() == "true"
        
        alerts = audit_log.get_critical_alerts(
            limit=limit,
            unresolved_only=unresolved_only,
            unnotified_only=unnotified_only
        )
        
        # Enviar notificación por WebSocket si hay alertas no notificadas
        unnotified = [a for a in alerts if not a.get('notified')]
        if unnotified:
            for alert in unnotified:
                socketio.emit('critical_alert', {
                    'alert_id': alert['id'],
                    'alert_type': alert['alert_type'],
                    'description': alert['description'],
                    'severity': alert['severity'],
                    'timestamp': str(alert['timestamp'])
                })
                # Marcar como notificada
                audit_log.mark_alert_notified(alert['id'])
        
        return jsonify({
            "status": "success",
            "total": len(alerts),
            "data": alerts
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/audit/alerts/<int:alert_id>/resolve", methods=["POST"])
def resolve_alert_api(alert_id):
    """Marca una alerta como resuelta."""
    try:
        data = request.json or {}
        resolved_by = data.get("resolved_by")
        
        audit_log.resolve_alert(alert_id, resolved_by)
        
        return jsonify({
            "status": "success",
            "message": "Alerta resuelta"
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/audit/statistics", methods=["GET"])
def get_audit_statistics_api():
    """Obtiene estadísticas de auditoría."""
    try:
        days = int(request.args.get("days", 7))
        stats = audit_log.get_audit_statistics(days)
        
        return jsonify({
            "status": "success",
            "data": stats
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# -- SOCKETIO --

@socketio.on("connect")
def handle_connect():
    client_id = request.sid
    connected_clients.add(client_id)
    print(f"Cliente conectado: {client_id}")
    print(f"Total de clientes conectados: {len(connected_clients)}")
    
    # Enviar mensaje de bienvenida al cliente que se acaba de conectar
    emit("welcome", {
        "message": "Conectado al servidor",
        "your_id": client_id,
        "total_clients": len(connected_clients)
    })
    
    # Notificar a todos los clientes sobre el nuevo conteo
    emit("online_count", {
        "count": len(connected_clients),
        "clients": list(connected_clients)
    }, broadcast=True)

@socketio.on("disconnect")
def handle_disconnect():
    client_id = request.sid
    connected_clients.discard(client_id)
    print(f"Cliente desconectado: {client_id}")
    print(f"Total de clientes conectados: {len(connected_clients)}")
    
    # Notificar a todos los clientes sobre el nuevo conteo
    socketio.emit("online_count", {
        "count": len(connected_clients),
        "clients": list(connected_clients)
    })

@socketio.on("ping")
def handle_ping(data):
    emit("pong", {"message": "pong"})

@socketio.on("chat_message")
def handle_chat_message(data):
    client_id = request.sid
    message_text = data.get("text", "")
    print(f"Mensaje de {client_id}: {message_text}")
    
    # Reemite el mensaje a todos los clientes conectados
    emit("chat_message", {
        "from": client_id,
        "text": message_text,
        "timestamp": data.get("timestamp")
    }, broadcast=True)

@app.route("/api/broadcast-test", methods=["GET"])
def broadcast_test():
    # Emite un mensaje de prueba a todos los clientes conectados
    socketio.emit("chat_message", {"from": "server", "text": "Hola a todos"})
    return jsonify({"status": "ok"}), 200




if __name__ == "__main__":
    print("="*50)
    print("Servidor Flask + Socket.IO iniciado")
    print("Los clientes pueden conectarse vía WebSocket")
    print("URL: http://localhost:5000")
    print("="*50)
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
