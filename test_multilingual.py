# -*- coding: utf-8 -*-
"""
test_multilingual.py
Comprehensive automated test suite for MomCare Multilingual Implementation.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import app
from database import get_db, get_user_by_email

PRIYA_EMAIL = "priya.nair@example.com"
PRIYA_PASS = "MotherPassword123!"
RAJESH_EMAIL = "rajesh.kumar@example.com"
RAJESH_PASS = "DoctorPassword123!"
ADMIN_EMAIL = "admin@momcare.org"
ADMIN_PASS = "Admin@12345"

def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

# ---------------------------------------------------------------------------
# Test 1 – Language switcher endpoint updates session and sets cookie
# ---------------------------------------------------------------------------
def test_language_switch_endpoint():
    print("=== 1. Test Language Switcher Endpoint ===")
    with app.test_client() as c:
        for lang in ['Malayalam', 'Hindi', 'Kannada', 'English']:
            r = c.get(f'/set-language/{lang}', follow_redirects=True)
            assert r.status_code == 200, f"Expected 200, got {r.status_code} for {lang}"
            with c.session_transaction() as sess:
                assert sess.get('user_language') == lang, f"Session user_language not set to {lang}"
            print(f"  Switched to {lang} successfully via route OK!")

# ---------------------------------------------------------------------------
# Test 2 – Database persistence for logged-in user
# ---------------------------------------------------------------------------
def test_database_persistence():
    print("\n=== 2. Test Language Database Persistence ===")
    with app.test_client() as c:
        login(c, PRIYA_EMAIL, PRIYA_PASS)
        # Switch to Hindi
        c.get('/set-language/Hindi', follow_redirects=True)
        user = get_user_by_email(PRIYA_EMAIL)
        assert user['language'] == 'Hindi', f"Database user language expected Hindi, got {user['language']}"
        print("  Database language updated to Hindi for logged-in user OK!")

        # Switch back to Malayalam
        c.get('/set-language/Malayalam', follow_redirects=True)
        user = get_user_by_email(PRIYA_EMAIL)
        assert user['language'] == 'Malayalam', f"Database user language expected Malayalam, got {user['language']}"
        print("  Database language restored to Malayalam for logged-in user OK!")

# ---------------------------------------------------------------------------
# Test 3 – Malayalam UI Rendering
# ---------------------------------------------------------------------------
def test_malayalam_ui():
    print("\n=== 3. Test Malayalam UI Rendering ===")
    with app.test_client() as c:
        login(c, PRIYA_EMAIL, PRIYA_PASS)
        c.get('/set-language/Malayalam', follow_redirects=True)
        r = c.get('/dashboard/mother')
        assert r.status_code == 200
        html = r.data.decode('utf-8')
        
        # Check Malayalam keywords
        malayalam_terms = [
            'മാതൃ പരിചരണ പോർട്ടൽ',
            'എന്റെ പ്രൊഫൈൽ',
            'പുറത്തുകടക്കുക',
            'രജിസ്റ്റർ ചെയ്ത കുട്ടികൾ'
        ]
        for term in malayalam_terms:
            assert term in html, f"Malayalam term '{term}' not found in mother dashboard"
        print("  All Malayalam terms verified in Mother Dashboard OK!")

# ---------------------------------------------------------------------------
# Test 4 – Hindi UI Rendering
# ---------------------------------------------------------------------------
def test_hindi_ui():
    print("\n=== 4. Test Hindi UI Rendering ===")
    with app.test_client() as c:
        login(c, PRIYA_EMAIL, PRIYA_PASS)
        c.get('/set-language/Hindi', follow_redirects=True)
        r = c.get('/dashboard/mother')
        assert r.status_code == 200
        html = r.data.decode('utf-8')
        
        hindi_terms = [
            'मातृ देखभाल पोर्टल',
            'मेरी प्रोफ़ाइल',
            'साइन आउट',
            'पंजीकृत बच्चे'
        ]
        for term in hindi_terms:
            assert term in html, f"Hindi term '{term}' not found in mother dashboard"
        print("  All Hindi terms verified in Mother Dashboard OK!")

# ---------------------------------------------------------------------------
# Test 5 – Kannada UI Rendering
# ---------------------------------------------------------------------------
def test_kannada_ui():
    print("\n=== 5. Test Kannada UI Rendering ===")
    with app.test_client() as c:
        login(c, PRIYA_EMAIL, PRIYA_PASS)
        c.get('/set-language/Kannada', follow_redirects=True)
        r = c.get('/dashboard/mother')
        assert r.status_code == 200
        html = r.data.decode('utf-8')
        
        kannada_terms = [
            'ತಾಯಿಯ ಆರೈಕೆ ಪೋರ್ಟಲ್',
            'ನನ್ನ ಪ್ರೊಫೈಲ್',
            'ಸೈನ್ ಔಟ್',
            'ನೋಂದಾಯಿತ ಮಕ್ಕಳು'
        ]
        for term in kannada_terms:
            assert term in html, f"Kannada term '{term}' not found in mother dashboard"
        print("  All Kannada terms verified in Mother Dashboard OK!")

# ---------------------------------------------------------------------------
# Test 6 – Persistence across navigation & login
# ---------------------------------------------------------------------------
def test_persistence_across_navigation():
    print("\n=== 6. Test Persistence Across Navigation & Re-Login ===")
    with app.test_client() as c:
        login(c, PRIYA_EMAIL, PRIYA_PASS)
        c.get('/set-language/Malayalam', follow_redirects=True)

        # Navigate to another page (Profile)
        r_prof = c.get('/profile/mother')
        assert r_prof.status_code == 200
        html_prof = r_prof.data.decode('utf-8')
        assert 'എന്റെ പ്രൊഫൈൽ' in html_prof or 'പ്രൊഫൈൽ' in html_prof
        print("  Language persisted on /profile/mother navigation OK!")

        # Navigate to Chatbot
        r_chat = c.get('/chatbot')
        assert r_chat.status_code == 200
        html_chat = r_chat.data.decode('utf-8')
        assert 'പോഷകാഹാര' in html_chat
        print("  Language persisted on /chatbot navigation OK!")

        # Logout and re-login
        c.get('/logout', follow_redirects=True)
        login(c, PRIYA_EMAIL, PRIYA_PASS)
        with c.session_transaction() as sess:
            assert sess.get('user_language') == 'Malayalam', "Re-login did not restore Malayalam language preference"
        print("  Re-login automatically restores user language preference OK!")

# ---------------------------------------------------------------------------
# Test 7 – Healthcare Worker and Admin Dashboards
# ---------------------------------------------------------------------------
def test_worker_and_admin_dashboards():
    print("\n=== 7. Test Worker and Admin Dashboards ===")
    # Worker in Kannada
    with app.test_client() as c:
        login(c, RAJESH_EMAIL, RAJESH_PASS)
        c.get('/set-language/Kannada', follow_redirects=True)
        r_w = c.get('/dashboard/healthcare-worker')
        assert r_w.status_code == 200
        html_w = r_w.data.decode('utf-8')
        assert 'ಆರೋಗ್ಯ ಕಾರ್ಯಕರ್ತೆ' in html_w or 'ಸ್ವಾಗತ' in html_w
        print("  Healthcare Worker dashboard renders in Kannada OK!")

    # Admin in Hindi
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASS)
        c.get('/set-language/Hindi', follow_redirects=True)
        r_a = c.get('/dashboard/admin')
        assert r_a.status_code == 200
        html_a = r_a.data.decode('utf-8')
        assert 'प्रशासक' in html_a or 'व्यवस्थापक' in html_a or 'नियंत्रण कक्ष' in html_a
        print("  Admin dashboard renders in Hindi OK!")

# ---------------------------------------------------------------------------
# Test 8 – Chatbot Multilingual Questions and Answers
# ---------------------------------------------------------------------------
def test_chatbot_multilingual():
    print("\n=== 8. Test Chatbot Multilingual Questions & Answers ===")
    from chatbot_engine import get_ai_response

    # Malayalam Question
    m_ans, _ = get_ai_response("ഇരുമ്പ് അടങ്ങിയ ഭക്ഷണം ഏതാണ്?", "General Nutrition", "Malayalam")
    assert any(w in m_ans for w in ['ഇരുമ്പ്', 'ഭക്ഷണ', 'വിവരങ്ങൾ']), f"Malayalam response unexpected: {m_ans[:100]}"
    print("  Chatbot understands Malayalam question and replies in Malayalam OK!")

    # Hindi Question
    h_ans, _ = get_ai_response("कैल्शियम युक्त खाद्य पदार्थ कौन से हैं?", "General Nutrition", "Hindi")
    assert any(w in h_ans for w in ['कैल्शियम', 'स्रोत', 'पोषण']), f"Hindi response unexpected: {h_ans[:100]}"
    print("  Chatbot understands Hindi question and replies in Hindi OK!")

    # Kannada Question
    k_ans, _ = get_ai_response("ಕಬ್ಬಿಣಾಂಶವಿರುವ ಆಹಾರ ಯಾವುದು?", "General Nutrition", "Kannada")
    assert any(w in k_ans for w in ['ಕಬ್ಬಿಣ', 'ಆಹಾರ', 'ಮಾಹಿತಿ']), f"Kannada response unexpected: {k_ans[:100]}"
    print("  Chatbot understands Kannada question and replies in Kannada OK!")

# ---------------------------------------------------------------------------
# Test 9 – Default language is English
# ---------------------------------------------------------------------------
def test_default_language():
    print("\n=== 9. Test Default Language is English ===")
    with app.test_client() as c:
        r = c.get('/')
        assert r.status_code == 200
        html = r.data.decode('utf-8')
        assert 'MomCare' in html
        assert 'Transforming maternal health' in html
        print("  Default language is English for anonymous visitor OK!")

# ---------------------------------------------------------------------------
# Run All Tests
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    tests = [
        test_language_switch_endpoint,
        test_database_persistence,
        test_malayalam_ui,
        test_hindi_ui,
        test_kannada_ui,
        test_persistence_across_navigation,
        test_worker_and_admin_dashboards,
        test_chatbot_multilingual,
        test_default_language
    ]

    failed = []
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failed.append((t.__name__, str(e)))
        except Exception as e:
            print(f"  ERROR in {t.__name__}: {e}")
            failed.append((t.__name__, str(e)))

    print()
    if failed:
        print(f">>> {len(failed)} TEST(S) FAILED <<<")
        for name, err in failed:
            print(f"  - {name}: {err}")
        sys.exit(1)
    else:
        print(">>> ALL MULTILINGUAL TESTS PASSED SUCCESSFULLY! <<<")
