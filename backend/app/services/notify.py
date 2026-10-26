import os
import smtplib
from email.message import EmailMessage

# ==========================================================
# Sends the password reset code to the user.
# If SMTP is configured in .env the code is emailed,
# otherwise it is printed in the server terminal.
# ==========================================================

def send_reset_code(detail,code):
    smtp_host = os.getenv("SMTP_HOST")
    if smtp_host and "@" in detail:
        try:
            message = EmailMessage()
            message["Subject"] = "Your OpenLane password reset code"
            message["From"] = os.getenv("SMTP_FROM",os.getenv("SMTP_USER","no-reply@openlane.local"))
            message["To"] = detail
            message.set_content(
                f"Your OpenLane password reset code is {code}.\n\n"
                "It expires in 5 minutes. If you did not ask for this, you can ignore this email."
            )
            with smtplib.SMTP(smtp_host,int(os.getenv("SMTP_PORT","587"))) as server:
                server.starttls()
                if os.getenv("SMTP_USER"):
                    server.login(os.getenv("SMTP_USER"),os.getenv("SMTP_PASSWORD",""))
                server.send_message(message)
            return True
        except Exception as error:
            print(f"Could not send reset email: {error}")

    print(f"[OpenLane] Password reset code for {detail}: {code}")
    return False

def show_reset_code():
    # Only for local development , never turn this on in production
    return os.getenv("SHOW_RESET_CODE","false").lower() == "true"
