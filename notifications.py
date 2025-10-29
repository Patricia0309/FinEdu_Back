# backend/notifications.py
from firebase_admin import messaging
import models

def send_fcm_notification(student: models.Student, title: str, body: str):
    """Envía una notificación push a un estudiante si tiene un token FCM."""
    if not student.fcm_token:
        print(f"INFO: El estudiante {student.id} no tiene token FCM registrado.")
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=student.fcm_token,
    )

    try:
        response = messaging.send(message)
        print(f"INFO: Notificación enviada exitosamente a estudiante {student.id}: {response}")
    except Exception as e:
        print(f"ERROR: No se pudo enviar notificación a estudiante {student.id}: {e}")