import re
import os
from fastapi import HTTPException, status, File
from datetime import date,datetime, timedelta
import pytz
from email_validator import validate_email as ev_validate_email, EmailNotValidError

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
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 special character
    """
    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*(),.?\":{}|<>])(?=.{12,})", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Password must be at least 12 characters long, "
                "contain at least 1 uppercase letter, 1 lowercase letter, and 1 special character."
            )
        )

#Check for valid NRIC format

def validate_nric(nric: str) -> str:
    if not nric:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NRIC is required."
        )

    nric = nric.strip().upper()

    pattern = r"^[STFGM]\d{7}[A-Z]$"
    if not re.match(pattern, nric):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC format"
        )

    weights = [2, 7, 6, 5, 4, 3, 2]
    digits = [int(char) for char in nric[1:8]]

    total = sum(d * w for d, w in zip(digits, weights))

    prefix = nric[0]
    suffix = nric[-1]

    if prefix in ["T", "G"]:
        total += 4
    elif prefix == "M":
        total += 3

    st_table = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "Z", "J"]
    gf_table = ["K", "L", "M", "N", "P", "Q", "R", "T", "U", "W", "X"]
    m_table = ["K", "L", "J", "N", "P", "Q", "R", "T", "U", "W", "X"]

    remainder = total % 11
    check_index = 11 - (remainder + 1)

    if prefix in ["S", "T"]:
        expected_suffix = st_table[check_index]
    elif prefix in ["F", "G"]:
        expected_suffix = gf_table[check_index]
    elif prefix == "M":
        expected_suffix = m_table[check_index]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC prefix."
        )

    if suffix != expected_suffix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC. Please check the last letter"
        )

    return nric
#Check for contact No format
def validate_contactNo(contactNo):
    #Contact No regex pattern
    contactNo_pattern = r'^[89]\d{7}$'
    if not re.match(contactNo_pattern, contactNo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Contact No. Format. Contact No. must start with 8 or 9 and contain 8 digits."
        )
    return contactNo
    
# Check for Date of Birth format and constraints
def validate_dob(DOB: date):
        
    # Calculate age constraints
    today = datetime.now(sgt_tz).date()  # Convert to date
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
    return DOB
    
# Constants for file size limits
MIN_FILE_SIZE = 5 * 1024        # 5 KB
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB

def validate_profile_picture_format(file: File):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not an image")

    # Validate allowed content types
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
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to the end of the file
    file_size = file.file.tell()
    file.file.seek(0)     # Reset file pointer to the beginning

    if file_size < MIN_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too small. Minimum size is {MIN_FILE_SIZE // 1024} KB."
        )
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)} MB."
        )

def validate_email(email: str) -> str:
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required."
        )

    email = email.strip()

    try:
        validated = ev_validate_email(email, check_deliverability=True)
        return validated.normalized
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Check for uppercase name format
def validate_uppercase_name(name: str, field_name: str = "Name") -> str:
    if not name:
        return name

    name = name.strip().upper()

    name_pattern = r'^[A-Z\s]+$'
    if not re.match(name_pattern, name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} can only contain uppercase letters and spaces."
        )

    return name