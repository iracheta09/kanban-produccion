"""
run_production.py
Inicia la aplicación FastAPI en modo producción
Ejecutar con: python -m uvicorn run_production:app --host 0.0.0.0 --port 8000
O directamente: python run_production.py
"""

import os
import logging
from dotenv import load_dotenv
from app.main import app

# Cargar variables de entorno desde .env (ruta explícita)
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app_production.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    
    # Configuración de producción
    print(f"[DEBUG] .env path: {env_path}, exists: {os.path.exists(env_path)}")
    print(f"[DEBUG] Environment variables loaded")
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    workers = int(os.getenv("APP_WORKERS", "4"))
    
    print(f"[DEBUG] APP_HOST={host}, APP_PORT={port}, APP_WORKERS={workers}")
    
    logger.info(f"[KANBAN] Iniciando Kanban FastAPI en {host}:{port}")
    logger.info(f"[WORKERS] Workers: {workers}")
    logger.info(f"[LOGS] Logs en: logs/app_production.log")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info",
        access_log=True
    )
