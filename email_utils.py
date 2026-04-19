# backend/email_utils.py
import smtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "dev.finedu@gmail.com" 
SENDER_PASSWORD = "kpuplxdvonavmwgm" 

def send_otp_email(target_email: str, otp_code: str):
    msg = EmailMessage()
    msg["Subject"] = "Código de Seguridad FinEdu 🛡️"
    msg["From"] = SENDER_EMAIL
    msg["To"] = target_email
    
    # Un diseño sencillo para que no se vea como spam
    content = f"""
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
    msg.add_alternative(content, subtype="html")

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"❌ ERROR SMTP: {e}")
        return False