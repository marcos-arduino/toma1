"""
ARCHIVO UNICAMENTE DE PRUEBA PARA PROBAR PONGS
"""
import socketio
import time
import sys

# ID del cliente (puedes pasarlo como argumento)
client_name = sys.argv[1] if len(sys.argv) > 1 else f"Cliente_{time.time()}"

# Crear cliente Socket.IO con configuración de logging
sio = socketio.Client(logger=False, engineio_logger=False)

@sio.event
def connect():
    print(f"[{client_name}] Conectado al servidor exitosamente!")

@sio.event
def disconnect():
    print(f"[{client_name}] Desconectado del servidor")

@sio.event
def connect_error(data):
    print(f"[{client_name}] Error de conexion: {data}")

@sio.on('welcome')
def on_welcome(data):
    print(f"[{client_name}] Bienvenida recibida:")
    print(f"  - Tu ID: {data['your_id']}")
    print(f"  - Total clientes: {data['total_clients']}")

@sio.on('online_count')
def on_online_count(data):
    print(f"[{client_name}] Clientes conectados: {data['count']}")
    print(f"   - IDs: {data.get('clients', [])}")

@sio.on('chat_message')
def on_chat_message(data):
    print(f"[{client_name}] Mensaje recibido:")
    print(f"   - De: {data['from']}")
    print(f"   - Texto: {data['text']}")

@sio.on('pong')
def on_pong(data):
    print(f"[{client_name}] Pong recibido: {data['message']}")

def main():
    try:
        # Conectar al servidor
        print(f"[{client_name}] Intentando conectar a http://localhost:5000...")
        sio.connect('http://localhost:5000', wait_timeout=10)
        
        # Esperar un momento para asegurar la conexión
        time.sleep(0.5)
        
        if sio.connected:
            # Enviar un ping de prueba
            print(f"[{client_name}] Enviando ping...")
            sio.emit('ping', {'data': 'test'})
            
            # Enviar un mensaje de chat
            time.sleep(1)
            print(f"[{client_name}] Enviando mensaje de chat...")
            sio.emit('chat_message', {
                'text': f'Hola desde {client_name}!',
                'timestamp': time.time()
            })
            
            # Mantener la conexión activa
            print(f"[{client_name}] Manteniendo conexión activa (Ctrl+C para salir)...")
            sio.wait()
        else:
            print(f"[{client_name}] No se pudo establecer la conexion")
        
    except KeyboardInterrupt:
        print(f"\n[{client_name}] Desconectando...")
        if sio.connected:
            sio.disconnect()
    except Exception as e:
        print(f"[{client_name}] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
