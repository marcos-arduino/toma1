# Análisis de Arquitectura y Seguridad - Sistema de Reseñas de Películas

## 1. Arquitectura en Capas

### 1.1 Capa de Presentación
- **Componentes**:
  - [app.py](cci:7://file:///c:/Users/valen/OneDrive/Escritorio/toma1/toma1/app.py:0:0-0:0): Endpoints de la API REST y lógica de enrutamiento
  - Templates HTML: Páginas web renderizadas en el servidor
  - WebSockets: Para notificaciones en tiempo real (nuevas reseñas)

### 1.2 Capa de Lógica de Negocio
- **Componentes**:
  - [app.py](cci:7://file:///c:/Users/valen/OneDrive/Escritorio/toma1/toma1/app.py:0:0-0:0): Lógica principal de la aplicación
  - `audit_log.py`: Manejo de registro de auditoría
  - `crypto_utils.py`: Utilidades de cifrado/descifrado

### 1.3 Capa de Acceso a Datos
- **Componentes**:
  - [db.py](cci:7://file:///c:/Users/valen/OneDrive/Escritorio/toma1/toma1/db.py:0:0-0:0): Manejo de la base de datos
  - SQLAlchemy: ORM para interacción con PostgreSQL

## 2. Modelo de Datos

### 2.1 Tablas Principales

#### usuarios
```sql
CREATE TABLE usuarios (
  id SERIAL PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  email VARCHAR(150) UNIQUE NOT NULL,
  contrasena_hash TEXT NOT NULL,
  fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  es_admin BOOLEAN NOT NULL DEFAULT FALSE,
  activo BOOLEAN NOT NULL DEFAULT TRUE
);
```

#### peliculas
```sql
CREATE TABLE peliculas (
  id SERIAL PRIMARY KEY,
  titulo VARCHAR(150) NOT NULL,
  anio INT,
  duracion INT,
  sinopsis TEXT,
  id_director INT REFERENCES directores(id) ON DELETE SET NULL
);
```

#### reviews
```sql
CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  id_usuario INT REFERENCES usuarios(id) ON DELETE CASCADE,
  id_pelicula INT REFERENCES peliculas(id) ON DELETE CASCADE,
  rating NUMERIC(3,1),
  titulo VARCHAR(150),
  comentario TEXT,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### lista_usuario
```sql
CREATE TABLE lista_usuario (
  id_usuario INT REFERENCES usuarios(id) ON DELETE CASCADE,
  id_pelicula INT NOT NULL,
  titulo VARCHAR(150) NOT NULL,
  poster_url TEXT,
  fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id_usuario, id_pelicula)
);
```

## 3. Política de Cifrado

### 3.1 Cifrado Irreversible (Hashing)
- **Uso**: Almacenamiento seguro de contraseñas
- **Tecnología**: Bcrypt
- **Implementación**:
  ```python
  # En db.py
  password_hash = bcrypt.generate_password_hash(contrasena).decode("utf-8")
  ```
- **Ventajas**:
  - Protección contra filtraciones de datos
  - Resistente a ataques de fuerza bruta
  - Incluye "salt" automático

### 3.2 Cifrado Reversible
- **Uso**: Almacenamiento seguro de claves de API (TMDB)
- **Tecnología**: Cifrado simétrico (AES)
- **Implementación**:
  ```python
  # En app.py
  ENCRYPTED_API_KEY = os.getenv('TMDB_API_KEY')
  API_KEY = decrypt_token(ENCRYPTED_API_KEY) if ENCRYPTED_API_KEY.startswith('gAAAA') else ENCRYPTED_API_KEY
  ```
- **Ventajas**:
  - Permite recuperar la clave original cuando es necesario
  - Protege la clave en reposo

## 4. Endpoints Principales

### 4.1 Autenticación
- `POST /register`: Registro de nuevos usuarios
- `POST /login`: Inicio de sesión

### 4.2 Películas
- `GET /api/peliculas/<categoria>`: Obtiene películas por categoría
- `GET /peliculas/<int:movie_id>`: Detalles de una película

### 4.3 Reseñas
- `GET /api/reviews/<int:movie_id>`: Obtiene reseñas de una película
- `POST /api/reviews/<int:movie_id>`: Crea una nueva reseña
- `GET /api/users/<int:user_id>/reviews`: Obtiene reseñas de un usuario

### 4.4 Lista de Usuario
- `POST /api/lista/agregar`: Agrega película a la lista
- `DELETE /api/lista/eliminar/<int:pelicula_id>`: Elimina película de la lista
- `GET /api/lista/<int:user_id>`: Obtiene la lista de un usuario

### 4.5 Administración
- `GET /admin/usuarios`: Lista usuarios (requiere admin)
- `POST /admin/usuarios/<int:user_id>/desactivar`: Desactiva usuario (admin)

## 5. Ejemplos de Uso

### 5.1 Obtener películas populares
```http
GET /api/peliculas/popular
```

**Respuesta:**
```json
{
  "status": "success",
  "total": 20,
  "data": [
    {
      "id": 123,
      "title": "Título de la Película",
      "text": "Sinopsis...",
      "imageUrl": "https://image.tmdb.org/t/p/w500/poster.jpg",
      "updated": "2023-01-01",
      "vote_average": 7.8
    }
  ]
}
```

### 5.2 Crear reseña
```http
POST /api/reviews/123
Content-Type: application/json

{
  "user_id": 1,
  "rating": 8.5,
  "titulo": "Excelente película",
  "comentario": "Me encantó la trama."
}
```

### 5.3 Registrar usuario
```http
POST /register
Content-Type: application/json

{
  "nombre": "Juan Pérez",
  "email": "juan@example.com",
  "contrasena": "miclave123"
}
```

## 6. Consideraciones de Seguridad

1. **Autenticación**:
   - Sesiones seguras con cookies HTTP-Only
   - Contraseñas hasheadas con Bcrypt

2. **Autorización**:
   - Verificación de roles para accesos administrativos
   - Validación de propiedad de recursos

3. **Protección de Datos**:
   - Cifrado en tránsito (HTTPS)
   - Validación de entrada en todos los endpoints
   - Logging de eventos de seguridad

4. **Rendimiento**:
   - Pool de conexiones a la base de datos
   - Caché de consultas frecuentes

Este documento proporciona una visión general de la arquitectura, seguridad y funcionalidades principales del sistema de reseñas de películas.
