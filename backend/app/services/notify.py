import os
import json
import smtplib
import urllib.request
import urllib.error
from email.message import EmailMessage

# ==========================================================
# Sends the password reset code to the user.
#
# 1. BREVO_API_KEY set  -> email sent through the Brevo API (HTTPS).
#    Use this on Render / Railway / DigitalOcean , they block SMTP ports.
# 2. SMTP_HOST set      -> email sent through SMTP (e.g. Gmail on your own PC / VPS).
# 3. Nothing set        -> code printed in the server terminal (local development).
# ==========================================================

SUBJECT = "Your OpenLane password reset code"

def reset_email_text(code):
    return (
        f"Your OpenLane password reset code is {code}.\n\n"
        "It expires in 5 minutes and can only be used once.\n"
        "If you did not ask to reset your password, you can ignore this email."
    )

def reset_email_html(code):
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;color:#0f172a">
        <h2 style="color:#0a7a4b">OpenLane</h2>
        <p>Use this code to reset your password:</p>
        <p style="font-size:32px;font-weight:bold;letter-spacing:6px;margin:20px 0">{code}</p>
        <p style="color:#64748b">It expires in 5 minutes and can only be used once.
        If you did not ask to reset your password, you can ignore this email.</p>
    </div>"""

def email_configured():
    return bool(os.getenv("BREVO_API_KEY") or os.getenv("SMTP_HOST"))

def send_with_brevo(to_email,code):
    sender_email = os.getenv("MAIL_FROM_EMAIL")
    if not sender_email:
        print("[OpenLane] MAIL_FROM_EMAIL is not set , Brevo needs a verified sender address")
        return False
    payload = {
        "sender": {"name": os.getenv("MAIL_FROM_NAME","OpenLane"),"email": sender_email},
        "to": [{"email": to_email}],
        "subject": SUBJECT,
        "textContent": reset_email_text(code),
        "htmlContent": reset_email_html(code),
    }
    request = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": os.getenv("BREVO_API_KEY"),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request,timeout=15) as response:
            return 200 <= response.status < 300
    except urllib.error.HTTPError as error:
        print(f"[OpenLane] Brevo refused the email: {error.code} {error.read().decode('utf-8','ignore')}")
    except Exception as error:
        print(f"[OpenLane] Could not reach Brevo: {error}")
    return False

def send_with_smtp(to_email,code):
    try:
        message = EmailMessage()
        message["Subject"] = SUBJECT
        message["From"] = os.getenv("SMTP_FROM",os.getenv("SMTP_USER","no-reply@openlane.local"))
        message["To"] = to_email
        message.set_content(reset_email_text(code))
        message.add_alternative(reset_email_html(code),subtype="html")
        with smtplib.SMTP(os.getenv("SMTP_HOST"),int(os.getenv("SMTP_PORT","587")),timeout=15) as server:
            server.starttls()
            if os.getenv("SMTP_USER"):
                server.login(os.getenv("SMTP_USER"),os.getenv("SMTP_PASSWORD",""))
            server.send_message(message)
        return True
    except Exception as error:
        print(f"[OpenLane] Could not send reset email: {error}")
        return False

def send_reset_code(to_email,code):
    # Returns True only when an email really went out
    if to_email and "@" in to_email:
        if os.getenv("BREVO_API_KEY"):
            return send_with_brevo(to_email,code)
        if os.getenv("SMTP_HOST"):
            return send_with_smtp(to_email,code)

    if not email_configured():
        print(f"[OpenLane] Password reset code for {to_email}: {code}")
    return False

def show_reset_code():
    # Only for local development , never turn this on in production
    return os.getenv("SHOW_RESET_CODE","false").lower() == "true"
