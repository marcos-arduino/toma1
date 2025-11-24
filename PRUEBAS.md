# Guía de Pruebas

## 🚀 Acceso a la Aplicación
- **URL de Producción**: [https://tomauno.onrender.com](https://tomauno.onrender.com)
- **Usuario Administrador**: 
  - Email: `admin@mitoma.com`
  - Contraseña: `alanteamo`
- **Clave de Acceso Admin**: `alanteamo` (para operaciones administrativas)

## 🔄 Prueba de Concurrencia

### Objetivo
Verificar el manejo de múltiples usuarios realizando operaciones simultáneas.

### Pasos para la Prueba

1. **Preparación**:
   - Abrir dos navegadores diferentes (ej: Chrome y Firefox)
   - Navegar a [https://tomauno.onrender.com](https://tomauno.onrender.com)

2. **Prueba de Escritura Concurrente**:
   - **Navegador 1**:
     1. Registrarse como nuevo usuario
     2. Navegar a una película
     3. Hacer clic en "Escribir reseña"
     4. Comenzar a escribir (no enviar)
   
   - **Navegador 2**:
     1. Registrarse como nuevo usuario
     2. Ir a la misma película
     3. Completar y enviar una reseña

   - **Verificación**: Ambas reseñas deben aparecer correctamente sin refrescar la página

## 🔐 Pruebas de Autenticación

### 1. Inicio de Sesión de Administrador
1. Ir a [https://tomauno.onrender.com/login](https://tomauno.onrender.com/login)
2. Ingresar:
   - Email: `admin@mitoma.com`
   - Contraseña: `alanteamo`
3. Verificar que se muestre el panel de administración agregando /admin al final de la URL

### 2. Registro de Nuevo Usuario
1. Cerrar sesión si está autenticado
2. Hacer clic en "Registrarse"
3. Completar el formulario con datos válidos
4. Verificar que se pueda iniciar sesión con el nuevo usuario

## 🛡️ Pruebas de Seguridad

### Intento de Inyección SQL
1. Ir a la barra de búsqueda
2. Ingresar: `' OR '1'='1`
3. Verificar que el sistema bloquee el intento

## 📊 Verificación de Integridad

### 1. Historial de Auditoría
1. Iniciar sesión como administrador
2. Navegar a `https://tomauno.onrender.com/admin/audit`
3. Verificar que se registren los eventos:
   - Inicios de sesión
   - Creación/edición de reseñas
   - Intentos fallidos

## 🎥 Video Demostrativo

**Duración**: 2-3 minutos

**Secciones**:
1. Inicio de sesión (30s)
2. Navegación básica (30s)
3. Prueba de concurrencia (30s)
4. Verificación de seguridad (30s)
