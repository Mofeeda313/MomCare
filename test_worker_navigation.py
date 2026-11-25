"""
Test Suite: Healthcare Worker Navigation Bar, Hamburger Sidebar Menu & Hero Section Verification
Verifies consistent navigation and hero redesign across Healthcare Worker pages in MomCare.
"""
from app import app
import re
import sqlite3

def run_tests():
    client = app.test_client()

    # Reset language
    conn = sqlite3.connect('momcare.db')
    c = conn.cursor()
    c.execute("UPDATE users SET language = 'English'")
    conn.commit()
    conn.close()

    # Login as Healthcare Worker
    login_res = client.post('/login', data={
        'email': 'rajesh.kumar@example.com',
        'password': 'DoctorPassword123!'
    }, follow_redirects=True)
    assert login_res.status_code == 200, f"Login failed: {login_res.status_code}"

    # 1. Test worker dashboard
    worker_res = client.get('/dashboard/healthcare-worker')
    assert worker_res.status_code == 200, f"Worker dashboard failed: {worker_res.status_code}"
    worker_html = worker_res.get_data(as_text=True)

    # Check hamburger button and sidebar drawer
    assert 'id="sidebar-toggle"' in worker_html, "sidebar-toggle not in worker dashboard"
    assert 'id="momcare-sidebar"' in worker_html, "momcare-sidebar not in worker dashboard"
    assert 'healthcare-worker-hero.png' in worker_html, "hero image not in worker dashboard"
    assert 'Child Growth Monitoring' in worker_html, "Child Growth Monitoring not in sidebar"
    assert 'Immunization Management' in worker_html, "Immunization Management not in sidebar"
    assert 'Registered Mothers' in worker_html, "Registered Mothers not in sidebar"
    assert ('Antenatal Checkups &amp; Field Home Visits' in worker_html or 
            'Antenatal Checkups & Field Home Visits' in worker_html), "Antenatal Checkups not in sidebar"
    assert 'static/js/main.js' in worker_html, "main.js not in worker dashboard"

    # Check only one 'Welcome back'
    wb_count = len(re.findall(r'Welcome back', worker_html, re.IGNORECASE))
    print(f"Count of Welcome back: {wb_count}")
    assert wb_count == 1, f"Expected 1 Welcome back, found {wb_count}"

    # 2. Test community growth directory page
    growth_res = client.get('/growth/community')
    assert growth_res.status_code == 200, f"Growth community failed: {growth_res.status_code}"
    growth_html = growth_res.get_data(as_text=True)

    assert 'id="sidebar-toggle"' in growth_html, "sidebar-toggle not in community growth"
    assert 'id="momcare-sidebar"' in growth_html, "momcare-sidebar not in community growth"
    assert 'static/js/main.js' in growth_html, "main.js not in community growth"

    print("============================================================")
    print("=== All Healthcare Worker Navigation & Hero Tests Passed! ===")
    print("============================================================")

if __name__ == '__main__':
    run_tests()
