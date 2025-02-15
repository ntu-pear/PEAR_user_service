import re

def mask_NRIC(nric):
    return "X"*5+nric[-4:]
