import os
import requests

def send_otp_email(target_email: str, otp_code: str):
    # 🌟 1. PRIMERO definimos la variable (Este era el error)
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    
    url = "https://api.brevo.com/v3/smtp/email"
    
    # 2. El contenido
    html_content = f"""
    <html>
      <body style="font-family: sans-serif;">
        <h2>¡Hola!</h2>
        <p>Tu código de seguridad FinEdu es: <b>{otp_code}</b></p>
      </body>
    </html>
    """

    # 3. Los encabezados usando la variable que definimos arriba
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key  # 👈 Aquí ya existe porque la definimos en el paso 1
    }

    payload = {
        "sender": {"name": "FinEdu", "email": "dev.finedu@gmail.com"},
        "to": [{"email": target_email}],
        "subject": "Código de Seguridad FinEdu 🛡️",
        "htmlContent": html_content
    }

    try:
        print(f"🔍 Intentando enviar correo a {target_email}...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"✅ ¡Éxito! Correo aceptado por Brevo.")
            return True
        else:
            print(f"❌ Error de Brevo ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"💥 Error crítico: {e}")
        return False
