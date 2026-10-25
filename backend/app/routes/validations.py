import re
import email_validator
from email_validator import validate_email ,  EmailNotValidError

def validate_the_email(email):
    if email:
        try:
            result = validate_email(email)
            email = result.normalized
            return [True]
                    
        except EmailNotValidError:
            return [False,"Provide a valid Email address"]
    return [False,"Provide a valid Email address"]
    
def validate_phone(phone):
    if phone[0] == "+":
        phone2 = "0" + phone[len(phone)-9:]
        if not(phone2.isdigit()):
            return [False,"Provide a valid Phone number"]

        return [True]
    else:
        if len(phone) == 10:
            return [True]
        return [False,"Provide a valid Phone number"]

def password_strength(password):
    pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{12,}$"
    if len(password) >= 2 and re.search(pattern,password):
        return [True]
    return [False,"Enter strong password"]