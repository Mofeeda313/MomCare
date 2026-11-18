import os
from datetime import date, timedelta
from app import app
from database import (
    get_user_by_email, get_db, get_children_by_mother, get_child_by_id,
    calculate_bmi, get_who_growth_benchmark, get_child_age_in_months,
    record_growth_measurement, update_growth_measurement,
    get_growth_measurement_by_id, get_child_growth_history,
    get_latest_growth_measurement, get_community_growth_stats,
    get_all_children_growth_for_workers
)

print('=== 1. Test BMI & Age Math Helper Functions ===')
# BMI calculation: 5.5 kg, 60.0 cm -> 5.5 / (0.6^2) = 15.277... -> 15.3 kg/m²
bmi1 = calculate_bmi(5.5, 60.0)
assert bmi1 == 15.3, f"Expected 15.3, got {bmi1}"

bmi2 = calculate_bmi(12.0, 85.0)
# 12 / (0.85^2) = 16.608... -> 16.6
assert bmi2 == 16.6, f"Expected 16.6, got {bmi2}"

# Invalid inputs
assert calculate_bmi(0, 50) is None
assert calculate_bmi(-5, 50) is None
assert calculate_bmi(5, 0) is None
print('BMI calculations verified OK!')

# Age in months
dob_3m_ago = (date.today() - timedelta(days=95)).strftime('%Y-%m-%d')
m_count = get_child_age_in_months(dob_3m_ago)
assert m_count == 3, f"Expected 3 months, got {m_count}"
print(f'Age in months calculation ({m_count} mos) OK!')

print('\n=== 2. Test WHO Child Growth Standards Benchmarks ===')
# Boy at 6 months
who_boy_6m = get_who_growth_benchmark(6, 'Male')
assert who_boy_6m is not None
assert who_boy_6m['w_med'] == 7.9
assert who_boy_6m['w_min'] == 6.4
assert who_boy_6m['w_max'] == 9.8
assert who_boy_6m['h_med'] == 67.6

# Girl at 12 months
who_girl_12m = get_who_growth_benchmark(12, 'Female')
assert who_girl_12m is not None
assert who_girl_12m['w_med'] == 8.9
assert who_girl_12m['w_min'] == 7.0

# Interpolation test at 4 months
who_boy_4m = get_who_growth_benchmark(4, 'Male')
assert who_boy_4m is not None
assert 6.4 < who_boy_4m['w_med'] < 7.9

# Child > 5 years (61 months) should return None per guideline
who_older = get_who_growth_benchmark(65, 'Male')
assert who_older is None, "WHO benchmarks should return None for children > 60 months"
print('WHO Child Growth Standards benchmarks verified OK!')

print('\n=== 3. Test Setup: Prepare Test Child for Priya Nair ===')
priya = get_user_by_email('priya.nair@example.com')
assert priya is not None
priya_id = priya['id']

conn = get_db()
# Clean previous growth measurements for Priya's children
conn.execute("DELETE FROM growth_history_logs WHERE child_id IN (SELECT id FROM child_profiles WHERE mother_id = ?)", (priya_id,))
conn.execute("DELETE FROM growth_measurements WHERE child_id IN (SELECT id FROM child_profiles WHERE mother_id = ?)", (priya_id,))
conn.commit()

children = get_children_by_mother(priya_id)
dob_child = (date.today() - timedelta(days=120)).strftime('%Y-%m-%d')
if not children:
    conn.execute('''
        INSERT INTO child_profiles (mother_id, full_name, dob, gender, birth_weight, blood_group)
        VALUES (?, 'Baby Vihaan', ?, 'Male', 3.2, 'B+')
    ''', (priya_id, dob_child))
    conn.commit()
    children = get_children_by_mother(priya_id)

child = children[0]
child_id = child['id']
# Ensure child DOB is 120 days ago (4 months old)
conn.execute("UPDATE child_profiles SET dob = ? WHERE id = ?", (dob_child, child_id))
conn.commit()
child = get_child_by_id(child_id)
print(f"Using child '{child['full_name']}' (ID: {child_id}, DOB: {child['dob']}) for tests OK!")

print('\n=== 4. Test Recording Initial Growth Measurement & Audit Log ===')
worker = get_user_by_email('rajesh.kumar@example.com')
assert worker is not None
worker_id = worker['id']

date_m1 = (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')
m1_id = record_growth_measurement(
    child_id=child_id,
    measurement_date=date_m1,
    weight=5.4,
    height=59.5,
    head_circumference=39.8,
    observations='Healthy baby, exclusive breastfeeding, alert and active.',
    recorded_by_id=worker_id,
    recorded_by_name='Dr. Rajesh Kumar',
    change_reason='Routine 2-month physical checkup'
)
assert m1_id > 0

rec1 = get_growth_measurement_by_id(m1_id)
assert rec1 is not None
assert rec1['weight'] == 5.4
assert rec1['height'] == 59.5
assert rec1['bmi'] == 15.3
assert rec1['recorded_by_name'] == 'Dr. Rajesh Kumar'

# Verify audit log
cursor = conn.cursor()
cursor.execute("SELECT * FROM growth_history_logs WHERE measurement_id = ?", (m1_id,))
log1 = cursor.fetchone()
assert log1 is not None
assert log1['action'] == 'RECORDED'
assert log1['new_weight'] == 5.4
print('Initial growth measurement recorded and audit trail verified OK!')

print('\n=== 5. Test Multiple Measurements, Deltas & Growth Velocity ===')
date_m2 = (date.today() - timedelta(days=15)).strftime('%Y-%m-%d')
m2_id = record_growth_measurement(
    child_id=child_id,
    measurement_date=date_m2,
    weight=6.2,
    height=62.5,
    head_circumference=41.2,
    observations='Consistent developmental milestones. Good weight gain.',
    recorded_by_id=worker_id,
    recorded_by_name='Dr. Rajesh Kumar',
    change_reason='Routine 3.5-month physical checkup'
)

history = get_child_growth_history(child_id)
assert len(history) == 2, f"Expected 2 measurement records, got {len(history)}"

# Baseline check
assert history[0]['weight_delta_str'] == 'Baseline'

# Second visit deltas
m2 = history[1]
assert m2['weight_delta'] == 0.8, f"Expected weight gain of +0.8 kg, got {m2['weight_delta']}"
assert m2['weight_delta_str'] == '+0.8 kg'
assert m2['height_delta'] == 3.0, f"Expected height gain of +3.0 cm, got {m2['height_delta']}"
assert m2['height_delta_str'] == '+3.0 cm'
assert m2['head_circ_delta'] == 1.4
assert m2['days_since_prev'] == 45
assert m2['needs_followup'] is False
assert 'Normal Growth' in m2['who_status'] or 'WHO' in m2['who_status']

latest = get_latest_growth_measurement(child_id)
assert latest['id'] == m2_id
assert latest['weight'] == 6.2
print(f"Growth deltas verified: Weight={m2['weight_delta_str']}, Height={m2['height_delta_str']}, Status={m2['who_status']} OK!")

print('\n=== 6. Test Correcting Growth Measurement with Clinical Audit Reason ===')
success_update = update_growth_measurement(
    measurement_id=m2_id,
    measurement_date=date_m2,
    weight=6.25,
    height=62.8,
    head_circumference=41.3,
    observations='Updated per calibrated pediatric clinical scale reading.',
    changed_by_id=worker_id,
    changed_by_name='Dr. Rajesh Kumar',
    change_reason='Corrected scale tare offset by +0.05 kg per clinical card'
)
assert success_update is True

# Check record updated
rec2_updated = get_growth_measurement_by_id(m2_id)
assert rec2_updated['weight'] == 6.25
assert rec2_updated['height'] == 62.8

# Check audit log contains correction
cursor.execute("SELECT * FROM growth_history_logs WHERE measurement_id = ? ORDER BY id DESC LIMIT 1", (m2_id,))
audit_entry = cursor.fetchone()
assert audit_entry is not None
assert audit_entry['action'] == 'CORRECTED'
assert audit_entry['previous_weight'] == 6.2
assert audit_entry['new_weight'] == 6.25
assert audit_entry['change_reason'] == 'Corrected scale tare offset by +0.05 kg per clinical card'
print('Clinical correction and audit log verified OK!')

print('\n=== 7. Test Mother Dashboard & Growth View Integration ===')
client_priya = app.test_client()
client_priya.post('/login', data={
    'email': 'priya.nair@example.com',
    'password': 'MotherPassword123!'
}, follow_redirects=True)

# Mother Dashboard contains Growth Monitoring section & links
res = client_priya.get('/dashboard/mother')
assert res.status_code == 200
assert b'Child Growth &amp; Development Monitoring' in res.data or b'Child Growth' in res.data
assert b'Current Weight' in res.data
assert b'Pediatric BMI' in res.data
assert b'6.25 kg' in res.data

# Mother views dedicated growth curves & records page
res_growth = client_priya.get(f'/growth/child/{child_id}')
assert res_growth.status_code == 200
assert b'Interactive Child Growth Curves' in res_growth.data
assert b'Complete Growth Measurement History' in res_growth.data
assert b'6.25 kg' in res_growth.data
assert b'Weight (kg)' in res_growth.data
assert b'Height (cm)' in res_growth.data
assert b'WHO Child Growth Standards' in res_growth.data
print('Mother dashboard and growth curves view verified OK!')

print('\n=== 8. Test Cross-Mother Access Control & Privacy Protection ===')
# Meera tries to view Priya's child growth records -> 403 Forbidden
client_meera = app.test_client()
client_meera.post('/login', data={
    'email': 'meera.patel@example.com',
    'password': 'MeeraPassword123!'
}, follow_redirects=True)

res_unauth = client_meera.get(f'/growth/child/{child_id}')
assert res_unauth.status_code == 403, f"Expected 403 when Meera accesses Priya's child growth, got {res_unauth.status_code}"

# Mother tries to access healthcare worker growth recording form -> 403 Forbidden
res_record_unauth = client_priya.get(f'/growth/record/{child_id}')
assert res_record_unauth.status_code == 403

# Mother tries to access healthcare worker growth edit form -> 403 Forbidden
res_edit_unauth = client_priya.get(f'/growth/edit/{m1_id}')
assert res_edit_unauth.status_code == 403

# Mother tries to access community directory -> 403 Forbidden
res_dir_unauth = client_priya.get('/growth/community')
assert res_dir_unauth.status_code == 403
print('Role-based security & cross-mother 403 access control verified OK!')

print('\n=== 9. Test Healthcare Worker Dashboard, Community Directory & Recording ===')
client_worker = app.test_client()
client_worker.post('/login', data={
    'email': 'rajesh.kumar@example.com',
    'password': 'DoctorPassword123!'
}, follow_redirects=True)

# Worker Dashboard shows Growth Monitoring section & stat card
res_worker = client_worker.get('/dashboard/healthcare-worker')
assert res_worker.status_code == 200
assert b'Growth Monitored' in res_worker.data
assert b'Community Child Growth' in res_worker.data or b'Growth Monitoring' in res_worker.data

# Worker Community Growth Directory
res_comm = client_worker.get('/growth/community')
assert res_comm.status_code == 200
assert b'Community Child Growth Monitoring' in res_comm.data
assert b'Vihaan' in res_comm.data
assert b'6.25 kg' in res_comm.data

# Search query
res_search = client_worker.get('/growth/community?q=Vihaan')
assert res_search.status_code == 200
assert b'Vihaan' in res_search.data

# Worker logs third measurement via web form
date_m3 = date.today().strftime('%Y-%m-%d')
res_post_growth = client_worker.post(f'/growth/record/{child_id}', data={
    'measurement_date': date_m3,
    'weight': '6.9',
    'height': '64.5',
    'head_circumference': '42.0',
    'observations': 'Growing steadily, smiles and tracks objects.'
}, follow_redirects=True)
assert res_post_growth.status_code == 200

# Verify third measurement was added
new_history = get_child_growth_history(child_id)
assert len(new_history) == 3
assert new_history[-1]['weight'] == 6.9
print('Healthcare worker dashboard, community directory, and web form recording verified OK!')

print('\n=== 10. Test Admin Dashboard Growth Metrics Integration ===')
client_admin = app.test_client()
client_admin.post('/login', data={
    'email': 'admin@momcare.org',
    'password': 'Admin@12345'
}, follow_redirects=True)

res_admin = client_admin.get('/dashboard/admin')
assert res_admin.status_code == 200
assert b'Clinical Governance &amp; Pediatric Growth Reports' in res_admin.data or b'Growth Reports' in res_admin.data
assert b'Measurements Recorded' in res_admin.data

# Community growth stats check
stats = get_community_growth_stats()
assert stats['children_measured'] >= 1
assert stats['total_records'] >= 3
print(f'Admin dashboard and growth stats ({stats}) verified OK!')

print('\n>>> ALL 10 PHASE 4 CHILD GROWTH MONITORING TESTS PASSED SUCCESSFULLY! <<<')
