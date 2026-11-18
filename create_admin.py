"""
Secure Development Command to create or reset an Administrator account in MomCare.
Usage:
    python create_admin.py
    python create_admin.py --email admin@momcare.org --password AdminSecurePassword123! --name "MomCare Admin" --phone 9876543210
"""
import sys
import argparse
import sqlite3
import os
from werkzeug.security import generate_password_hash
from database import DATABASE_PATH, init_db

def create_admin(email, password, full_name="MomCare Administrator", phone="9998887770", language="English"):
    init_db() # Ensure tables exist
    
    email = email.lower().strip()
    if not email or "@" not in email:
        print("[ERROR] Please provide a valid email address.")
        sys.exit(1)
        
    if len(password) < 6:
        print("[ERROR] Password must be at least 6 characters.")
        sys.exit(1)

    hashed_pw = generate_password_hash(password)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT id, role FROM users WHERE LOWER(email) = ?', (email,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, full_name = ?, phone = ?, role = 'Admin', language = ?
            WHERE id = ?
        ''', (hashed_pw, full_name, phone, language, existing[0]))
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Updated existing user '{email}' with new Admin credentials.")
    else:
        cursor.execute('''
            INSERT INTO users (full_name, email, phone, password_hash, language, role)
            VALUES (?, ?, ?, ?, ?, 'Admin')
        ''', (full_name, email, phone, hashed_pw, language))
        conn.commit()
        conn.close()
        print(f"[SUCCESS] Created new Administrator account: {email}")

    print("\n--- Admin Login Credentials ---")
    print(f"Email:    {email}")
    print(f"Password: {password}")
    print(f"Role:     Admin")
    print("--------------------------------\n")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Secure command to create MomCare Administrator")
    parser.add_argument('--email', default='admin@momcare.org', help="Admin email address")
    parser.add_argument('--password', default='Admin@12345', help="Admin password (min 6 characters)")
    parser.add_argument('--name', default='System Administrator', help="Admin full name")
    parser.add_argument('--phone', default='9876543210', help="Admin contact phone number")
    parser.add_argument('--language', default='English', help="Admin preferred language")

    args = parser.parse_args()
    create_admin(
        email=args.email,
        password=args.password,
        full_name=args.name,
        phone=args.phone,
        language=args.language
    )

