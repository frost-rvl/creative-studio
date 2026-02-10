from flask import current_app, render_template

from flaskr.email import send_email


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        "Creative Studio - Reset Your Password",
        sender=current_app.config["ADMINS"][0],
        recipients=[user.email],
        text_body=render_template(
            "email/reset_password_template.txt", user=user, token=token
        ),
        html_body=render_template(
            "email/reset_password_template.html", user=user, token=token
        ),
    )


def send_email_verficication_email(user):
    token = user.get_email_verification_token()
    send_email(
        "Creative Studio - Email Verification",
        sender=current_app.config["ADMINS"][0],
        recipients=[user.email],
        text_body=render_template(
            "email/email_verification_template.txt", user=user, token=token
        ),
        html_body=render_template(
            "email/email_verification_template.html", user=user, token=token
        ),
    )
