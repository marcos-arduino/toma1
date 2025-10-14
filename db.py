
from sqlalchemy import text, create_engine

DATABASE_URL = "postgresql+psycopg2://postgres:3NdzzkT5@localhost:5432/toma1"

engine = create_engine(DATABASE_URL, echo=True)  # echo=True para ver las queries

schema_sql = """
CREATE TABLE IF NOT EXISTS usuarios (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  contrasena_hash TEXT NOT NULL,
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
  comentario TEXT,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.begin() as conn:
    conn.execute(text(schema_sql))

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

def listar_peliculas():
    query = text("""
        SELECT p.id, p.titulo, p.anio, d.nombre AS director
        FROM peliculas p
        LEFT JOIN directores d ON p.id_director = d.id
        ORDER BY p.anio DESC;
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        return [dict(row) for row in result]

def buscar_pelicula_por_titulo(nombre):
    query = text("""
        SELECT * FROM peliculas WHERE LOWER(titulo) LIKE LOWER(:nombre);
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"nombre": f"%{nombre}%"})
        return [dict(row) for row in result]

