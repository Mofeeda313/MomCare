import os
from app import app
from database import get_user_by_email, get_children_by_mother

client = app.test_client()

# Login as Priya Nair
priya = get_user_by_email('priya.nair@example.com')
assert priya is not None
children = get_children_by_mother(priya['id'])
assert len(children) > 0
child_id = children[0]['id']

client.post('/login', data={
    'email': 'priya.nair@example.com',
    'password': 'MotherPassword123!'
}, follow_redirects=True)

print('=== 1. Test Default / All Schedule View ===')
res = client.get(f'/vaccinations/child/{child_id}')
assert res.status_code == 200
html = res.data.decode('utf-8')

# Verify all 5 filter tabs exist with data-filter attribute
assert 'data-filter="all"' in html
assert 'data-filter="overdue"' in html
assert 'data-filter="due"' in html
assert 'data-filter="upcoming"' in html
assert 'data-filter="completed"' in html
print('All 5 filter tabs present with data-filter attributes OK!')

# Verify data-status attribute on rows
assert 'data-status="overdue"' in html or 'data-status="due"' in html
assert 'data-status="upcoming"' in html
print('Dose rows rendered with data-status attributes for instant client filtering OK!')

# Verify JavaScript client-side handler is included
assert 'document.addEventListener(\'DOMContentLoaded\'' in html
assert 'e.preventDefault()' in html
assert 'applyFilter' in html
assert 'window.history.replaceState' in html
print('Client-side zero-reload, zero-jump filtering script present OK!')

print('\n=== 2. Test Direct Server Filter Request (Overdue) ===')
res_overdue = client.get(f'/vaccinations/child/{child_id}?status=overdue')
assert res_overdue.status_code == 200
html_overdue = res_overdue.data.decode('utf-8')

# Overdue tab active
assert 'data-filter="overdue"' in html_overdue
assert 'class="vax-filter-pill active"' in html_overdue or 'vax-filter-pill active' in html_overdue

# Non-overdue rows hidden on initial server render
assert 'display: none;' in html_overdue
print('Direct ?status=overdue request correctly renders with overdue tab active OK!')

print('\n=== 3. Test Empty State Handling for Filters with Zero Doses ===')
res_completed = client.get(f'/vaccinations/child/{child_id}?status=completed')
assert res_completed.status_code == 200
html_completed = res_completed.data.decode('utf-8')
assert 'id="vax-empty-filter"' in html_completed
assert 'id="vax-show-all-btn"' in html_completed
print('Empty state handling and "View All Doses" button verified OK!')

print('\n>>> ALL VACCINATION FILTER TAB TESTS PASSED SUCCESSFULLY! <<<')

