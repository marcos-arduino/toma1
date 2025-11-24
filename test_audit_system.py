import requests
import time
import json

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_failed_logins():
    """Prueba múltiples intentos de login fallidos para generar alerta crítica"""
    print_section("TEST: Múltiples Intentos de Login Fallidos")
    
    for i in range(6):
        print(f"\nIntento {i+1} de login fallido...")
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@example.com",
            "contrasena": "wrong_password"
        })
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        time.sleep(0.5)
    
    print("\n✓ Debería haberse generado una alerta crítica después de 5 intentos")

def test_register_user():
    """Prueba registro de usuario"""
    print_section("TEST: Registro de Usuario")
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json={
        "nombre": "Usuario Test",
        "email": f"test_{int(time.time())}@example.com",
        "contrasena": "password123"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 201:
        print("\n✓ Usuario registrado exitosamente")
        return response.json().get("user_id")
    return None

def test_create_review(user_id):
    """Prueba creación de review"""
    print_section("TEST: Creación de Review")
    
    # Review válida
    print("\n1. Creando review válida...")
    response = requests.post(f"{BASE_URL}/api/reviews/550", json={
        "user_id": user_id or 1,
        "rating": 8.5,
        "titulo": "Excelente película",
        "comentario": "Me encantó esta película de prueba"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Review con rating inválido
    print("\n2. Intentando crear review con rating inválido...")
    response = requests.post(f"{BASE_URL}/api/reviews/550", json={
        "user_id": user_id or 1,
        "rating": 15.0,  # Rating inválido
        "titulo": "Review inválida",
        "comentario": "Esto debería fallar"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("\n✓ Debería haberse registrado un error de validación")

def test_list_operations(user_id):
    print_section("TEST: Operaciones de Lista")
    
    # Agregar película a lista
    print("\n1. Agregando película a lista...")
    response = requests.post(f"{BASE_URL}/api/mi-lista/550/", json={
        "user_id": user_id or 1,
        "titulo": "Fight Club",
        "poster_url": "https://example.com/poster.jpg"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Eliminar película de lista
    print("\n2. Eliminando película de lista...")
    response = requests.delete(f"{BASE_URL}/api/mi-lista/550/?user_id={user_id or 1}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n✓ Operaciones de lista completadas")

def test_get_audit_logs():
    print_section("TEST: Consultar Logs de Auditoría")
    
    response = requests.get(f"{BASE_URL}/api/audit/logs?limit=20")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal de logs: {data['total']}")
        print("\nÚltimos eventos:")
        for log in data['data'][:5]:
            print(f"\n  - [{log['timestamp']}] {log['event_type']}")
            print(f"    Severidad: {log['severity']}")
            print(f"    Descripción: {log['action_description']}")
            print(f"    Resultado: {log['result']}")
    else:
        print(f"Error: {response.json()}")

def test_get_critical_alerts():
    print_section("TEST: Consultar Alertas Críticas")
    
    response = requests.get(f"{BASE_URL}/api/audit/alerts?unresolved_only=true")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal de alertas: {data['total']}")
        
        if data['total'] > 0:
            print("\nAlertas críticas:")
            for alert in data['data']:
                print(f"\n  - [{alert['timestamp']}] {alert['alert_type']}")
                print(f"    Severidad: {alert['severity']}")
                print(f"    Descripción: {alert['description']}")
                print(f"    Notificada: {alert['notified']}")
                print(f"    Resuelta: {alert['resolved']}")
        else:
            print("\nNo hay alertas críticas pendientes")
    else:
        print(f"Error: {response.json()}")

def test_get_statistics():
    print_section("TEST: Estadísticas de Auditoría")
    
    response = requests.get(f"{BASE_URL}/api/audit/statistics?days=7")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        stats = data['data']
        print("\nEstadísticas de los últimos 7 días:")
        print(f"  - Total de eventos: {stats.get('total_events', 0)}")
        print(f"  - Usuarios únicos: {stats.get('unique_users', 0)}")
        print(f"  - Eventos críticos: {stats.get('critical_events', 0)}")
        print(f"  - Eventos de error: {stats.get('error_events', 0)}")
        print(f"  - Advertencias: {stats.get('warning_events', 0)}")
        print(f"  - Acciones fallidas: {stats.get('failed_actions', 0)}")
        print(f"  - Logins fallidos: {stats.get('failed_logins', 0)}")
    else:
        print(f"Error: {response.json()}")

def main():
    print("\n" + "="*60)
    print("  SISTEMA DE AUDITORÍA - SUITE DE PRUEBAS")
    print("="*60)
    print("\nAsegúrate de que el servidor Flask esté corriendo en http://localhost:5000")
    input("\nPresiona ENTER para continuar...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print("\n✓ Servidor Flask está corriendo")
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: No se puede conectar al servidor Flask")
        print("  Asegúrate de que el servidor esté corriendo en http://localhost:5000")
        return
    
    # Ejecutar pruebas
    user_id = test_register_user()
    time.sleep(1)
    
    test_create_review(user_id)
    time.sleep(1)
    
    test_list_operations(user_id)
    time.sleep(1)
    
    test_failed_logins()
    time.sleep(2)
    
    # Consultar resultados
    test_get_audit_logs()
    time.sleep(1)
    
    test_get_critical_alerts()
    time.sleep(1)
    
    test_get_statistics()
    
    print_section("PRUEBAS COMPLETADAS")
    print("\n✓ Todas las pruebas han sido ejecutadas")
    print("\nRevisa:")
    print("  1. La base de datos (tablas audit_log y critical_alerts)")
    print("  2. El archivo critical_alerts.log")
    print("  3. Las notificaciones WebSocket (si tienes un cliente conectado)")
    print("\nPara ver los logs en la base de datos:")
    print("  SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 20;")
    print("\nPara ver las alertas críticas:")
    print("  SELECT * FROM critical_alerts ORDER BY timestamp DESC;")

if __name__ == "__main__":
    main()
