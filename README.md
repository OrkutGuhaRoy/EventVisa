
# 📦 Project Dependencies & Optional Features Guide

## 📝 Overview

This project includes several features and optional integrations. Some modules like **Redis** and **Celery** are disabled by default to avoid unnecessary setup for users not intending to use them. Please note dependencies are mentioned in "README_DEPENDENCIES.md"

**Note:** SMTP email functionality is implemented, but real credentials have been **intentionally removed** from the codebase to prevent misuse.

** Admin Credentials : **
        ```User : admin
        Password : Admin@123```
---

## ✅ Quick Start (Without Email or Celery)

To run the main features of the application:

1. Run the following command in your terminal:
   ```bash
   python main.py
   ```
2. Open your browser and go to:
   ```
   http://localhost:8080
   ```

All features **except** scheduled tasks or email-sending will work out of the box.

---

## ✉️ Email Functionality

- The app supports email sending via **SMTP**.
- To enable it, you'll need to:
  - Use your **own email credentials** (SMTP user & password) in celerytask.py
  - This feature is **disabled by default** for safety and to avoid misuse of sensitive credentials.

---

## 🕐 Scheduled Tasks (Using Redis & Celery)

**Optional** – Only needed if you want background/scheduled job execution.

### ⚙️ Requirements:
- Recommended OS: **Ubuntu** or any Debian-based system
- Tools used: **Redis**, **Celery**

### 🛠️ Setup Steps:

1. Start Redis:
   ```bash
   sudo snap start redis
   ```
   *(Skip this if not using Celery or Redis)*

2. Uncomment the following:
   Line 11 and 12 in main.py
   ```
   from celerytask import send_email , download_csv 
   from tasks import send_daily_emails

   ```
   Line 101 in main.py
    ```
   send_daily_emails.delay()
    ```

2. Run the app:
   ```bash
   python main.py
   ```

3. In VS Code terminal, open 3 separate terminals and run:

   **Terminal 1:**
   ```bash
   celery -A celerytask worker --loglevel=INFO
   ```

   **Terminal 2:**
   ```bash
   celery -A tasks worker --loglevel=INFO
   ```

   **Terminal 3:**
   ```bash
   celery -A tasks beat --loglevel=INFO
   ```

---


