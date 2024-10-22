# PEAR_user_service

to do:
- distribute the secret key to each microservice (they validate jwt on their own service)
- our service will deal with login, account creation, rbac, and generating jwt


Email Generation:
1. Go to your Google Account.
2. Click on Security on the left menu.
3. Under the "Signing in to Google" section, enable 2-Step Verification (if not already enabled).
4. After enabling 2-Step Verification, you will see an option to "App passwords".
5. Click on App passwords, and you can generate a password specifically for your FastAPI email service (select Mail as the app and Other for the device).
7. Google will generate a 16-character password. Use this password in place of your Gmail password.