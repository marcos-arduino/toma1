# toma1

- **Logs.py** :
Cada acción que altere el estado del sistema (altas, modificaciones,
eliminaciones, inicios de sesión fallidos, intentos de acceso no autorizado,
cambios en configuraciones críticas) deberá registrarse en una bitácora de
auditoría persistente: cada entrada debe incluir quién realizó la acción, qué se hizo,
fecha/hora y resultado. El sistema deberá además detectar y notificar, a quién
corresponda, eventos críticos (por ejemplo: intento múltiple de login fallido,
detección de escritura concurrente conflictiva, o inserción de datos inválidos en
masa). Las notificaciones críticas deben enviarse a un canal que el equipo elija (por
ejemplo: un endpoint de alertas, un archivo de log separado, o mensajes en tiempo
real vía socket TCP/WebSocket) y registrar cada aviso en la bitácora.

