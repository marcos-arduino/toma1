"""
Sistema de Auditoría y Bitácora
Registra todas las acciones que alteran el estado del sistema y detecta eventos críticos.
"""
from sqlalchemy import text, create_engine
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, Any
from collections import defaultdict
import threading

# Usar la misma configuración de base de datos
DATABASE_URL = "postgresql+psycopg2://postgres:3NdzzkT5@localhost:5432/toma1"
engine = create_engine(DATABASE_URL)

# Contador de intentos fallidos por usuario/IP
failed_login_attempts = defaultdict(list)
failed_attempts_lock = threading.Lock()

# Tipos de eventos
EVENT_TYPES = {
    'LOGIN_SUCCESS': 'Inicio de sesión exitoso',
    'LOGIN_FAILED': 'Intento de inicio de sesión fallido',
    'REGISTER': 'Registro de nuevo usuario',
    'REVIEW_CREATE': 'Creación de review',
    'REVIEW_UPDATE': 'Actualización de review',
    'REVIEW_DELETE': 'Eliminación de review',
    'LIST_ADD': 'Agregar película a lista',
    'LIST_REMOVE': 'Eliminar película de lista',
    'MOVIE_ADD': 'Agregar película',
    'MOVIE_UPDATE': 'Actualizar película',
    'MOVIE_DELETE': 'Eliminar película',
    'UNAUTHORIZED_ACCESS': 'Intento de acceso no autorizado',
    'CONFIG_CHANGE': 'Cambio en configuración crítica',
    'DATA_VALIDATION_ERROR': 'Error de validación de datos',
    'CONCURRENT_WRITE_CONFLICT': 'Conflicto de escritura concurrente',
    'BULK_INVALID_DATA': 'Inserción de datos inválidos en masa'
}

# Niveles de severidad
SEVERITY_LEVELS = {
    'INFO': 'Información',
    'WARNING': 'Advertencia',
    'ERROR': 'Error',
    'CRITICAL': 'Crítico'
}

# Esquema de la tabla de auditoría
audit_schema_sql = """
-- Tabla principal de auditoría
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    user_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    user_email VARCHAR(150),
    ip_address VARCHAR(45),
    action_description TEXT NOT NULL,
    entity_type VARCHAR(50),
    entity_id INT,
    old_value JSONB,
    new_value JSONB,
    result VARCHAR(20) NOT NULL,
    error_message TEXT,
    metadata JSONB
);

-- Índices para mejorar el rendimiento de consultas
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_log(severity);
CREATE INDEX IF NOT EXISTS idx_audit_result ON audit_log(result);

-- Tabla de alertas críticas
CREATE TABLE IF NOT EXISTS critical_alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    affected_user_id INT REFERENCES usuarios(id) ON DELETE SET NULL,
    ip_address VARCHAR(45),
    details JSONB,
    notified BOOLEAN DEFAULT FALSE,
    notification_channel VARCHAR(50),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by INT REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON critical_alerts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_notified ON critical_alerts(notified);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON critical_alerts(resolved);

-- Tabla de configuraciones críticas (para auditar cambios)
CREATE TABLE IF NOT EXISTS critical_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by INT REFERENCES usuarios(id) ON DELETE SET NULL
);
"""

# Inicializar esquema
with engine.begin() as conn:
    conn.execute(text(audit_schema_sql))


def log_audit_event(
    event_type: str,
    action_description: str,
    severity: str = 'INFO',
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    ip_address: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None,
    result: str = 'SUCCESS',
    error_message: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> int:
    """
    Registra un evento de auditoría en la bitácora.
    
    Args:
        event_type: Tipo de evento (usar EVENT_TYPES)
        action_description: Descripción de la acción realizada
        severity: Nivel de severidad (INFO, WARNING, ERROR, CRITICAL)
        user_id: ID del usuario que realizó la acción
        user_email: Email del usuario
        ip_address: Dirección IP desde donde se realizó la acción
        entity_type: Tipo de entidad afectada (usuario, pelicula, review, etc.)
        entity_id: ID de la entidad afectada
        old_value: Valor anterior (para actualizaciones)
        new_value: Valor nuevo (para creaciones/actualizaciones)
        result: Resultado de la acción (SUCCESS, FAILED, PARTIAL)
        error_message: Mensaje de error si la acción falló
        metadata: Información adicional en formato JSON
    
    Returns:
        ID del registro de auditoría creado
    """
    query = text("""
        INSERT INTO audit_log (
            event_type, severity, user_id, user_email, ip_address,
            action_description, entity_type, entity_id, old_value,
            new_value, result, error_message, metadata
        )
        VALUES (
            :event_type, :severity, :user_id, :user_email, :ip_address,
            :action_description, :entity_type, :entity_id, :old_value,
            :new_value, :result, :error_message, :metadata
        )
        RETURNING id;
    """)
    
    with engine.begin() as conn:
        result_obj = conn.execute(query, {
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "user_email": user_email,
            "ip_address": ip_address,
            "action_description": action_description,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": json.dumps(old_value) if old_value else None,
            "new_value": json.dumps(new_value) if new_value else None,
            "result": result,
            "error_message": error_message,
            "metadata": json.dumps(metadata) if metadata else None
        })
        audit_id = result_obj.scalar()
        
        # Si es un evento crítico, verificar si requiere alerta
        if severity == 'CRITICAL':
            _check_critical_event(event_type, user_id, user_email, ip_address, action_description, metadata)
        
        return audit_id


def create_critical_alert(
    alert_type: str,
    description: str,
    severity: str = 'CRITICAL',
    affected_user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict] = None,
    notification_channel: str = 'LOG'
) -> int:
    """
    Crea una alerta crítica que requiere notificación.
    
    Args:
        alert_type: Tipo de alerta
        description: Descripción de la alerta
        severity: Nivel de severidad
        affected_user_id: ID del usuario afectado
        ip_address: Dirección IP relacionada
        details: Detalles adicionales
        notification_channel: Canal de notificación (LOG, SOCKET, EMAIL, etc.)
    
    Returns:
        ID de la alerta creada
    """
    query = text("""
        INSERT INTO critical_alerts (
            alert_type, severity, description, affected_user_id,
            ip_address, details, notification_channel
        )
        VALUES (
            :alert_type, :severity, :description, :affected_user_id,
            :ip_address, :details, :notification_channel
        )
        RETURNING id;
    """)
    
    with engine.begin() as conn:
        result = conn.execute(query, {
            "alert_type": alert_type,
            "severity": severity,
            "description": description,
            "affected_user_id": affected_user_id,
            "ip_address": ip_address,
            "details": json.dumps(details) if details else None,
            "notification_channel": notification_channel
        })
        alert_id = result.scalar()
        
        # Escribir en archivo de log crítico
        _write_critical_log(alert_type, description, details)
        
        return alert_id


def _write_critical_log(alert_type: str, description: str, details: Optional[Dict] = None):
    """Escribe alertas críticas en un archivo de log separado."""
    try:
        with open('critical_alerts.log', 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] [{alert_type}] {description}"
            if details:
                log_entry += f" | Detalles: {json.dumps(details, ensure_ascii=False)}"
            f.write(log_entry + '\n')
    except Exception as e:
        print(f"Error escribiendo log crítico: {e}")


def _check_critical_event(
    event_type: str,
    user_id: Optional[int],
    user_email: Optional[str],
    ip_address: Optional[str],
    description: str,
    metadata: Optional[Dict]
):
    """Verifica si un evento crítico requiere alerta."""
    
    # Detectar múltiples intentos de login fallidos
    if event_type == 'LOGIN_FAILED':
        _check_failed_login_attempts(user_email, ip_address, description, metadata)
    
    # Detectar intentos de acceso no autorizado
    elif event_type == 'UNAUTHORIZED_ACCESS':
        create_critical_alert(
            alert_type='UNAUTHORIZED_ACCESS_ATTEMPT',
            description=f"Intento de acceso no autorizado: {description}",
            affected_user_id=user_id,
            ip_address=ip_address,
            details=metadata,
            notification_channel='LOG'
        )
    
    # Detectar inserción de datos inválidos en masa
    elif event_type == 'BULK_INVALID_DATA':
        create_critical_alert(
            alert_type='BULK_INVALID_DATA_DETECTED',
            description=f"Inserción masiva de datos inválidos: {description}",
            affected_user_id=user_id,
            ip_address=ip_address,
            details=metadata,
            notification_channel='LOG'
        )
    
    # Detectar conflictos de escritura concurrente
    elif event_type == 'CONCURRENT_WRITE_CONFLICT':
        create_critical_alert(
            alert_type='CONCURRENT_WRITE_DETECTED',
            description=f"Conflicto de escritura concurrente: {description}",
            affected_user_id=user_id,
            ip_address=ip_address,
            details=metadata,
            notification_channel='LOG'
        )


def _check_failed_login_attempts(
    user_email: Optional[str],
    ip_address: Optional[str],
    description: str,
    metadata: Optional[Dict]
):
    """Detecta múltiples intentos de login fallidos."""
    with failed_attempts_lock:
        key = user_email or ip_address or 'unknown'
        now = datetime.now()
        
        # Agregar intento actual
        failed_login_attempts[key].append(now)
        
        # Limpiar intentos antiguos (más de 15 minutos)
        failed_login_attempts[key] = [
            attempt for attempt in failed_login_attempts[key]
            if now - attempt < timedelta(minutes=15)
        ]
        
        # Si hay 5 o más intentos fallidos en 15 minutos, crear alerta
        if len(failed_login_attempts[key]) >= 5:
            create_critical_alert(
                alert_type='MULTIPLE_FAILED_LOGINS',
                description=f"Múltiples intentos de login fallidos detectados para {key}",
                ip_address=ip_address,
                details={
                    'user_email': user_email,
                    'attempt_count': len(failed_login_attempts[key]),
                    'time_window': '15 minutos',
                    'metadata': metadata
                },
                notification_channel='LOG'
            )
            # Limpiar después de alertar
            failed_login_attempts[key] = []


def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list:
    """
    Obtiene registros de auditoría con filtros opcionales.
    
    Args:
        limit: Número máximo de registros a retornar
        offset: Número de registros a saltar
        user_id: Filtrar por ID de usuario
        event_type: Filtrar por tipo de evento
        severity: Filtrar por severidad
        start_date: Fecha de inicio
        end_date: Fecha de fin
    
    Returns:
        Lista de registros de auditoría
    """
    conditions = []
    params = {"limit": limit, "offset": offset}
    
    if user_id:
        conditions.append("user_id = :user_id")
        params["user_id"] = user_id
    
    if event_type:
        conditions.append("event_type = :event_type")
        params["event_type"] = event_type
    
    if severity:
        conditions.append("severity = :severity")
        params["severity"] = severity
    
    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = text(f"""
        SELECT * FROM audit_log
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().fetchall()
        return [dict(row) for row in rows]


def get_critical_alerts(
    limit: int = 50,
    unresolved_only: bool = True,
    unnotified_only: bool = False
) -> list:
    """
    Obtiene alertas críticas.
    
    Args:
        limit: Número máximo de alertas a retornar
        unresolved_only: Solo alertas no resueltas
        unnotified_only: Solo alertas no notificadas
    
    Returns:
        Lista de alertas críticas
    """
    conditions = []
    params = {"limit": limit}
    
    if unresolved_only:
        conditions.append("resolved = FALSE")
    
    if unnotified_only:
        conditions.append("notified = FALSE")
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    query = text(f"""
        SELECT * FROM critical_alerts
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit
    """)
    
    with engine.connect() as conn:
        rows = conn.execute(query, params).mappings().fetchall()
        return [dict(row) for row in rows]


def mark_alert_notified(alert_id: int):
    """Marca una alerta como notificada."""
    query = text("""
        UPDATE critical_alerts
        SET notified = TRUE
        WHERE id = :alert_id
    """)
    
    with engine.begin() as conn:
        conn.execute(query, {"alert_id": alert_id})


def resolve_alert(alert_id: int, resolved_by: Optional[int] = None):
    """Marca una alerta como resuelta."""
    query = text("""
        UPDATE critical_alerts
        SET resolved = TRUE, resolved_at = CURRENT_TIMESTAMP, resolved_by = :resolved_by
        WHERE id = :alert_id
    """)
    
    with engine.begin() as conn:
        conn.execute(query, {"alert_id": alert_id, "resolved_by": resolved_by})


def get_audit_statistics(days: int = 7) -> Dict[str, Any]:
    """
    Obtiene estadísticas de auditoría de los últimos N días.
    
    Args:
        days: Número de días a analizar
    
    Returns:
        Diccionario con estadísticas
    """
    query = text("""
        SELECT 
            COUNT(*) as total_events,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_events,
            COUNT(CASE WHEN severity = 'ERROR' THEN 1 END) as error_events,
            COUNT(CASE WHEN severity = 'WARNING' THEN 1 END) as warning_events,
            COUNT(CASE WHEN result = 'FAILED' THEN 1 END) as failed_actions,
            COUNT(CASE WHEN event_type = 'LOGIN_FAILED' THEN 1 END) as failed_logins
        FROM audit_log
        WHERE timestamp >= NOW() - INTERVAL ':days days'
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {"days": days}).mappings().fetchone()
        return dict(result) if result else {}
