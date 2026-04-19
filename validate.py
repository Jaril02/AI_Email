import dns.resolver
import re

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

def is_valid_syntax(email: str) -> bool:
    return re.match(EMAIL_REGEX, email) is not None


def has_mx_record(domain: str) -> bool:
    try:
        records = dns.resolver.resolve(domain, "MX")
        return len(records) > 0
    except:
        return False

def validate_email(email: str) -> dict:
    result = {
        "email": email,
        "valid": False,
        "reason": None
    }

    # Step 1: Syntax
    if not is_valid_syntax(email):
        result["reason"] = "Invalid syntax"
        return result

    # Step 2: Domain check
    domain = email.split("@")[1]
    if not has_mx_record(domain):
        result["reason"] = "Domain has no MX records"
        return result

    result["valid"] = True
    return result
