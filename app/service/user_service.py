import re
from fastapi import HTTPException, status

### Check new user details
def verify_userDetails(db_user, user):
    # Define the fields to compare
    fields_to_check = ["nric_FullName","nric", "email", "nric_DateOfBirth", "contactNo", "roleName"]
    for field in fields_to_check:
        if getattr(db_user, field) != getattr(user, field):
            return False
    return True

#Check for valid password format
def validate_password_format(password: str):
    """
    Validate password with the following rules:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 special character
    """
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*(),.?\":{}|<>])(?=.{8,})", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password must be at least 8 characters long, "
                "contain at least 1 uppercase letter, 1 lowercase letter, and 1 special character."
            )
        )

#Check for valid NRIC format
def validate_nric(nric):
    # NRIC regex pattern
    nric_pattern = r'^[STFG]\d{7}[A-Z]$'
    if not re.match(nric_pattern, nric):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Invalid NRIC Format")
            )
