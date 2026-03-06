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


def validate_nric(nric: str):
    """
    Validate NRIC format and checksum.
    """
    nric = nric.strip().upper()

    nric_pattern = r"^[STFGM]\d{7}[A-Z]$"
    if not re.match(nric_pattern, nric):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid NRIC format. Expected format: [STFGM]XXXXXXXC (e.g., S1234567D)",
        )

    first_char = nric[0]
    digits = nric[1:8]
    checksum = nric[8]

    calculated_checksum = _calculate_nric_checksum(first_char, digits)

    if checksum != calculated_checksum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid NRIC checksum"
        )


def _calculate_nric_checksum(first_char: str, digits_str: str) -> str:
    """
    Calculate the NRIC checksum based on Singapore NRIC algorithm.
    """
    weights = [2, 7, 6, 5, 4, 3, 2]
    digits = [int(d) for d in digits_str]

    weighted_sum = sum(digit * weight for digit, weight in zip(digits, weights))

    if first_char in ("T", "G"):
        offset = 4
    elif first_char == "M":
        offset = 3
    else:
        offset = 0

    index = (offset + weighted_sum) % 11

    checksum_table = _get_checksum_table(first_char)

    return checksum_table[index]


def _get_checksum_table(first_char: str) -> list[str]:
    """
    Get the checksum table based on the first character.
    """
    checksums = {
        "ST": ["J", "Z", "I", "H", "G", "F", "E", "D", "C", "B", "A"],
        "FGM": ["X", "W", "U", "T", "R", "Q", "P", "N", "M", "L", "K"],
    }

    for key, table in checksums.items():
        if first_char in key:
            return table

    raise ValueError(f"Unable to find checksum table for '{first_char}'")

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