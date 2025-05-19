# # this script tests the rate limiter (only test locally and exclude from CI/CD)
# # PS C:\Users\nat\PEAR_user_service> Remove-Item -Recurse -Force .\pear_user_service
# # >> 
# # PS C:\Users\nat\PEAR_user_service> python -m venv pear_user_service
# # >> 
# # PS C:\Users\nat\PEAR_user_service> .\pear_user_service\Scripts\Activate
# # (pear_user_service) PS C:\Users\nat\PEAR_user_service> python -m pip install --upgrade pip
# # pip install -r requirements.txt
# # pip show pydantic
# # pip show pydantic_core
# # uvicorn app.main:app --reload  

# # python tests\test_rate_limiter.py



# import sys
# sys.path.append('c:/Users/nat/PEAR_user_service')

# from app.service.user_auth_service import create_access_token
# import httpx
# import time
# from unittest import mock
# # from fastapi.testclient import TestClient
# # from app.main import app  # Replace with your actual FastAPI app

# API_URL = "http://127.0.0.1:8000/test-rate-limit"  # Adjust based on your server
# API_IP_URL = "http://127.0.0.1:8000/test-ip-rate-limit"
# API_LOGIN_URL = "http://127.0.0.1:8000/api/v1/login/"
# API_USER_URL = "http://127.0.0.1:8000/api/v1/user/get_user/"

# # Simulating different IPs
# TEST_IPS = ["192.168.1.1", "192.168.1.2"]

# # the test route will initialise with a token bucket of capacity 2
# # and fills 1 token every second, so it should allow the first 2 requests
# # and then only after 1 second from the 1st request, allow another request
# # i.e. requests should be allowed at time stamps 0.0s, 0.2s and 1.0s within this 0.2*10=5s time frame
# def test_rate_limiter(requests_to_send=10, delay_between_requests=0.2):
#     """
#     Sends multiple requests to the rate-limited endpoint and checks when it gets blocked.
    
#     :param requests_to_send: Number of requests to send.
#     :param delay_between_requests: Time delay between requests (seconds).
#     """
#     with httpx.Client() as client:
#         for i in range(requests_to_send):
#             response = client.get(API_URL)
#             status = response.status_code
#             data = response.json()

#             if status == 200:
#                 print(f"✅ Request {i+1}: Allowed - {data}")
#             else:
#                 print(f"❌ Request {i+1}: Blocked - Status {status} - {data}")

#             time.sleep(delay_between_requests)  # Control request rate

# def test_rate_limiter_ip(requests_to_send=30, delay_between_requests=0.1):
#     """
#     Sends multiple requests to the rate-limited endpoint and checks when it gets blocked.
#     """
#     with httpx.Client() as client:
#         for i in range(requests_to_send):
#             ip = TEST_IPS[i % len(TEST_IPS)]  # Rotate between different IPs
#             headers = {"X-Forwarded-For": ip}  # Mock client IP
            
#             response = client.get(API_IP_URL, headers=headers)
#             status = response.status_code
#             data = response.json()

#             if status == 200:
#                 print(f"✅ Request {i+1} (IP: {ip}): Allowed - {data}")
#             else:
#                 print(f"❌ Request {i+1} (IP: {ip}): Blocked - Status {status} - {data}")

#             time.sleep(delay_between_requests)  # Control request rate




# # to test this, you need to first reduce the global bucket rate to 0.1 or something, cos rn its at 5, so it refills 5 tokens each second
# # you can change it at PEAR_user_service\app\routers\user_router.py
# def test_login():
#     with httpx.Client() as client:
#         # Step 1: Perform login
#         # login
#         data = {
#             "username": "janice@gmail.com",
#             "password": "Admin!23"
#         }
#         login_response = client.post(API_LOGIN_URL, data=data)
        
#         if login_response.status_code != 200:
#             print(f"❌ Login failed: {login_response.json()}")
#             return
        
#         # Extract access token
#         token = login_response.json().get("access_token")
#         if not token:
#             print("❌ No access token received.")
#             return
        
#         # Set Authorization header for future requests
#         headers = {
#             "Authorization": f"Bearer {token}"
#         }
#         print("token obtained", token)


#         requests_to_send = 15
#         delay_between_requests = 0.1
#         for i in range(requests_to_send):
#             response = client.get(API_USER_URL, headers = headers)
#             status = response.status_code
#             data = response.json()

#             if status == 200:
#                 print(f"✅ Request {i+1}: Allowed - {data}")
#             else:
#                 print(f"❌ Request {i+1}: Blocked - Status {status} - {data}")

#             time.sleep(delay_between_requests)  # Control request rate
        

# if __name__ == "__main__":
#     print("TESTING Normal Rate Limiter ====")
#     test_rate_limiter()
#     print("TESTING IP Rate Limiter ====")
#     test_rate_limiter_ip()
#     print("TESTING GET USER Rate Limiter ====")
#     test_login()
