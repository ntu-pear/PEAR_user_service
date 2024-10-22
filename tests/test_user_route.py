# test_user_router.py

import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../app")

from app.main import app
from app.models.user_model import User 

client = TestClient(app)

# Test: Create a new user
# def test_create_user():
#     response = client.post(
#         "/api/v1/users/", 
#         json={
#         "firstName": "Mark",
#         "lastName": "Johnson",
#         "preferredName": "MJ",
#         "nric": "S2345678G",
#         "address": "789 Bukit Timah, #12-01, Singapore 589123",
#         "dateOfBirth": "1992-12-15T00:00:00Z",
#         "gender": "M",
#         "contactNo": "+65 92345678",
#         "allowNotification": "T",
#         "profilePicture": "https://example.com/profile",
#         "lockoutReason": "None",
#         "loginTimeStamp": "2024-09-25T09:30:45.100Z",
#         "lastPasswordChanged": "2024-08-20T14:25:30.789Z",
#         "status": "Active",
#         "userName": "mark.johnson",
#         "email": "mark.johnson@example.com",
#         "emailConfirmed": "T",
#         "passwordHash": "hashed_password_string_3",
#         "securityStamp": "random_security_stamp_3",
#         "concurrencyStamp": "random_concurrency_stamp_3",
#         "phoneNumber": "+65 92345678",
#         "phoneNumberConfirmed": "T",
#         "twoFactorEnabled": "T",
#         "lockOutEnd": "2024-09-25T09:30:45.100Z",
#         "lockOutEnabled": "T",
#         "accessFailedCount": 0
#         }

#     )
#     assert response.status_code == 200
#     data = response.json()
#     assert data["userName"] == "mark.johnson"
#     assert data["email"] == "mark.johnson@example.com"

# Test: Get a user by ID
def test_get_user_by_id():
    user_id = 1  
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["userName"] == "john.doe1"

def test_get_non_existent_user_by_id():
    user_id = 10  
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404


# Test: Update user information
def test_update_user():
    user_id = 1  
    response = client.put(
        f"/api/v1/users/{user_id}",
        json={
            "firstName": "John",
            "lastName": "Doe",
            "preferredName": "Johnny",
            "nric": "S1234567D",
            "address": "123 Orchard Road, #12-34, Singapore 238888",
            "dateOfBirth": "1990-05-14T00:00:00Z",
            "gender": "M",
            "contactNo": "+65 91234567",
            "allowNotification": "T",
            "profilePicture": "https://example.com/",
            "lockoutReason": "None",
            "loginTimeStamp": "2024-09-20T04:03:39.213Z",
            "lastPasswordChanged": "2024-08-15T12:34:56.789Z",
            "status": "Active",
            "userName": "john.doe1",
            "email": "john.doe@example.com",
            "emailConfirmed": "T",
            "passwordHash": "hashed_password_string",
            "securityStamp": "random_security_stamp",
            "concurrencyStamp": "random_concurrency_stamp",
            "phoneNumber": "+65 91234567",
            "phoneNumberConfirmed": "T",
            "twoFactorEnabled": "T",
            "lockOutEnd": "2024-09-20T04:03:39.213Z",
            "lockOutEnabled": "T",
            "accessFailedCount": 0
            }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["userName"] == "john.doe1"

# def test_delete_user():
#     user_id = 6  
#     response = client.delete(f"/api/v1/users/{user_id}")
#     assert response.status_code == 200  
