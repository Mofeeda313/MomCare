# MomCare - Mother & Child Healthcare Application

A web application designed for mother and child healthcare monitoring and support, built with Python Flask, SQLite, HTML5, CSS3, and JavaScript.

---

## Project Structure

```text
MomCare/
├── app.py                      # Main Flask application, routes & role authorization
├── database.py                 # SQLite connection handling, schema & queries
├── create_admin.py             # Secure development CLI to provision Administrator accounts
├── test_auth.py                # Automated test suite for registration, auth & dashboards
├── requirements.txt            # Project dependencies (Flask)
├── README.md                   # Instructions to set up and run the application
├── static/
│   ├── css/
│   │   └── style.css           # Healthcare-themed styling (Teal & White theme)
│   └── js/
│       └── main.js             # Client-side interactivity, password toggle & health check
└── templates/
    ├── index.html              # Home page with preserved status & auth navigation
    ├── register.html           # Professional registration form (Mother & Healthcare Worker)
    ├── login.html              # Sign in page with show/hide password & forgot password link
    ├── forgot_password.html    # Password recovery instructions
    ├── dashboard_mother.html   # Mother dashboard (Maternal care & wellness milestones)
    ├── dashboard_worker.html   # Healthcare Worker portal (Community mothers & field tools)
    └── dashboard_admin.html    # Administrator dashboard (User management & system controls)
```

---

## Prerequisites

- **Python 3.8+** installed on your system.

---

## Quick Start Guide

### 1. Open Terminal or PowerShell
Navigate to the project root directory:
```bash
cd c:\Users\HP\Desktop\MomCare
```

### 2. Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

---

### 3. Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

---

### 4. Create an Administrator Account
Because public registration only allows **Mother** and **Healthcare Worker** roles, create the Admin account via the secure development command:

```bash
python create_admin.py --email admin@momcare.org --password "Admin@12345" --name "MomCare Administrator"
```
*(You can also use custom flags for `--email`, `--password`, `--name`, and `--phone`)*.

---

### 5. Run the Application

Start the Flask server:
```bash
python app.py
```

Open your browser at:
```
http://127.0.0.1:5000/
```

---

## How to Test Each Role

### 1. Testing Mother Role
1. Navigate to `http://127.0.0.1:5000/register`.
2. Enter Full Name, Email, Phone, Password, choose a language (e.g., Malayalam), and select **Role: Mother**.
3. Click **Complete Registration**. You will be redirected to `/login` with a success alert.
4. Log in with the registered credentials.
5. You are automatically routed to the **Mother Dashboard** (`/dashboard/mother`), displaying personalized maternal wellness tips and assigned care contacts.
6. Try visiting `/dashboard/admin`: you will be blocked and redirected back with an **Access Denied** message.

### 2. Testing Healthcare Worker Role
1. Navigate to `http://127.0.0.1:5000/register`.
2. Enter details, select **Role: Healthcare Worker**, and submit.
3. Sign in at `http://127.0.0.1:5000/login`.
4. You are automatically routed to the **Healthcare Worker Dashboard** (`/dashboard/healthcare-worker`).
5. You will see community field statistics and the table of all registered mothers dynamically loaded from the SQLite database.
6. Try visiting `/dashboard/admin`: access is restricted to Admins only.

### 3. Testing Administrator Role
1. Ensure the admin is created using `python create_admin.py`.
2. Sign in at `http://127.0.0.1:5000/login` with:
   - **Email:** `admin@momcare.org`
   - **Password:** `Admin@12345`
3. You are automatically routed to the **Admin Dashboard** (`/dashboard/admin`).
4. The admin panel displays system-wide statistics and a user directory containing all registered users, roles, contact numbers, and registration timestamps.

### 4. Testing Logout & Session Protection
1. Click the **Sign Out** / **Logout** button from any dashboard or top navigation bar.
2. The session cookie is invalidated and you are redirected to `/login`.
3. Try directly accessing any dashboard (e.g. `http://127.0.0.1:5000/dashboard`). You will be blocked and prompted to log in.
