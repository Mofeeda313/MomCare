import os
import re
from datetime import datetime, date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    get_db, close_db, init_db, create_user, 
    get_user_by_email, get_user_by_id, get_all_users, 
    get_users_by_role, get_user_stats,
    get_mother_profile, save_mother_profile, calculate_edd_from_lmp,
    calculate_profile_completion, get_children_by_mother, get_child_by_id,
    add_child, update_child, delete_child, update_user_basic, update_user_language,
    generate_child_vaccination_schedule, get_child_vaccination_summary,
    record_vaccination, get_vaccination_record_by_id, get_all_children_for_workers,
    get_in_app_reminders_for_child, get_in_app_reminders_for_mother,
    get_community_vaccination_stats, NIS_VACCINE_SCHEDULE,
    calculate_bmi, get_child_age_in_months, get_who_growth_benchmark,
    record_growth_measurement, update_growth_measurement, get_growth_measurement_by_id,
    get_child_growth_history, get_latest_growth_measurement, get_community_growth_stats,
    get_all_children_growth_for_workers, get_database_viewer_table, get_database_viewer_counts,
    # Phase 5 – Chatbot
    create_chat_session, get_active_chat_session, get_or_create_chat_session,
    save_chat_message, get_chat_messages, get_all_chat_sessions,
    get_chat_session_by_id, close_chat_session
)

from translations import translate_text, SUPPORTED_LANGUAGES
app = Flask(__name__)
# Secret key for cryptographically signed session cookies
app.secret_key = os.environ.get('SECRET_KEY', 'momcare-forest-secure-key-2026-auth')

# Teardown database connection per request
app.teardown_appcontext(close_db)

# Ensure database tables exist on startup
with app.app_context():
    init_db()

# --- Multilingual Context Processor & Filters ---
@app.template_filter('t')
def filter_translate(text, **kwargs):
    lang = session.get('user_language', 'English')
    return translate_text(text, lang, **kwargs)

@app.context_processor
def inject_translations():
    lang = session.get('user_language', 'English')
    return {
        'current_lang': lang,
        't': lambda text, **kwargs: translate_text(text, lang, **kwargs),
        'supported_languages': SUPPORTED_LANGUAGES
    }

@app.before_request
def resolve_language():
    # If ?lang= parameter is present, update session immediately
    q_lang = request.args.get('lang')
    if q_lang and q_lang in ('English', 'Malayalam', 'Hindi', 'Kannada'):
        session['user_language'] = q_lang
        if 'user_id' in session:
            try:
                update_user_language(session['user_id'], q_lang)
            except Exception:
                pass
    elif 'user_language' not in session:
        if 'user_id' in session:
            try:
                user = get_user_by_id(session['user_id'])
                if user and user['language'] in ('English', 'Malayalam', 'Hindi', 'Kannada'):
                    session['user_language'] = user['language']
                else:
                    session['user_language'] = request.cookies.get('momcare_lang', 'English')
            except Exception:
                session['user_language'] = request.cookies.get('momcare_lang', 'English')
        else:
            session['user_language'] = request.cookies.get('momcare_lang', 'English')

@app.route('/set-language/<lang>')
def set_language_route(lang):
    """Switches the active language, updates DB if logged in, and redirects back."""
    valid_langs = ('English', 'Malayalam', 'Hindi', 'Kannada')
    if lang in valid_langs:
        session['user_language'] = lang
        if 'user_id' in session:
            try:
                update_user_language(session['user_id'], lang)
            except Exception:
                pass

    referrer = request.referrer
    if not referrer or '/set-language' in referrer:
        referrer = url_for('home')

    response = redirect(referrer)
    response.set_cookie('momcare_lang', session.get('user_language', 'English'), max_age=60*60*24*365)
    return response


# --- Role Normalization & Authorization Helper ---
def normalize_role(role_raw):
    """
    Normalizes any role variation into one of the three canonical roles:
    'Mother', 'Healthcare Worker', 'Admin'.
    
    Handles:
      - 'mother', 'Mother', 'MOTHER', 'mom', 'parent', 'patient' -> 'Mother'
      - 'healthcare_worker', 'healthcare-worker', 'Healthcare Worker',
        'healthcare worker', 'nurse', 'Nurse', 'NURSE', 'doctor', 'worker',
        'asha', 'health_worker', 'health worker', 'provider' -> 'Healthcare Worker'
      - 'admin', 'Admin', 'administrator', 'Administrator', 'ADMIN', 'superuser' -> 'Admin'
    """
    if not role_raw:
        return None
    r = str(role_raw).strip().lower().replace('-', '_').replace(' ', '_')
    if r in ('mother', 'mom', 'patient', 'parent'):
        return 'Mother'
    elif r in ('healthcare_worker', 'healthcareworker', 'nurse', 'doctor', 'asha', 'worker', 'health_worker', 'provider'):
        return 'Healthcare Worker'
    elif r in ('admin', 'administrator', 'superuser', 'admin_user'):
        return 'Admin'
    return role_raw.strip().title()

def get_role_dashboard_url(role):
    """Returns the dedicated dashboard URL for a canonical role."""
    canonical = normalize_role(role)
    if canonical == 'Healthcare Worker':
        return url_for('worker_dashboard')
    elif canonical == 'Mother':
        return url_for('mother_dashboard')
    elif canonical == 'Admin':
        return url_for('admin_dashboard')
    return url_for('home')

# --- Authorization Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Protects routes by verifying user's role against allowed roles using normalization."""
    normalized_allowed = [normalize_role(r) for r in allowed_roles]
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.path))
            
            user_role = normalize_role(session.get('user_role'))
            if user_role not in normalized_allowed:
                return render_template(
                    '403.html',
                    required_roles=", ".join(allowed_roles),
                    user_role=user_role,
                    user_name=session.get('user_name')
                ), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Existing Core Routes ---
@app.route('/')
def home():
    """Renders the MomCare home page with database status and user session state."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT app_name, status, version, created_at FROM app_info LIMIT 1')
    info = cursor.fetchone()
    return render_template('index.html', info=info)

@app.route('/health')
def health():
    """Health check endpoint to verify Flask app and SQLite connectivity."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'app': 'MomCare'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# --- Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Professional registration with validation for Mothers and Healthcare Workers."""
    # Redirect already logged in users to their role dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard_router'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        language = request.form.get('language', 'English').strip()
        raw_role = request.form.get('role', '').strip()

        allowed_languages = ['English', 'Malayalam', 'Kannada', 'Hindi']
        canonical_role = normalize_role(raw_role)

        # Validation rules
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')

        email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not email or not re.match(email_regex, email):
            errors.append('Please provide a valid email address.')

        phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not phone or len(phone_clean) < 7 or not phone_clean.isdigit():
            errors.append('Please provide a valid phone number (at least 7 digits).')

        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')

        if password != confirm_password:
            errors.append('Passwords do not match.')

        if language not in allowed_languages:
            errors.append('Please select a valid preferred language.')

        if canonical_role not in ('Mother', 'Healthcare Worker'):
            errors.append('Invalid role selected. Public registration only allows Mother or Healthcare Worker.')

        # Check duplicate email
        if not errors:
            existing_user = get_user_by_email(email)
            if existing_user:
                errors.append('An account with this email address already exists. Please log in.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'register.html', 
                form_data={
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'language': language,
                    'role': canonical_role or raw_role
                }
            ), 400

        # Hash password securely
        password_hash = generate_password_hash(password)

        try:
            create_user(full_name, email, phone, password_hash, language, canonical_role)
            flash(f'Registration successful! Welcome to MomCare, {full_name}. Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration error: {str(e)}', 'danger')
            return render_template('register.html'), 500

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Professional login with credentials verification, session regeneration,
    and strict role-based dashboard redirection.
    """
    if 'user_id' in session and request.method == 'GET':
        return redirect(url_for('dashboard_router'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html', email=email), 400

        user = get_user_by_email(email)

        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', email=email), 401

        # Clear any existing session completely to prevent cross-account contamination
        session.clear()

        # Derive canonical role directly from authenticated database record
        canonical_role = normalize_role(user['role'])

        # Establish fresh authenticated session
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['user_email'] = user['email']
        session['user_role'] = canonical_role
        session['user_language'] = user['language']
        session['user_phone'] = user['phone']

        flash(f'Welcome back, {user["full_name"]}!', 'success')

        # Role-based redirection logic:
        # If 'next' was requested and matches the user's role dashboard, follow it.
        # Otherwise, ALWAYS redirect directly to the user's canonical role dashboard.
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            if canonical_role == 'Healthcare Worker' and next_page.startswith('/dashboard/healthcare-worker'):
                return redirect(next_page)
            elif canonical_role == 'Mother' and next_page.startswith('/dashboard/mother'):
                return redirect(next_page)
            elif canonical_role == 'Admin' and next_page.startswith('/dashboard/admin'):
                return redirect(next_page)

        # Direct, definitive redirection to the user's authentic dashboard
        return redirect(get_role_dashboard_url(canonical_role))

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Completely clears user session data and logs out safely."""
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'You have been safely logged out. See you soon, {user_name}!', 'info')
    return redirect(url_for('login'))

@app.route('/forgot-password')
def forgot_password():
    """Information and support contact for password recovery."""
    return render_template('forgot_password.html')

# --- Role-Based Dashboard Routing & Views ---
@app.route('/dashboard')
@login_required
def dashboard_router():
    """
    Automatically routes the user to their designated role dashboard
    using normalized role mapping and live database verification.
    """
    role = normalize_role(session.get('user_role'))
    
    # If session role is missing, query database using authenticated user_id
    if not role:
        user = get_user_by_id(session.get('user_id'))
        if user:
            role = normalize_role(user['role'])
            session['user_role'] = role

    if role == 'Healthcare Worker':
        return redirect(url_for('worker_dashboard'))
    elif role == 'Mother':
        return redirect(url_for('mother_dashboard'))
    elif role == 'Admin':
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Unrecognized user role. Please sign in again.', 'danger')
        return redirect(url_for('logout'))

@app.route('/dashboard/mother')
@login_required
@role_required('Mother')
def mother_dashboard():
    """Mother Dashboard with personalized maternal, child care, and vaccination widgets."""
    user = get_user_by_id(session['user_id'])
    profile = get_mother_profile(session['user_id'])
    completion_pct = calculate_profile_completion(user, profile)
    children = get_children_by_mother(session['user_id'])
    
    # Handle Child Vaccination & Growth Monitoring selection
    selected_child = None
    selected_child_schedule = []
    selected_child_summary = None
    selected_child_growth = None
    selected_child_growth_history = []
    
    if children and len(children) > 0:
        child_id_param = request.args.get('child_id', type=int)
        if child_id_param:
            selected_child = next((c for c in children if c['id'] == child_id_param), children[0])
        else:
            selected_child = children[0]
            
        selected_child_schedule = generate_child_vaccination_schedule(selected_child['id'])
        selected_child_summary = get_child_vaccination_summary(selected_child['id'])
        selected_child_growth = get_latest_growth_measurement(selected_child['id'])
        selected_child_growth_history = get_child_growth_history(selected_child['id'])
        
    in_app_reminders = get_in_app_reminders_for_mother(session['user_id'])
    
    return render_template(
        'dashboard_mother.html',
        user=user,
        profile=profile,
        completion_pct=completion_pct,
        children=children,
        selected_child=selected_child,
        selected_child_schedule=selected_child_schedule,
        selected_child_summary=selected_child_summary,
        selected_child_growth=selected_child_growth,
        selected_child_growth_history=selected_child_growth_history,
        in_app_reminders=in_app_reminders
    )

# --- Mother Profile Management Routes ---
@app.route('/profile/mother')
@login_required
@role_required('Mother')
def mother_profile_view():
    """Displays comprehensive profile details for the authenticated mother."""
    user = get_user_by_id(session['user_id'])
    profile = get_mother_profile(session['user_id'])
    completion_pct = calculate_profile_completion(user, profile)
    children = get_children_by_mother(session['user_id'])
    return render_template(
        'profile_mother.html',
        user=user,
        profile=profile,
        completion_pct=completion_pct,
        children=children
    )

@app.route('/profile/mother/edit', methods=['GET', 'POST'])
@login_required
@role_required('Mother')
def mother_profile_edit():
    """Enables mother to create or update personal, medical, and emergency contact details."""
    user = get_user_by_id(session['user_id'])
    profile = get_mother_profile(session['user_id'])
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        dob = request.form.get('dob', '').strip()
        address = request.form.get('address', '').strip()
        pregnancy_status = request.form.get('pregnancy_status', 'Pregnant').strip()
        lmp = request.form.get('lmp', '').strip()
        edd = request.form.get('edd', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        medical_history = request.form.get('medical_history', '').strip()
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
        
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Full name must be at least 2 characters.')
        
        phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not phone or len(phone_clean) < 7 or not phone_clean.isdigit():
            errors.append('Please provide a valid phone number (at least 7 digits).')
            
        allowed_statuses = ['Pregnant', 'Not Pregnant', 'Postnatal']
        if pregnancy_status not in allowed_statuses:
            errors.append('Please select a valid pregnancy status.')
            
        allowed_blood_groups = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_group not in allowed_blood_groups:
            errors.append('Please select a valid blood group.')
            
        # Automatic EDD calculation if LMP is provided and EDD was left blank
        if lmp and not edd:
            edd = calculate_edd_from_lmp(lmp)
            
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'profile_mother_edit.html',
                user=user,
                profile={
                    'dob': dob,
                    'address': address,
                    'pregnancy_status': pregnancy_status,
                    'lmp': lmp,
                    'edd': edd,
                    'blood_group': blood_group,
                    'medical_history': medical_history,
                    'emergency_contact_name': emergency_contact_name,
                    'emergency_contact_phone': emergency_contact_phone
                }
            ), 400
            
        # Update user name and phone
        update_user_basic(session['user_id'], full_name, phone)
        session['user_name'] = full_name
        session['user_phone'] = phone
        
        # Save profile
        save_mother_profile(
            session['user_id'], dob, address, pregnancy_status,
            lmp, edd, blood_group, medical_history,
            emergency_contact_name, emergency_contact_phone
        )
        
        flash('Mother profile successfully updated!', 'success')
        return redirect(url_for('mother_profile_view'))
        
    return render_template('profile_mother_edit.html', user=user, profile=profile)

# --- Child Profile Management Routes ---
@app.route('/children/add', methods=['GET', 'POST'])
@login_required
@role_required('Mother')
def child_add():
    """Allows a registered mother to add a child to her account."""
    user = get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        dob = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        birth_weight_raw = request.form.get('birth_weight', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        allergies = request.form.get('allergies', '').strip()
        medical_history = request.form.get('medical_history', '').strip()
        
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Child's full name must be at least 2 characters.")
            
        if not dob:
            errors.append("Child's date of birth is required.")
        else:
            try:
                datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                errors.append("Invalid date format for child's birth date.")
                
        allowed_genders = ['Male', 'Female', 'Other']
        if gender not in allowed_genders:
            errors.append("Please select child's gender.")
            
        birth_weight = None
        if birth_weight_raw:
            try:
                birth_weight = float(birth_weight_raw)
                if birth_weight <= 0 or birth_weight > 20:
                    errors.append('Birth weight must be between 0.1 and 20.0 kg.')
            except ValueError:
                errors.append('Birth weight must be a valid number (e.g. 3.2).')
                
        allowed_blood_groups = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_group not in allowed_blood_groups:
            errors.append('Please select a valid blood group.')
            
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template(
                'child_add.html',
                user=user,
                form_data={
                    'full_name': full_name,
                    'dob': dob,
                    'gender': gender,
                    'birth_weight': birth_weight_raw,
                    'blood_group': blood_group,
                    'allergies': allergies,
                    'medical_history': medical_history
                }
            ), 400
            
        child_id = add_child(
            session['user_id'], full_name, dob, gender,
            birth_weight, blood_group, allergies, medical_history
        )
        flash(f'Child profile for "{full_name}" registered successfully!', 'success')
        return redirect(url_for('child_detail', child_id=child_id))
        
    return render_template('child_add.html', user=user)

@app.route('/children/<int:child_id>')
@login_required
def child_detail(child_id):
    """View details of a registered child with strict ownership authorization."""
    child = get_child_by_id(child_id)
    if not child:
        flash('Child profile not found.', 'warning')
        return redirect(url_for('dashboard_router'))
        
    # Strict ownership check: Mothers can only view their own children
    user_role = session.get('user_role')
    if user_role == 'Mother' and child['mother_id'] != session.get('user_id'):
        return render_template(
            '403.html',
            required_roles='Child Parent / Authorized Clinician',
            user_role=user_role,
            user_name=session.get('user_name')
        ), 403
        
    mother = get_user_by_id(child['mother_id'])
    return render_template('child_detail.html', child=child, mother=mother)

@app.route('/children/<int:child_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Mother')
def child_edit(child_id):
    """Edit child profile with strict ownership verification."""
    child = get_child_by_id(child_id)
    if not child:
        flash('Child profile not found.', 'warning')
        return redirect(url_for('dashboard_router'))
        
    # Strict ownership check
    if child['mother_id'] != session.get('user_id'):
        return render_template(
            '403.html',
            required_roles='Child Parent',
            user_role=session.get('user_role'),
            user_name=session.get('user_name')
        ), 403
        
    user = get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        dob = request.form.get('dob', '').strip()
        gender = request.form.get('gender', '').strip()
        birth_weight_raw = request.form.get('birth_weight', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        allergies = request.form.get('allergies', '').strip()
        medical_history = request.form.get('medical_history', '').strip()
        
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append("Child's full name must be at least 2 characters.")
            
        if not dob:
            errors.append("Child's date of birth is required.")
        else:
            try:
                datetime.strptime(dob, '%Y-%m-%d')
            except ValueError:
                errors.append("Invalid date format for child's birth date.")
                
        allowed_genders = ['Male', 'Female', 'Other']
        if gender not in allowed_genders:
            errors.append("Please select child's gender.")
            
        birth_weight = None
        if birth_weight_raw:
            try:
                birth_weight = float(birth_weight_raw)
                if birth_weight <= 0 or birth_weight > 20:
                    errors.append('Birth weight must be between 0.1 and 20.0 kg.')
            except ValueError:
                errors.append('Birth weight must be a valid number.')
                
        allowed_blood_groups = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_group not in allowed_blood_groups:
            errors.append('Please select a valid blood group.')
            
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('child_edit.html', user=user, child=child), 400
            
        update_child(
            child_id, session['user_id'], full_name, dob, gender,
            birth_weight, blood_group, allergies, medical_history
        )
        flash(f'Child profile for "{full_name}" updated successfully!', 'success')
        return redirect(url_for('child_detail', child_id=child_id))
        
    return render_template('child_edit.html', user=user, child=child)

@app.route('/children/<int:child_id>/delete', methods=['POST'])
@login_required
@role_required('Mother')
def child_delete(child_id):
    """Removes a child profile with ownership check."""
    child = get_child_by_id(child_id)
    if not child or child['mother_id'] != session.get('user_id'):
        flash('Unauthorized action or child profile not found.', 'danger')
        return redirect(url_for('mother_dashboard'))
        
    child_name = child['full_name']
    delete_child(child_id, session['user_id'])
    flash(f'Record for "{child_name}" has been removed.', 'info')
    return redirect(url_for('mother_dashboard'))

@app.route('/dashboard/healthcare-worker')
@login_required
@role_required('Healthcare Worker', 'Admin')
def worker_dashboard():
    """Healthcare Worker Dashboard with community mothers, children vaccination management & field tools."""
    user = get_user_by_id(session['user_id'])
    mothers = get_users_by_role('Mother')
    
    # Community search, vaccination statistics & growth monitoring
    search_q = request.args.get('q', '').strip()
    community_children = get_all_children_for_workers(search_query=search_q)
    vax_stats = get_community_vaccination_stats()
    growth_stats = get_community_growth_stats()
    growth_children = get_all_children_growth_for_workers(search_query=search_q)
    
    return render_template(
        'dashboard_worker.html',
        user=user,
        mothers=mothers,
        community_children=community_children,
        vax_stats=vax_stats,
        growth_stats=growth_stats,
        growth_children=growth_children,
        search_query=search_q
    )

# --- Phase 3 Vaccination Management Routes ---
@app.route('/vaccinations/child/<int:child_id>')
@login_required
def child_vaccination_schedule(child_id):
    """
    Displays the complete National Immunization Schedule for a child as
    continuous vertical menu rows. Authorized for the child's mother,
    Healthcare Workers, and Admins.
    """
    child = get_child_by_id(child_id)
    if not child:
        flash('Child record not found.', 'warning')
        return redirect(url_for('dashboard_router'))
        
    user_role = session.get('user_role')
    # Strict role/ownership authorization
    if user_role == 'Mother' and child['mother_id'] != session.get('user_id'):
        return render_template(
            '403.html',
            required_roles='Child Parent / Authorized Healthcare Provider',
            user_role=user_role,
            user_name=session.get('user_name')
        ), 403
        
    mother = get_user_by_id(child['mother_id'])
    schedule = generate_child_vaccination_schedule(child_id)
    summary = get_child_vaccination_summary(child_id)
    reminders = get_in_app_reminders_for_child(child_id)
    
    # Optional status filter (all, upcoming, due, overdue, completed)
    status_filter = request.args.get('status', 'all').lower()
    if status_filter in ('upcoming', 'due', 'overdue', 'completed'):
        filtered_schedule = [s for s in schedule if s['status'].lower() == status_filter]
    else:
        filtered_schedule = schedule
        status_filter = 'all'
        
    return render_template(
        'vaccination_schedule.html',
        child=child,
        mother=mother,
        schedule=filtered_schedule,
        all_schedule=schedule,
        summary=summary,
        reminders=reminders,
        status_filter=status_filter,
        user_role=user_role
    )

@app.route('/vaccinations/record/<int:child_id>/<vaccine_code>', methods=['GET', 'POST'])
@login_required
@role_required('Healthcare Worker', 'Admin')
def vaccination_record_form(child_id, vaccine_code):
    """Allows authorized healthcare workers to record a completed vaccination dose."""
    child = get_child_by_id(child_id)
    if not child:
        flash('Child record not found.', 'warning')
        return redirect(url_for('worker_dashboard'))
        
    mother = get_user_by_id(child['mother_id'])
    meta = next((item for item in NIS_VACCINE_SCHEDULE if item['code'] == vaccine_code), None)
    
    if request.method == 'POST':
        admin_date = request.form.get('administered_date', '').strip()
        batch_num = request.form.get('batch_number', '').strip()
        notes = request.form.get('notes', '').strip()
        
        errors = []
        if not admin_date:
            errors.append('Administration date is required.')
        else:
            try:
                datetime.strptime(admin_date, '%Y-%m-%d')
            except ValueError:
                errors.append('Invalid date format for administration date.')
                
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('vaccination_record.html', child=child, mother=mother, meta=meta), 400
            
        record_vaccination(
            child_id=child_id,
            vaccine_code=vaccine_code,
            administered_date=admin_date,
            administered_by_id=session.get('user_id'),
            administered_by_name=session.get('user_name', 'Healthcare Staff'),
            batch_number=batch_num,
            notes=notes
        )
        
        flash(f'Vaccination dose for {meta["name"] if meta else vaccine_code} successfully recorded!', 'success')
        return redirect(url_for('child_vaccination_schedule', child_id=child_id))
        
    return render_template('vaccination_record.html', child=child, mother=mother, meta=meta, today_str=datetime.now().strftime('%Y-%m-%d'))

@app.route('/vaccinations/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
@role_required('Healthcare Worker', 'Admin')
def vaccination_edit_form(record_id):
    """Enables authorized clinical staff to correct an existing vaccination record while logging change reason."""
    record = get_vaccination_record_by_id(record_id)
    if not record:
        flash('Vaccination record not found.', 'warning')
        return redirect(url_for('worker_dashboard'))
        
    child = get_child_by_id(record['child_id'])
    
    if request.method == 'POST':
        admin_date = request.form.get('administered_date', '').strip()
        batch_num = request.form.get('batch_number', '').strip()
        notes = request.form.get('notes', '').strip()
        change_reason = request.form.get('change_reason', '').strip()
        
        errors = []
        if not admin_date:
            errors.append('Administration date is required.')
        if not change_reason:
            errors.append('Clinical correction reason is required for audit verification.')
            
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('vaccination_edit.html', record=record, child=child), 400
            
        record_vaccination(
            child_id=record['child_id'],
            vaccine_code=record['vaccine_code'],
            administered_date=admin_date,
            administered_by_id=session.get('user_id'),
            administered_by_name=session.get('user_name', 'Healthcare Staff'),
            batch_number=batch_num,
            notes=notes,
            change_reason=change_reason
        )
        
        flash(f'Correction logged for {record["vaccine_name"]} successfully.', 'success')
        return redirect(url_for('child_vaccination_schedule', child_id=record['child_id']))
        
    return render_template('vaccination_edit.html', record=record, child=child)

# --- Phase 4 Child Growth Monitoring Routes ---
@app.route('/growth/child/<int:child_id>')
@login_required
def child_growth_view(child_id):
    """
    Displays comprehensive growth monitoring history, WHO benchmarks,
    deltas, and interactive growth charts for a child.
    Mothers can only view their own children; Healthcare Workers and Admins can view any child.
    """
    child = get_child_by_id(child_id)
    if not child:
        flash('Child record not found.', 'warning')
        return redirect(url_for('dashboard_router'))

    user_role = session.get('user_role')
    # Strict cross-mother privacy protection
    if user_role == 'Mother' and child['mother_id'] != session.get('user_id'):
        return render_template(
            '403.html',
            required_roles='Child Parent / Authorized Healthcare Provider',
            user_role=user_role,
            user_name=session.get('user_name')
        ), 403

    mother = get_user_by_id(child['mother_id'])
    history = get_child_growth_history(child_id)
    latest = get_latest_growth_measurement(child_id)
    
    # Sibling children for switching tabs
    sibling_children = get_children_by_mother(child['mother_id'])
    
    # Current age calculation
    current_age_mos = get_child_age_in_months(child['dob'])
    who_ref = get_who_growth_benchmark(current_age_mos, child.get('gender'))

    return render_template(
        'child_growth.html',
        child=child,
        mother=mother,
        history=history,
        latest=latest,
        sibling_children=sibling_children,
        current_age_mos=current_age_mos,
        who_ref=who_ref,
        user_role=user_role
    )

@app.route('/growth/record/<int:child_id>', methods=['GET', 'POST'])
@login_required
@role_required('Healthcare Worker', 'Admin')
def growth_record_form(child_id):
    """
    Form for authorized healthcare workers to log physical growth measurements
    (weight, height, head circumference, observations).
    """
    child = get_child_by_id(child_id)
    if not child:
        flash('Child record not found.', 'warning')
        return redirect(url_for('dashboard_router'))

    mother = get_user_by_id(child['mother_id'])
    today_str = date.today().strftime('%Y-%m-%d')
    latest = get_latest_growth_measurement(child_id)

    if request.method == 'POST':
        measurement_date = request.form.get('measurement_date', '').strip()
        weight_raw = request.form.get('weight', '').strip()
        height_raw = request.form.get('height', '').strip()
        head_circ_raw = request.form.get('head_circumference', '').strip()
        observations = request.form.get('observations', '').strip()

        # Validation
        if not measurement_date:
            flash('Measurement date is required.', 'danger')
            return render_template('growth_record.html', child=child, mother=mother, today_str=today_str, latest=latest)

        try:
            w_val = float(weight_raw)
            h_val = float(height_raw)
            if w_val <= 0 or h_val <= 0:
                flash('Weight and height must be positive numbers.', 'danger')
                return render_template('growth_record.html', child=child, mother=mother, today_str=today_str, latest=latest)
        except (ValueError, TypeError):
            flash('Please enter valid numeric values for weight and height.', 'danger')
            return render_template('growth_record.html', child=child, mother=mother, today_str=today_str, latest=latest)

        hc_val = None
        if head_circ_raw:
            try:
                hc_val = float(head_circ_raw)
                if hc_val <= 0:
                    hc_val = None
            except ValueError:
                flash('Please enter a valid number for head circumference.', 'danger')
                return render_template('growth_record.html', child=child, mother=mother, today_str=today_str, latest=latest)

        worker_name = session.get('user_name', 'Healthcare Staff')
        worker_id = session.get('user_id')

        record_growth_measurement(
            child_id=child_id,
            measurement_date=measurement_date,
            weight=w_val,
            height=h_val,
            head_circumference=hc_val,
            observations=observations,
            recorded_by_id=worker_id,
            recorded_by_name=worker_name,
            change_reason='Clinical growth monitoring visit'
        )

        flash(f'Growth measurement for {child["full_name"]} recorded successfully.', 'success')
        return redirect(url_for('child_growth_view', child_id=child_id))

    return render_template('growth_record.html', child=child, mother=mother, today_str=today_str, latest=latest)

@app.route('/growth/edit/<int:measurement_id>', methods=['GET', 'POST'])
@login_required
@role_required('Healthcare Worker', 'Admin')
def growth_edit_form(measurement_id):
    """
    Enables authorized clinicians to correct an existing growth measurement
    while mandating a reason for audit traceability.
    """
    record = get_growth_measurement_by_id(measurement_id)
    if not record:
        flash('Measurement record not found.', 'warning')
        return redirect(url_for('dashboard_router'))

    child = get_child_by_id(record['child_id'])
    mother = get_user_by_id(child['mother_id'])

    if request.method == 'POST':
        measurement_date = request.form.get('measurement_date', '').strip()
        weight_raw = request.form.get('weight', '').strip()
        height_raw = request.form.get('height', '').strip()
        head_circ_raw = request.form.get('head_circumference', '').strip()
        observations = request.form.get('observations', '').strip()
        change_reason = request.form.get('change_reason', '').strip()

        if not change_reason:
            flash('A clinical reason for correcting this record is required for audit purposes.', 'danger')
            return render_template('growth_edit.html', record=record, child=child, mother=mother)

        try:
            w_val = float(weight_raw)
            h_val = float(height_raw)
            if w_val <= 0 or h_val <= 0:
                flash('Weight and height must be positive numbers.', 'danger')
                return render_template('growth_edit.html', record=record, child=child, mother=mother)
        except (ValueError, TypeError):
            flash('Please enter valid numeric values for weight and height.', 'danger')
            return render_template('growth_edit.html', record=record, child=child, mother=mother)

        hc_val = None
        if head_circ_raw:
            try:
                hc_val = float(head_circ_raw)
            except ValueError:
                pass

        update_growth_measurement(
            measurement_id=measurement_id,
            measurement_date=measurement_date,
            weight=w_val,
            height=h_val,
            head_circumference=hc_val,
            observations=observations,
            changed_by_id=session.get('user_id'),
            changed_by_name=session.get('user_name', 'Healthcare Staff'),
            change_reason=change_reason
        )

        flash(f'Growth measurement record updated with clinical audit log.', 'success')
        return redirect(url_for('child_growth_view', child_id=record['child_id']))

    return render_template('growth_edit.html', record=record, child=child, mother=mother)

@app.route('/growth/community')
@login_required
@role_required('Healthcare Worker', 'Admin')
def community_growth_directory():
    """
    Community directory of all registered children with growth indicators,
    follow-up flags, and search filtering for Healthcare Workers and Admins.
    """
    user = get_user_by_id(session['user_id'])
    search_q = request.args.get('q', '').strip()
    filter_tab = request.args.get('filter', 'all').lower()

    all_children = get_all_children_growth_for_workers(search_query=search_q)
    growth_stats = get_community_growth_stats()

    # Filter tab
    if filter_tab == 'followup':
        filtered_children = [c for c in all_children if c['needs_followup']]
    elif filter_tab == 'measured':
        filtered_children = [c for c in all_children if c['measurement_count'] > 0]
    elif filter_tab == 'unmeasured':
        filtered_children = [c for c in all_children if c['measurement_count'] == 0]
    else:
        filtered_children = all_children
        filter_tab = 'all'

    return render_template(
        'growth_community.html',
        user=user,
        community_children=filtered_children,
        all_children=all_children,
        growth_stats=growth_stats,
        search_query=search_q,
        filter_tab=filter_tab
    )

@app.route('/dashboard/admin')
@login_required
@role_required('Admin')
def admin_dashboard():
    """System Administrator Dashboard with system stats and user management."""
    user = get_user_by_id(session['user_id'])
    users = get_all_users()
    stats = get_user_stats()
    growth_stats = get_community_growth_stats()
    vax_stats = get_community_vaccination_stats()
    return render_template('dashboard_admin.html', user=user, users=users, stats=stats, growth_stats=growth_stats, vax_stats=vax_stats)

@app.route('/admin/database-viewer')
@login_required
@role_required('Admin')
def admin_database_viewer():
    """
    Visual spreadsheet-like database viewer for system administrators.
    Allows inspection of live SQLite tables with search, pagination,
    and sanitized credentials.
    """
    user = get_user_by_id(session['user_id'])
    table_key = request.args.get('table', 'users').lower()
    search_q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 15, type=int)

    table_data = get_database_viewer_table(
        table_key=table_key,
        search_query=search_q,
        page=page,
        per_page=per_page
    )

    return render_template(
        'admin_database_viewer.html',
        user=user,
        table_data=table_data,
        table_key=table_key,
        search_query=search_q
    )

# =============================================================================
# Phase 5 – AI Nutrition and Health Awareness Chatbot Routes
# =============================================================================

@app.route('/chatbot')
@login_required
@role_required('Mother')
def chatbot_view():
    """Main chatbot page for authenticated mothers."""
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    children = get_children_by_mother(user_id)
    profile = get_mother_profile(user_id)

    # Determine default language from user's registered preference
    default_language = session.get('user_language') or (user['language'] if user['language'] in ('English', 'Malayalam', 'Kannada', 'Hindi') else 'English')

    # Determine context from query parameters or profile
    context = request.args.get('context', 'General Nutrition')
    language = request.args.get('lang', default_language)
    child_id_param = request.args.get('child_id', type=int)

    valid_contexts = ('General Nutrition', 'Pregnancy', 'Postnatal Care', 'Child Nutrition')
    if context not in valid_contexts:
        context = 'General Nutrition'

    valid_languages = ('English', 'Malayalam', 'Kannada', 'Hindi')
    if language not in valid_languages:
        language = 'English'

    selected_child = None
    child_age_months = None

    # Set child context if a child is selected
    if child_id_param:
        for c in children:
            if c['id'] == child_id_param:
                selected_child = c
                child_age_months = get_child_age_in_months(c['dob'])
                context = 'Child Nutrition'
                break

    # Get or create a chat session for the current settings
    active_session = get_active_chat_session(user_id)
    if active_session:
        session_id = active_session['id']
        messages = [dict(m) for m in get_chat_messages(session_id)]
    else:
        session_id = None
        messages = []

    # Pregnancy context from profile
    pregnancy_status = profile['pregnancy_status'] if profile else 'Unknown'

    return render_template(
        'chatbot.html',
        user=user,
        children=children,
        profile=profile,
        context=context,
        language=language,
        selected_child=selected_child,
        child_age_months=child_age_months,
        pregnancy_status=pregnancy_status,
        active_session_id=session_id,
        messages=messages,
        gemini_configured=bool(os.environ.get('GEMINI_API_KEY', '').strip())
    )


@app.route('/chatbot/chat', methods=['POST'])
@login_required
@role_required('Mother')
def chatbot_send():
    """
    AJAX endpoint: receives a question and returns a JSON response.
    Never exposes personal data in the AI response.
    """
    user_id = session['user_id']

    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    context = data.get('context', 'General Nutrition')
    language = data.get('language') or session.get('user_language', 'English')
    child_id_param = data.get('child_id')
    session_id_param = data.get('session_id')

    if not question:
        return jsonify({'error': 'Please type a question.'}), 400

    if len(question) > 1000:
        return jsonify({'error': 'Question is too long. Please keep it under 1000 characters.'}), 400

    valid_contexts = ('General Nutrition', 'Pregnancy', 'Postnatal Care', 'Child Nutrition')
    if context not in valid_contexts:
        context = 'General Nutrition'

    valid_languages = ('English', 'Malayalam', 'Kannada', 'Hindi')
    if language not in valid_languages:
        language = 'English'

    # Resolve child context safely (verify ownership)
    child_age_months = None
    child_name = None
    resolved_child_id = None

    if child_id_param:
        try:
            resolved_child_id = int(child_id_param)
            child = get_child_by_id(resolved_child_id)
            if child and child['mother_id'] == user_id:
                child_age_months = get_child_age_in_months(child['dob'])
                child_name = child['full_name']
            else:
                resolved_child_id = None  # Security: ignore if not owner
        except (ValueError, TypeError):
            resolved_child_id = None

    # Ensure we have a valid session
    if session_id_param:
        try:
            session_id = int(session_id_param)
            existing = get_chat_session_by_id(session_id, user_id)
            if not existing:
                session_id = None
        except (ValueError, TypeError):
            session_id = None
    else:
        session_id = None

    if not session_id:
        session_id = create_chat_session(
            user_id=user_id,
            context=context,
            language=language,
            child_id=resolved_child_id,
            child_name=child_name,
            child_age_months=child_age_months
        )

    # Retrieve conversation history for multi-turn context
    history_rows = get_chat_messages(session_id)
    history = [{'role': r['role'], 'content': r['content']} for r in history_rows]

    # Save the user's question
    save_chat_message(session_id, 'user', question)

    # Get AI or fallback response
    from chatbot_engine import get_ai_response
    response_text, used_ai = get_ai_response(
        question=question,
        context=context,
        language=language,
        chat_history=history,
        child_age_months=child_age_months,
        child_name=None  # Never pass the real child name to AI for privacy
    )

    # Save assistant response
    save_chat_message(session_id, 'assistant', response_text)

    return jsonify({
        'response': response_text,
        'session_id': session_id,
        'used_ai': used_ai,
        'context': context,
        'language': language
    })


@app.route('/chatbot/new', methods=['POST'])
@login_required
@role_required('Mother')
def chatbot_new_session():
    """Closes the current active session and redirects to a fresh chatbot."""
    user_id = session['user_id']
    active = get_active_chat_session(user_id)
    if active:
        close_chat_session(active['id'], user_id)
    flash('Started a new conversation.', 'success')
    return redirect(url_for('chatbot_view'))


@app.route('/chatbot/history')
@login_required
@role_required('Mother')
def chatbot_history():
    """Shows a mother's past chat sessions."""
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    all_sessions = get_all_chat_sessions(user_id)
    return render_template(
        'chatbot_history.html',
        user=user,
        sessions=all_sessions
    )


@app.route('/chatbot/history/<int:session_id>')
@login_required
@role_required('Mother')
def chatbot_history_detail(session_id):
    """Shows the full message transcript of one past session."""
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    chat_session = get_chat_session_by_id(session_id, user_id)
    if not chat_session:
        flash('Conversation not found.', 'danger')
        return redirect(url_for('chatbot_history'))
    messages = [dict(m) for m in get_chat_messages(session_id)]
    return render_template(
        'chatbot_history.html',
        user=user,
        sessions=get_all_chat_sessions(user_id),
        active_session=dict(chat_session),
        messages=messages
    )


# CLI command for admin creation
@app.cli.command('create-admin')
def cli_create_admin():
    """Flask CLI command: flask create-admin"""
    from create_admin import create_admin
    create_admin(
        email="admin@momcare.org",
        password="Admin@12345",
        full_name="System Administrator",
        phone="9876543210",
        language="English"
    )

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
