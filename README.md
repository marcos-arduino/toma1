# TomaUNO

TomaUNO es una aplicación web desarrollada con Flask que permite descubrir, listar y reseñar películas utilizando la API de The Movie Database (TMDB).
El proyecto está inspirado en plataformas como Letterboxd / IMDb / Filmafinity, priorizando una interfaz limpia y una experiencia de usuario fluida.

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

## Estructura de Frontend (CSS/JS)

La app organiza los estilos y scripts para mejorar mantenibilidad, consistencia y caché.

- **static/css/**
  - Hojas globales y por página: `css/style.css`, `css/index.css`, `css/perfil.css`, `css/pelicula.css`, `css/grid.css`, `css/buscar.css`.
  - En los templates se cargan con `{% block extra_css %}` para evitar cargar CSS innecesario.

- **static/js/core/** (núcleo compartido)
  - `api.js`: resuelve `API_BASE` por entorno y expone `fetchJSON(url, opts)`.
  - `utils.js`: utilidades genéricas (por ejemplo `formatDateDMY`).
  - `ui.js`: componentes UI reutilizables (`crearPosterCard`, `crearBotonLista`, `initRatingWidget`).
  - Se importan desde los scripts de página con ES Modules.

- **static/js/global/** (scripts del layout base)
  - `login.js`: maneja login/registro en los modales globales.
  - `navbar.js`: estado de sesión en el navbar y logout.
  - Se cargan en `templates/base.html` y están disponibles en todas las páginas.

- **static/js/pages/** (lógica específica por página)
  - `index.js`, `grid.js`, `buscar.js`, `pelicula.js`, `perfil.js`.
  - Los templates cargan su script con `<script type="module" src="...">` dentro de `{% block scripts %}`.

### Cómo agregar una nueva página

1. Crear el template `templates/nueva.html` extendiendo `base.html`.
2. (Opcional) Crear `static/css/nueva.css` y enlazarlo con `{% block extra_css %}`.
3. Crear `static/js/pages/nueva.js` y cargarlo con:

   ```html
   {% block scripts %}
   <script type="module" src="{{ url_for('static', filename='js/pages/nueva.js') }}"></script>
   {% endblock %}
   ```

4. Reutilizar utilidades desde core cuando sea posible:

   ```js
   import { API_BASE, fetchJSON } from '../core/api.js'
   import { crearPosterCard } from '../core/ui.js'
   ```

### Notas

- Los archivos antiguos en `static/` raíz fueron migrados a `static/css` y `static/js`.
- Si agregás nuevas utilidades compartidas, ubícalas en `static/js/core/` para que puedan importarse desde cualquier página.
