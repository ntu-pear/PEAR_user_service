# PEAR_user_service

## Overview
PEAR User Service is a microservice for managing user-related data. This repository provides the setup and development instructions to get the service running locally.

## IMPORTANT
Keep any keys that you set in env secret especially when in production. This uses a symmetric key algorithm so leaking the key will leak every possible password too.

## Setup
### Run(Current):
Environment Configuration
Fill up the configuration file in .env.example

```bash
docker compose up --build
```
### When Deployed for Local Development:
Clone the repository using the following command:
```bash
git clone https://github.com/ntu-pear/PEAR_user_service.git
cd PEAR_user_service
```
Setting Up Your Environment
1. Create a Virtual Environment:
Conda:
```bash
# This is to set the python version in your conda environment to 3.9.19
conda create -n pear_user_service python=3.9.19
conda activate pear_user_service
```
Python
```bash
python -m venv pear_user_service
pear_user_service/Scripts/activate #for windows
# source pear_user_service/bin/activate for linux
```
Install the required dependencies
```bash
#install the necessary requirements in the conda environment
pip install -r requirements.txt
```

Environment Configuration
Fill up the configuration file in .env.example

Running the Application 
After the installation is completed, run the application on your machine
```bash
uvicorn app.main:app --reload
```


## To Do:
- Deploy user service
- Create SMTP service to replace email sending
- Populate Database
- Add in 2FA authorization (pending if needed)
- Add in security level check in functions (Should be done after gateway is completed?)
- NRIC returned as masked depending on security level

## Structure
Project structure was taken from: https://medium.com/@amirm.lavasani/how-to-structure-your-fastapi-projects-0219a6600a8f 

# Features
## User authorization
Functions related to user authorization is in the ./service/user_auth_service.py

## Email Service
NOTE: DO NOT refer to the old codebase to implement the email service for this. The method has been discontinued by Google and will be permanently disabled for use fully by Jan 2025. There is also security risk involved when doing it as it involved turning down ur security level to allow any application to login to your main account.

### Currently

NOTE: Requires 2FA authorization linked account

The main code is in service/email_service.py
How to set up Email to send:
1. Go to your Google Account.
2. Click on Security on the left menu.
3. Under the "Signing in to Google" section, enable 2-Step Verification (if not already enabled).
4. After enabling 2-Step Verification, you will see an option to "App passwords".
5. Click on App passwords, and you can generate a password specifically for your FastAPI email service (select Mail as the app and Other for the device).
7. Google will generate a 16-character password. Use this password in place of your Gmail password.
8. Put it in .env file as GOOGLE_SERVICE_ACCOUNT_KEY and the email that is sending as MAIL_USERNAME and MAIL_FROM

### Google Workspace
Another set of code to work around is in service/googleemail_service.py which is not implemented in as it is more or less a roundabout method for the same result as the current method unless a Google Organization account is created.

How to set up Email to send:
This uses Google Workspace to send out emails to users using a service account for security issues. It requires user to be under and organization too or verified too so either ways some method of authorization is needed.

### To Shift To
As per prof request, this should be shifted to creating a SMTP server. This is basically creating a seperate email service entity that handles just the sending of email.

## Currently
- User
For the simple CRUD of user
- Role
To store all the roles availble like Caregiver and Administrator
- Secret Question
To make default secret questions for users to answer and store as an identity
- User Role
Maps user to their role
- User Secret Question
Maps user to their secret question and answer
