import re

# NRIC regex pattern
nric_pattern = r'^[STFG]\d{7}[A-Z]$'

def validate_nric(nric):
    if re.match(nric_pattern, nric):
        return True
    else:
        return False

def mask_NRIC(nric):
    return "X"*5+nric[-4:]
