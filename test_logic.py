# test_logic.py
import sys
import os

# Esto ayuda a que Python encuentre tus carpetas locales
sys.path.append(os.getcwd())

from database import SessionLocal
from analytics.profiling import train_and_cluster_students

def test_profiling():
    # Creamos la conexión a tu base local
    db = SessionLocal()
    try:
        print("🔍 Buscando alumnos y calculando perfiles en local...")
        df = train_and_cluster_students(db)
        
        if df is not None and not df.empty:
            print("\n✅ ¡LOGRADO! RESULTADOS DEL CLUSTERING:")
            print("=" * 60)
            # Mostramos los datos clave
            print(df[['student_id', 'savings_rate', 'profile_id', 'profile_name']])
            print("=" * 60)
            
            # Verificación del Guardián
            guardian = df[df['profile_id'] == 1]
            if not guardian.empty:
                print(f"💎 El Guardián del Futuro tiene un ahorro de: {guardian['savings_rate'].iloc[0]:.2%}")
        else:
            print("\n⚠️ No hay suficientes datos.")
            print("Asegúrate de tener al menos 5 usuarios con 15 transacciones cada uno.")
            print("TIP: Puedes correr primero una función que llame a 'create_demo_data(db)'")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_profiling()