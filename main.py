from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import engine, SessionLocal
import firebase_admin
from firebase_admin import credentials
import models
import crud
# Importamos todos tus routers
from routers import students, auth, transactions, analytics, budgets, content
from fastapi.middleware.cors import CORSMiddleware

# --- NO INICIALIZAR FIREBASE AQUÍ ---
# (Hemos movido este bloque al 'lifespan')

from sqlalchemy.orm import Session
from fastapi import Depends
from database import get_db # Asegúrate de que esta función esté en tu database.py
from notifications import send_fcm_notification # La función que creamos
from tasks import scheduler
from routers import students, auth, transactions, analytics, budgets, content

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando aplicación y sembrando la base de datos...")
    
    # --- INICIALIZAR FIREBASE ADMIN (EL LUGAR CORRECTO) ---
    try:
        # Usamos la ruta simple (relativa al WORKDIR /app)
        cred = credentials.Certificate("firebase-credentials.json") 
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK inicializado.")
    except ValueError:
        # Esto maneja el error "app ya existe" si el reloader de Uvicorn se activa
        print("Firebase Admin SDK ya está inicializado (hot-reload).")
    except Exception as e:
        # Esto atrapa otros errores (ej. archivo no encontrado)
        print(f"Error inicializando Firebase Admin SDK: {e}")
    # --- FIN INICIALIZACIÓN ---

    # INICIAR EL SCHEDULER (RECORDATORIOS)
    if not scheduler.running:
        scheduler.start()
        print("⏰ Scheduler de recordatorios nocturnos iniciado.")

    # --- SEMBRAR LA BASE DE DATOS ---
    db = SessionLocal()
    try:
        crud.create_initial_categories(db)
        crud.create_initial_microcontent(db)
    finally:
        db.close()
    
    yield

    if scheduler.running:
        scheduler.shutdown()
        print("⏰ Scheduler apagado.")
    
    print("Apagando aplicación...")

# Crear tablas (esto va después de definir el lifespan)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinEdu API",
    description="La API para el proyecto de tesis FinEdu.",
    version="0.1.0",
    lifespan=lifespan # Se asigna la función de ciclo de vida
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["137.184.85.162"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluimos todos los routers
app.include_router(students.router)
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(analytics.router) 
app.include_router(budgets.router)
app.include_router(content.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "¡Bienvenido a la API de FinEdu!"}