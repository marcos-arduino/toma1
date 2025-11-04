# TomaUNO

TomaUNO es una aplicación web desarrollada con Flask que permite descubrir, listar y reseñar películas utilizando la API de The Movie Database (TMDB).
El proyecto está inspirado en plataformas como Letterboxd, priorizando una interfaz limpia y una experiencia de usuario fluida.

### 🧩 Funcionalidades principales

 - 🔍 Exploración de películas: secciones dinámicas como Populares, Mejor valoradas, Próximamente y En cartelera.
  
 - 🧠 Búsqueda avanzada: permite encontrar películas específicas mediante integración con TMDB.
  
 - 🎞️ Detalles individuales: visualización de información completa de cada película.
  
 - 📋 Mi lista personal: los usuarios pueden agregar o eliminar películas de su colección.
  
 - 💬 Reseñas y foros (en desarrollo): implementados mediante Socket.IO para comunicación en tiempo real.
  
 - 🔐 Autenticación segura: registro e inicio de sesión con contraseñas encriptadas usando Bcrypt.
  
### ⚙️ Tecnologías utilizadas

Backend: Flask, Flask-SocketIO, Flask-Bcrypt, Requests

Frontend: HTML, CSS (Bootstrap), JavaScript

Base de datos: PostgreSQL (con capa db.py)

API externa: The Movie Database (TMDB)

---

### 👥 Equipo de desarrollo

Marcos Arduino

Bautista Vadala

Valentín Ermel

---

⚙️ Instalación y ejecución local
1️⃣ Clonar el repositorio
git clone https://github.com/<tu-usuario>/TomaUNO.git
cd TomaUNO

2️⃣ Crear entorno virtual e instalar dependencias

Se recomienda usar un entorno virtual de Python:

python -m venv venv
source venv/bin/activate   # En Linux/Mac
venv\Scripts\activate      # En Windows


Luego instalar las dependencias:

pip install flask flask-socketio flask-bcrypt flask-cors requests sqlalchemy psycopg2-binary

3️⃣ Configurar PostgreSQL

Instalar PostgreSQL y pgAdmin si aún no lo tenés.

Descargar PostgreSQL

Crear una base de datos llamada toma1:

CREATE DATABASE toma1;


Verificar que el usuario postgres y la contraseña del archivo db.py coincidan con tu configuración local:

DATABASE_URL = "postgresql+psycopg2://postgres:<tu_contraseña>@localhost:5432/toma1"


Al ejecutar el proyecto, el script db.py crea automáticamente las tablas necesarias.

4️⃣ Configurar la API de TMDB

Creá una cuenta en The Movie Database (TMDB)
 y obtené tu API key.
Reemplazá la constante API_KEY en app.py:

API_KEY = "TU_API_KEY_AQUI"

5️⃣ Ejecutar la aplicación

Para iniciar el servidor Flask con soporte de Socket.IO:

python app.py


La aplicación estará disponible en:
👉 http://127.0.0.1:5000/

💻 Dependencias principales
Librería:	Uso
Flask:	Framework web principal
Flask-SocketIO:	Comunicación en tiempo real (reseñas y foros)
Flask-Bcrypt:	Encriptación de contraseñas
Flask-CORS:	Permite peticiones entre dominios
SQLAlchemy:	ORM y manejo de base de datos
psycopg2-binary:	Conector de PostgreSQL
Requests:	Comunicación con la API de TMDB
