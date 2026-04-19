from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
import models
from datetime import datetime, date
from notifications import send_fcm_notification
from pytz import timezone
import crud

# 1. Definimos la zona horaria de México (Pachuca)
mexico_tz = timezone('America/Mexico_City')

def check_daily_expenses():
    # 🔍 Tip de depuración: Verás esto en la terminal de Docker cuando el reloj suene
    print(f"⏰ [SCHEDULER] Iniciando verificación de gastos: {datetime.now(mexico_tz)}")
    
    db = SessionLocal()
    try:
        students = db.query(models.Student).all()
        
        for student in students:
            # Usamos la fecha de México para comparar
            today = datetime.now(mexico_tz).date()
            
            expense_count = db.query(models.Transaction).filter(
                models.Transaction.student_id == student.id,
                models.Transaction.ts >= today
            ).count()

            print(f"📊 Usuario {student.email}: {expense_count} gastos hoy.")

            if expense_count == 0 and student.fcm_token:
                print(f"🚀 Enviando notificación a {student.email}...")
                send_fcm_notification(
                    token=student.fcm_token,
                    title="¡No lo olvides 📝!",
                    body="No olvides registrar tus gastos de hoy. ¡Tu presupuesto te lo agradecerá! 💸",
                    data={"screen": "add_expense"}
                )
    except Exception as e:
        print(f"❌ Error en la tarea programada: {e}")
    finally:
        db.close()

def send_weekly_personalized_tips():
    print(f"💡 [SCHEDULER] Generando consejos semanales: {datetime.now(mexico_tz)}")
    
    db = SessionLocal()
    try:
        students = db.query(models.Student).all()
        
        for student in students:
            # 1. Obtenemos su reporte de gastos por categoría (tu lógica de semáforo)
            report = crud.get_category_spending_report(db, student_id=student.id)
            
            # 2. Si tiene reporte y tiene token, mandamos el consejo
            if report and student.fcm_token:
                # Buscamos la categoría donde más gastó
                # Ordenamos las categorías de mayor a menor gasto
                sorted_categories = sorted(report.categories, key=lambda x: x.total_spent, reverse=True)
                
                if sorted_categories:
                    top_cat = sorted_categories[0]
                    
                    print(f"🚀 Enviando consejo semanal a {student.email}...")
                    send_fcm_notification(
                        token=student.fcm_token,
                        title="💡 Tip Financiero de la Semana",
                        body=f"Hola {student.display_name}, esta semana tu mayor gasto fue en {top_cat.category_name}. ¡Checa tu perfil para ver cómo ahorrar!",
                        data={"screen": "analysis_screen"}
                    )
    except Exception as e:
        print(f"❌ Error en la tarea de consejos: {e}")
    finally:
        db.close()

# 2. Configuramos el despertador con la zona horaria correcta
scheduler = BackgroundScheduler(timezone=mexico_tz)

# 3. PROGRAMACIÓN PARA PRUEBA (Son las 10:28 PM, pongamos 10:32 PM)
# Cámbialo a las 21:00 cuando ya termines tus pruebas
# 💡 Esto va a intentar mandar la notificación cada 1 minuto
scheduler.add_job(check_daily_expenses, 'cron', hour=20, minute=00)  # Cambia a 'hour=21, minute=0' para producción
scheduler.add_job(send_weekly_personalized_tips, 'cron', day_of_week='mon', hour=9, minute=0)