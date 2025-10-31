from firebase_admin import messaging
import models # Para acceder al student.fcm_token

def send_fcm_notification(token: str, title: str, body: str, data: dict = None):
    """
    Envía una notificación push a un token de dispositivo específico.
    """
    if not token:
        print(f"Error de Notificación: El usuario no tiene un token FCM registrado.")
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        # 'data' se usa si quieres enviar datos para que la app navegue a una pantalla
        data=data or {} 
    )
    
    try:
        response = messaging.send(message)
        print(f"Notificación enviada exitosamente: {response}")
    except Exception as e:
        print(f"Error al enviar notificación: {e}")