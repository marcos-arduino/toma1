from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv, set_key
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_or_create_encryption_key():
    """Obtiene la clave de cifrado del entorno o genera una nueva."""
    load_dotenv()
    key = os.getenv('ENCRYPTION_KEY')
    
    if not key:
        key = Fernet.generate_key().decode()
        set_key('.env', 'ENCRYPTION_KEY', key)
        logger.info("Nueva clave de cifrado generada")
    
    return key

# Inicializar cifrador con la clave
try:
    key = get_or_create_encryption_key()
    cipher = Fernet(key.encode())
except Exception as e:
    logger.error(f"Error al inicializar el cifrado: {e}")
    raise

def encrypt_token(token: str) -> str:
    """Cifra un token de API."""
    try:
        return cipher.encrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"Error al cifrar el token: {e}")
        raise

def decrypt_token(encrypted_token: str) -> str:
    """Descifra un token de API previamente cifrado."""
    try:
        return cipher.decrypt(encrypted_token.encode()).decode()
    except Exception as e:
        logger.error(f"Error al descifrar el token: {e}")
        raise

# Al importar este módulo, aseguramos que el token de TMDB esté cifrado
load_dotenv()
tmdb_token = os.getenv('TMDB_API_KEY')
if tmdb_token and not tmdb_token.startswith('gAAAA'):
    encrypted = encrypt_token(tmdb_token)
    set_key('.env', 'TMDB_API_KEY', encrypted)
    logger.info("Token de TMDB cifrado exitosamente")
