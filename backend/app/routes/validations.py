import re
import email_validator
from email_validator import validate_email ,  EmailNotValidError

def validate_email(email):
    if email.strip():
        try:
            result = validate_email(email.strip(),check_deliverability=False)
            email = result.normalized
            return True
                    
        except EmailNotValidError:
            return {"error":"Provide a valid email address"}
    
def validate_phone(phone):
    if phone[0] == "+":
        # if phone = +54653 763 3324 ----> 14 - 10 = 4 ...from  
        phone2 = "0" + phone[len(phone)-9:]
        if not(phone2.isdigit()):
            return {"message":"Provide a valid Phone number"}

        return True

def password_strength(password):
    pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^a-zA-Z0-9]).{12,}$"
    if len(password) >= 2 and re.search(all,password):
        return True
    return {"error":"Enter strong password"}