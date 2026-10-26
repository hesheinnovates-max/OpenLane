import re
import email_validator
from email_validator import validate_email ,  EmailNotValidError

def validate_the_email(email):
    if email:
        try:
            result = validate_email(email,check_deliverability=False)
            email = result.normalized
            return [True]
                    
        except EmailNotValidError:
            return [False,"Provide a valid Email address"]
    return [False,"Provide a valid Email address"]

def normalize_phone(phone):
    # Remove spaces , dashes and brackets so "082 123 4567" and "0821234567" match
    if not phone:
        return ""
    return re.sub(r"[\s\-\(\)]","",phone.strip())

def validate_phone(phone):
    phone = normalize_phone(phone)
    if not phone:
        return [False,"Provide a valid Phone number"]
    if phone[0] == "+":
        # International number e.g +27821234567
        if not(phone[1:].isdigit()) or len(phone) < 11 or len(phone) > 15:
            return [False,"Provide a valid Phone number"]

        return [True]
    else:
        if len(phone) == 10 and phone.isdigit():
            return [True]
        return [False,"Provide a valid Phone number"]

def password_strength(password):
    pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{12,}$"
    if len(password) >= 2 and re.search(pattern,password):
        return [True]
    return [False,"Password needs 12+ characters with an uppercase letter, a lowercase letter, a number and a special character"]

def validate_required(value,field_name,max_length=None):
    # Check that a required text field was filled in and is not too long
    if not value or not value.strip():
        return [False,f"{field_name} is required"]
    if max_length and len(value.strip()) > max_length:
        return [False,f"{field_name} must be {max_length} characters or less"]
    return [True]

def validate_optional_url(url):
    if not url:
        return [True]
    if re.match(r"^https?://[^\s]+\.[^\s]+$",url.strip()):
        return [True]
    return [False,"Provide a valid link starting with http:// or https://"]
