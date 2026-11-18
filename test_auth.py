from app import app
from database import get_user_by_email, get_db

# Clean up test users so test runs cleanly every time
conn = get_db()
conn.execute("DELETE FROM users WHERE email IN ('priya.nair@example.com', 'rajesh.kumar@example.com', 'fakeadmin@example.com')")
conn.commit()

client = app.test_client()

print('=== 1. Test Home & Health ===')
res = client.get('/')
assert res.status_code == 200
assert b'MomCare' in res.data
assert b'Login' in res.data
assert b'Register' in res.data
print('Home page OK!')

res = client.get('/health')
assert res.status_code == 200
assert res.get_json()['status'] == 'healthy'
print('Health check OK!')

print('\n=== 2. Test Mother Registration ===')
res = client.post('/register', data={
    'full_name': 'Priya Nair',
    'email': 'priya.nair@example.com',
    'phone': '9876543211',
    'password': 'MotherPassword123!',
    'confirm_password': 'MotherPassword123!',
    'language': 'Malayalam',
    'role': 'Mother'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Registration successful' in res.data
print('Mother registration OK!')

# Verify password is hashed, NOT plaintext
priya = get_user_by_email('priya.nair@example.com')
assert priya is not None
assert priya['password_hash'] != 'MotherPassword123!'
assert priya['password_hash'].startswith('scrypt:') or priya['password_hash'].startswith('pbkdf2:')
print('Password securely hashed verified!')

print('\n=== 3. Test Healthcare Worker Registration ===')
res = client.post('/register', data={
    'full_name': 'Dr. Rajesh Kumar',
    'email': 'rajesh.kumar@example.com',
    'phone': '9876543212',
    'password': 'DoctorPassword123!',
    'confirm_password': 'DoctorPassword123!',
    'language': 'Kannada',
    'role': 'Healthcare Worker'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Registration successful' in res.data
print('Healthcare Worker registration OK!')

print('\n=== 4. Test Duplicate Email Prevention ===')
res = client.post('/register', data={
    'full_name': 'Duplicate User',
    'email': 'priya.nair@example.com',
    'phone': '9876543299',
    'password': 'Password123!',
    'confirm_password': 'Password123!',
    'language': 'English',
    'role': 'Mother'
}, follow_redirects=False)
assert res.status_code == 400
assert b'already exists' in res.data
print('Duplicate email rejected OK!')

print('\n=== 5. Test Rejecting Public Admin Registration ===')
res = client.post('/register', data={
    'full_name': 'Fake Admin',
    'email': 'fakeadmin@example.com',
    'phone': '9876543299',
    'password': 'Password123!',
    'confirm_password': 'Password123!',
    'language': 'English',
    'role': 'Admin'
}, follow_redirects=False)
assert res.status_code == 400
assert b'Invalid role selected' in res.data
print('Public Admin registration blocked OK!')

print('\n=== 6. Test Mother Login & Role Authorization ===')
client_mother = app.test_client()
res = client_mother.post('/login', data={
    'email': 'priya.nair@example.com',
    'password': 'MotherPassword123!'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Priya Nair' in res.data
assert (b'Welcome' in res.data or 'സ്വാഗതം'.encode('utf-8') in res.data)
assert (b'Mother Care Portal' in res.data or 'മാതൃ പരിചരണ പോർട്ടൽ'.encode('utf-8') in res.data)
print('Mother logged in and routed to Mother Dashboard OK!')

# Try accessing Admin Dashboard as Mother -> receives dedicated 403 Access Denied page
res_unauth = client_mother.get('/dashboard/admin', follow_redirects=True)
assert res_unauth.status_code == 403
assert b'403 - Access Denied' in res_unauth.data
assert b'Return to My Dashboard' in res_unauth.data
print('Mother blocked from Admin Dashboard with dedicated 403 page OK!')

# Test login with stale ?next=/dashboard/admin ignores forbidden destination
client_mother_stale = app.test_client()
res_stale = client_mother_stale.post('/login?next=/dashboard/admin', data={
    'email': 'priya.nair@example.com',
    'password': 'MotherPassword123!'
}, follow_redirects=True)
assert res_stale.status_code == 200
assert (b'Mother Care Portal' in res_stale.data or 'മാതൃ പരിചരണ പോർട്ടൽ'.encode('utf-8') in res_stale.data)
assert b'Access denied' not in res_stale.data
print('Mother login with stale next param safely goes to Mother Dashboard without errors OK!')

print('\n=== 7. Test Healthcare Worker Login & Patient View ===')
client_worker = app.test_client()
res = client_worker.post('/login', data={
    'email': 'rajesh.kumar@example.com',
    'password': 'DoctorPassword123!'
}, follow_redirects=True)
assert res.status_code == 200
assert (b'Community Healthcare Portal' in res.data or b'Healthcare Worker Portal' in res.data or 'ಆರೋಗ್ಯ ಕಾರ್ಯಕರ್ತರ ಪೋರ್ಟಲ್'.encode('utf-8') in res.data)
assert b'Priya Nair' in res.data
print('Healthcare Worker logged in, routed to Worker Dashboard, sees Priya Nair OK!')

# Try accessing Admin Dashboard as Worker
res_unauth2 = client_worker.get('/dashboard/admin', follow_redirects=True)
assert res_unauth2.status_code == 403
assert b'403 - Access Denied' in res_unauth2.data
print('Worker blocked from Admin Dashboard with dedicated 403 page OK!')

print('\n=== 8. Test Admin Login & Superuser View ===')
client_admin = app.test_client()
res = client_admin.post('/login', data={
    'email': 'admin@momcare.org',
    'password': 'Admin@12345'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Administrator Control Panel' in res.data or b'Control Panel' in res.data
assert b'Priya Nair' in res.data
assert b'Dr. Rajesh Kumar' in res.data
assert b'admin@momcare.org' in res.data
print('Admin logged in, routed to Admin Dashboard, sees all users OK!')

print('\n=== 9. Test Logout ===')
res_logout = client_admin.get('/logout', follow_redirects=True)
assert res_logout.status_code == 200
assert b'logged out' in res_logout.data
# Verify dashboard is no longer accessible
res_protected = client_admin.get('/dashboard', follow_redirects=True)
assert b'Please log in' in res_protected.data
print('Logout and session protection OK!')

print('\n>>> ALL 9 AUTH & DASHBOARD TESTS PASSED SUCCESSFULLY! <<<')
