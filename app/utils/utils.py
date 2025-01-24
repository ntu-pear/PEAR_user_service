def mask_nric(nric: str, visible_chars: int = 4) -> str:
    
    """
    Mask NRIC by showing only the first and last 3 characters.
    For example: 'S0001230A' -> 'S***230A'.
    """
    if len(nric) <= 4:
        return "S***"

    return nric[0] + '*' * (len(nric) - visible_chars - 1) + nric[-visible_chars:]
