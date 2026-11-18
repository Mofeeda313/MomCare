import os
from app import app
from database import (
    get_user_by_email, get_db, get_mother_profile, 
    get_children_by_mother, format_child_age, calculate_edd_from_lmp
)

client = app.test_client()

print('=== 1. Test Helper Functions ===')
# Test EDD calculation (+280 days)
edd = calculate_edd_from_lmp('2026-01-01')
assert edd == '2026-10-08', f"Expected 2026-10-08, got {edd}"
print('calculate_edd_from_lmp OK!')

# Test Child Age Formatting
age_str = format_child_age('2025-01-01')
assert 'old' in age_str or 'month' in age_str or 'year' in age_str
print(f'format_child_age("2025-01-01") -> {age_str} OK!')

print('\n=== 2. Test Mother Authentication & Initial Profile ===')
# Clean test child and profile records for priya.nair@example.com
priya = get_user_by_email('priya.nair@example.com')
assert priya is not None, "Priya account must exist"
priya_id = priya['id']

conn = get_db()
conn.execute("DELETE FROM child_profiles WHERE mother_id = ?", (priya_id,))
conn.execute("DELETE FROM mother_profiles WHERE user_id = ?", (priya_id,))
conn.commit()

# Login as Priya
client_priya = app.test_client()
res = client_priya.post('/login', data={
    'email': 'priya.nair@example.com',
    'password': 'MotherPassword123!'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Priya' in res.data
client_priya.get('/set-language/English')
print('Priya login OK!')

# View initial profile page
res = client_priya.get('/profile/mother')
assert res.status_code == 200
assert b'Priya' in res.data
assert b'Profile Completeness' in res.data
print('View initial mother profile OK!')

print('\n=== 3. Test Updating Mother Profile ===')
res = client_priya.post('/profile/mother/edit', data={
    'full_name': 'Priya Nair',
    'phone': '9876543211',
    'dob': '1996-04-12',
    'address': '42 Lotus Lane, Bengaluru, Karnataka - 560001',
    'pregnancy_status': 'Pregnant',
    'lmp': '2026-03-01',
    'edd': '', # Left empty to verify automatic EDD calculation
    'blood_group': 'B+',
    'medical_history': 'No major illnesses. Mild morning sickness in first trimester.',
    'emergency_contact_name': 'Ramesh Nair',
    'emergency_contact_phone': '9876500000'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Mother profile successfully updated' in res.data
assert b'42 Lotus Lane' in res.data
assert b'B+' in res.data
# Verify automatic EDD calculation in database: 2026-03-01 + 280 days = 2026-12-06
profile = get_mother_profile(priya_id)
assert profile is not None
assert profile['edd'] == '2026-12-06', f"Expected EDD 2026-12-06, got {profile['edd']}"
assert profile['blood_group'] == 'B+'
assert profile['pregnancy_status'] == 'Pregnant'
print('Mother profile updated & EDD auto-calculated OK!')

print('\n=== 4. Test Registering Children ===')
# Add Child 1 (Male)
res = client_priya.post('/children/add', data={
    'full_name': 'Aarav Nair',
    'dob': '2024-05-10',
    'gender': 'Male',
    'birth_weight': '3.35',
    'blood_group': 'B+',
    'allergies': 'None',
    'medical_history': 'Vaccinations up to date. Healthy birth.'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Aarav Nair' in res.data
assert b'3.35 kg' in res.data
print('Child 1 (Aarav) added successfully!')

# Add Child 2 (Female)
res = client_priya.post('/children/add', data={
    'full_name': 'Diya Nair',
    'dob': '2022-09-15',
    'gender': 'Female',
    'birth_weight': '3.10',
    'blood_group': 'O+',
    'allergies': 'Mild peanut sensitivity',
    'medical_history': 'Normal full-term delivery.'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Diya Nair' in res.data
print('Child 2 (Diya) added successfully!')

# Verify in DB
children = get_children_by_mother(priya_id)
assert len(children) == 2
print(f'Total children for Priya: {len(children)} OK!')

child1_id = [c['id'] for c in children if c['full_name'] == 'Aarav Nair'][0]
child2_id = [c['id'] for c in children if c['full_name'] == 'Diya Nair'][0]

print('\n=== 5. Test Viewing and Editing Child Profile ===')
# View Child 1 details
res = client_priya.get(f'/children/{child1_id}')
assert res.status_code == 200
assert b'Aarav Nair' in res.data
assert b'Vital Birth &amp; Growth Statistics' in res.data or b'Vital Birth & Growth Statistics' in res.data
print('Child 1 detail view OK!')

# Edit Child 1 birth weight
res = client_priya.post(f'/children/{child1_id}/edit', data={
    'full_name': 'Aarav Nair',
    'dob': '2024-05-10',
    'gender': 'Male',
    'birth_weight': '3.50', # updated
    'blood_group': 'B+',
    'allergies': 'Dust allergy', # updated
    'medical_history': 'Healthy and active.'
}, follow_redirects=True)
assert res.status_code == 200
assert b'Aarav Nair' in res.data and b'updated successfully' in res.data
assert b'3.5 kg' in res.data
assert b'Dust allergy' in res.data
print('Child 1 edit and update OK!')

print('\n=== 6. Test Mother Dashboard Integration ===')
res = client_priya.get('/dashboard/mother')
assert res.status_code == 200
assert b'Aarav Nair' in res.data
assert b'Diya Nair' in res.data
assert b'Registered Children' in res.data
assert b'2' in res.data # 2 children
assert b'Pregnant' in res.data
assert b'2026-12-06' in res.data # EDD
print('Mother Dashboard shows profile summary, pregnancy status, EDD, and child cards OK!')

print('\n=== 7. Test Cross-Mother Authorization & Privacy Protection ===')
# Register a second mother (Meera)
res = client.post('/register', data={
    'full_name': 'Meera Patel',
    'email': 'meera.patel@example.com',
    'phone': '9876543290',
    'password': 'MeeraPassword123!',
    'confirm_password': 'MeeraPassword123!',
    'language': 'Hindi',
    'role': 'Mother'
}, follow_redirects=True)

client_meera = app.test_client()
res = client_meera.post('/login', data={
    'email': 'meera.patel@example.com',
    'password': 'MeeraPassword123!'
}, follow_redirects=True)
assert res.status_code == 200

# Meera attempts to view Ananya's child -> MUST BE BLOCKED WITH 403
res_unauth = client_meera.get(f'/children/{child1_id}', follow_redirects=True)
assert res_unauth.status_code == 403
assert b'403 - Access Denied' in res_unauth.data
print('Cross-mother child view blocked with 403 OK!')

# Meera attempts to edit Ananya's child -> MUST BE BLOCKED WITH 403
res_unauth_edit = client_meera.post(f'/children/{child1_id}/edit', data={
    'full_name': 'Hacked Name',
    'dob': '2024-05-10',
    'gender': 'Male'
}, follow_redirects=True)
assert res_unauth_edit.status_code == 403
assert b'403 - Access Denied' in res_unauth_edit.data
print('Cross-mother child edit blocked with 403 OK!')

# Meera's dashboard should have 0 children
res_meera_dash = client_meera.get('/dashboard/mother')
assert res_meera_dash.status_code == 200
assert b'No Children Registered Yet' in res_meera_dash.data
assert b'Aarav Sharma' not in res_meera_dash.data
print("Meera's dashboard is completely isolated with 0 children OK!")

print('\n=== 8. Test Child Profile Deletion ===')
res_delete = client_priya.post(f'/children/{child2_id}/delete', follow_redirects=True)
assert res_delete.status_code == 200
assert b'Diya Nair' in res_delete.data and b'has been removed' in res_delete.data

# Verify 1 child left
children_after = get_children_by_mother(priya_id)
assert len(children_after) == 1
assert children_after[0]['full_name'] == 'Aarav Nair'
print('Child profile deletion and dashboard update OK!')

# Clean up Meera test account
conn = get_db()
conn.execute("DELETE FROM users WHERE email = 'meera.patel@example.com'")
conn.commit()

print('\n>>> ALL PHASE 2 TESTS PASSED SUCCESSFULLY! <<<')
