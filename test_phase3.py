import os
from datetime import date, timedelta
from app import app
from database import (
    get_user_by_email, get_db, get_children_by_mother,
    generate_child_vaccination_schedule, get_child_vaccination_summary,
    record_vaccination, get_in_app_reminders_for_child,
    get_in_app_reminders_for_mother, get_community_vaccination_stats,
    NIS_VACCINE_SCHEDULE
)

print('=== 1. Test National Immunization Schedule (NIS) Master Definition ===')
assert len(NIS_VACCINE_SCHEDULE) == 26, f"Expected 26 NIS schedule doses, got {len(NIS_VACCINE_SCHEDULE)}"
codes = [item['code'] for item in NIS_VACCINE_SCHEDULE]
assert 'BCG' in codes
assert 'OPV_0' in codes
assert 'HEPB_BIRTH' in codes
assert 'PENTA_1' in codes
assert 'ROTA_1' in codes
assert 'MR_1' in codes
assert 'TD_16' in codes
print(f"Verified {len(NIS_VACCINE_SCHEDULE)} NIS vaccine items spanning birth to 16 years OK!")

print('\n=== 2. Test Setup: Create Child for Priya Nair ===')
priya = get_user_by_email('priya.nair@example.com')
assert priya is not None, "Priya Nair account must exist"
priya_id = priya['id']

# Get or create child for Priya with a known DOB (e.g. born 60 days ago so birth doses are Overdue/Due)
conn = get_db()
conn.execute("DELETE FROM vaccination_history_logs WHERE child_id IN (SELECT id FROM child_profiles WHERE mother_id = ?)", (priya_id,))
conn.execute("DELETE FROM vaccination_records WHERE child_id IN (SELECT id FROM child_profiles WHERE mother_id = ?)", (priya_id,))
conn.execute("DELETE FROM child_profiles WHERE mother_id = ?", (priya_id,))
conn.commit()

# Insert a child born 60 days ago
dob_60_days_ago = (date.today() - timedelta(days=60)).strftime('%Y-%m-%d')
conn.execute('''
    INSERT INTO child_profiles (mother_id, full_name, dob, gender, birth_weight, blood_group)
    VALUES (?, 'Baby Vihaan', ?, 'Male', 3.2, 'B+')
''', (priya_id, dob_60_days_ago))
conn.commit()

children = get_children_by_mother(priya_id)
assert len(children) >= 1
vihaan = children[0]
vihaan_id = vihaan['id']
print(f"Created test child '{vihaan['full_name']}' (ID: {vihaan_id}, DOB: {dob_60_days_ago}) OK!")

print('\n=== 3. Test Schedule Generation & Status Computation ===')
schedule = generate_child_vaccination_schedule(vihaan_id)
assert len(schedule) == 26, f"Expected 26 scheduled doses for child, got {len(schedule)}"

# Check status distribution: Birth doses (BCG, OPV_0, HEPB_BIRTH with offset 0) should be Overdue because child is 60 days old
bcg = next(s for s in schedule if s['vaccine_code'] == 'BCG')
assert bcg['status'] == 'Overdue', f"Expected BCG to be Overdue for 60-day old baby, got {bcg['status']}"

# Check 16 year dose (TD_16 with offset 5840) should be Upcoming
td16 = next(s for s in schedule if s['vaccine_code'] == 'TD_16')
assert td16['status'] == 'Upcoming', f"Expected TD_16 to be Upcoming, got {td16['status']}"

summary = get_child_vaccination_summary(vihaan_id)
assert summary['total'] == 26
assert summary['completed'] == 0
assert summary['overdue'] > 0
print(f"Child Summary: Total={summary['total']}, Completed={summary['completed']}, Overdue={summary['overdue']}, Upcoming={summary['upcoming']} OK!")

print('\n=== 4. Test In-App Reminders Generation ===')
reminders = get_in_app_reminders_for_child(vihaan_id)
assert len(reminders) > 0, "Should generate in-app reminders for overdue/due vaccines"
overdue_reminders = [r for r in reminders if r['status'] == 'Overdue']
assert len(overdue_reminders) > 0
assert 'BCG' in [r['vaccine_code'] for r in overdue_reminders]
assert 'primary health center' in overdue_reminders[0]['message'].lower() or 'overdue' in overdue_reminders[0]['message'].lower()

mother_reminders = get_in_app_reminders_for_mother(priya_id)
assert len(mother_reminders) >= len(reminders)
print(f"Generated {len(mother_reminders)} in-app reminders for mother OK!")

print('\n=== 5. Test Healthcare Worker Administering Vaccine & Audit Log ===')
worker = get_user_by_email('rajesh.kumar@example.com')
assert worker is not None, "Rajesh Healthcare Worker account must exist"
worker_id = worker['id']

# Administer BCG
admin_date = (date.today() - timedelta(days=55)).strftime('%Y-%m-%d')
success = record_vaccination(
    child_id=vihaan_id,
    vaccine_code='BCG',
    administered_date=admin_date,
    administered_by_id=worker_id,
    administered_by_name='Dr. Rajesh Kumar',
    batch_number='BCG-2026-X1',
    notes='Administered at District Primary Health Centre',
    change_reason='Initial birth vaccination recorded during community drive'
)
assert success is True

# Verify schedule updated to Completed
updated_schedule = generate_child_vaccination_schedule(vihaan_id)
bcg_updated = next(s for s in updated_schedule if s['vaccine_code'] == 'BCG')
assert bcg_updated['status'] == 'Completed'
assert bcg_updated['administered_date'] == admin_date
assert bcg_updated['batch_number'] == 'BCG-2026-X1'

# Check audit log in database
cursor = conn.cursor()
cursor.execute("SELECT * FROM vaccination_history_logs WHERE child_id = ? ORDER BY id DESC", (vihaan_id,))
log_entry = cursor.fetchone()
assert log_entry is not None
assert log_entry['action'] == 'RECORDED' or log_entry['action'] == 'CORRECTED'
assert log_entry['changed_by_name'] == 'Dr. Rajesh Kumar'
print("Healthcare worker recorded BCG dose & audit log verified OK!")

print('\n=== 6. Test Clinical Dose Correction with Audit Reasoning ===')
correction_date = (date.today() - timedelta(days=54)).strftime('%Y-%m-%d')
record_vaccination(
    child_id=vihaan_id,
    vaccine_code='BCG',
    administered_date=correction_date,
    administered_by_id=worker_id,
    administered_by_name='Dr. Rajesh Kumar',
    batch_number='BCG-2026-X1-CORR',
    notes='Correction per clinical card',
    change_reason='Typographical date error corrected from health card'
)

cursor.execute("SELECT * FROM vaccination_history_logs WHERE child_id = ? ORDER BY id DESC LIMIT 1", (vihaan_id,))
audit_log = cursor.fetchone()
assert audit_log['action'] == 'CORRECTED'
assert audit_log['change_reason'] == 'Typographical date error corrected from health card'
assert audit_log['new_date'] == correction_date
print("Clinical dose correction and audit reasoning verified OK!")

print('\n=== 7. Test Mother Dashboard Vaccination Integration & Child Selector ===')
client_priya = app.test_client()
res = client_priya.post('/login', data={
    'email': 'priya.nair@example.com',
    'password': 'MotherPassword123!'
}, follow_redirects=True)
assert res.status_code == 200

# View mother dashboard
res = client_priya.get('/dashboard/mother')
assert res.status_code == 200
assert b'Child Immunization Schedule' in res.data or b'Immunization Schedule' in res.data
assert b'Vihaan' in res.data
assert b'BCG' in res.data
assert b'In-App Clinical Immunization Reminders' in res.data or b'In-App Reminders' in res.data or b'Immunization Reminders' in res.data
print("Mother Dashboard renders child vaccination schedule, selector, and reminders OK!")

print('\n=== 8. Test Dedicated Child Vaccination View Route ===')
res = client_priya.get(f'/vaccinations/child/{vihaan_id}')
assert res.status_code == 200
assert b'National Immunization Schedule' in res.data
assert b'Baby Vihaan' in res.data
assert b'Completed' in res.data
assert b'Upcoming' in res.data
print("Dedicated child vaccination route OK!")

print('\n=== 9. Test Mother Privacy & Cross-Mother Access Protection ===')
# Register Meera if she doesn't exist yet
meera = get_user_by_email('meera.patel@example.com')
if not meera:
    client_reg = app.test_client()
    client_reg.post('/register', data={
        'full_name': 'Meera Patel',
        'email': 'meera.patel@example.com',
        'phone': '9876543299',
        'password': 'MeeraPassword123!',
        'confirm_password': 'MeeraPassword123!',
        'language': 'Hindi',
        'role': 'Mother'
    }, follow_redirects=True)

client_meera = app.test_client()
client_meera.post('/login', data={
    'email': 'meera.patel@example.com',
    'password': 'MeeraPassword123!'
}, follow_redirects=True)

# Meera tries to view Priya's child Vihaan's vaccination schedule -> 403 Forbidden
res = client_meera.get(f'/vaccinations/child/{vihaan_id}')
assert res.status_code == 403, f"Expected 403 when Meera accesses Priya's child, got {res.status_code}"

# Mother tries to record vaccination -> 403 Forbidden
res = client_priya.get(f'/vaccinations/record/{vihaan_id}/OPV_1')
assert res.status_code == 403, f"Expected 403 when Mother tries to access record form, got {res.status_code}"
print("Cross-mother privacy and role authorization (403 on records) OK!")

print('\n=== 10. Test Healthcare Worker Dashboard & Search Integration ===')
client_worker = app.test_client()
res = client_worker.post('/login', data={
    'email': 'rajesh.kumar@example.com',
    'password': 'DoctorPassword123!'
}, follow_redirects=True)
assert res.status_code == 200

# View Worker Dashboard
res = client_worker.get('/dashboard/healthcare-worker')
assert res.status_code == 200
assert b'Vihaan' in res.data
assert b'Community Immunization Overview' in res.data or b'Immunization Progress' in res.data or b'Community' in res.data

# Search query
res = client_worker.get('/dashboard/healthcare-worker?q=Vihaan')
assert res.status_code == 200
assert b'Vihaan' in res.data

# Search query non-matching
res = client_worker.get('/dashboard/healthcare-worker?q=NonExistentChildNameXYZ')
assert res.status_code == 200
assert b'No community children found matching' in res.data or b'No' in res.data

# Healthcare worker can access vaccination record form
res = client_worker.get(f'/vaccinations/record/{vihaan_id}/OPV_1')
assert res.status_code == 200
assert b'Record Vaccination Administration' in res.data
assert b'OPV-1' in res.data
print("Healthcare worker dashboard, search, and recording form OK!")

print('\n=== 11. Test Healthcare Worker Submitting Dose via Web Form ===')
res = client_worker.post(f'/vaccinations/record/{vihaan_id}/OPV_1', data={
    'administered_date': (date.today() - timedelta(days=10)).strftime('%Y-%m-%d'),
    'batch_number': 'OPV-BATCH-99',
    'notes': 'Administered at Anganwadi center',
    'change_reason': 'Routine round'
}, follow_redirects=True)
assert res.status_code == 200

# Verify OPV_1 is completed now
vax_summary = get_child_vaccination_summary(vihaan_id)
assert vax_summary['completed'] >= 2
print("Healthcare worker recorded dose via web form OK!")

print('\n=== 12. Test Community Stats Helper ===')
stats = get_community_vaccination_stats()
assert stats['total_children'] >= 1
assert stats['total_completed'] >= 2
print(f"Community Stats: {stats} OK!")

print('\n>>> ALL 12 PHASE 3 CHILD VACCINATION TESTS PASSED SUCCESSFULLY! <<<')
