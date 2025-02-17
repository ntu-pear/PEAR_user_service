import re
import os
from fastapi import HTTPException, status, File
from datetime import date,datetime, timedelta
import pytz

# Set timezone to Singapore Time (SGT)
sgt_tz = pytz.timezone("Asia/Singapore")
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
#Check for contact No format
def validate_contactNo(contactNo):
    #Contact No regex pattern
    contactNo_pattern = r'^[89]\d{7}$'
    if not re.match(contactNo_pattern, contactNo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Contact No. Format. Contact No. must start with 8 or 9 and contain 8 digits."
        )
    
# Check for Date of Birth format and constraints
def validate_dob(DOB: date):
        
    # Calculate age constraints
    today = date.today(sgt_tz)
    min_date = today - timedelta(days=15 * 365.25)  # 15 years ago
    max_date = today - timedelta(days=150 * 365.25)  # 150 years ago

    if DOB > min_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date of Birth indicates the person is younger than 15 years old."
        )
    
    if DOB < max_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date of Birth indicates the person is older than 150 years old."
        )
    
#Check for profile file format
def validate_profile_picture_format(file: File):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")
    
    # Validate file type
    ALLOWED_FILE_TYPES = ["image/jpeg", "image/png"]
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPG and PNG images are allowed."
        )
    
    # Validate file extension
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension. Only JPG and PNG images are allowed."
        )
