from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os

import pickle

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
USER_EMAIL = "fyppear@gmail.com"  # The email you want to impersonate
SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(__file__), "client_secret_572628089702-oiv4cm3r0s2mqq2c9j6p1nrv2vv1uqvg.apps.googleusercontent.com.json"
)# Create credentials directly from the parsed JSON
TOKEN_FILE = "token.pickle"

def authenticate():
    creds = None
    # Check if we have saved credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials, go through the console flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Starting OAuth authorization flow...")
            flow = InstalledAppFlow.from_client_secrets_file(SERVICE_ACCOUNT_FILE, SCOPES)
            try:
                creds = flow.fetch_token(code="4/0AVG7fiQ8iOd9Meqvaoy9hKWeaExDsP8wT2hJScscvyOK56bXl2VfT-wzQ7pTiJZyo_3XxA")  # Automatically handles authorization
                print("Authorization successful, credentials received.")
            except Exception as e:
                print(f"Error during authorization flow: {e}")
                return None  # Exit if authentication fails
        # Save the credentials for the next run
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)
    return creds

# Authenticate and create the Gmail service
creds = authenticate()

service = build("gmail", "v1", credentials=creds)
def send_email(subject, body, recipient):
    from email.mime.text import MIMEText
    import base64

    # Create the email
    message = MIMEText(body)
    message["to"] = recipient
    message["from"] = "your_email@gmail.com"
    message["subject"] = subject

    # Encode the email
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"raw": encoded_message}

    # Send the email
    try:
        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        print(f"Message Id: {send_message['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")