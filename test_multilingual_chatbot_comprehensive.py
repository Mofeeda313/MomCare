# -*- coding: utf-8 -*-
"""
test_multilingual_chatbot_comprehensive.py
Comprehensive test suite for Phase 5 Multilingual Chatbot in MomCare.
Covers:
  - English, Malayalam, Hindi, Kannada
  - Topics: Pregnancy Care, Nutrition, Calcium & Iron, Child Vaccination, General Maternal Health
  - Script Language Detection
  - Safety Disclaimers in all 4 languages
  - API endpoint integration
"""

import os
import sys
import unittest
from app import app
from chatbot_engine import (
    get_ai_response,
    build_fallback_response,
    detect_script_language,
    find_all_nutrient_matches,
    NUTRIENT_KB,
    VACCINATION_GUIDANCE,
    MATERNAL_HEALTH_GUIDANCE,
    DISCLAIMERS
)

class TestMultilingualChatbot(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_script_language_detection(self):
        """Test automatic script language detection for Indic languages and fallback."""
        print("\n--- 1. Testing Script Language Detection ---")
        # Malayalam
        self.assertEqual(detect_script_language("ഇരുമ്പ് അടങ്ങിയ ഭക്ഷണം ഏതാണ്?"), "Malayalam")
        self.assertEqual(detect_script_language("കുഞ്ഞിന്റെ കുത്തിവയ്പ്പ് വിവരങ്ങൾ"), "Malayalam")

        # Hindi
        self.assertEqual(detect_script_language("गर्भावस्था के दौरान क्या खाना चाहिए?"), "Hindi")
        self.assertEqual(detect_script_language("कैल्शियम और आयरन की कमी के लक्षण"), "Hindi")

        # Kannada
        self.assertEqual(detect_script_language("ಮಗುವಿನ ಲಸಿಕೆ ವೇಳಾಪಟ್ಟಿ ಯಾವುದು?"), "Kannada")
        self.assertEqual(detect_script_language("ಕಬ್ಬಿಣಾಂಶವಿರುವ ಆಹಾರಗಳು"), "Kannada")

        # English (returns None so it respects selected language)
        self.assertIsNone(detect_script_language("What foods are rich in iron?"))
        self.assertIsNone(detect_script_language("What vaccines does my child need?"))
        print("  Language detection verified for Malayalam, Hindi, Kannada, and English fallback!")

    def test_02_nutrition_and_deficiencies_all_languages(self):
        """Test nutrition and nutrient deficiency questions across all 4 languages."""
        print("\n--- 2. Testing Nutrition, Calcium & Iron Deficiency Across 4 Languages ---")

        # English - Calcium
        resp_en, _ = get_ai_response("Which foods contain calcium?", "General Nutrition", "English")
        self.assertIn("calcium", resp_en.lower())
        self.assertIn("milk", resp_en.lower())
        self.assertIn(DISCLAIMERS["English"][:30], resp_en)
        print("  English calcium response OK!")

        # Malayalam - Iron
        resp_ml, _ = get_ai_response("ഇരുമ്പ് അടങ്ങിയ ഭക്ഷണം ഏതാണ്?", "General Nutrition", "Malayalam")
        self.assertTrue(any(w in resp_ml for w in ['ഇരുമ്പ്', 'ഭക്ഷണ', 'വിവരങ്ങൾ']))
        self.assertIn(DISCLAIMERS["Malayalam"][:25], resp_ml)
        print("  Malayalam iron response OK!")

        # Hindi - Calcium & Iron combined
        resp_hi, _ = get_ai_response("कैल्शियम और आयरन की कमी के क्या लक्षण हैं?", "General Nutrition", "Hindi")
        self.assertIn("कैल्शियम", resp_hi)
        self.assertIn("आयरन", resp_hi)
        self.assertIn(DISCLAIMERS["Hindi"][:25], resp_hi)
        print("  Hindi combined calcium & iron response OK!")

        # Kannada - Iron
        resp_kn, _ = get_ai_response("ಕಬ್ಬಿಣಾಂಶವಿರುವ ಆಹಾರಗಳು ಯಾವುವು ಮತ್ತು ಕೊರತೆಯ ಲಕ್ಷಣಗಳು?", "General Nutrition", "Kannada")
        self.assertIn("ಕಬ್ಬಿಣ", resp_kn)
        self.assertIn(DISCLAIMERS["Kannada"][:25], resp_kn)
        print("  Kannada iron response OK!")

    def test_03_child_vaccination_all_languages(self):
        """Test child vaccination schedule across all 4 languages."""
        print("\n--- 3. Testing Child Vaccination Schedule Across 4 Languages ---")

        # English
        resp_en, _ = get_ai_response("What vaccines are needed for my child?", "General Nutrition", "English")
        self.assertIn("BCG", resp_en)
        self.assertIn("Pentavalent", resp_en)
        self.assertIn("Immunization Schedule", resp_en)
        print("  English child vaccination response OK!")

        # Malayalam
        resp_ml, _ = get_ai_response("കുഞ്ഞിന്റെ പ്രതിരോധ കുത്തിവയ്പ്പ് ഷെഡ്യൂൾ എന്താണ്?", "Child Nutrition", "Malayalam")
        self.assertIn("ബിസിജി", resp_ml)
        self.assertIn("പെന്റാവാലന്റ്", resp_ml)
        self.assertIn("കുത്തിവയ്പ്പ്", resp_ml)
        print("  Malayalam child vaccination response OK!")

        # Hindi
        resp_hi, _ = get_ai_response("शिशु के टीकाकरण की समय सारिणी क्या है?", "Child Nutrition", "Hindi")
        self.assertIn("बीसीजी", resp_hi)
        self.assertIn("पेंटावेलेंट", resp_hi)
        self.assertIn("टीकाकरण", resp_hi)
        print("  Hindi child vaccination response OK!")

        # Kannada
        resp_kn, _ = get_ai_response("ಮಗುವಿನ ಲಸಿಕೆ ವೇಳಾಪಟ್ಟಿ ತಿಳಿಸಿ", "Child Nutrition", "Kannada")
        self.assertIn("ಬಿಸಿಜಿ", resp_kn)
        self.assertIn("ಪೆಂಟಾವಲೆಂಟ್", resp_kn)
        self.assertIn("ಲಸಿಕೆ", resp_kn)
        print("  Kannada child vaccination response OK!")

    def test_04_pregnancy_and_maternal_health_all_languages(self):
        """Test pregnancy care and general maternal health guidance across all 4 languages."""
        print("\n--- 4. Testing Pregnancy Care & General Maternal Health Across 4 Languages ---")

        # English - Maternal Health & Checkups
        resp_en, _ = get_ai_response("What health checkups and care are essential during pregnancy?", "Pregnancy", "English")
        self.assertTrue("ANC" in resp_en or "Antenatal" in resp_en or "Blood Pressure" in resp_en or "Pregnancy" in resp_en)
        print("  English maternal health & pregnancy care response OK!")

        # Malayalam - Maternal Health
        resp_ml, _ = get_ai_response("ഗർഭകാലത്തെ അത്യാവശ്യ പരിശോധനകളും മാതൃ ആരോഗ്യ സംരക്ഷണവും എന്തൊക്കെയാണ്?", "Pregnancy", "Malayalam")
        self.assertTrue("പരിശോധന" in resp_ml or "രക്തസമ്മർദ്ദം" in resp_ml or "ഗർഭകാല" in resp_ml)
        print("  Malayalam maternal health response OK!")

        # Hindi - Pregnancy Care
        resp_hi, _ = get_ai_response("गर्भावस्था में प्रसव पूर्व देखभाल और जांच के बारे में बताएं", "Pregnancy", "Hindi")
        self.assertTrue("जांच" in resp_hi or "रक्तचाप" in resp_hi or "गर्भावस्था" in resp_hi)
        print("  Hindi pregnancy care response OK!")

        # Kannada - Maternal Health
        resp_kn, _ = get_ai_response("ಗರ್ಭಾವಸ್ಥೆಯ ತಪಾಸಣೆಗಳು ಮತ್ತು ಮಾತೃ ಆರೋಗ್ಯ ರಕ್ಷಣೆ", "Pregnancy", "Kannada")
        self.assertTrue("ತಪಾಸಣೆ" in resp_kn or "ರಕ್ತದೊತ್ತಡ" in resp_kn or "ಆರೋಗ್ಯ" in resp_kn)
        print("  Kannada maternal health response OK!")

    def test_05_automatic_language_routing_when_input_in_indic_script(self):
        """Verify that when a user asks in an Indic script, the response matches that script even if language='English'."""
        print("\n--- 5. Testing Automatic Language Routing from Indic Script ---")

        # User asks in Malayalam but language param says English
        ans_ml, _ = get_ai_response("വിറ്റാമിൻ എ അടങ്ങിയ ഭക്ഷണങ്ങൾ ഏതൊക്കെയാണ്?", "General Nutrition", "English")
        self.assertIn("വിറ്റാമിൻ എ", ans_ml)
        self.assertIn("കാരറ്റ്", ans_ml)
        print("  Auto-routed Malayalam script query to Malayalam response OK!")

        # User asks in Hindi but language param says English
        ans_hi, _ = get_ai_response("विटामिन डी की कमी के क्या लक्षण हैं?", "General Nutrition", "English")
        self.assertIn("विटामिन डी", ans_hi)
        self.assertIn("हड्डियों", ans_hi)
        print("  Auto-routed Hindi script query to Hindi response OK!")

        # User asks in Kannada but language param says English
        ans_kn, _ = get_ai_response("ಕ್ಯಾಲ್ಸಿಯಂ ಕೊರತೆಯ ಲಕ್ಷಣಗಳು ಮತ್ತು ಆಹಾರ ಮೂಲಗಳು", "General Nutrition", "English")
        self.assertIn("ಕ್ಯಾಲ್ಸಿಯಂ", ans_kn)
        self.assertIn("ಹಾಲು", ans_kn)
        print("  Auto-routed Kannada script query to Kannada response OK!")

    def test_06_chat_api_endpoint_multilingual(self):
        """Test /chatbot/chat POST endpoint with authenticated mother in multiple languages."""
        print("\n--- 6. Testing /chatbot/chat AJAX Endpoint with Mother Session ---")
        with self.client as c:
            # Login as mother Priya (priya.nair@example.com / MotherPassword123!)
            r_login = c.post('/login', data={'email': 'priya.nair@example.com', 'password': 'MotherPassword123!'}, follow_redirects=True)
            self.assertEqual(r_login.status_code, 200)

            # 1. English Chat
            r_en = c.post('/chatbot/chat', json={
                'question': 'What foods are rich in Vitamin C?',
                'context': 'General Nutrition',
                'language': 'English'
            })
            self.assertEqual(r_en.status_code, 200)
            data_en = r_en.get_json()
            self.assertIn('vitamin c', data_en['response'].lower())
            self.assertEqual(data_en['language'], 'English')

            # 2. Malayalam Chat
            r_ml = c.post('/chatbot/chat', json={
                'question': 'ഇരുമ്പ് അടങ്ങിയ പ്രധാന ഭക്ഷണങ്ങൾ ഏതാണ്?',
                'context': 'General Nutrition',
                'language': 'Malayalam'
            })
            self.assertEqual(r_ml.status_code, 200)
            data_ml = r_ml.get_json()
            self.assertIn('ഇരുമ്പ്', data_ml['response'])
            self.assertEqual(data_ml['language'], 'Malayalam')

            # 3. Hindi Chat
            r_hi = c.post('/chatbot/chat', json={
                'question': 'गर्भावस्था में क्या खाना चाहिए?',
                'context': 'Pregnancy',
                'language': 'Hindi'
            })
            self.assertEqual(r_hi.status_code, 200)
            data_hi = r_hi.get_json()
            self.assertIn('गर्भावस्था', data_hi['response'])
            self.assertEqual(data_hi['language'], 'Hindi')

            # 4. Kannada Chat
            r_kn = c.post('/chatbot/chat', json={
                'question': 'ಮಗುವಿನ ಲಸಿಕೆ ವೇಳಾಪಟ್ಟಿ ಯಾವುದು?',
                'context': 'Child Nutrition',
                'language': 'Kannada'
            })
            self.assertEqual(r_kn.status_code, 200)
            data_kn = r_kn.get_json()
            self.assertIn('ಲಸಿಕೆ', data_kn['response'])
            self.assertEqual(data_kn['language'], 'Kannada')

            # Clean up user language to English
            c.get('/set-language/English', follow_redirects=True)
            print("  All 4 languages successfully processed via /chatbot/chat endpoint!")

if __name__ == '__main__':
    unittest.main()
