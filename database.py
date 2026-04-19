# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Buscamos el host. Si no existe (como en tu PC), usamos 'localhost'
DB_HOST = os.getenv("DB_HOST", "localhost")

# 2. Tus credenciales se quedan exactamente igual
DB_USER = os.getenv("DB_USER", "findedu_user")
DB_PASS = os.getenv("DB_PASS", "findedu_pass")
DB_NAME = os.getenv("DB_NAME", "findedu_db")

# URL de conexión a la base de datos que definimos en docker-compose.yml
# Formato: postgresql://<user>:<password>@<host>:<port>/<dbname>
SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

# El 'engine' es el punto de entrada a la base de datos.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Cada instancia de SessionLocal será una sesión de base de datos.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base será la clase base para nuestros modelos de SQLAlchemy
Base = declarative_base()

# Función para obtener una sesión de la base de datos en cada request
# y cerrarla al terminar. Esto es un patrón de inyección de dependencias.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()