import firebase_admin
from firebase_admin import credentials, messaging
import os

# 1. Configuración de la "llave"
# Asegúrate de que este archivo esté en la misma carpeta que notifications.py
cred_path = "firebase-credentials.json"

if not firebase_admin._apps:
    try:
        # Cargamos las credenciales desde el JSON que descargaste de Firebase
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("🔥 Firebase Admin inicializado correctamente.")
    except Exception as e:
        print(f"❌ Error al inicializar Firebase: {e}")

def send_fcm_notification(token: str, title: str, body: str, data: dict = None):
    """
    Envía una notificación push a un dispositivo específico.
    """
    if not token:
        print("⚠️ Error: El usuario no tiene un token FCM registrado.")
        return False

    # Creamos el mensaje
    # 'notification' es lo que ve el usuario (banner)
    # 'data' son metadatos que Flutter puede leer (invisible para el usuario)
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        android=messaging.AndroidConfig(
            notification=messaging.AndroidNotification(
                icon='ic_notification', # 👈 Debe coincidir con el nombre en 'drawable'
                color='#3c503d'        # Tu verde de FinEdu
            ),
        ),
        token=token,
        data=data or {} 
    )
    
    try:
        response = messaging.send(message)
        print(f"✅ Notificación enviada: {response}")
        return True
    except Exception as e:
        print(f"❌ Error de Firebase: {e}")
        return False