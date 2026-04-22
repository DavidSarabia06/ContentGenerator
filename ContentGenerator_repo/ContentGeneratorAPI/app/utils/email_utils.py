import smtplib  # Librería estándar para enviar correos por SMTP
from email.mime.text import MIMEText  # Para construir el cuerpo del email como texto plano
from email.mime.multipart import MIMEMultipart  # Para permitir múltiples partes (texto, HTML, adjuntos, etc.)
import os  # Para acceder a variables de entorno
from dotenv import load_dotenv  # Carga variables del archivo .env

# 📦 Cargar variables del archivo .env
load_dotenv()

# 📬 Configuración SMTP obtenida desde .env
SMTP_SERVER = os.getenv("SMTP_SERVER")            # Servidor SMTP (ej: smtp.gmail.com)
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))      # Puerto (465 = SSL por defecto)
SMTP_USER = os.getenv("SMTP_USER")                # Correo del remitente (usado para autenticar)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")        # Contraseña de aplicación
EMAIL_FROM = os.getenv("EMAIL_FROM")              # Dirección desde la que se envía el correo

def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Envía un correo electrónico simple con texto plano.

    Args:
        to_email: destinatario del correo.
        subject: asunto del correo.
        body: cuerpo del mensaje en texto plano.

    Returns:
        True si el correo se envió con éxito, False si hubo error.
    """
    try:
        # 📄 Crear el mensaje MIME (estructura del correo)
        msg = MIMEMultipart()
        msg["From"] = EMAIL_FROM          # Remitente
        msg["To"] = to_email              # Destinatario
        msg["Subject"] = subject          # Asunto del mensaje

        # ✉️ Agregar el cuerpo como texto plano
        msg.attach(MIMEText(body, "plain"))

        # 📡 Conectarse al servidor SMTP con SSL (puerto 465)
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)  # 🔐 Autenticarse
            server.send_message(msg)                # 📤 Enviar el mensaje

        print(f"📨 Email enviado a {to_email}")
        return True  # ✅ Envío exitoso

    # ⚠️ Captura de errores comunes

    except smtplib.SMTPAuthenticationError:
        print("❌ Error de autenticación SMTP. Verifica usuario/contraseña.")
    except smtplib.SMTPConnectError:
        print("❌ No se pudo conectar al servidor SMTP.")
    except smtplib.SMTPRecipientsRefused:
        print(f"❌ Dirección rechazada: {to_email}")
    except smtplib.SMTPException as e:
        print(f"❌ Error SMTP general: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

    return False  # ❌ Fallo al enviar el correo
