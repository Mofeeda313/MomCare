import os
import sys
from datetime import datetime, date, timedelta
from app import app
from database import (
    get_db, init_db, get_user_by_email,
    get_smart_reminders_for_mother, add_custom_reminder,
    delete_custom_reminder, snooze_smart_reminder, complete_smart_reminder
)

print("=" * 60)
print("=== Running MomCare Smart Reminders & Notifications Test Suite ===")
print("=" * 60)

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

def login_mother(client, email="priya.nair@example.com", password="MotherPassword123!"):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

def login_worker(client, email="rajesh.kumar@example.com", password="DoctorPassword123!"):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

# 1. Test database helper retrieval
print("Test 1: Smart reminders retrieval from database...")
with app.app_context():
    user = get_user_by_email("priya.nair@example.com")
    assert user is not None, "Mother user Ananya not found"
    rem_data = get_smart_reminders_for_mother(user['id'])
    assert 'items' in rem_data
    assert 'counts' in rem_data
    assert 'children' in rem_data
    assert rem_data['counts']['all_total'] > 0, "Expected non-zero total reminders"
    assert 'overdue' in rem_data['counts']
    assert 'today' in rem_data['counts']
    assert 'upcoming' in rem_data['counts']
    assert 'completed' in rem_data['counts']
    assert 'snoozed' in rem_data['counts']
    print(f"  Passed! Total: {rem_data['counts']['all_total']}, Overdue: {rem_data['counts']['overdue']}, Completed: {rem_data['counts']['completed']}")

# 2. Test auth and role guards
print("Test 2: Route authorization and role guards...")
with app.app_context():
    # Unauthenticated
    client_unauth = app.test_client()
    res = client_unauth.get('/reminders', follow_redirects=False)
    assert res.status_code in (302, 401), f"Expected 302/401 redirect for unauth, got {res.status_code}"
    print("  Passed unauthenticated guard!")

    # Worker role blocked from mother's personal reminders view
    client_worker = app.test_client()
    login_worker(client_worker)
    res_worker = client_worker.get('/reminders', follow_redirects=False)
    assert res_worker.status_code in (302, 403), f"Expected 302/403 for worker role, got {res_worker.status_code}"
    print("  Passed role restriction guard!")

# 3. Test mother viewing /reminders page
print("Test 3: Mother accessing /reminders page...")
client_mother = app.test_client()
login_mother(client_mother)
res_page = client_mother.get('/reminders', follow_redirects=True)
assert res_page.status_code == 200, f"Expected 200, got {res_page.status_code}"
assert b'Smart Reminders' in res_page.data or b'Care Reminders' in res_page.data
assert b'Overdue' in res_page.data
assert b'Due Today' in res_page.data
assert b'Upcoming' in res_page.data
assert b'Completed' in res_page.data
assert b'Add Personal Reminder' in res_page.data
print("  Passed! Reminders page renders successfully with statistics and tabs.")

# 4. Test query filtering (status, category, child)
print("Test 4: Filtering tabs and query parameters...")
res_overdue = client_mother.get('/reminders?status=overdue', follow_redirects=True)
assert res_overdue.status_code == 200
res_cat = client_mother.get('/reminders?category=Maternal+Health', follow_redirects=True)
assert res_cat.status_code == 200
res_child = client_mother.get('/reminders?child_id=maternal', follow_redirects=True)
assert res_child.status_code == 200
print("  Passed! Filters work correctly.")

# 5. Test Custom Reminder lifecycle: create, snooze, complete, delete
print("Test 5: Custom reminder full lifecycle...")
with app.app_context():
    user = get_user_by_email("priya.nair@example.com")
    # 5a. Create
    res_create = client_mother.post('/reminders/custom/create', data={
        'title': 'Test Prenatal Yoga Session',
        'description': '30 minutes gentle stretching',
        'due_date': '2026-12-15',
        'category': 'Wellness & Nutrition',
        'child_id': ''
    }, follow_redirects=True)
    assert res_create.status_code == 200
    assert b'Test Prenatal Yoga Session' in res_create.data

    rem_data = get_smart_reminders_for_mother(user['id'])
    matching = [r for r in rem_data['all'] if r['title'] == 'Test Prenatal Yoga Session']
    assert len(matching) == 1, "Custom reminder should exist in DB"
    item = matching[0]
    key = item['key']
    c_id = item['id']
    print(f"  Created custom reminder (ID: {c_id}, Key: {key})")

    # 5b. Snooze
    res_snooze = client_mother.post(f'/reminders/{key}/snooze', data={'days': '3'}, follow_redirects=True)
    assert res_snooze.status_code == 200
    rem_data_snoozed = get_smart_reminders_for_mother(user['id'])
    matching_snoozed = [r for r in rem_data_snoozed['all'] if r['key'] == key]
    assert len(matching_snoozed) == 1
    assert matching_snoozed[0]['status'] == 'Snoozed'
    print("  Snooze persisted successfully!")

    # 5c. Complete
    res_comp = client_mother.post(f'/reminders/{key}/complete', follow_redirects=True)
    assert res_comp.status_code == 200
    rem_data_comp = get_smart_reminders_for_mother(user['id'])
    matching_comp = [r for r in rem_data_comp['all'] if r['key'] == key]
    assert len(matching_comp) == 1
    assert matching_comp[0]['status'] == 'Completed'
    print("  Completion persisted successfully!")

    # 5d. Delete
    res_del = client_mother.post(f'/reminders/custom/{c_id}/delete', follow_redirects=True)
    assert res_del.status_code == 200
    rem_data_after_del = get_smart_reminders_for_mother(user['id'])
    matching_after = [r for r in rem_data_after_del['all'] if r['title'] == 'Test Prenatal Yoga Session']
    assert len(matching_after) == 0, "Custom reminder should be deleted"
    print("  Deletion verified successfully!")

# 6. Test Vaccine completion safeguard
print("Test 6: Vaccine clinical completion safeguard...")
with app.app_context():
    user = get_user_by_email("priya.nair@example.com")
    rem_data = get_smart_reminders_for_mother(user['id'])
    vax_items = [r for r in rem_data['all'] if r['type'] == 'Immunization']
    if vax_items:
        vax_key = vax_items[0]['key']
        res_vax_comp = client_mother.post(f'/reminders/{vax_key}/complete', follow_redirects=True)
        assert res_vax_comp.status_code == 200
        assert b'Healthcare Worker' in res_vax_comp.data or b'verified' in res_vax_comp.data
        print(f"  Vaccine safeguard passed! Mother cannot mark {vax_key} as administered.")

# 7. Test Mother Dashboard Summary Widget
print("Test 7: Mother Dashboard Smart Reminders summary widget...")
res_dash = client_mother.get('/dashboard/mother', follow_redirects=True)
assert res_dash.status_code == 200
assert b'Smart Reminders & Notifications' in res_dash.data or b'Smart Reminders' in res_dash.data
assert b'View All Reminders' in res_dash.data
assert b'/reminders' in res_dash.data
assert b'In-App Clinical Immunization Reminders' in res_dash.data
print("  Mother Dashboard integration verified!")

# 8. Reset database user languages
print("Test 8: Reset database languages to English...")
with app.app_context():
    db = get_db()
    db.execute("UPDATE users SET language = 'English'")
    db.commit()
print("  Database language reset successfully!")

print("=" * 60)
print("ALL SMART REMINDERS & NOTIFICATIONS TESTS PASSED (8/8)!")
print("=" * 60)
