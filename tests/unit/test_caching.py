# # this script tests the caching (only test locally and exclude from CI/CD)
# # python tests\test_caching.py

# # TESTING Caching Performance ====
# # Token obtained: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ7XCJ1c2VySWRcIjogXCJBZmE1M2VjNDhlMmZcIiwgXCJmdWxsTmFtZVwiOiBcIkpBTklDRSBPTkdcIiwgXCJyb2xlTmFtZVwiOiBcIkFETUlOXCIsIFwic2Vzc2lvbklkXCI6IFwiNDNmNmI2MDFjYTQwNDdhYWI1YjFcIn0iLCJleHAiOjE3NDE5NTQwMTJ9.jYQEUMQY2z54xyWUZCcOxfw_o7mhoDLq38ZpBJu0MJg


# # --- Caching Test (First Request) ---
# # ✅ Request Data: {'id': 'Afa53ec48e2f', 'preferredName': None, 'nric_FullName': 'JANICE ONG', 'nric': '*****323D', 'nric_Address': '123 Serangoon Ave 1 #04-332 Singapore 550123', 'nric_DateOfBirth': '2000-02-01', 'nric_Gender': 'F', 'roleName': 'ADMIN', 'contactNo': '81241223', 'allowNotification': True, 'profilePicture': 'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162954/profile_pictures/user_Ufa53ec48e2f_profile_picture.jpg', 'status': 'ACTIVE', 'email': 'janice@gmail.com', 'emailConfirmed': True, 'verified': True, 'active': True, 'twoFactorEnabled': False}
# # Time: 0.0125 seconds

# # --- Caching Test (Second Request) ---
# # ✅ Request Data: {'id': 'Afa53ec48e2f', 'preferredName': None, 'nric_FullName': 'JANICE ONG', 'nric': '*****323D', 'nric_Address': '123 Serangoon Ave 1 #04-332 Singapore 550123', 'nric_DateOfBirth': '2000-02-01', 'nric_Gender': 'F', 'roleName': 'ADMIN', 'contactNo': '81241223', 'allowNotification': True, 'profilePicture': 'https://res.cloudinary.com/dnusi4qsd/image/upload/v1739162954/profile_pictures/user_Ufa53ec48e2f_profile_picture.jpg', 'status': 'ACTIVE', 'email': 'janice@gmail.com', 'emailConfirmed': True, 'verified': True, 'active': True, 'twoFactorEnabled': False}
# # Cache Time: 0.0100 seconds
# # Database Time: 0.0125 seconds
# # Cache Time: 0.0100 seconds
# # ✅ Cache hit and performance improvement!

# import httpx
# import time

# API_URL = "http://127.0.0.1:8000/test-rate-limit"  # Adjust based on your server
# API_IP_URL = "http://127.0.0.1:8000/test-ip-rate-limit"
# API_LOGIN_URL = "http://127.0.0.1:8000/api/v1/login/"
# API_USER_URL = "http://127.0.0.1:8000/api/v1/user/get_user/"

# def test_caching():
#     with httpx.Client() as client:
#         # Step 1: Perform login (Same as your login test)
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
#         print("Token obtained:", token)
#         print(" ")

#         # Step 2: Perform two requests for the same user to show caching speedup
#         print("\n--- Caching Test (First Request) ---")
#         delay_between_requests = 0.1

#         # Measure time for the first request (database fetch)
#         start_time = time.time()
#         response = client.get(f"{API_USER_URL}", headers=headers)
#         db_time = time.time() - start_time
#         status = response.status_code
#         data = response.json()

#         if status == 200:
#             print(f"✅ Request Data: {data}")
#             print(f"Time: {db_time:.4f} seconds")
#         else:
#             print(f"❌ Request Error {status} - {data}")

#         time.sleep(delay_between_requests)

#         # Step 3: Perform the same request again to test caching speedup
#         print("\n--- Caching Test (Second Request) ---")
#         # Measure time for the second request (cache hit)
#         start_time = time.time()
#         response = client.get(f"{API_USER_URL}", headers=headers)
#         cache_time = time.time() - start_time
#         status = response.status_code
#         data = response.json()

#         if status == 200:
#             print(f"✅ Request Data: {data}")
#             print(f"Cache Time: {cache_time:.4f} seconds")
#         else:
#             print(f"❌ Request Error {status} - {data}")
        
#         print(f"Database Time: {db_time:.4f} seconds")
#         print(f"Cache Time: {cache_time:.4f} seconds")

#         # Additional Check for Cache Hit
#         if db_time > cache_time:
#             print("✅ Cache hit and performance improvement!")
#         else:
#             print("❌ Cache did not improve performance.")
        
#         time.sleep(delay_between_requests)

# if __name__ == "__main__":
#     print("TESTING Caching Performance ====")
#     test_caching()