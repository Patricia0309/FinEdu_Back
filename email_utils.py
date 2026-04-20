import os
import requests


def send_otp_email(target_email: str, otp_code: str):
    API_KEY = "BREVO_API_KEY" 
    URL = "https://api.brevo.com/v3/smtp/email"

    # 🎨 2. El mismo diseño que ya tenías
    html_content = f"""
    <html>
      <body style="font-family: sans-serif; color: #333;">
        <div style="max-width: 400px; margin: auto; border: 1px solid #eee; padding: 20px;">
          <h2 style="color: #2E7D32;">¡Hola!</h2>
          <p>Tu código de recuperación para <b>FinEdu</b> es:</p>
          <div style="font-size: 32px; font-weight: bold; background: #E8F5E9; padding: 10px; text-align: center; letter-spacing: 5px; color: #1B5E20;">
            {otp_code}
          </div>
          <p style="font-size: 12px; color: #666; margin-top: 20px;">
            Este código expira en 10 minutos. Si no solicitaste esto, ignora este mensaje.
          </p>
        </div>
      </body>
    </html>
    """

    # 📦 3. El paquete que enviamos a la API
    payload = {
        "sender": {
            "name": "FinEdu 🛡️", 
            "email": "dev.finedu@gmail.com" # El correo que registraste en Brevo
        },
        "to": [{"email": target_email}],
        "subject": "Código de Seguridad FinEdu 🛡️",
        "htmlContent": html_content
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": API_KEY
    }

    try:
        # ⚡ Usamos puerto 443 (HTTPS), que nunca está bloqueado
        response = requests.post(URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 201:
            print(f"✅ OTP enviado con éxito a {target_email}")
            return True
        else:
            print(f"❌ Error de Brevo ({response.status_code}): {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error de conexión al enviar OTP: {e}")
        return False