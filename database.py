import sqlite3
import os
from datetime import datetime, date, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'momcare.db')

def get_db():
    """
    Opens a new database connection if there is none yet for the current application context.
    Falls back gracefully to a direct connection if running outside an app context (e.g. scripts/tests).
    """
    try:
        from flask import has_app_context, g
        if has_app_context():
            if 'db' not in g:
                g.db = sqlite3.connect(DATABASE_PATH)
                g.db.row_factory = sqlite3.Row
            return g.db
    except Exception:
        pass

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(e=None):
    """Closes the database again at the end of the request."""
    try:
        from flask import has_app_context, g
        if has_app_context():
            db = g.pop('db', None)
            if db is not None:
                db.close()
    except Exception:
        pass

def init_db():
    """Initializes the database schema with basic tables for MomCare."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Existing app_info table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            status TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM app_info')
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            'INSERT INTO app_info (app_name, status, version) VALUES (?, ?, ?)',
            ('MomCare - Mother & Child Healthcare', 'Operational', '1.0.0')
        )
        
    # Users table for secure authentication & role-based access
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'English',
            role TEXT NOT NULL CHECK(role IN ('Mother', 'Healthcare Worker', 'Admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Mother Profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mother_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            dob TEXT,
            address TEXT,
            pregnancy_status TEXT NOT NULL DEFAULT 'Pregnant',
            lmp TEXT,
            edd TEXT,
            blood_group TEXT,
            medical_history TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Child Profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS child_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mother_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT NOT NULL,
            birth_weight REAL,
            blood_group TEXT,
            allergies TEXT,
            medical_history TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (mother_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Child Vaccination Records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vaccination_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER NOT NULL,
            vaccine_code TEXT NOT NULL,
            vaccine_name TEXT NOT NULL,
            dose_number TEXT NOT NULL,
            recommended_date TEXT NOT NULL,
            administered_date TEXT,
            status TEXT NOT NULL DEFAULT 'Upcoming',
            administered_by_id INTEGER,
            administered_by_name TEXT,
            notes TEXT,
            batch_number TEXT,
            category TEXT NOT NULL DEFAULT 'Government (NIS)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES child_profiles(id) ON DELETE CASCADE,
            FOREIGN KEY (administered_by_id) REFERENCES users(id) ON DELETE SET NULL,
            UNIQUE(child_id, vaccine_code)
        )
    ''')

    # Vaccination History & Correction Audit Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vaccination_history_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            previous_date TEXT,
            new_date TEXT,
            previous_status TEXT,
            new_status TEXT,
            changed_by_name TEXT NOT NULL,
            change_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES vaccination_records(id) ON DELETE CASCADE
        )
    ''')

    # Phase 4: Child Growth Measurements table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS growth_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER NOT NULL,
            measurement_date TEXT NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            head_circumference REAL,
            bmi REAL,
            observations TEXT,
            recorded_by_id INTEGER,
            recorded_by_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES child_profiles(id) ON DELETE CASCADE,
            FOREIGN KEY (recorded_by_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')

    # Phase 4: Growth Measurement History & Correction Audit Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS growth_history_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            measurement_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            previous_weight REAL,
            new_weight REAL,
            previous_height REAL,
            new_height REAL,
            previous_head_circ REAL,
            new_head_circ REAL,
            changed_by_id INTEGER,
            changed_by_name TEXT NOT NULL,
            change_reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (measurement_id) REFERENCES growth_measurements(id) ON DELETE CASCADE
        )
    ''')


    # Phase 5: Chatbot – chat sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            context TEXT NOT NULL DEFAULT 'General Nutrition',
            language TEXT NOT NULL DEFAULT 'English',
            child_id INTEGER,
            child_name TEXT,
            child_age_months INTEGER,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES child_profiles(id) ON DELETE SET NULL
        )
    ''')

    # Phase 5: Chatbot – individual messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
    ''')

    # Smart Reminders & Notifications – reminder action logs (snooze, complete for dynamic reminders)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminder_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reminder_key TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            snoozed_until TEXT,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, reminder_key),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Smart Reminders & Notifications – custom user-created reminders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER,
            title TEXT NOT NULL,
            description TEXT,
            due_date TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'Personal',
            status TEXT NOT NULL DEFAULT 'Pending',
            snoozed_until TEXT,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES child_profiles(id) ON DELETE SET NULL
        )
    ''')

    # Healthcare Worker Field Home Visits & Maternal Community Care
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS field_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_id INTEGER NOT NULL,
            mother_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,
            purpose TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Completed',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (mother_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# Database helper functions for users
def create_user(full_name, email, phone, password_hash, language, role):
    """Inserts a new user into the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (full_name, email, phone, password_hash, language, role)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (full_name, email.lower().strip(), phone.strip(), password_hash, language, role))
    conn.commit()
    return cursor.lastrowid

def get_user_by_email(email):
    """Finds a user by email (case-insensitive)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE LOWER(email) = LOWER(?)', (email.strip(),))
    return cursor.fetchone()

def get_user_by_id(user_id):
    """Finds a user by their user ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()

def get_all_users():
    """Retrieves all users for the Admin dashboard."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, email, phone, language, role, created_at FROM users ORDER BY created_at DESC')
    return cursor.fetchall()

def get_users_by_role(role):
    """Retrieves all users belonging to a specific role."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, full_name, email, phone, language, role, created_at FROM users WHERE role = ? ORDER BY created_at DESC', (role,))
    return cursor.fetchall()

def get_user_stats():
    """Returns user counts grouped by role for dashboard analytics."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            COUNT(*) as total_users,
            SUM(CASE WHEN role = 'Mother' THEN 1 ELSE 0 END) as total_mothers,
            SUM(CASE WHEN role = 'Healthcare Worker' THEN 1 ELSE 0 END) as total_workers,
            SUM(CASE WHEN role = 'Admin' THEN 1 ELSE 0 END) as total_admins
        FROM users
    ''')
    row = cursor.fetchone()
    return {
        'total_users': row['total_users'] or 0,
        'total_mothers': row['total_mothers'] or 0,
        'total_workers': row['total_workers'] or 0,
        'total_admins': row['total_admins'] or 0
    }

def update_user_basic(user_id, full_name, phone):
    """Updates basic contact details in the users table."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET full_name = ?, phone = ? 
        WHERE id = ?
    ''', (full_name.strip(), phone.strip(), user_id))
    conn.commit()

def update_user_language(user_id, language):
    """Updates the preferred language for a user in the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET language = ? 
        WHERE id = ?
    ''', (language.strip(), user_id))
    conn.commit()

# --- Mother Profile Helpers ---
def get_mother_profile(user_id):
    """Retrieves mother profile row by user_id."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM mother_profiles WHERE user_id = ?', (user_id,))
    return cursor.fetchone()

def save_mother_profile(user_id, dob, address, pregnancy_status, lmp, edd, blood_group, medical_history, emergency_contact_name, emergency_contact_phone):
    """Inserts or updates a mother's detailed healthcare profile."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate EDD automatically if LMP provided and EDD not set
    if lmp and not edd:
        edd = calculate_edd_from_lmp(lmp)
        
    cursor.execute('SELECT id FROM mother_profiles WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute('''
            UPDATE mother_profiles
            SET dob = ?, address = ?, pregnancy_status = ?, lmp = ?, edd = ?,
                blood_group = ?, medical_history = ?, emergency_contact_name = ?,
                emergency_contact_phone = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (
            dob.strip() if dob else None,
            address.strip() if address else None,
            pregnancy_status.strip() if pregnancy_status else 'Pregnant',
            lmp.strip() if lmp else None,
            edd.strip() if edd else None,
            blood_group.strip() if blood_group else None,
            medical_history.strip() if medical_history else None,
            emergency_contact_name.strip() if emergency_contact_name else None,
            emergency_contact_phone.strip() if emergency_contact_phone else None,
            user_id
        ))
    else:
        cursor.execute('''
            INSERT INTO mother_profiles (
                user_id, dob, address, pregnancy_status, lmp, edd, blood_group,
                medical_history, emergency_contact_name, emergency_contact_phone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            dob.strip() if dob else None,
            address.strip() if address else None,
            pregnancy_status.strip() if pregnancy_status else 'Pregnant',
            lmp.strip() if lmp else None,
            edd.strip() if edd else None,
            blood_group.strip() if blood_group else None,
            medical_history.strip() if medical_history else None,
            emergency_contact_name.strip() if emergency_contact_name else None,
            emergency_contact_phone.strip() if emergency_contact_phone else None
        ))
    conn.commit()
    return get_mother_profile(user_id)

def calculate_edd_from_lmp(lmp_str):
    """Calculates Estimated Due Date (EDD) from LMP (+280 days)."""
    if not lmp_str:
        return None
    try:
        lmp_date = datetime.strptime(lmp_str.strip(), '%Y-%m-%d').date()
        edd_date = lmp_date + timedelta(days=280)
        return edd_date.strftime('%Y-%m-%d')
    except Exception:
        return None

def calculate_profile_completion(user, profile):
    """
    Computes profile completion percentage based on filled personal,
    clinical, and emergency contact details.
    """
    if not user:
        return 0
    
    # Track completion items
    total_items = 9
    completed_items = 0
    
    # 1. Full Name (from user)
    if user['full_name'] and len(user['full_name'].strip()) > 0:
        completed_items += 1
    # 2. Phone (from user)
    if user['phone'] and len(user['phone'].strip()) > 0:
        completed_items += 1
    # 3. Email (from user)
    if user['email'] and len(user['email'].strip()) > 0:
        completed_items += 1
        
    if profile:
        # 4. DOB
        if profile['dob']:
            completed_items += 1
        # 5. Address
        if profile['address'] and len(profile['address'].strip()) > 0:
            completed_items += 1
        # 6. Pregnancy Status
        if profile['pregnancy_status']:
            completed_items += 1
        # 7. Blood Group
        if profile['blood_group']:
            completed_items += 1
        # 8. Emergency Contact Name & Phone
        if profile['emergency_contact_name'] and profile['emergency_contact_phone']:
            completed_items += 1
        elif profile['emergency_contact_name'] or profile['emergency_contact_phone']:
            completed_items += 0.5
        # 9. Medical History or LMP/EDD
        if profile['medical_history'] or profile['lmp'] or profile['edd']:
            completed_items += 1
            
    pct = int(round((completed_items / total_items) * 100))
    return min(100, max(0, pct))

# --- Child Profile Helpers ---
def get_children_by_mother(mother_id):
    """Retrieves all registered children for a mother, sorted by DOB descending."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM child_profiles 
        WHERE mother_id = ? 
        ORDER BY dob DESC, id DESC
    ''', (mother_id,))
    rows = cursor.fetchall()
    
    # Format age for each child
    children = []
    for row in rows:
        c_dict = dict(row)
        c_dict['age_display'] = format_child_age(c_dict.get('dob'))
        children.append(c_dict)
    return children

def get_child_by_id(child_id):
    """Finds a child profile by id."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM child_profiles WHERE id = ?', (child_id,))
    row = cursor.fetchone()
    if row:
        c_dict = dict(row)
        c_dict['age_display'] = format_child_age(c_dict.get('dob'))
        return c_dict
    return None

def add_child(mother_id, full_name, dob, gender, birth_weight, blood_group, allergies, medical_history):
    """Inserts a new child profile connected to the mother's user account."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO child_profiles (
            mother_id, full_name, dob, gender, birth_weight, blood_group,
            allergies, medical_history
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        mother_id,
        full_name.strip(),
        dob.strip(),
        gender.strip(),
        float(birth_weight) if birth_weight else None,
        blood_group.strip() if blood_group else None,
        allergies.strip() if allergies else None,
        medical_history.strip() if medical_history else None
    ))
    conn.commit()
    return cursor.lastrowid

def update_child(child_id, mother_id, full_name, dob, gender, birth_weight, blood_group, allergies, medical_history):
    """Updates child details ensuring only the owning mother can modify it."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE child_profiles
        SET full_name = ?, dob = ?, gender = ?, birth_weight = ?,
            blood_group = ?, allergies = ?, medical_history = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND mother_id = ?
    ''', (
        full_name.strip(),
        dob.strip(),
        gender.strip(),
        float(birth_weight) if birth_weight else None,
        blood_group.strip() if blood_group else None,
        allergies.strip() if allergies else None,
        medical_history.strip() if medical_history else None,
        child_id,
        mother_id
    ))
    conn.commit()
    return cursor.rowcount > 0

def delete_child(child_id, mother_id):
    """Safely removes a child profile if belonging to the authenticated mother."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM child_profiles WHERE id = ? AND mother_id = ?', (child_id, mother_id))
    conn.commit()
    return cursor.rowcount > 0

def format_child_age(dob_str):
    """
    Computes and formats a child's age dynamically from their birth date.
    Examples: '15 days old', '6 months old', '2 years, 3 months old'.
    """
    if not dob_str:
        return 'Age unknown'
    try:
        birth_date = datetime.strptime(dob_str.strip(), '%Y-%m-%d').date()
        today = date.today()
        
        if birth_date > today:
            days_until = (birth_date - today).days
            return f"Due in {days_until} days (Future date)"
            
        days = (today - birth_date).days
        
        if days == 0:
            return "Newborn (Born today)"
        elif days < 30:
            return f"{days} day{'s' if days > 1 else ''} old"
        elif days < 365:
            months = max(1, days // 30)
            return f"{months} month{'s' if months > 1 else ''} old"
        else:
            years = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            remaining_months = (today.month - birth_date.month) % 12
            if remaining_months > 0:
                return f"{years} yr{'s' if years > 1 else ''}, {remaining_months} mo{'s' if remaining_months > 1 else ''} old"
            return f"{years} year{'s' if years > 1 else ''} old"
    except Exception:
        return 'Age unavailable'

# ==========================================================================
# Phase 3 - Medically Reviewed National Immunization Schedule (NIS - India)
# ==========================================================================

NIS_VACCINE_SCHEDULE = [
    # At Birth
    {
        'code': 'BCG',
        'name': 'BCG (Bacillus Calmette–Guérin)',
        'dose': 'Dose 1',
        'recommended_age': 'At birth (up to 1 year)',
        'offset_days': 0,
        'category': 'Government (NIS)'
    },
    {
        'code': 'OPV_0',
        'name': 'OPV-0 (Oral Polio Vaccine)',
        'dose': 'Birth Dose',
        'recommended_age': 'At birth (within 15 days)',
        'offset_days': 0,
        'category': 'Government (NIS)'
    },
    {
        'code': 'HEPB_BIRTH',
        'name': 'Hepatitis B (Birth Dose)',
        'dose': 'Birth Dose',
        'recommended_age': 'Within 24 hours of birth',
        'offset_days': 0,
        'category': 'Government (NIS)'
    },
    # 6 Weeks (42 days)
    {
        'code': 'OPV_1',
        'name': 'OPV-1 (Oral Polio Vaccine)',
        'dose': 'Dose 1',
        'recommended_age': '6 weeks',
        'offset_days': 42,
        'category': 'Government (NIS)'
    },
    {
        'code': 'PENTA_1',
        'name': 'Pentavalent-1 (DTP + HepB + Hib)',
        'dose': 'Dose 1',
        'recommended_age': '6 weeks',
        'offset_days': 42,
        'category': 'Government (NIS)'
    },
    {
        'code': 'ROTA_1',
        'name': 'Rotavirus Vaccine (RVV-1)',
        'dose': 'Dose 1',
        'recommended_age': '6 weeks',
        'offset_days': 42,
        'category': 'Government (NIS)'
    },
    {
        'code': 'FIPV_1',
        'name': 'fIPV-1 (Fractional Inactivated Polio)',
        'dose': 'Dose 1',
        'recommended_age': '6 weeks',
        'offset_days': 42,
        'category': 'Government (NIS)'
    },
    {
        'code': 'PCV_1',
        'name': 'PCV-1 (Pneumococcal Conjugate)',
        'dose': 'Dose 1',
        'recommended_age': '6 weeks',
        'offset_days': 42,
        'category': 'Government (NIS)'
    },
    # 10 Weeks (70 days)
    {
        'code': 'OPV_2',
        'name': 'OPV-2 (Oral Polio Vaccine)',
        'dose': 'Dose 2',
        'recommended_age': '10 weeks',
        'offset_days': 70,
        'category': 'Government (NIS)'
    },
    {
        'code': 'PENTA_2',
        'name': 'Pentavalent-2 (DTP + HepB + Hib)',
        'dose': 'Dose 2',
        'recommended_age': '10 weeks',
        'offset_days': 70,
        'category': 'Government (NIS)'
    },
    {
        'code': 'ROTA_2',
        'name': 'Rotavirus Vaccine (RVV-2)',
        'dose': 'Dose 2',
        'recommended_age': '10 weeks',
        'offset_days': 70,
        'category': 'Government (NIS)'
    },
    # 14 Weeks (98 days)
    {
        'code': 'OPV_3',
        'name': 'OPV-3 (Oral Polio Vaccine)',
        'dose': 'Dose 3',
        'recommended_age': '14 weeks',
        'offset_days': 98,
        'category': 'Government (NIS)'
    },
    {
        'code': 'PENTA_3',
        'name': 'Pentavalent-3 (DTP + HepB + Hib)',
        'dose': 'Dose 3',
        'recommended_age': '14 weeks',
        'offset_days': 98,
        'category': 'Government (NIS)'
    },
    {
        'code': 'ROTA_3',
        'name': 'Rotavirus Vaccine (RVV-3)',
        'dose': 'Dose 3',
        'recommended_age': '14 weeks',
        'offset_days': 98,
        'category': 'Government (NIS)'
    },
    {
        'code': 'FIPV_2',
        'name': 'fIPV-2 (Fractional Inactivated Polio)',
        'dose': 'Dose 2',
        'recommended_age': '14 weeks',
        'offset_days': 98,
        'category': 'Government (NIS)'
    },
    {
        'code': 'PCV_2',
        'name': 'PCV-2 (Pneumococcal Conjugate)',
        'dose': 'Dose 2',
        'recommended_age': '14 weeks',
        'offset_days': 98,
        'category': 'Government (NIS)'
    },
    # 9-12 Months (274 days)
    {
        'code': 'MR_1',
        'name': 'MR-1 (Measles & Rubella)',
        'dose': 'Dose 1',
        'recommended_age': '9-12 completed months',
        'offset_days': 274,
        'category': 'Government (NIS)'
    },
    {
        'code': 'PCV_BOOSTER',
        'name': 'PCV Booster',
        'dose': 'Booster',
        'recommended_age': '9 completed months',
        'offset_days': 274,
        'category': 'Government (NIS)'
    },
    {
        'code': 'JE_1',
        'name': 'Japanese Encephalitis (JE-1)',
        'dose': 'Dose 1',
        'recommended_age': '9-12 months',
        'offset_days': 274,
        'category': 'Optional / Regional'
    },
    {
        'code': 'VITA_1',
        'name': 'Vitamin A (Dose 1 - 100,000 IU)',
        'dose': 'Dose 1',
        'recommended_age': '9 months (alongside MR-1)',
        'offset_days': 274,
        'category': 'Government (NIS)'
    },
    # 16-24 Months (486 days)
    {
        'code': 'MR_2',
        'name': 'MR-2 (Measles & Rubella)',
        'dose': 'Dose 2',
        'recommended_age': '16-24 months',
        'offset_days': 486,
        'category': 'Government (NIS)'
    },
    {
        'code': 'DPT_BOOSTER_1',
        'name': 'DPT Booster-1',
        'dose': 'Booster 1',
        'recommended_age': '16-24 months',
        'offset_days': 486,
        'category': 'Government (NIS)'
    },
    {
        'code': 'OPV_BOOSTER',
        'name': 'OPV Booster',
        'dose': 'Booster',
        'recommended_age': '16-24 months',
        'offset_days': 486,
        'category': 'Government (NIS)'
    },
    # 5-6 Years (1825 days)
    {
        'code': 'DPT_BOOSTER_2',
        'name': 'DPT Booster-2',
        'dose': 'Booster 2',
        'recommended_age': '5-6 years',
        'offset_days': 1825,
        'category': 'Government (NIS)'
    },
    # 10 Years (3650 days)
    {
        'code': 'TD_10',
        'name': 'Td (Tetanus & adult Diphtheria)',
        'dose': 'Dose 1',
        'recommended_age': '10 years',
        'offset_days': 3650,
        'category': 'Government (NIS)'
    },
    # 16 Years (5840 days)
    {
        'code': 'TD_16',
        'name': 'Td (Tetanus & adult Diphtheria)',
        'dose': 'Dose 2',
        'recommended_age': '16 years',
        'offset_days': 5840,
        'category': 'Government (NIS)'
    }
]

def generate_child_vaccination_schedule(child_id):
    """
    Synchronizes and returns the complete vaccination schedule for a child.
    Calculates recommended dates dynamically from child's DOB and evaluates
    real-time statuses: Upcoming, Due, Overdue, or Completed.
    """
    child = get_child_by_id(child_id)
    if not child or not child.get('dob'):
        return []

    try:
        birth_date = datetime.strptime(child['dob'].strip(), '%Y-%m-%d').date()
    except Exception:
        return []

    today = date.today()
    conn = get_db()
    cursor = conn.cursor()

    # Load existing recorded vaccinations
    cursor.execute('SELECT * FROM vaccination_records WHERE child_id = ?', (child_id,))
    existing_map = {row['vaccine_code']: dict(row) for row in cursor.fetchall()}

    schedule = []
    for item in NIS_VACCINE_SCHEDULE:
        code = item['code']
        rec_date = birth_date + timedelta(days=item['offset_days'])
        rec_date_str = rec_date.strftime('%Y-%m-%d')
        existing = existing_map.get(code)

        # Determine real-time status
        if existing and (existing.get('administered_date') or existing.get('status') == 'Completed'):
            status = 'Completed'
            admin_date = existing.get('administered_date') or rec_date_str
            admin_by_id = existing.get('administered_by_id')
            admin_by_name = existing.get('administered_by_name')
            notes = existing.get('notes')
            batch_num = existing.get('batch_number')
            record_id = existing['id']
        else:
            admin_date = None
            admin_by_id = None
            admin_by_name = None
            notes = None
            batch_num = None
            record_id = existing['id'] if existing else None

            # Calculate timeliness
            days_diff = (rec_date - today).days
            if days_diff > 7:
                status = 'Upcoming'
            elif -30 <= days_diff <= 7:
                status = 'Due'
            else:
                status = 'Overdue'

        # Ensure record row is persisted/synchronized in database
        if not existing:
            cursor.execute('''
                INSERT INTO vaccination_records (
                    child_id, vaccine_code, vaccine_name, dose_number,
                    recommended_date, status, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                child_id, code, item['name'], item['dose'],
                rec_date_str, status, item['category']
            ))
            record_id = cursor.lastrowid
        elif existing.get('status') != status and not existing.get('administered_date') and existing.get('status') != 'Completed':
            cursor.execute('''
                UPDATE vaccination_records
                SET status = ?, recommended_date = ?
                WHERE id = ?
            ''', (status, rec_date_str, record_id))

        schedule.append({
            'record_id': record_id,
            'child_id': child_id,
            'vaccine_code': code,
            'vaccine_name': item['name'],
            'dose_number': item['dose'],
            'recommended_age': item['recommended_age'],
            'recommended_date': rec_date_str,
            'administered_date': admin_date,
            'status': status,
            'administered_by_id': admin_by_id,
            'administered_by_name': admin_by_name,
            'notes': notes,
            'batch_number': batch_num,
            'category': item['category']
        })

    conn.commit()
    return schedule

def get_child_vaccination_summary(child_id):
    """
    Computes summary metrics for a child's vaccination progress:
    completed, due, overdue, upcoming counts, and the next vaccine info.
    """
    schedule = generate_child_vaccination_schedule(child_id)
    total = len(schedule)
    completed = sum(1 for s in schedule if s['status'] == 'Completed')
    due = sum(1 for s in schedule if s['status'] == 'Due')
    overdue = sum(1 for s in schedule if s['status'] == 'Overdue')
    upcoming = sum(1 for s in schedule if s['status'] == 'Upcoming')

    # Find the next pending vaccine (sorted by recommended_date)
    pending_list = [s for s in schedule if s['status'] in ('Due', 'Overdue', 'Upcoming')]
    pending_list.sort(key=lambda s: s['recommended_date'])
    next_vaccine = pending_list[0] if pending_list else None

    # Calculate percentage
    progress_pct = int(round((completed / total) * 100)) if total > 0 else 0

    return {
        'total': total,
        'completed': completed,
        'due': due,
        'overdue': overdue,
        'upcoming': upcoming,
        'progress_pct': progress_pct,
        'next_vaccine': next_vaccine
    }

def record_vaccination(child_id, vaccine_code, administered_date, administered_by_id, administered_by_name, batch_number=None, notes=None, change_reason=None):
    """
    Allows authorized healthcare workers to record or correct a child's vaccination,
    preserving full audit trail history in vaccination_history_logs.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM vaccination_records WHERE child_id = ? AND vaccine_code = ?', (child_id, vaccine_code))
    existing = cursor.fetchone()

    if existing:
        record_id = existing['id']
        prev_date = existing['administered_date']
        prev_status = existing['status']
        action = 'CORRECTED' if prev_date else 'RECORDED'

        cursor.execute('''
            UPDATE vaccination_records
            SET administered_date = ?, status = 'Completed',
                administered_by_id = ?, administered_by_name = ?,
                batch_number = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            administered_date.strip(),
            administered_by_id,
            administered_by_name.strip(),
            batch_number.strip() if batch_number else None,
            notes.strip() if notes else None,
            record_id
        ))

        # Log to audit history
        cursor.execute('''
            INSERT INTO vaccination_history_logs (
                record_id, child_id, action, previous_date, new_date,
                previous_status, new_status, changed_by_name, change_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_id, child_id, action, prev_date, administered_date.strip(),
            prev_status, 'Completed', administered_by_name.strip(),
            change_reason.strip() if change_reason else 'Clinical dose administration'
        ))

        # Synchronize reminder_actions so no conflicting stale pending or snoozed record lingers
        cursor.execute('''
            DELETE FROM reminder_actions
            WHERE reminder_key LIKE ?
        ''', (f"vax_{child_id}_{vaccine_code}_%",))
    else:
        # Search item in NIS_VACCINE_SCHEDULE
        meta = next((item for item in NIS_VACCINE_SCHEDULE if item['code'] == vaccine_code), None)
        v_name = meta['name'] if meta else vaccine_code
        v_dose = meta['dose'] if meta else 'Dose 1'
        v_cat = meta['category'] if meta else 'Government (NIS)'

        cursor.execute('''
            INSERT INTO vaccination_records (
                child_id, vaccine_code, vaccine_name, dose_number,
                recommended_date, administered_date, status,
                administered_by_id, administered_by_name, batch_number, notes, category
            ) VALUES (?, ?, ?, ?, ?, ?, 'Completed', ?, ?, ?, ?, ?)
        ''', (
            child_id, vaccine_code, v_name, v_dose,
            administered_date.strip(), administered_date.strip(),
            administered_by_id, administered_by_name.strip(),
            batch_number.strip() if batch_number else None,
            notes.strip() if notes else None, v_cat
        ))
        record_id = cursor.lastrowid

        cursor.execute('''
            INSERT INTO vaccination_history_logs (
                record_id, child_id, action, previous_date, new_date,
                previous_status, new_status, changed_by_name, change_reason
            ) VALUES (?, ?, 'RECORDED', NULL, ?, 'Pending', 'Completed', ?, ?)
        ''', (
            record_id, child_id, administered_date.strip(),
            administered_by_name.strip(), change_reason.strip() if change_reason else 'New vaccination record'
        ))

        # Synchronize reminder_actions so no conflicting stale pending or snoozed record lingers
        cursor.execute('''
            DELETE FROM reminder_actions
            WHERE reminder_key LIKE ?
        ''', (f"vax_{child_id}_{vaccine_code}_%",))

    conn.commit()
    return True

def get_vaccination_record_by_id(record_id):
    """Retrieves a single vaccination record with child details."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT vr.*, cp.full_name as child_name, cp.dob as child_dob, cp.mother_id
        FROM vaccination_records vr
        JOIN child_profiles cp ON vr.child_id = cp.id
        WHERE vr.id = ?
    ''', (record_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_all_children_for_workers(search_query=None):
    """
    Retrieves all registered children alongside their mothers' details
    and computed vaccination progress for the Healthcare Worker dashboard.
    """
    conn = get_db()
    cursor = conn.cursor()

    sql = '''
        SELECT 
            cp.*,
            u.full_name as mother_name,
            u.phone as mother_phone,
            u.email as mother_email
        FROM child_profiles cp
        JOIN users u ON cp.mother_id = u.id
    '''
    params = []
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        sql += " WHERE cp.full_name LIKE ? OR u.full_name LIKE ? OR u.phone LIKE ? "
        params = [q, q, q]

    sql += " ORDER BY cp.dob DESC, cp.id DESC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        c_dict = dict(row)
        c_dict['age_display'] = format_child_age(c_dict.get('dob'))
        summary = get_child_vaccination_summary(c_dict['id'])
        c_dict['vax_summary'] = summary
        result.append(c_dict)

    return result

def get_in_app_reminders_for_child(child_id):
    """
    Generates structured in-app reminders for upcoming, due, and overdue vaccinations
    for a specific child based on the National Immunization Schedule.
    """
    child = get_child_by_id(child_id)
    if not child:
        return []

    schedule = generate_child_vaccination_schedule(child_id)
    today = date.today()
    reminders = []

    for item in schedule:
        status = item['status']
        if status in ('Overdue', 'Due', 'Upcoming'):
            rec_date = datetime.strptime(item['recommended_date'], '%Y-%m-%d').date()
            diff_days = (rec_date - today).days

            if status == 'Overdue':
                severity = 'danger'
                badge_text = 'Overdue'
                message = f"Immediate action recommended: {item['vaccine_name']} ({item['dose_number']}) was recommended on {item['recommended_date']}. Please visit your nearest primary health center to catch up."
            elif status == 'Due':
                severity = 'warning'
                badge_text = 'Due Now'
                message = f"Vaccination window active: {item['vaccine_name']} ({item['dose_number']}) is due on {item['recommended_date']}. Community immunization visits available this week."
            elif status == 'Upcoming' and diff_days <= 14:
                severity = 'info'
                badge_text = 'Upcoming'
                message = f"Upcoming immunization: {item['vaccine_name']} ({item['dose_number']}) scheduled for {item['recommended_date']} (in {diff_days} days)."
            else:
                continue

            reminders.append({
                'child_id': child_id,
                'child_name': child['full_name'],
                'vaccine_code': item['vaccine_code'],
                'vaccine_name': item['vaccine_name'],
                'dose_number': item['dose_number'],
                'recommended_date': item['recommended_date'],
                'status': status,
                'severity': severity,
                'badge_text': badge_text,
                'message': message
            })

    reminders.sort(key=lambda r: (0 if r['status'] == 'Overdue' else (1 if r['status'] == 'Due' else 2), r['recommended_date']))
    return reminders

def get_in_app_reminders_for_mother(mother_id):
    """Aggregates all in-app vaccination reminders across all children of a mother."""
    children = get_children_by_mother(mother_id)
    all_reminders = []
    for c in children:
        child_reminders = get_in_app_reminders_for_child(c['id'])
        all_reminders.extend(child_reminders)

    all_reminders.sort(key=lambda r: (0 if r['status'] == 'Overdue' else (1 if r['status'] == 'Due' else 2), r['recommended_date']))
    return all_reminders

def get_community_vaccination_stats():
    """Aggregates community vaccination statistics for the Healthcare Worker overview."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM child_profiles')
    total_children = cursor.fetchone()['total'] or 0

    cursor.execute('''
        SELECT 
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as total_completed,
            SUM(CASE WHEN status = 'Due' THEN 1 ELSE 0 END) as total_due,
            SUM(CASE WHEN status = 'Overdue' THEN 1 ELSE 0 END) as total_overdue,
            SUM(CASE WHEN status = 'Upcoming' THEN 1 ELSE 0 END) as total_upcoming
        FROM vaccination_records
    ''')
    row = cursor.fetchone()

    return {
        'total_children': total_children,
        'total_completed': row['total_completed'] or 0,
        'total_due': row['total_due'] or 0,
        'total_overdue': row['total_overdue'] or 0,
        'total_upcoming': row['total_upcoming'] or 0
    }

# ==========================================
# PHASE 4: CHILD GROWTH MONITORING HELPERS
# ==========================================

# WHO Child Growth Standards (0 to 60 months) from WHO Multicentre Growth Reference Study
# Weight: (w_min = -2SD, w_med = Median, w_max = +2SD) in kg
# Height: (h_med = Median) in cm
# Head Circumference: (hc_med = Median) in cm
WHO_GROWTH_STANDARDS = {
    'Male': {
        0: {'w_min': 2.5, 'w_med': 3.3, 'w_max': 4.4, 'h_med': 49.9, 'hc_med': 34.5},
        3: {'w_min': 5.0, 'w_med': 6.4, 'w_max': 8.0, 'h_med': 61.4, 'hc_med': 40.5},
        6: {'w_min': 6.4, 'w_med': 7.9, 'w_max': 9.8, 'h_med': 67.6, 'hc_med': 43.3},
        9: {'w_min': 7.1, 'w_med': 8.9, 'w_max': 11.0, 'h_med': 72.0, 'hc_med': 45.0},
        12: {'w_min': 7.7, 'w_med': 9.6, 'w_max': 12.0, 'h_med': 75.7, 'hc_med': 46.1},
        18: {'w_min': 8.8, 'w_med': 10.9, 'w_max': 13.7, 'h_med': 82.3, 'hc_med': 47.4},
        24: {'w_min': 9.7, 'w_med': 12.2, 'w_max': 15.3, 'h_med': 87.8, 'hc_med': 48.3},
        36: {'w_min': 11.3, 'w_med': 14.3, 'w_max': 18.3, 'h_med': 96.1, 'hc_med': 49.5},
        48: {'w_min': 12.7, 'w_med': 16.3, 'w_max': 21.2, 'h_med': 103.3, 'hc_med': 50.2},
        60: {'w_min': 14.1, 'w_med': 18.3, 'w_max': 24.2, 'h_med': 110.0, 'hc_med': 50.7}
    },
    'Female': {
        0: {'w_min': 2.4, 'w_med': 3.2, 'w_max': 4.2, 'h_med': 49.1, 'hc_med': 33.9},
        3: {'w_min': 4.5, 'w_med': 5.8, 'w_max': 7.5, 'h_med': 59.8, 'hc_med': 39.5},
        6: {'w_min': 5.7, 'w_med': 7.3, 'w_max': 9.3, 'h_med': 65.7, 'hc_med': 42.2},
        9: {'w_min': 6.5, 'w_med': 8.2, 'w_max': 10.5, 'h_med': 70.1, 'hc_med': 44.0},
        12: {'w_min': 7.0, 'w_med': 8.9, 'w_max': 11.5, 'h_med': 74.0, 'hc_med': 44.9},
        18: {'w_min': 8.1, 'w_med': 10.2, 'w_max': 13.2, 'h_med': 80.7, 'hc_med': 46.2},
        24: {'w_min': 9.0, 'w_med': 11.5, 'w_max': 14.8, 'h_med': 86.4, 'hc_med': 47.2},
        36: {'w_min': 10.8, 'w_med': 13.9, 'w_max': 18.1, 'h_med': 95.1, 'hc_med': 48.5},
        48: {'w_min': 12.3, 'w_med': 16.1, 'w_max': 21.5, 'h_med': 102.7, 'hc_med': 49.3},
        60: {'w_min': 13.7, 'w_med': 18.2, 'w_max': 24.9, 'h_med': 109.4, 'hc_med': 49.9}
    }
}

def calculate_bmi(weight_kg, height_cm):
    """
    Calculates Body Mass Index (BMI = weight_kg / (height_m ^ 2))
    rounded to 1 decimal place. Returns None if invalid.
    """
    try:
        w = float(weight_kg)
        h_cm = float(height_cm)
        if w > 0 and h_cm > 0:
            h_m = h_cm / 100.0
            return round(w / (h_m * h_m), 1)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return None

def get_child_age_in_months(dob_str, target_date_str=None):
    """Calculates age in completed months between DOB and a target measurement date."""
    try:
        dob = datetime.strptime(dob_str.strip(), '%Y-%m-%d').date()
        target = datetime.strptime(target_date_str.strip(), '%Y-%m-%d').date() if target_date_str else date.today()
        months = (target.year - dob.year) * 12 + (target.month - dob.month)
        if target.day < dob.day:
            months -= 1
        return max(0, months)
    except Exception:
        return 0

def get_who_growth_benchmark(age_months, gender):
    """
    Retrieves interpolated WHO Child Growth reference values for a given age in months and sex.
    Returns None if child is > 60 months (5 years) to prevent non-standard classification.
    """
    if age_months is None or age_months > 60:
        return None

    norm_gender = 'Female' if str(gender).strip().lower() in ('female', 'girl', 'f') else 'Male'
    standards = WHO_GROWTH_STANDARDS.get(norm_gender, WHO_GROWTH_STANDARDS['Male'])
    
    milestones = sorted(standards.keys())
    if age_months in standards:
        ref = standards[age_months].copy()
        ref['milestone_month'] = age_months
        ref['gender'] = norm_gender
        return ref

    # Find bounding milestones for interpolation
    lower_m = milestones[0]
    upper_m = milestones[-1]
    for m in milestones:
        if m <= age_months:
            lower_m = m
        if m >= age_months and upper_m == milestones[-1]:
            upper_m = m
            break

    if lower_m == upper_m:
        ref = standards[lower_m].copy()
    else:
        fraction = (age_months - lower_m) / (upper_m - lower_m)
        low = standards[lower_m]
        up = standards[upper_m]
        ref = {
            'w_min': round(low['w_min'] + fraction * (up['w_min'] - low['w_min']), 2),
            'w_med': round(low['w_med'] + fraction * (up['w_med'] - low['w_med']), 2),
            'w_max': round(low['w_max'] + fraction * (up['w_max'] - low['w_max']), 2),
            'h_med': round(low['h_med'] + fraction * (up['h_med'] - low['h_med']), 1),
            'hc_med': round(low['hc_med'] + fraction * (up['hc_med'] - low['hc_med']), 1)
        }

    ref['milestone_month'] = age_months
    ref['gender'] = norm_gender
    return ref

def record_growth_measurement(child_id, measurement_date, weight, height, head_circumference, observations, recorded_by_id, recorded_by_name, change_reason=None):
    """
    Allows authorized healthcare workers to log a child's clinical growth measurement.
    Calculates BMI automatically and logs an audit trail entry.
    """
    conn = get_db()
    cursor = conn.cursor()

    w = round(float(weight), 2)
    h = round(float(height), 1)
    hc = round(float(head_circumference), 1) if head_circumference and str(head_circumference).strip() else None
    bmi_val = calculate_bmi(w, h)
    obs = observations.strip() if observations else None
    m_date = measurement_date.strip()

    cursor.execute('''
        INSERT INTO growth_measurements (
            child_id, measurement_date, weight, height, head_circumference,
            bmi, observations, recorded_by_id, recorded_by_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (child_id, m_date, w, h, hc, bmi_val, obs, recorded_by_id, recorded_by_name.strip()))
    
    measurement_id = cursor.lastrowid

    # Log to audit history
    cursor.execute('''
        INSERT INTO growth_history_logs (
            measurement_id, child_id, action,
            previous_weight, new_weight,
            previous_height, new_height,
            previous_head_circ, new_head_circ,
            changed_by_id, changed_by_name, change_reason
        ) VALUES (?, ?, 'RECORDED', NULL, ?, NULL, ?, NULL, ?, ?, ?, ?)
    ''', (
        measurement_id, child_id, w, h, hc,
        recorded_by_id, recorded_by_name.strip(),
        change_reason.strip() if change_reason else 'Initial clinical growth measurement'
    ))

    conn.commit()
    return measurement_id

def update_growth_measurement(measurement_id, measurement_date, weight, height, head_circumference, observations, changed_by_id, changed_by_name, change_reason):
    """
    Allows authorized healthcare workers to correct an existing growth measurement
    while preserving complete clinical audit trail history in growth_history_logs.
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM growth_measurements WHERE id = ?', (measurement_id,))
    prev = cursor.fetchone()
    if not prev:
        return False

    w = round(float(weight), 2)
    h = round(float(height), 1)
    hc = round(float(head_circumference), 1) if head_circumference and str(head_circumference).strip() else None
    bmi_val = calculate_bmi(w, h)
    obs = observations.strip() if observations else None
    m_date = measurement_date.strip()

    cursor.execute('''
        UPDATE growth_measurements
        SET measurement_date = ?, weight = ?, height = ?, head_circumference = ?,
            bmi = ?, observations = ?, recorded_by_id = ?, recorded_by_name = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (m_date, w, h, hc, bmi_val, obs, changed_by_id, changed_by_name.strip(), measurement_id))

    # Audit log entry
    cursor.execute('''
        INSERT INTO growth_history_logs (
            measurement_id, child_id, action,
            previous_weight, new_weight,
            previous_height, new_height,
            previous_head_circ, new_head_circ,
            changed_by_id, changed_by_name, change_reason
        ) VALUES (?, ?, 'CORRECTED', ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        measurement_id, prev['child_id'],
        prev['weight'], w,
        prev['height'], h,
        prev['head_circumference'], hc,
        changed_by_id, changed_by_name.strip(),
        change_reason.strip() if change_reason else 'Clinical dose measurement correction'
    ))

    conn.commit()
    return True

def get_growth_measurement_by_id(measurement_id):
    """Retrieves a single growth measurement record with associated child info."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT gm.*, cp.full_name as child_name, cp.dob as child_dob, cp.gender as child_gender, cp.mother_id
        FROM growth_measurements gm
        JOIN child_profiles cp ON gm.child_id = cp.id
        WHERE gm.id = ?
    ''', (measurement_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def get_child_growth_history(child_id):
    """
    Returns the complete chronological growth measurement history for a child,
    calculating measurement age, deltas since previous checkup, growth velocity,
    and WHO Child Growth Standards evaluation.
    """
    child = get_child_by_id(child_id)
    if not child:
        return []

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM growth_measurements
        WHERE child_id = ?
        ORDER BY measurement_date ASC, id ASC
    ''', (child_id,))
    rows = cursor.fetchall()

    history = []
    prev_item = None

    for row in rows:
        item = dict(row)
        m_date_str = item['measurement_date']
        age_mos = get_child_age_in_months(child['dob'], m_date_str)
        item['age_months'] = age_mos

        # Exact age text at checkup
        try:
            c_dob = datetime.strptime(child['dob'].strip(), '%Y-%m-%d').date()
            m_dt = datetime.strptime(m_date_str.strip(), '%Y-%m-%d').date()
            diff_days = (m_dt - c_dob).days
            if diff_days < 30:
                item['age_display'] = f"{diff_days} days old"
            elif diff_days < 365:
                item['age_display'] = f"{age_mos} mos old"
            else:
                yrs = age_mos // 12
                rem_m = age_mos % 12
                item['age_display'] = f"{yrs} yr{'s' if yrs != 1 else ''}, {rem_m} mo{'s' if rem_m != 1 else ''}"
        except Exception:
            item['age_display'] = f"{age_mos} mos"

        # Difference / Delta compared to immediately preceding measurement
        if prev_item:
            w_diff = round(item['weight'] - prev_item['weight'], 2)
            h_diff = round(item['height'] - prev_item['height'], 1)
            item['weight_delta'] = w_diff
            item['height_delta'] = h_diff
            item['weight_delta_str'] = f"{'+' if w_diff > 0 else ''}{w_diff} kg"
            item['height_delta_str'] = f"{'+' if h_diff > 0 else ''}{h_diff} cm"
            
            if item.get('head_circumference') and prev_item.get('head_circumference'):
                hc_diff = round(item['head_circumference'] - prev_item['head_circumference'], 1)
                item['head_circ_delta'] = hc_diff
                item['head_circ_delta_str'] = f"{'+' if hc_diff > 0 else ''}{hc_diff} cm"
            else:
                item['head_circ_delta'] = None
                item['head_circ_delta_str'] = "—"

            # Days elapsed
            try:
                prev_d = datetime.strptime(prev_item['measurement_date'], '%Y-%m-%d').date()
                curr_d = datetime.strptime(m_date_str, '%Y-%m-%d').date()
                item['days_since_prev'] = (curr_d - prev_d).days
            except Exception:
                item['days_since_prev'] = 0
        else:
            item['weight_delta'] = None
            item['weight_delta_str'] = "Baseline"
            item['height_delta'] = None
            item['height_delta_str'] = "Baseline"
            item['head_circ_delta'] = None
            item['head_circ_delta_str'] = "Baseline"
            item['days_since_prev'] = 0

        # WHO Growth Benchmark evaluation (for children 0-5 years / 60 months)
        who_ref = get_who_growth_benchmark(age_mos, child.get('gender'))
        item['who_ref'] = who_ref

        if who_ref:
            w_val = item['weight']
            if w_val < who_ref['w_min']:
                item['who_status'] = 'Underweight (< -2SD)'
                item['who_badge_class'] = 'vax-cat-opt'
                item['needs_followup'] = True
                item['status_summary'] = 'Weight below WHO -2SD reference. Follow-up recommended.'
            elif w_val > who_ref['w_max']:
                item['who_status'] = 'Above +2SD'
                item['who_badge_class'] = 'status-pill-due'
                item['needs_followup'] = False
                item['status_summary'] = 'Weight above WHO +2SD reference.'
            else:
                item['who_status'] = 'Normal Growth (WHO)'
                item['who_badge_class'] = 'vax-cat-nis'
                item['needs_followup'] = False
                item['status_summary'] = 'Weight tracking within healthy WHO reference range.'

            # Check velocity flag: weight loss or flat growth over >= 30 days
            if item.get('weight_delta') is not None and item['weight_delta'] < 0:
                item['who_status'] = 'Weight Loss'
                item['needs_followup'] = True
                item['status_summary'] = f"Weight dropped by {abs(item['weight_delta'])} kg. Close monitoring advised."
            elif item.get('weight_delta') == 0 and item.get('days_since_prev', 0) >= 30:
                item['who_status'] = 'Static Weight'
                item['needs_followup'] = True
                item['status_summary'] = 'Zero weight gain over 30+ days. Follow-up recommended.'
        else:
            # Over 5 years (no speculative classification)
            item['who_status'] = 'Standard Pediatric Measurement'
            item['who_badge_class'] = 'vax-cat-nis'
            item['needs_followup'] = False
            item['status_summary'] = 'Measured per standard pediatric guidelines.'

        history.append(item)
        prev_item = item

    return history

def get_latest_growth_measurement(child_id):
    """Retrieves the latest growth measurement for a child, or None if unmeasured."""
    history = get_child_growth_history(child_id)
    return history[-1] if history else None

def get_community_growth_stats():
    """Aggregates growth monitoring statistics for Healthcare Worker and Admin overviews."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM child_profiles')
    total_children = cursor.fetchone()['total'] or 0

    cursor.execute('SELECT COUNT(DISTINCT child_id) as measured_count, COUNT(*) as total_records FROM growth_measurements')
    row = cursor.fetchone()
    children_measured = row['measured_count'] or 0
    total_records = row['total_records'] or 0

    # Children needing growth follow-up
    cursor.execute('SELECT id FROM child_profiles')
    child_ids = [r['id'] for r in cursor.fetchall()]
    followup_count = 0
    for c_id in child_ids:
        latest = get_latest_growth_measurement(c_id)
        if latest and latest.get('needs_followup'):
            followup_count += 1

    return {
        'total_children': total_children,
        'children_measured': children_measured,
        'total_records': total_records,
        'needing_followup': followup_count
    }

def get_all_children_growth_for_workers(search_query=None):
    """
    Retrieves all registered children with their latest growth metrics,
    mother's contact details, and follow-up indicators for the worker portal.
    """
    conn = get_db()
    cursor = conn.cursor()

    sql = '''
        SELECT 
            cp.*,
            u.full_name as mother_name,
            u.phone as mother_phone,
            u.email as mother_email
        FROM child_profiles cp
        JOIN users u ON cp.mother_id = u.id
    '''
    params = []
    if search_query and search_query.strip():
        q = f"%{search_query.strip()}%"
        sql += " WHERE cp.full_name LIKE ? OR u.full_name LIKE ? OR u.phone LIKE ? "
        params = [q, q, q]

    sql += " ORDER BY cp.dob DESC, cp.id DESC"
    cursor.execute(sql, params)
    rows = cursor.fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item['age_display'] = format_child_age(item.get('dob'))
        history = get_child_growth_history(item['id'])
        item['measurement_count'] = len(history)
        item['latest_growth'] = history[-1] if history else None
        item['needs_followup'] = item['latest_growth'].get('needs_followup', False) if item['latest_growth'] else False
        result.append(item)

    return result

# ==========================================
# ADMIN DATABASE VIEWER HELPERS
# ==========================================

def get_database_viewer_counts():
    """Returns live record counts for all database tables and views."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as c FROM users')
    c_users = cursor.fetchone()['c'] or 0

    cursor.execute('SELECT COUNT(*) as c FROM mother_profiles')
    c_mothers = cursor.fetchone()['c'] or 0

    cursor.execute("SELECT COUNT(*) as c FROM mother_profiles WHERE pregnancy_status = 'Pregnant'")
    c_pregnant = cursor.fetchone()['c'] or 0

    cursor.execute('SELECT COUNT(*) as c FROM child_profiles')
    c_children = cursor.fetchone()['c'] or 0

    cursor.execute('SELECT COUNT(*) as c FROM vaccination_records')
    c_vax = cursor.fetchone()['c'] or 0

    cursor.execute('SELECT COUNT(*) as c FROM growth_measurements')
    c_growth = cursor.fetchone()['c'] or 0

    cursor.execute('SELECT (SELECT COUNT(*) FROM vaccination_history_logs) + (SELECT COUNT(*) FROM growth_history_logs) as c')
    c_audit = cursor.fetchone()['c'] or 0

    return {
        'users': c_users,
        'mothers': c_mothers,
        'pregnant': c_pregnant,
        'children': c_children,
        'vaccinations': c_vax,
        'growth': c_growth,
        'audit': c_audit
    }

def get_database_viewer_table(table_key='users', search_query=None, page=1, per_page=15):
    """
    Retrieves human-readable database records formatted like an Excel spreadsheet.
    Supports search, pagination, table joins for human-friendly names, and sanitizes credentials.
    """
    conn = get_db()
    cursor = conn.cursor()
    all_counts = get_database_viewer_counts()

    valid_keys = ('users', 'mothers', 'pregnant', 'children', 'vaccinations', 'growth', 'audit')
    if table_key not in valid_keys:
        table_key = 'users'

    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = max(5, min(100, int(per_page)))
    except (ValueError, TypeError):
        per_page = 15

    q_filter = search_query.strip() if search_query else ''
    q_param = f"%{q_filter}%" if q_filter else None

    columns = []
    table_title = ""
    table_desc = ""

    if table_key == 'users':
        table_title = "Registered Users"
        table_desc = "Master authentication and role-based account directory. Cryptographic password hashes are kept strictly confidential."
        columns = [
            {'key': 'id', 'label': '#ID'},
            {'key': 'full_name', 'label': 'Full Name'},
            {'key': 'email', 'label': 'Email Address'},
            {'key': 'phone', 'label': 'Phone Number'},
            {'key': 'role', 'label': 'Role'},
            {'key': 'language', 'label': 'Language'},
            {'key': 'password_status', 'label': 'Password Security'},
            {'key': 'created_at', 'label': 'Registered Date'}
        ]

        count_sql = "SELECT COUNT(*) as total FROM users"
        data_sql = """
            SELECT id, full_name, email, phone, role, language, created_at,
                   '•••••••• (scrypt secured)' as password_status
            FROM users
        """
        params = []
        if q_param:
            count_sql += " WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR role LIKE ?"
            data_sql += " WHERE full_name LIKE ? OR email LIKE ? OR phone LIKE ? OR role LIKE ?"
            params = [q_param, q_param, q_param, q_param]

        data_sql += " ORDER BY id ASC LIMIT ? OFFSET ?"

    elif table_key == 'mothers':
        table_title = "Mother Profiles"
        table_desc = "Comprehensive maternal healthcare profiles linked with authenticated user accounts."
        columns = [
            {'key': 'id', 'label': '#Profile ID'},
            {'key': 'mother_name', 'label': 'Mother Name'},
            {'key': 'phone', 'label': 'Phone Number'},
            {'key': 'email', 'label': 'Email Address'},
            {'key': 'pregnancy_status', 'label': 'Pregnancy Status'},
            {'key': 'dob', 'label': 'Date of Birth'},
            {'key': 'blood_group', 'label': 'Blood Group'},
            {'key': 'address', 'label': 'Residential Address'},
            {'key': 'emergency_contact_name', 'label': 'Emergency Contact'},
            {'key': 'emergency_contact_phone', 'label': 'Emergency Phone'}
        ]

        count_sql = """
            SELECT COUNT(*) as total 
            FROM mother_profiles mp 
            JOIN users u ON mp.user_id = u.id
        """
        data_sql = """
            SELECT mp.id, u.full_name as mother_name, u.phone, u.email,
                   mp.pregnancy_status, COALESCE(mp.dob, '—') as dob,
                   COALESCE(mp.blood_group, '—') as blood_group,
                   COALESCE(mp.address, '—') as address,
                   COALESCE(mp.emergency_contact_name, '—') as emergency_contact_name,
                   COALESCE(mp.emergency_contact_phone, '—') as emergency_contact_phone
            FROM mother_profiles mp
            JOIN users u ON mp.user_id = u.id
        """
        params = []
        if q_param:
            count_sql += " WHERE u.full_name LIKE ? OR u.phone LIKE ? OR u.email LIKE ? OR mp.pregnancy_status LIKE ?"
            data_sql += " WHERE u.full_name LIKE ? OR u.phone LIKE ? OR u.email LIKE ? OR mp.pregnancy_status LIKE ?"
            params = [q_param, q_param, q_param, q_param]

        data_sql += " ORDER BY mp.id ASC LIMIT ? OFFSET ?"

    elif table_key == 'pregnant':
        table_title = "Pregnant Women Information"
        table_desc = "Active prenatal beneficiaries tracking Last Menstrual Period (LMP) and Estimated Due Date (EDD)."
        columns = [
            {'key': 'id', 'label': '#Profile ID'},
            {'key': 'mother_name', 'label': 'Mother Name'},
            {'key': 'phone', 'label': 'Phone Number'},
            {'key': 'lmp', 'label': 'Last Menstrual Period (LMP)'},
            {'key': 'edd', 'label': 'Estimated Due Date (EDD)'},
            {'key': 'blood_group', 'label': 'Blood Group'},
            {'key': 'emergency_contact_name', 'label': 'Emergency Contact'},
            {'key': 'emergency_contact_phone', 'label': 'Emergency Phone'}
        ]

        count_sql = """
            SELECT COUNT(*) as total 
            FROM mother_profiles mp 
            JOIN users u ON mp.user_id = u.id
            WHERE mp.pregnancy_status = 'Pregnant'
        """
        data_sql = """
            SELECT mp.id, u.full_name as mother_name, u.phone,
                   COALESCE(mp.lmp, 'Not recorded') as lmp,
                   COALESCE(mp.edd, 'Not calculated') as edd,
                   COALESCE(mp.blood_group, '—') as blood_group,
                   COALESCE(mp.emergency_contact_name, '—') as emergency_contact_name,
                   COALESCE(mp.emergency_contact_phone, '—') as emergency_contact_phone
            FROM mother_profiles mp
            JOIN users u ON mp.user_id = u.id
            WHERE mp.pregnancy_status = 'Pregnant'
        """
        params = []
        if q_param:
            count_sql += " AND (u.full_name LIKE ? OR u.phone LIKE ? OR mp.blood_group LIKE ?)"
            data_sql += " AND (u.full_name LIKE ? OR u.phone LIKE ? OR mp.blood_group LIKE ?)"
            params = [q_param, q_param, q_param]

        data_sql += " ORDER BY mp.id ASC LIMIT ? OFFSET ?"

    elif table_key == 'children':
        table_title = "Child Profiles"
        table_desc = "Registered pediatric beneficiaries connected directly to their mother's account."
        columns = [
            {'key': 'id', 'label': '#Child ID'},
            {'key': 'child_name', 'label': 'Child Name'},
            {'key': 'dob', 'label': 'Date of Birth'},
            {'key': 'age_display', 'label': 'Current Age'},
            {'key': 'gender', 'label': 'Gender'},
            {'key': 'birth_weight', 'label': 'Birth Weight (kg)'},
            {'key': 'blood_group', 'label': 'Blood Group'},
            {'key': 'mother_name', 'label': 'Mother Name'},
            {'key': 'mother_phone', 'label': 'Mother Phone'},
            {'key': 'allergies', 'label': 'Allergies / Notes'}
        ]

        count_sql = """
            SELECT COUNT(*) as total 
            FROM child_profiles cp 
            JOIN users u ON cp.mother_id = u.id
        """
        data_sql = """
            SELECT cp.id, cp.full_name as child_name, cp.dob, cp.gender,
                   COALESCE(cp.birth_weight || ' kg', '—') as birth_weight,
                   COALESCE(cp.blood_group, '—') as blood_group,
                   u.full_name as mother_name, u.phone as mother_phone,
                   COALESCE(cp.allergies, 'None reported') as allergies
            FROM child_profiles cp
            JOIN users u ON cp.mother_id = u.id
        """
        params = []
        if q_param:
            count_sql += " WHERE cp.full_name LIKE ? OR u.full_name LIKE ? OR u.phone LIKE ? OR cp.blood_group LIKE ?"
            data_sql += " WHERE cp.full_name LIKE ? OR u.full_name LIKE ? OR u.phone LIKE ? OR cp.blood_group LIKE ?"
            params = [q_param, q_param, q_param, q_param]

        data_sql += " ORDER BY cp.id ASC LIMIT ? OFFSET ?"

    elif table_key == 'vaccinations':
        table_title = "Vaccination Records"
        table_desc = "Clinical immunization history adhering to India's National Immunization Schedule (NIS)."
        columns = [
            {'key': 'id', 'label': '#Record ID'},
            {'key': 'child_name', 'label': 'Child Name'},
            {'key': 'vaccine_name', 'label': 'Vaccine Name'},
            {'key': 'dose_number', 'label': 'Dose'},
            {'key': 'recommended_date', 'label': 'Recommended Date'},
            {'key': 'administered_date', 'label': 'Date Administered'},
            {'key': 'status', 'label': 'Immunization Status'},
            {'key': 'administered_by_name', 'label': 'Healthcare Staff'},
            {'key': 'batch_number', 'label': 'Batch Number'},
            {'key': 'category', 'label': 'Schedule Category'}
        ]

        count_sql = """
            SELECT COUNT(*) as total 
            FROM vaccination_records vr 
            JOIN child_profiles cp ON vr.child_id = cp.id
        """
        data_sql = """
            SELECT vr.id, cp.full_name as child_name, vr.vaccine_name, vr.dose_number,
                   vr.recommended_date, COALESCE(vr.administered_date, 'Pending') as administered_date,
                   vr.status, COALESCE(vr.administered_by_name, '—') as administered_by_name,
                   COALESCE(vr.batch_number, '—') as batch_number, vr.category
            FROM vaccination_records vr
            JOIN child_profiles cp ON vr.child_id = cp.id
        """
        params = []
        if q_param:
            count_sql += " WHERE cp.full_name LIKE ? OR vr.vaccine_name LIKE ? OR vr.status LIKE ? OR vr.dose_number LIKE ?"
            data_sql += " WHERE cp.full_name LIKE ? OR vr.vaccine_name LIKE ? OR vr.status LIKE ? OR vr.dose_number LIKE ?"
            params = [q_param, q_param, q_param, q_param]

        data_sql += " ORDER BY vr.id ASC LIMIT ? OFFSET ?"

    elif table_key == 'growth':
        table_title = "Child Growth Records"
        table_desc = "Physical developmental measurements with calculated BMI and WHO Child Growth Standard evaluations."
        columns = [
            {'key': 'id', 'label': '#Record ID'},
            {'key': 'child_name', 'label': 'Child Name'},
            {'key': 'measurement_date', 'label': 'Visit Date'},
            {'key': 'weight', 'label': 'Weight (kg)'},
            {'key': 'height', 'label': 'Height (cm)'},
            {'key': 'head_circumference', 'label': 'Head Circ (cm)'},
            {'key': 'bmi', 'label': 'Pediatric BMI'},
            {'key': 'recorded_by_name', 'label': 'Clinician'},
            {'key': 'observations', 'label': 'Clinical Observations'}
        ]

        count_sql = """
            SELECT COUNT(*) as total 
            FROM growth_measurements gm 
            JOIN child_profiles cp ON gm.child_id = cp.id
        """
        data_sql = """
            SELECT gm.id, cp.full_name as child_name, gm.measurement_date,
                   gm.weight || ' kg' as weight,
                   gm.height || ' cm' as height,
                   COALESCE(gm.head_circumference || ' cm', '—') as head_circumference,
                   COALESCE(gm.bmi || ' kg/m²', '—') as bmi,
                   gm.recorded_by_name,
                   COALESCE(gm.observations, '—') as observations
            FROM growth_measurements gm
            JOIN child_profiles cp ON gm.child_id = cp.id
        """
        params = []
        if q_param:
            count_sql += " WHERE cp.full_name LIKE ? OR gm.recorded_by_name LIKE ? OR gm.observations LIKE ?"
            data_sql += " WHERE cp.full_name LIKE ? OR gm.recorded_by_name LIKE ? OR gm.observations LIKE ?"
            params = [q_param, q_param, q_param]

        data_sql += " ORDER BY gm.id DESC LIMIT ? OFFSET ?"

    elif table_key == 'audit':
        table_title = "Clinical Audit Logs"
        table_desc = "Permanent change history and audit trail tracking dose administrations and measurement corrections."
        columns = [
            {'key': 'id', 'label': '#Log ID'},
            {'key': 'category', 'label': 'Category'},
            {'key': 'child_name', 'label': 'Child Name'},
            {'key': 'action', 'label': 'Action'},
            {'key': 'change_summary', 'label': 'Previous &rarr; New Value'},
            {'key': 'changed_by_name', 'label': 'Changed By'},
            {'key': 'change_reason', 'label': 'Clinical Reason'},
            {'key': 'created_at', 'label': 'Timestamp'}
        ]

        count_sql = """
            SELECT (
                (SELECT COUNT(*) FROM vaccination_history_logs) + 
                (SELECT COUNT(*) FROM growth_history_logs)
            ) as total
        """
        data_sql = """
            SELECT * FROM (
                SELECT 
                    vl.id, 'Vaccination' as category, cp.full_name as child_name,
                    vl.action,
                    COALESCE(vl.previous_date || ' (' || vl.previous_status || ')', 'None') || ' → ' || vl.new_date || ' (' || vl.new_status || ')' as change_summary,
                    vl.changed_by_name, vl.change_reason, vl.created_at
                FROM vaccination_history_logs vl
                JOIN child_profiles cp ON vl.child_id = cp.id
                UNION ALL
                SELECT 
                    gl.id, 'Growth' as category, cp.full_name as child_name,
                    gl.action,
                    COALESCE(gl.previous_weight || 'kg', 'None') || ' → ' || gl.new_weight || 'kg (' || gl.new_height || 'cm)' as change_summary,
                    gl.changed_by_name, gl.change_reason, gl.created_at
                FROM growth_history_logs gl
                JOIN child_profiles cp ON gl.child_id = cp.id
            ) AS combined_logs
        """
        params = []
        if q_param:
            data_sql += " WHERE child_name LIKE ? OR changed_by_name LIKE ? OR change_reason LIKE ? OR action LIKE ?"
            params = [q_param, q_param, q_param, q_param]
            cursor.execute(f"SELECT COUNT(*) as total FROM ({data_sql})", params)
            total_count = cursor.fetchone()['total'] or 0
        else:
            cursor.execute(count_sql)
            total_count = cursor.fetchone()['total'] or 0

        data_sql += " ORDER BY id DESC LIMIT ? OFFSET ?"

    # Execute count if not already calculated
    if table_key != 'audit' or not q_param:
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()['total'] or 0

    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    exec_params = list(params) + [per_page, offset]
    cursor.execute(data_sql, exec_params)
    raw_rows = cursor.fetchall()

    rows = []
    for r in raw_rows:
        row_dict = dict(r)
        if table_key == 'children' and 'dob' in row_dict:
            row_dict['age_display'] = format_child_age(row_dict['dob'])
        rows.append(row_dict)

    return {
        'table_key': table_key,
        'table_title': table_title,
        'table_desc': table_desc,
        'columns': columns,
        'rows': rows,
        'total_count': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'all_counts': all_counts,
        'search_query': q_filter
    }


# =============================================================================
# Phase 5 – AI Nutrition Chatbot DB Helpers
# =============================================================================

def create_chat_session(user_id, context='General Nutrition', language='English',
                        child_id=None, child_name=None, child_age_months=None):
    """Creates a new chat session for a mother and returns its ID."""
    conn = get_db()
    cursor = conn.cursor()
    # Close any previously active session for this user
    cursor.execute(
        "UPDATE chat_sessions SET is_active = 0, updated_at = CURRENT_TIMESTAMP "
        "WHERE user_id = ? AND is_active = 1",
        (user_id,)
    )
    cursor.execute(
        """INSERT INTO chat_sessions
           (user_id, context, language, child_id, child_name, child_age_months, is_active)
           VALUES (?, ?, ?, ?, ?, ?, 1)""",
        (user_id, context, language, child_id, child_name, child_age_months)
    )
    conn.commit()
    return cursor.lastrowid


def get_active_chat_session(user_id):
    """Returns the most recent active chat session for a mother, or None."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM chat_sessions
           WHERE user_id = ? AND is_active = 1
           ORDER BY updated_at DESC LIMIT 1""",
        (user_id,)
    )
    return cursor.fetchone()


def get_or_create_chat_session(user_id, context='General Nutrition',
                               language='English', child_id=None,
                               child_name=None, child_age_months=None):
    """Returns the active session ID, creating one if none exists."""
    existing = get_active_chat_session(user_id)
    if existing:
        return existing['id']
    return create_chat_session(user_id, context, language,
                               child_id, child_name, child_age_months)


def save_chat_message(session_id, role, content):
    """Saves a single chat message (user or assistant) to the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content)
    )
    # Update session timestamp
    cursor.execute(
        "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (session_id,)
    )
    conn.commit()
    return cursor.lastrowid


def get_chat_messages(session_id):
    """Returns all messages in a session ordered chronologically."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    )
    return cursor.fetchall()


def get_all_chat_sessions(user_id, limit=20):
    """Returns a list of all chat sessions for a mother, newest first."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT cs.*,
               (SELECT COUNT(*) FROM chat_messages WHERE session_id = cs.id) as message_count,
               (SELECT content FROM chat_messages
                WHERE session_id = cs.id AND role = 'user'
                ORDER BY id ASC LIMIT 1) as first_question
           FROM chat_sessions cs
           WHERE cs.user_id = ?
           ORDER BY cs.updated_at DESC
           LIMIT ?""",
        (user_id, limit)
    )
    return cursor.fetchall()


def get_chat_session_by_id(session_id, user_id):
    """Returns a specific session only if it belongs to the given user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    )
    return cursor.fetchone()


def close_chat_session(session_id, user_id):
    """Closes (deactivates) a chat session. Only the owner can close it."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE chat_sessions SET is_active = 0, updated_at = CURRENT_TIMESTAMP
           WHERE id = ? AND user_id = ?""",
        (session_id, user_id)
    )
    conn.commit()


# ==============================================================================
# Smart Reminders & Notifications System
# ==============================================================================

def add_custom_reminder(user_id, title, description, due_date, category='Personal', child_id=None):
    """Creates a custom user reminder for a mother."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO custom_reminders (user_id, child_id, title, description, due_date, category, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    ''', (user_id, child_id if child_id else None, title.strip(), (description or '').strip(), due_date, category))
    conn.commit()
    return cursor.lastrowid


def delete_custom_reminder(reminder_id, user_id):
    """Deletes a custom reminder belonging to a user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM custom_reminders WHERE id = ? AND user_id = ?
    ''', (reminder_id, user_id))
    conn.commit()
    return cursor.rowcount > 0


def snooze_smart_reminder(user_id, reminder_key, days=1):
    """Snoozes any reminder (dynamic or custom) until date.today() + days."""
    snoozed_until = (date.today() + timedelta(days=days)).strftime('%Y-%m-%d')
    conn = get_db()
    cursor = conn.cursor()

    if reminder_key.startswith('custom_'):
        try:
            custom_id = int(reminder_key.replace('custom_', ''))
            cursor.execute('''
                UPDATE custom_reminders 
                SET status = 'Snoozed', snoozed_until = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (snoozed_until, custom_id, user_id))
            conn.commit()
            return snoozed_until
        except (ValueError, TypeError):
            pass

    # Dynamic reminder: upsert into reminder_actions
    cursor.execute('''
        INSERT INTO reminder_actions (user_id, reminder_key, status, snoozed_until, updated_at)
        VALUES (?, ?, 'Snoozed', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, reminder_key) DO UPDATE SET
            status = 'Snoozed',
            snoozed_until = excluded.snoozed_until,
            updated_at = CURRENT_TIMESTAMP
    ''', (user_id, reminder_key, snoozed_until))
    conn.commit()
    return snoozed_until


def complete_smart_reminder(user_id, reminder_key):
    """Marks a non-vaccine reminder as completed."""
    now_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db()
    cursor = conn.cursor()

    if reminder_key.startswith('custom_'):
        try:
            custom_id = int(reminder_key.replace('custom_', ''))
            cursor.execute('''
                UPDATE custom_reminders 
                SET status = 'Completed', completed_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            ''', (now_ts, custom_id, user_id))
            conn.commit()
            return True
        except (ValueError, TypeError):
            pass

    # Dynamic reminder: upsert into reminder_actions
    cursor.execute('''
        INSERT INTO reminder_actions (user_id, reminder_key, status, completed_at, updated_at)
        VALUES (?, ?, 'Completed', ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id, reminder_key) DO UPDATE SET
            status = 'Completed',
            completed_at = excluded.completed_at,
            snoozed_until = NULL,
            updated_at = CURRENT_TIMESTAMP
    ''', (user_id, reminder_key, now_ts))
    conn.commit()
    return True


def get_smart_reminders_for_mother(mother_id, status_filter=None, category_filter=None, child_filter=None):
    """
    Dynamically generates, aggregates, and categorizes all smart reminders for a mother across:
      1. Child Immunization (Upcoming, Due Today, Overdue, Completed)
      2. Child Growth Monitoring (Clinical follow-ups, routine checks)
      3. Maternal Health & Wellness (ANC trimesters, EDD delivery check, PNC visits, daily hydration/nutrition)
      4. Custom Reminders created by the mother
    """
    today = date.today()
    today_str = today.strftime('%Y-%m-%d')
    conn = get_db()
    cursor = conn.cursor()

    # 1. Fetch persistent action states
    cursor.execute('SELECT * FROM reminder_actions WHERE user_id = ?', (mother_id,))
    actions_map = {row['reminder_key']: dict(row) for row in cursor.fetchall()}

    # 2. Fetch mother profile & registered children
    raw_profile = get_mother_profile(mother_id)
    profile = dict(raw_profile) if raw_profile else None
    children = get_children_by_mother(mother_id)
    children_map = {c['id']: c for c in children}

    all_reminders = []

    # --------------------------------------------------------------------------
    # A. Custom Reminders
    # --------------------------------------------------------------------------
    cursor.execute('SELECT * FROM custom_reminders WHERE user_id = ? ORDER BY due_date ASC', (mother_id,))
    for cr in cursor.fetchall():
        cr_dict = dict(cr)
        key = f"custom_{cr_dict['id']}"
        ch_name = children_map[cr_dict['child_id']]['full_name'] if cr_dict['child_id'] in children_map else None
        due_d_str = cr_dict['due_date']

        if cr_dict['status'] == 'Completed':
            st = 'Completed'
        elif cr_dict['snoozed_until'] and cr_dict['snoozed_until'] > today_str:
            st = 'Snoozed'
        elif due_d_str < today_str:
            st = 'Overdue'
        elif due_d_str == today_str:
            st = 'Today'
        else:
            st = 'Upcoming'

        all_reminders.append({
            'key': key,
            'id': cr_dict['id'],
            'type': 'Custom',
            'category': cr_dict['category'] or 'Personal',
            'title': cr_dict['title'],
            'description': cr_dict['description'] or '',
            'child_id': cr_dict['child_id'],
            'child_name': ch_name,
            'due_date': due_d_str,
            'original_due_date': due_d_str,
            'status': st,
            'snoozed_until': cr_dict['snoozed_until'],
            'completed_at': cr_dict['completed_at'],
            'can_complete': st != 'Completed',
            'can_snooze': st != 'Completed',
            'can_delete': True,
            'action_url': None,
            'action_label': None,
            'icon_type': 'calendar'
        })

    # --------------------------------------------------------------------------
    # B. Child Immunization Reminders
    # --------------------------------------------------------------------------
    for ch in children:
        schedule = generate_child_vaccination_schedule(ch['id'])
        for vax in schedule:
            key = f"vax_{ch['id']}_{vax['vaccine_code']}_{vax['dose_number']}"
            action = actions_map.get(key)
            rec_date_str = vax['recommended_date']

            if vax['status'] == 'Completed':
                st = 'Completed'
                display_date = vax.get('administered_date') or rec_date_str
                desc = f"Administered on {vax.get('administered_date') or rec_date_str} by {vax.get('administered_by_name') or 'Clinician'}."
            elif action and action['snoozed_until'] and action['snoozed_until'] > today_str:
                st = 'Snoozed'
                display_date = rec_date_str
                desc = f"National Immunization Schedule (NIS) dose. Snoozed until {action['snoozed_until']}."
            elif vax['status'] == 'Overdue':
                st = 'Overdue'
                display_date = rec_date_str
                desc = f"Scheduled for age {vax['recommended_age']}. Action recommended: Visit your community healthcare worker or PHC to receive this vaccination."
            elif vax['status'] == 'Due' or rec_date_str == today_str:
                st = 'Today'
                display_date = rec_date_str
                desc = f"Active vaccination window ({vax['recommended_age']}). Community immunization visits available."
            else:
                st = 'Upcoming'
                display_date = rec_date_str
                desc = f"Scheduled for age {vax['recommended_age']} adhering to India's National Immunization Schedule."

            all_reminders.append({
                'key': key,
                'id': vax.get('record_id') or key,
                'type': 'Immunization',
                'category': 'Child Immunization',
                'title': f"{vax['vaccine_name']} ({vax['dose_number']})",
                'description': desc,
                'child_id': ch['id'],
                'child_name': ch['full_name'],
                'due_date': display_date,
                'original_due_date': rec_date_str,
                'status': st,
                'snoozed_until': action['snoozed_until'] if (action and action['snoozed_until']) else None,
                'completed_at': vax.get('administered_date'),
                'can_complete': False,  # Mother cannot mark vaccine as administered
                'can_snooze': st != 'Completed',
                'can_delete': False,
                'action_url': f"/vaccination/child/{ch['id']}",
                'action_label': 'View Schedule',
                'icon_type': 'syringe'
            })

    # --------------------------------------------------------------------------
    # C. Child Growth Monitoring Reminders
    # --------------------------------------------------------------------------
    for ch in children:
        raw_growth = get_latest_growth_measurement(ch['id'])
        latest_growth = dict(raw_growth) if raw_growth else None
        if latest_growth and latest_growth.get('needs_followup'):
            key = f"growth_followup_{ch['id']}_{latest_growth['id']}"
            action = actions_map.get(key)
            try:
                meas_d = datetime.strptime(latest_growth['measurement_date'], '%Y-%m-%d').date()
                followup_date_str = (meas_d + timedelta(days=14)).strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                followup_date_str = today_str

            if action and action['status'] == 'Completed':
                st = 'Completed'
            elif action and action['snoozed_until'] and action['snoozed_until'] > today_str:
                st = 'Snoozed'
            elif followup_date_str < today_str:
                st = 'Overdue'
            elif followup_date_str == today_str:
                st = 'Today'
            else:
                st = 'Upcoming'

            obs = f": \"{latest_growth['observations']}\"" if latest_growth.get('observations') else ''
            all_reminders.append({
                'key': key,
                'id': key,
                'type': 'Growth Monitoring',
                'category': 'Growth Monitoring',
                'title': f"Pediatric Growth Follow-up: {ch['full_name']}",
                'description': f"Clinical assessment noted {latest_growth['who_status']} ({latest_growth['status_summary']}){obs}. Follow-up measurement advised.",
                'child_id': ch['id'],
                'child_name': ch['full_name'],
                'due_date': followup_date_str,
                'original_due_date': followup_date_str,
                'status': st,
                'snoozed_until': action['snoozed_until'] if (action and action['snoozed_until']) else None,
                'completed_at': action['completed_at'] if (action and action['completed_at']) else None,
                'can_complete': st != 'Completed',
                'can_snooze': st != 'Completed',
                'can_delete': False,
                'action_url': f"/growth/child/{ch['id']}",
                'action_label': 'View Growth Charts',
                'icon_type': 'activity'
            })

    # --------------------------------------------------------------------------
    # D. Maternal Health & Prenatal / Postnatal Reminders
    # --------------------------------------------------------------------------
    if profile:
        preg_status = profile.get('pregnancy_status')
        if preg_status == 'Pregnant' and profile.get('edd'):
            try:
                edd_date = datetime.strptime(profile['edd'], '%Y-%m-%d').date()
                lmp_date = edd_date - timedelta(days=280)
                anc_milestones = [
                    ('anc_1', 'Antenatal Checkup 1 (1st Trimester)', 'Initial clinical screening, registration, routine blood tests, and ultrasound.', lmp_date + timedelta(weeks=10)),
                    ('anc_2', 'Antenatal Checkup 2 (2nd Trimester)', 'Anomaly scan, maternal blood pressure check, and tetanus/Td vaccination.', lmp_date + timedelta(weeks=20)),
                    ('anc_3', 'Antenatal Checkup 3 (3rd Trimester)', 'Growth velocity review, fetal heartbeat monitoring, and hemoglobin test.', lmp_date + timedelta(weeks=30)),
                    ('anc_4', 'Antenatal Checkup 4 (Pre-delivery Checkup)', 'Delivery plan discussion, hospital readiness, and maternal vitals examination.', lmp_date + timedelta(weeks=36)),
                    ('delivery', 'Expected Delivery Preparation', 'Expected Date of Delivery (EDD). Hospital bag readiness and emergency contacts confirmation.', edd_date)
                ]

                for m_id, m_title, m_desc, m_date in anc_milestones:
                    key = f"{m_id}_{profile['id']}"
                    action = actions_map.get(key)
                    m_date_str = m_date.strftime('%Y-%m-%d')

                    if action and action['status'] == 'Completed':
                        st = 'Completed'
                    elif action and action['snoozed_until'] and action['snoozed_until'] > today_str:
                        st = 'Snoozed'
                    elif m_date_str < today_str:
                        st = 'Overdue'
                    elif m_date_str == today_str:
                        st = 'Today'
                    else:
                        st = 'Upcoming'

                    all_reminders.append({
                        'key': key,
                        'id': key,
                        'type': 'Maternal Health',
                        'category': 'Maternal Health',
                        'title': m_title,
                        'description': m_desc,
                        'child_id': None,
                        'child_name': None,
                        'due_date': m_date_str,
                        'original_due_date': m_date_str,
                        'status': st,
                        'snoozed_until': action['snoozed_until'] if (action and action['snoozed_until']) else None,
                        'completed_at': action['completed_at'] if (action and action['completed_at']) else None,
                        'can_complete': st != 'Completed',
                        'can_snooze': st != 'Completed',
                        'can_delete': False,
                        'action_url': '/profile/mother',
                        'action_label': 'View Profile',
                        'icon_type': 'heart'
                    })
            except (ValueError, TypeError):
                pass

        elif preg_status == 'Postnatal':
            pnc_milestones = [
                ('pnc_1', 'Postnatal Care Checkup (Week 1)', 'Maternal healing assessment, infant feeding evaluation, and clinical recovery check.', today - timedelta(days=2)),
                ('pnc_2', 'Postnatal Health Examination (Week 6)', 'Comprehensive 6-week postnatal checkup, mental wellness, and infant developmental review.', today + timedelta(days=20))
            ]
            for p_id, p_title, p_desc, p_date in pnc_milestones:
                key = f"{p_id}_{profile['id']}"
                action = actions_map.get(key)
                p_date_str = p_date.strftime('%Y-%m-%d')

                if action and action['status'] == 'Completed':
                    st = 'Completed'
                elif action and action['snoozed_until'] and action['snoozed_until'] > today_str:
                    st = 'Snoozed'
                elif p_date_str < today_str:
                    st = 'Overdue'
                elif p_date_str == today_str:
                    st = 'Today'
                else:
                    st = 'Upcoming'

                all_reminders.append({
                    'key': key,
                    'id': key,
                    'type': 'Maternal Health',
                    'category': 'Maternal Health',
                    'title': p_title,
                    'description': p_desc,
                    'child_id': None,
                    'child_name': None,
                    'due_date': p_date_str,
                    'original_due_date': p_date_str,
                    'status': st,
                    'snoozed_until': action['snoozed_until'] if (action and action['snoozed_until']) else None,
                    'completed_at': action['completed_at'] if (action and action['completed_at']) else None,
                    'can_complete': st != 'Completed',
                    'can_snooze': st != 'Completed',
                    'can_delete': False,
                    'action_url': '/profile/mother',
                    'action_label': 'View Profile',
                    'icon_type': 'heart'
                })

        # Daily Nutrition & Hydration Tip/Reminder
        daily_key = f"wellness_nutrition_{today_str}_{mother_id}"
        daily_action = actions_map.get(daily_key)
        daily_status = 'Completed' if (daily_action and daily_action['status'] == 'Completed') else 'Today'
        all_reminders.append({
            'key': daily_key,
            'id': daily_key,
            'type': 'Wellness & Nutrition',
            'category': 'Wellness & Nutrition',
            'title': 'Daily Hydration & Nutritional Care',
            'description': 'Remember to drink 8-10 glasses of water daily and consume iron-rich leafy greens, pulses, and recommended vitamins.',
            'child_id': None,
            'child_name': None,
            'due_date': today_str,
            'original_due_date': today_str,
            'status': daily_status,
            'snoozed_until': None,
            'completed_at': daily_action['completed_at'] if (daily_action and daily_action['completed_at']) else None,
            'can_complete': daily_status != 'Completed',
            'can_snooze': False,
            'can_delete': False,
            'action_url': '/chatbot',
            'action_label': 'Consult Nutrition Chatbot',
            'icon_type': 'sun'
        })

    # --------------------------------------------------------------------------
    # E. Helper Calculations & Relative Date Strings
    # --------------------------------------------------------------------------
    for r in all_reminders:
        try:
            r_d = datetime.strptime(r['due_date'], '%Y-%m-%d').date()
            delta_days = (r_d - today).days
            if r['status'] == 'Completed':
                r['relative_time'] = f"Completed"
            elif r['status'] == 'Snoozed':
                r['relative_time'] = f"Snoozed until {r['snoozed_until']}"
            elif delta_days < 0:
                abs_days = abs(delta_days)
                r['relative_time'] = f"Overdue by {abs_days} day{'s' if abs_days != 1 else ''}"
            elif delta_days == 0:
                r['relative_time'] = "Due Today"
            elif delta_days == 1:
                r['relative_time'] = "Due Tomorrow"
            else:
                r['relative_time'] = f"Due in {delta_days} days"
        except (ValueError, TypeError):
            r['relative_time'] = r['due_date']

    # Sort reminders: Overdue first (oldest first), Today, Upcoming (soonest first), Snoozed, Completed (newest first)
    status_order = {'Overdue': 0, 'Today': 1, 'Upcoming': 2, 'Snoozed': 3, 'Completed': 4}
    all_reminders.sort(key=lambda r: (
        status_order.get(r['status'], 5),
        -datetime.strptime(r['due_date'], '%Y-%m-%d').toordinal() if r['status'] == 'Completed' else datetime.strptime(r['due_date'], '%Y-%m-%d').toordinal()
    ))

    # 1. Apply Child Scope / Filter
    scoped = all_reminders
    if child_filter and str(child_filter).lower() != 'all':
        if str(child_filter).lower() == 'maternal':
            scoped = [r for r in scoped if r['child_id'] is None]
        else:
            try:
                ch_id_int = int(child_filter)
                scoped = [r for r in scoped if r['child_id'] == ch_id_int]
            except ValueError:
                pass

    # 2. Apply Category Scope if specified
    if category_filter and str(category_filter).lower() != 'all':
        cf = str(category_filter).lower()
        scoped = [r for r in scoped if cf in r['category'].lower() or cf in r['type'].lower()]

    # 3. Calculate Summary Counts for the current child & category scope
    counts = {
        'total': len([r for r in scoped if r['status'] != 'Completed']),
        'all_total': len(scoped),
        'overdue': len([r for r in scoped if r['status'] == 'Overdue']),
        'today': len([r for r in scoped if r['status'] == 'Today']),
        'upcoming': len([r for r in scoped if r['status'] == 'Upcoming']),
        'completed': len([r for r in scoped if r['status'] == 'Completed']),
        'snoozed': len([r for r in scoped if r['status'] == 'Snoozed'])
    }

    # Global summary counts across ALL children and maternal tasks
    global_counts = {
        'total': len([r for r in all_reminders if r['status'] != 'Completed']),
        'all_total': len(all_reminders),
        'overdue': len([r for r in all_reminders if r['status'] == 'Overdue']),
        'today': len([r for r in all_reminders if r['status'] == 'Today']),
        'upcoming': len([r for r in all_reminders if r['status'] == 'Upcoming']),
        'completed': len([r for r in all_reminders if r['status'] == 'Completed']),
        'snoozed': len([r for r in all_reminders if r['status'] == 'Snoozed'])
    }

    # 4. Apply Status Filter for final displayed items
    filtered = scoped
    if status_filter and str(status_filter).lower() != 'all':
        sf = str(status_filter).lower()
        filtered = [r for r in filtered if r['status'].lower() == sf]

    return {
        'items': filtered,
        'all': all_reminders,
        'scoped': scoped,
        'counts': counts,
        'global_counts': global_counts,
        'children': children,
        'mother_profile': profile
    }

# --------------------------------------------------------------------------
# Healthcare Worker Field Home Visits & Community Care Helpers
# --------------------------------------------------------------------------
def create_field_visit(worker_id, mother_id, visit_date, purpose, status='Completed', notes=None):
    """Logs a new field home visit performed by a healthcare worker."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO field_visits (worker_id, mother_id, visit_date, purpose, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (worker_id, mother_id, visit_date, purpose, status, notes.strip() if notes else None))
    conn.commit()
    return cursor.lastrowid

def get_field_visits_for_worker(worker_id=None):
    """Retrieves field home visits with mother details."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT fv.*, u.full_name as mother_name, u.phone as mother_phone, u.email as mother_email
        FROM field_visits fv
        JOIN users u ON fv.mother_id = u.id
        ORDER BY fv.visit_date DESC, fv.created_at DESC
    ''')
    rows = cursor.fetchall()
    return [dict(r) for r in rows]



