from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import os
from dotenv import load_dotenv
from sqlalchemy import text
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True,
    pool_recycle=300
)

schema_sql = """
CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  contrasena_hash TEXT NOT NULL,
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  es_admin BOOLEAN NOT NULL DEFAULT FALSE,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS directores (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  nacionalidad VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS peliculas (
  id SERIAL PRIMARY KEY,
  titulo VARCHAR(150) NOT NULL,
  anio INT,
  duracion INT,
  sinopsis TEXT,
  id_director INT REFERENCES directores(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS actores (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS reparto (
  id_pelicula INT REFERENCES peliculas(id) ON DELETE CASCADE,
  id_actor INT REFERENCES actores(id) ON DELETE CASCADE,
  rol VARCHAR(100),
  PRIMARY KEY (id_pelicula, id_actor)
);

CREATE TABLE IF NOT EXISTS generos (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS peliculas_generos (
  id_pelicula INT REFERENCES peliculas(id) ON DELETE CASCADE,
  id_genero INT REFERENCES generos(id) ON DELETE CASCADE,
  PRIMARY KEY (id_pelicula, id_genero)
);

CREATE TABLE IF NOT EXISTS reviews (
  id SERIAL PRIMARY KEY,
  id_usuario INT REFERENCES usuarios(id) ON DELETE CASCADE,
  id_pelicula INT REFERENCES peliculas(id) ON DELETE CASCADE,
  rating NUMERIC(3,1),
  titulo VARCHAR(150),
  comentario TEXT,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ensure titulo exists if table already created without it
ALTER TABLE reviews ADD COLUMN IF NOT EXISTS titulo VARCHAR(150);

CREATE TABLE IF NOT EXISTS lista_usuario (
    id_usuario INT REFERENCES usuarios(id) ON DELETE CASCADE,
    id_pelicula INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    poster_url TEXT,
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario, id_pelicula)
);
 
-- asegurar columnas para esquemas antiguos
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS es_admin BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;
"""

with engine.begin() as conn:
    conn.execute(text(schema_sql))


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ADMIN_NAME = os.getenv("ADMIN_NAME", "Administrador")


def asegurar_admin_por_defecto():
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        return

    query_select = text("SELECT id FROM usuarios WHERE email = :email")
    query_insert = text(
        """
        INSERT INTO usuarios (nombre, email, contrasena_hash, es_admin, activo)
        VALUES (:nombre, :email, :contrasena_hash, TRUE, TRUE)
        """
    )

    with engine.begin() as conn:
        existing = conn.execute(query_select, {"email": ADMIN_EMAIL}).fetchone()
        if existing:
            return

        password_hash = bcrypt.generate_password_hash(ADMIN_PASSWORD).decode("utf-8")
        conn.execute(
            query_insert,
            {
                "nombre": ADMIN_NAME,
                "email": ADMIN_EMAIL,
                "contrasena_hash": password_hash,
            },
        )


asegurar_admin_por_defecto()

def agregar_pelicula(titulo, anio, duracion, sinopsis, id_director):
    query = text("""
        INSERT INTO peliculas (titulo, anio, duracion, sinopsis, id_director)
        VALUES (:titulo, :anio, :duracion, :sinopsis, :id_director)
        RETURNING id;
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {
            "titulo": titulo,
            "anio": anio,
            "duracion": duracion,
            "sinopsis": sinopsis,
            "id_director": id_director
        })
        return result.scalar()

def crear_review(id_usuario, id_pelicula, rating, titulo, comentario):
    query = text("""
        INSERT INTO reviews (id_usuario, id_pelicula, rating, titulo, comentario)
        VALUES (:id_usuario, :id_pelicula, :rating, :titulo, :comentario)
        RETURNING id;
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {
            "id_usuario": id_usuario,
            "id_pelicula": id_pelicula,
            "rating": rating,
            "titulo": titulo,
            "comentario": comentario,
        })
        return result.scalar()

def listar_reviews_por_pelicula(id_pelicula):
    query = text("""
        SELECT r.id, r.id_usuario, r.id_pelicula, r.rating, r.titulo, r.comentario, r.fecha,
               u.nombre AS usuario
        FROM reviews r
        LEFT JOIN usuarios u ON u.id = r.id_usuario
        WHERE r.id_pelicula = :id_pelicula
        ORDER BY r.fecha DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"id_pelicula": id_pelicula}).mappings().fetchall()
        return [dict(row) for row in rows]

def listar_reviews_por_usuario(id_usuario):
    query = text("""
        SELECT r.id, r.id_usuario, r.id_pelicula, r.rating, r.titulo, r.comentario, r.fecha,
               p.titulo AS titulo_pelicula
        FROM reviews r
        LEFT JOIN peliculas p ON p.id = r.id_pelicula
        WHERE r.id_usuario = :id_usuario
        ORDER BY r.fecha DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"id_usuario": id_usuario}).mappings().fetchall()
        return [dict(row) for row in rows]

def listar_peliculas():
    query = text("""
        SELECT p.id, p.titulo, p.anio, d.nombre AS director
        FROM peliculas p
        LEFT JOIN directores d ON p.id_director = d.id
        ORDER BY p.anio DESC;
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result.mappings()]

def upsert_pelicula_minima(id_pelicula, titulo, anio=None):
    query = text("""
        INSERT INTO peliculas (id, titulo, anio)
        VALUES (:id, :titulo, :anio)
        ON CONFLICT (id) DO NOTHING;
    """)
    with engine.begin() as conn:
        conn.execute(query, {"id": id_pelicula, "titulo": titulo, "anio": anio})

def buscar_pelicula_por_titulo(nombre):
    query = text("""
        SELECT * FROM peliculas WHERE LOWER(titulo) LIKE LOWER(:nombre);
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"nombre": f"%{nombre}%"})
        return [dict(row) for row in result.mappings()]



def registrar_usuario(nombre, email, contrasena):
    contrasena_hash = bcrypt.generate_password_hash(contrasena).decode("utf-8")
    query = text("""
        INSERT INTO usuarios (nombre, email, contrasena_hash)
        VALUES (:nombre, :email, :contrasena_hash)
        RETURNING id;
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {
            "nombre": nombre,
            "email": email,
            "contrasena_hash": contrasena_hash
        })
        return result.scalar()

def buscar_usuario_por_email(email):
    query = text("SELECT * FROM usuarios WHERE email = :email")
    with engine.connect() as conn:
        result = conn.execute(query, {"email": email}).mappings().fetchone()
        return result

def agregar_a_lista(id_usuario, id_pelicula, titulo, poster_url):
    """Agrega una película a la lista del usuario."""
    query = text("""
        INSERT INTO lista_usuario (id_usuario, id_pelicula, titulo, poster_url)
        VALUES (:id_usuario, :id_pelicula, :titulo, :poster_url)
        ON CONFLICT (id_usuario, id_pelicula) DO NOTHING
    """)
def buscar_usuario_por_id(user_id: int):
    query = text("SELECT * FROM usuarios WHERE id = :id")
    with engine.connect() as conn:
        result = conn.execute(query, {"id": user_id}).mappings().fetchone()
        return result

def listar_usuarios():
    query = text(
        """
        SELECT id, nombre, email, fecha_registro, es_admin, activo
        FROM usuarios
        ORDER BY fecha_registro DESC;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().fetchall()
        return [dict(row) for row in rows]

def desactivar_usuario(user_id: int):
    query = text(
        """
        UPDATE usuarios
        SET activo = FALSE
        WHERE id = :id;
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"id": user_id})

# --- Lista de usuario (favoritos / mi lista) ---
def agregar_a_lista(id_usuario: int, id_pelicula: int, titulo: str, poster_url: str | None = None):
    """Inserta o actualiza una película en la lista del usuario."""
    query = text(
        """
        INSERT INTO lista_usuario (id_usuario, id_pelicula, titulo, poster_url)
        VALUES (:id_usuario, :id_pelicula, :titulo, :poster_url)
        ON CONFLICT (id_usuario, id_pelicula) DO UPDATE
        SET titulo = EXCLUDED.titulo,
            poster_url = EXCLUDED.poster_url,
            fecha_agregado = CURRENT_TIMESTAMP;
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {
            "id_usuario": id_usuario,
            "id_pelicula": id_pelicula,
            "titulo": titulo,
            "poster_url": poster_url
        })

def eliminar_de_lista(id_usuario, id_pelicula):
    """Elimina una película de la lista del usuario."""
    query = text("""
        DELETE FROM lista_usuario
        WHERE id_usuario = :id_usuario AND id_pelicula = :id_pelicula
    """)
    with engine.begin() as conn:
        conn.execute(query, {
            "id_usuario": id_usuario,
            "id_pelicula": id_pelicula
        })

def obtener_lista_usuario(id_usuario):
    """Obtiene la lista de películas de un usuario."""
    query = text("""
        SELECT id_pelicula, titulo, poster_url, fecha_agregado
        FROM lista_usuario
        WHERE id_usuario = :id_usuario
        ORDER BY fecha_agregado DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"id_usuario": id_usuario}).mappings().fetchall()
        return [dict(row) for row in rows]

def eliminar_de_lista(id_usuario: int, id_pelicula: int):
    query = text(
        """
        DELETE FROM lista_usuario
        WHERE id_usuario = :id_usuario AND id_pelicula = :id_pelicula;
        """
    )
    with engine.begin() as conn:
        conn.execute(query, {"id_usuario": id_usuario, "id_pelicula": id_pelicula})

def obtener_lista_usuario(id_usuario: int):
    query = text(
        """
        SELECT id_pelicula AS id, titulo, poster_url, fecha_agregado
        FROM lista_usuario
        WHERE id_usuario = :id_usuario
        ORDER BY fecha_agregado DESC;
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query, {"id_usuario": id_usuario}).mappings().fetchall()
        return [dict(row) for row in rows]
