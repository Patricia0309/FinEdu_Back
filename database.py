# backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de conexión a la base de datos que definimos en docker-compose.yml
# Formato: postgresql://<user>:<password>@<host>:<port>/<dbname>
SQLALCHEMY_DATABASE_URL = "postgresql://findedu_user:findedu_pass@db:5432/findedu_db"

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