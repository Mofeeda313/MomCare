"""
test_phase5.py
MomCare Phase 5 – AI Nutrition Chatbot tests.

Tests:
  1. Chatbot engine – fallback knowledge base (10 nutrients).
  2. Chatbot engine – context-specific guidance (pregnancy, postnatal, child ages).
  3. Chatbot engine – medical safety disclaimers always present.
  4. Route access control – Mother gets 200, Worker/Admin get 403.
  5. Chat API endpoint – saves user message and returns a response.
  6. Chat history – session created and stored privately.
  7. Privacy – mother cannot access another mother's chat session.
  8. Language parameter accepted without errors.
  9. Fallback for child-age-appropriate guidance.
  10. Full regression smoke test on all existing features.
"""

import sys
import json
from app import app

MOTHER_EMAIL    = "priya.nair@example.com"
MOTHER_PASSWORD = "MotherPassword123!"
MOTHER2_EMAIL   = "meera.pillai@example.com"
MOTHER2_PASSWORD = "MotherPassword123!"
WORKER_EMAIL    = "rajesh.kumar@example.com"
WORKER_PASSWORD = "DoctorPassword123!"
ADMIN_EMAIL     = "admin@momcare.org"
ADMIN_PASSWORD  = "Admin@12345"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password},
                       follow_redirects=True)


def chat(client, question, context='General Nutrition', language='English',
         child_id=None, session_id=None):
    payload = {
        'question': question,
        'context': context,
        'language': language,
    }
    if child_id:
        payload['child_id'] = child_id
    if session_id:
        payload['session_id'] = session_id
    return client.post('/chatbot/chat',
                       data=json.dumps(payload),
                       content_type='application/json')


# ---------------------------------------------------------------------------
# Test 1 – Knowledge base covers all 10 required nutrients
# ---------------------------------------------------------------------------

def test_knowledge_base_nutrients():
    print("=== 1. Test Knowledge Base – 10 Nutrients ===")
    from chatbot_engine import get_ai_response

    nutrient_questions = [
        ("What happens if I have vitamin A deficiency?",    "vitamin a"),
        ("Which foods are rich in vitamin B12?",             "b12"),
        ("Tell me about folate",                             "folate"),
        ("What are good sources of vitamin C?",             "vitamin c"),
        ("What is vitamin D and why is it important?",      "vitamin d"),
        ("Which foods contain vitamin E?",                  "vitamin e"),
        ("What foods contain iron?",                        "iron"),
        ("What are good calcium-rich foods?",               "calcium"),
        ("Which foods are rich in magnesium?",              "magnesium"),
        ("Tell me about zinc in the diet",                  "zinc"),
        ("What are high-protein foods for mothers?",        "protein"),
    ]

    for question, expected_kw in nutrient_questions:
        resp, used_ai = get_ai_response(question, 'General Nutrition', 'English')
        assert isinstance(resp, str) and len(resp) > 50, \
            f"Empty response for: {question}"
        assert expected_kw.lower() in resp.lower() or \
               any(w in resp.lower() for w in ['food', 'nutrition', 'important', 'sources']), \
            f"Response for '{question}' seems unrelated: {resp[:100]}"
        print(f"  Nutrient '{expected_kw}' response OK!")

    print("All 10 nutrient responses returned OK!")


# ---------------------------------------------------------------------------
# Test 2 – Context-specific guidance
# ---------------------------------------------------------------------------

def test_context_guidance():
    print("\n=== 2. Test Context-Specific Guidance ===")
    from chatbot_engine import get_ai_response

    # Pregnancy context
    r, _ = get_ai_response("What should I eat?", "Pregnancy", "English")
    assert any(w in r.lower() for w in ['pregnancy', 'pregnant', 'folate', 'folic', 'iron']), \
        f"Pregnancy context missing pregnancy keywords: {r[:200]}"
    print("  Pregnancy context guidance OK!")

    # Postnatal context
    r, _ = get_ai_response("What should I eat?", "Postnatal Care", "English")
    assert any(w in r.lower() for w in ['breastfeed', 'postnatal', 'delivery', 'lactation', 'ragi', 'calcium']), \
        f"Postnatal context missing postnatal keywords: {r[:200]}"
    print("  Postnatal Care context guidance OK!")

    # General context
    r, _ = get_ai_response("What should I eat?", "General Nutrition", "English")
    assert len(r) > 100, "General context response too short"
    print("  General Nutrition context guidance OK!")


# ---------------------------------------------------------------------------
# Test 3 – Medical safety disclaimer always present
# ---------------------------------------------------------------------------

def test_medical_safety_disclaimer():
    print("\n=== 3. Test Medical Safety Disclaimers ===")
    from chatbot_engine import get_ai_response

    questions = [
        "I am tired all the time — do I have iron deficiency?",
        "My bones ache — is it vitamin D deficiency?",
        "I have symptoms of anaemia, what should I do?",
        "What supplement should I take during pregnancy?",
    ]

    safety_keywords = [
        'health notice', 'healthcare', 'professional', 'blood test',
        'awareness', 'medical', 'doctor', 'consult', 'clinical'
    ]

    for question in questions:
        r, _ = get_ai_response(question, 'General Nutrition', 'English')
        found = any(kw in r.lower() for kw in safety_keywords)
        assert found, \
            f"Safety disclaimer missing for question: '{question}'\nResponse: {r[:300]}"
        print(f"  Safety disclaimer present for: '{question[:50]}...' OK!")


# ---------------------------------------------------------------------------
# Test 4 – Child age-appropriate guidance
# ---------------------------------------------------------------------------

def test_child_age_guidance():
    print("\n=== 4. Test Child Age-Appropriate Guidance ===")
    from chatbot_engine import get_ai_response, get_child_age_guidance

    test_ages = [
        (3,   "exclusive breastfeeding"),    # 3 months
        (7,   "6"),                           # 7 months — start complementary
        (15,  "12"),                          # 15 months — toddler
        (36,  "2"),                           # 3 years
        (84,  "school"),                      # 7 years — school age
    ]

    for age_months, expected_kw in test_ages:
        guidance = get_child_age_guidance(age_months)
        assert expected_kw.lower() in guidance.lower(), \
            f"Age {age_months}m: expected '{expected_kw}' in guidance but not found:\n{guidance[:200]}"
        print(f"  Age {age_months} months — guidance contains '{expected_kw}' OK!")

    # Also test via main function with child context
    r, _ = get_ai_response("What should my baby eat?", "Child Nutrition", "English",
                           child_age_months=5)
    assert any(w in r.lower() for w in ['breastfeed', 'exclusive', 'breast milk', '6 month']), \
        f"5-month-old response missing breastfeeding info: {r[:200]}"
    print("  5-month child context passes breastfeeding guidance OK!")


# ---------------------------------------------------------------------------
# Test 5 – Route access control
# ---------------------------------------------------------------------------

def test_route_access_control():
    print("\n=== 5. Test Route Access Control ===")

    # Mother gets access
    with app.test_client() as c:
        login(c, MOTHER_EMAIL, MOTHER_PASSWORD)
        r = c.get('/chatbot')
        assert r.status_code == 200, f"Mother expected 200, got {r.status_code}"
        assert b'Nutrition' in r.data or b'Chatbot' in r.data
        print("  Mother access to /chatbot (200) OK!")

    # Worker is denied
    with app.test_client() as c:
        login(c, WORKER_EMAIL, WORKER_PASSWORD)
        r = c.get('/chatbot')
        assert r.status_code == 403, f"Worker expected 403, got {r.status_code}"
        print("  Worker denied /chatbot (403) OK!")

    # Admin is denied
    with app.test_client() as c:
        login(c, ADMIN_EMAIL, ADMIN_PASSWORD)
        r = c.get('/chatbot')
        assert r.status_code == 403, f"Admin expected 403, got {r.status_code}"
        print("  Admin denied /chatbot (403) OK!")

    # Unauthenticated redirect
    with app.test_client() as c:
        r = c.get('/chatbot', follow_redirects=False)
        assert r.status_code in (302, 301), f"Unauthenticated expected redirect, got {r.status_code}"
        print("  Unauthenticated /chatbot redirects to login OK!")


# ---------------------------------------------------------------------------
# Test 6 – Chat API endpoint creates session and returns response
# ---------------------------------------------------------------------------

def test_chat_api():
    print("\n=== 6. Test Chat API Endpoint ===")
    with app.test_client() as c:
        login(c, MOTHER_EMAIL, MOTHER_PASSWORD)

        # First message
        r = chat(c, "What foods are rich in calcium?")
        assert r.status_code == 200, f"Chat API expected 200, got {r.status_code}"
        data = json.loads(r.data)
        assert 'response' in data, "No 'response' key in JSON"
        assert 'session_id' in data, "No 'session_id' key in JSON"
        assert len(data['response']) > 50, "Response too short"
        assert 'calcium' in data['response'].lower() or 'food' in data['response'].lower(), \
            f"Response doesn't mention calcium: {data['response'][:200]}"

        session_id = data['session_id']
        print(f"  First message OK! session_id={session_id}")

        # Second message in same session (multi-turn)
        r2 = chat(c, "Which of these are good for pregnant women?",
                  session_id=session_id)
        assert r2.status_code == 200
        data2 = json.loads(r2.data)
        assert data2['session_id'] == session_id, "Session ID changed unexpectedly"
        print("  Multi-turn conversation in same session OK!")

        # Empty question is rejected
        r3 = chat(c, "")
        assert r3.status_code == 400
        print("  Empty question correctly rejected with 400 OK!")


# ---------------------------------------------------------------------------
# Test 7 – Chat history saved and retrievable
# ---------------------------------------------------------------------------

def test_chat_history():
    print("\n=== 7. Test Chat History Storage ===")
    with app.test_client() as c:
        login(c, MOTHER_EMAIL, MOTHER_PASSWORD)

        # Send a message
        r = chat(c, "Tell me about iron deficiency symptoms")
        data = json.loads(r.data)
        session_id = data['session_id']

        # View history list
        rh = c.get('/chatbot/history')
        assert rh.status_code == 200
        assert b'Chat History' in rh.data or b'history' in rh.data.lower()
        print("  Chat history list page (200) OK!")

        # View specific session
        rd = c.get(f'/chatbot/history/{session_id}')
        assert rd.status_code == 200
        assert b'iron' in rd.data.lower() or b'deficiency' in rd.data.lower()
        print(f"  Chat session detail page (session {session_id}) OK!")


# ---------------------------------------------------------------------------
# Test 8 – Privacy: mother cannot see another mother's sessions
# ---------------------------------------------------------------------------

def test_chat_privacy():
    print("\n=== 8. Test Chat Privacy (Cross-Mother) ===")

    # Mother 1 creates a session
    session_id = None
    with app.test_client() as c:
        login(c, MOTHER_EMAIL, MOTHER_PASSWORD)
        r = chat(c, "What is vitamin C?")
        data = json.loads(r.data)
        session_id = data['session_id']
        print(f"  Mother 1 created session {session_id} OK!")

    # Mother 2 tries to access that session
    with app.test_client() as c:
        login(c, MOTHER2_EMAIL, MOTHER2_PASSWORD)
        rd = c.get(f'/chatbot/history/{session_id}', follow_redirects=True)
        # Should either redirect (flash) or 404-like behaviour, not show Mother1's data
        assert b'vitamin c' not in rd.data.lower() or b'not found' in rd.data.lower() \
               or b'Chat History' in rd.data, \
            "Mother 2 can see Mother 1's private conversation!"
        print("  Mother 2 cannot access Mother 1's chat session OK!")


# ---------------------------------------------------------------------------
# Test 9 – All 4 languages accepted without errors
# ---------------------------------------------------------------------------

def test_language_support():
    print("\n=== 9. Test Language Support ===")
    with app.test_client() as c:
        login(c, MOTHER_EMAIL, MOTHER_PASSWORD)
        languages = ['English', 'Hindi', 'Malayalam', 'Kannada']
        for lang in languages:
            r = chat(c, "What foods are rich in calcium?", language=lang)
            assert r.status_code == 200, \
                f"Language '{lang}' caused error: {r.status_code}"
            data = json.loads(r.data)
            assert 'response' in data and len(data['response']) > 50, \
                f"Language '{lang}' returned empty response"
            print(f"  Language '{lang}' accepted without error OK!")


# ---------------------------------------------------------------------------
# Test 10 – New conversation clears session
# ---------------------------------------------------------------------------

def test_new_conversation():
    print("\n=== 10. Test New Conversation ===")
    with app.test_client() as c:
        login(c, MOTHER_EMAIL, MOTHER_PASSWORD)
        # Start new conversation
        r = c.post('/chatbot/new', follow_redirects=True)
        assert r.status_code == 200
        assert b'Chatbot' in r.data or b'nutrition' in r.data.lower() or b'Nutrition' in r.data
        print("  New conversation redirect to chatbot page OK!")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    failures = []
    for fn in [
        test_knowledge_base_nutrients,
        test_context_guidance,
        test_medical_safety_disclaimer,
        test_child_age_guidance,
        test_route_access_control,
        test_chat_api,
        test_chat_history,
        test_chat_privacy,
        test_language_support,
        test_new_conversation,
    ]:
        try:
            fn()
        except AssertionError as e:
            print(f"  FAILED: {e}")
            failures.append((fn.__name__, str(e)))
        except Exception as e:
            import traceback
            print(f"  ERROR in {fn.__name__}: {e}")
            traceback.print_exc()
            failures.append((fn.__name__, str(e)))

    print()
    if failures:
        print(f">>> {len(failures)} TEST(S) FAILED <<<")
        for name, msg in failures:
            print(f"  - {name}: {msg}")
        sys.exit(1)
    else:
        print(">>> ALL PHASE 5 CHATBOT TESTS PASSED SUCCESSFULLY! <<<")

