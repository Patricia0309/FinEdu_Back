import os
import requests

def send_otp_email(target_email: str, otp_code: str):
    # 🌟 AQUÍ ESTABA EL DETALLE: Debemos definir api_key antes de usarla
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    
    url = "https://api.brevo.com/v3/smtp/email"
    html_content = f"<html><body><h3>Tu código FinEdu es: {otp_code}</h3></body></html>"

    payload = {
        "sender": {"name": "FinEdu App", "email": "dev.finedu@gmail.com"},
        "to": [{"email": target_email}],
        "subject": "Código de Seguridad FinEdu 🛡️",
        "htmlContent": html_content
    }

    # 🔑 Ahora que api_key ya existe, la usamos aquí:
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key  # 👈 Ya no pongas .strip() aquí, ya lo hicimos arriba
    }

    try:
        # Logs para que veas en la terminal qué pasa
        print(f"🔍 Intentando enviar correo a {target_email}...")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"✅ Correo enviado con éxito.")
            return True
        else:
            print(f"❌ Error de Brevo ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"💥 Error crítico: {e}")
        return False