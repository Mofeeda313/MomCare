"""
Test Suite: Mother Pages Navigation Bar & Hamburger Sidebar Menu Verification
Verifies consistent navigation across all Mother pages in MomCare.
"""
from app import app
from database import get_user_by_email, get_children_by_mother, get_db

def test_mother_navigation():
    client = app.test_client()
    
    # 1. Log in as Mother Priya Nair
    login_res = client.post('/login', data={
        'email': 'priya.nair@example.com',
        'password': 'MotherPassword123!'
    }, follow_redirects=True)
    assert login_res.status_code == 200

    mother = get_user_by_email('priya.nair@example.com')
    children = get_children_by_mother(mother['id'])
    child_id = children[0]['id'] if children else 1

    mother_routes = [
        ('/profile/mother', 'Mother Profile'),
        ('/profile/mother/edit', 'Mother Profile Edit'),
        ('/chatbot', 'Nutrition Chatbot'),
        ('/chatbot/history', 'Chatbot History'),
        ('/dashboard/mother', 'Mother Dashboard'),
        ('/reminders', 'Smart Reminders'),
        (f'/growth/child/{child_id}', 'Child Growth Monitoring'),
        (f'/vaccinations/child/{child_id}', 'Child Vaccination Schedule')
    ]

    expected_features = [
        b'#overview',
        b'/profile/mother',
        b'#registered-children-section',
        b'#growth-monitoring-section',
        b'#vaccination-management-section',
        b'#wellness-section',
        b'/reminders',
        b'/chatbot',
        b'#community-section',
        b'#consultation-section'
    ]

    print("\n============================================================")
    print("=== Testing Mother Navigation Bar & Hamburger Menu on Pages ===")
    print("============================================================")

    for route, page_name in mother_routes:
        res = client.get(route, follow_redirects=True)
        assert res.status_code == 200, f"Page {page_name} ({route}) returned {res.status_code}"
        
        # 1. Verify hamburger button exists
        assert b'id="sidebar-toggle"' in res.data, f"Missing hamburger button #sidebar-toggle on {page_name}"
        assert b'btn-hamburger' in res.data, f"Missing btn-hamburger class on {page_name}"
        
        # 2. Verify sidebar drawer exists
        assert b'id="momcare-sidebar"' in res.data, f"Missing #momcare-sidebar on {page_name}"
        assert b'id="sidebar-backdrop"' in res.data, f"Missing #sidebar-backdrop on {page_name}"
        
        # 3. Verify MomCare logo exists
        assert b'MomCare' in res.data, f"Missing MomCare logo on {page_name}"
        
        # 4. Verify language picker exists
        assert b'language-picker' in res.data or b'lang=' in res.data or b'data-lang=' in res.data, f"Missing language picker on {page_name}"
        
        # 5. Verify Mother role badge and user greeting
        assert b'badge-mother' in res.data, f"Missing Mother role badge on {page_name}"
        assert b'Priya' in res.data, f"Missing user greeting on {page_name}"
        
        # 6. Verify all 10 Mother Dashboard feature links exist in the navigation sidebar
        for feat in expected_features:
            assert feat in res.data, f"Missing sidebar link {feat.decode()} on {page_name}"

        # 7. Verify main.js script is included
        assert b'main.js' in res.data, f"Missing main.js script tag on {page_name}"

        print(f"  [PASSED] {page_name} ({route}): Hamburger menu, sidebar drawer, and all 10 features verified.")

    # Reset languages to English
    with app.app_context():
        db = get_db()
        db.execute("UPDATE users SET language = 'English'")
        db.commit()
    print("============================================================")
    print("ALL MOTHER NAVIGATION TESTS PASSED SUCCESSFULLY!")
    print("============================================================")

if __name__ == '__main__':
    test_mother_navigation()
