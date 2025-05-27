import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email_notification(name, email, institution, role, reason):
    sender_email = "noreply@aideatext.ai"  # Configura esto con tu dirección de correo
    receiver_email = "hello@aideatext.ai"
    password = os.environ.get("NOREPLY_EMAIL_PASSWORD")  # Configura esto en tus variables de entorno

    message = MIMEMultipart("alternative")
    message["Subject"] = "Nueva solicitud de prueba de AIdeaText"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = f"""\
    Nueva solicitud de prueba de AIdeaText:
    Nombre: {name}
    Email: {email}
    Institución: {institution}
    Rol: {role}
    Razón: {reason}
    """

    html = f"""\
    <html>
      <body>
        <h2>Nueva solicitud de prueba de AIdeaText</h2>
        <p><strong>Nombre:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Institución:</strong> {institution}</p>
        <p><strong>Rol:</strong> {role}</p>
        <p><strong>Razón:</strong> {reason}</p>
      </body>
    </html>
    """

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    try:
        with smtplib.SMTP_SSL("smtp.titan.email", 465) as server:
            logger.info("Conectado al servidor SMTP")
            server.login(sender_email, password)
            logger.info("Inicio de sesión exitoso")
            server.sendmail(sender_email, receiver_email, message.as_string())
            logger.info(f"Correo enviado de {sender_email} a {receiver_email}")
        logger.info(f"Email notification sent for application request: {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
        return False

def send_user_feedback_notification(name, email, feedback):
    sender_email = "noreply@aideatext.ai"
    receiver_email = "feedback@aideatext.ai"  # Cambia esto a la dirección que desees
    password = os.environ.get("NOREPLY_EMAIL_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Nuevo comentario de usuario en AIdeaText"
    message["From"] = sender_email
    message["To"] = receiver_email

    html = f"""\
    <html>
      <body>
        <h2>Nuevo comentario de usuario en AIdeaText</h2>
        <p><strong>Nombre:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Comentario:</strong> {feedback}</p>
      </body>
    </html>
    """

    part = MIMEText(html, "html")
    message.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.titan.email", 465) as server:
            logger.info("Conectado al servidor SMTP")
            server.login(sender_email, password)
            logger.info("Inicio de sesión exitoso")
            server.sendmail(sender_email, receiver_email, message.as_string())
            logger.info(f"Correo enviado de {sender_email} a {receiver_email}")
        logger.info(f"Email notification sent for user feedback from: {email}")
        return True
    except Exception as e:
        logger.error(f"Error sending user feedback email notification: {str(e)}")
        return False