from flask import current_app
from flask_mail import Message

from flaskr import mail


def send_email(subject, sender, recipients, text_body, html_body):
    try:
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        current_app.logger.info(f"Email send to {recipients}")
    except Exception as e:
        current_app.logger.error(f"Failed to send email : {str(e)}")
        raise
