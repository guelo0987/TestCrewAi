from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Obtener DATABASE_URL del .env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en el archivo .env")

# Crear el motor de base de datos
# Configuración optimizada para 100+ usuarios simultáneos
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_size=20,  # Número de conexiones en el pool (base)
    max_overflow=40,  # Conexiones adicionales permitidas (total: 60)
    pool_timeout=30,  # Timeout para obtener conexión del pool (segundos)
    pool_recycle=3600,  # Reciclar conexiones después de 1 hora
    echo=False  # Cambiar a True para ver las queries SQL
)

# Crear la clase base para los modelos
Base = declarative_base()

# Crear la fábrica de sesiones
# expire_on_commit=False permite leer objetos después de commit
# Esto es necesario porque hacemos commit temprano y luego leemos los objetos
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Permite leer objetos después de commit
)


def get_db():
    """Dependencia para obtener una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
