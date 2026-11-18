# -*- coding: utf-8 -*-
"""
chatbot_engine.py
MomCare Phase 5 & Multilingual – AI Nutrition Chatbot engine.

Supports 4 languages:
  1. English
  2. Malayalam (മലയാളം)
  3. Hindi (हिन्दी)
  4. Kannada (ಕನ್ನಡ)

Features:
  - Natural question understanding in English, Malayalam, Hindi, and Kannada.
  - Complete, evidence-based nutrition knowledge for 10 nutrients in all 4 languages.
  - Context-specific guidance (Pregnancy, Postnatal, Child Milestones, General).
  - Accurate Indian food recommendations (Ragi, Dal, Drumstick/Moringa, Amla, Khichdi, etc.).
  - Medical safety disclaimers always present in the chosen language.
  - Direct integration with Google Gemini API when GEMINI_API_KEY is configured.
  - Medically verified, culturally tailored fallback when no API key is set.
"""

import os
import re

# =============================================================================
# Multilingual Nutrient Knowledge Base (English, Malayalam, Hindi, Kannada)
# =============================================================================

NUTRIENT_KB = {
    # ── VITAMIN A ──────────────────────────────────────────────────────────
    "vitamin a": {
        "English": {
            "title": "Vitamin A — Nutrition Information",
            "importance": (
                "Vitamin A is essential for good vision, a healthy immune system, "
                "skin maintenance, and normal growth and development of cells."
            ),
            "food_sources": (
                "Rich Indian sources include:\n"
                "• Vegetarian: carrot, sweet potato, pumpkin, spinach, fenugreek leaves "
                "(methi), drumstick leaves (moringa), papaya, mango, tomato, egg yolk.\n"
                "• Non-vegetarian: liver (mutton or chicken), fish liver oil."
            ),
            "deficiency_symptoms": (
                "Possible signs of low Vitamin A include night blindness (difficulty seeing "
                "in dim light), dry eyes, frequent infections, and rough or dry skin. "
                "A blood test is needed to confirm a deficiency."
            ),
            "dietary_guidance": (
                "During pregnancy, adequate Vitamin A supports foetal development. "
                "Breastfeeding mothers also need sufficient Vitamin A. "
                "Excess supplementation during pregnancy can be harmful — always consult "
                "your healthcare provider before taking Vitamin A supplements."
            )
        },
        "Malayalam": {
            "title": "വിറ്റാമിൻ എ — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": (
                "കണ്ണുകളുടെ ആരോഗ്യം, പ്രതിരോധശേഷി, ചർമ്മ സംരക്ഷണം, കോശങ്ങളുടെ സാധാരണ വളർച്ച "
                "എന്നിവയ്ക്ക് വിറ്റാമിൻ എ അത്യന്താപേക്ഷിതമാണ്."
            ),
            "food_sources": (
                "പ്രധാന ഇന്ത്യൻ ഭക്ഷണ സ്രോതസ്സുകൾ:\n"
                "• സസ്യഭക്ഷണം: കാരറ്റ്, മധുരക്കിഴങ്ങ്, മത്തങ്ങ, ചീര, ഉലുവയില, മുരിങ്ങയില, പപ്പായ, മാമ്പഴം, തക്കാളി, മുട്ടയുടെ മഞ്ഞക്കരു.\n"
                "• മാംസാഹാരം: കരൾ (മട്ടൺ അല്ലെങ്കിൽ ചിക്കൻ), മീനെണ്ണ."
            ),
            "deficiency_symptoms": (
                "വിറ്റാമിൻ എ കുറവിന്റെ ലക്ഷണങ്ങളിൽ നിശാന്ധത (മങ്ങിയ വെളിച്ചത്തിൽ കാണാൻ ബുദ്ധിമുട്ട്), "
                "കണ്ണുകളിലെ വരൾച്ച, അടിക്കടിയുള്ള അണുബാധകൾ, വരണ്ട ചർമ്മം എന്നിവ ഉൾപ്പെടുന്നു. "
                "രോഗനിർണയത്തിന് രക്തപരിശോധന ആവശ്യമാണ്."
            ),
            "dietary_guidance": (
                "ഗർഭകാലത്ത് ഗർഭസ്ഥ ശിശുവിന്റെ വികാസത്തിനും മുലയൂട്ടുന്ന അമ്മമാർക്കും വിറ്റാമിൻ എ പ്രധാനമാണ്. "
                "എന്നാൽ ഗർഭകാലത്ത് അമിതമായ അളവിൽ സപ്ലിമെന്റുകൾ കഴിക്കുന്നത് ദോഷകരമാണ് — ഡോക്ടറുടെ നിർദ്ദേശപ്രകാരം മാത്രം കഴിക്കുക."
            )
        },
        "Hindi": {
            "title": "विटामिन ए — पोषण संबंधी जानकारी",
            "importance": (
                "विटामिन ए आंखों की रोशनी, मजबूत रोग प्रतिरोधक क्षमता (इम्यूनिटी), त्वचा की सेहत "
                "और कोशिकाओं के समुचित विकास के लिए बेहद जरूरी है।"
            ),
            "food_sources": (
                "प्रमुख भारतीय खाद्य स्रोत:\n"
                "• शाकाहारी: गाजर, शकरकंद, कद्दू, पालक, मेथी, सहजन/मोरिंगा के पत्ते, पपीता, आम, टमाटर, अंडे की जर्दी।\n"
                "• मांसाहारी: कलेजी (मटन या चिकन), मछली का तेल।"
            ),
            "deficiency_symptoms": (
                "विटामिन ए की कमी से रतौंधी (कम रोशनी में देखने में कठिनाई), आंखों का सूखापन, "
                "बार-बार संक्रमण और सूखी त्वचा की समस्या हो सकती है। पुष्टि के लिए रक्त परीक्षण आवश्यक है।"
            ),
            "dietary_guidance": (
                "गर्भावस्था और स्तनपान के दौरान शिशु के विकास के लिए विटामिन ए आवश्यक है। "
                "गर्भावस्था में बिना डॉक्टर की सलाह के उच्च खुराक वाली सप्लीमेंट्स न लें।"
            )
        },
        "Kannada": {
            "title": "ವಿಟಮಿನ್ ಎ — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": (
                "ವಿಟಮಿನ್ ಎ ಕಣ್ಣಿನ ಆರೋಗ್ಯ, ರೋಗನಿರೋಧಕ ಶಕ್ತಿ, ಚರ್ಮದ ಕಾಂತಿ ಮತ್ತು ಕೋಶಗಳ "
                "ಸಹಜ ಬೆಳವಣಿಗೆಗೆ ಅತ್ಯಗತ್ಯವಾಗಿದೆ."
            ),
            "food_sources": (
                "ಪ್ರಮುಖ ಭಾರತೀಯ ಆಹಾರ ಮೂಲಗಳು:\n"
                "• ಸಸ್ಯಾಹಾರಿ: ಕ್ಯಾರೆಟ್, ಸಿಹಿಗೆಣಸು, ಕುಂಬಳಕಾಯಿ, ಪಾಲಕ್, ಮೆಂತ್ಯ ಸೊಪ್ಪು, ನುಗ್ಗೆ ಸೊಪ್ಪು, ಪರಂಗಿಹಣ್ಣು (ಪಪ್ಪಾಯಿ), ಮಾವಿನಹಣ್ಣು, ಟೊಮೆಟೊ, ಮೊಟ್ಟೆಯ ಹಳದಿ ಭಾಗ.\n"
                "• ಮಾಂಸಾಹಾರಿ: ಲಿವರ್ (ಕುರಿ ಅಥವಾ ಚಿಕನ್), ಮೀನಿನ ಎಣ್ಣೆ."
            ),
            "deficiency_symptoms": (
                "ವಿಟಮಿನ್ ಎ ಕೊರತೆಯು ಇರುಳುಗಣ್ಣು (ಮಂದ ಬೆಳಕಿನಲ್ಲಿ ಕಾಣದಿರುವುದು), ಕಣ್ಣು ಒಣಗುವುದು, "
                "ಮತ್ತು ಚರ್ಮ ಒರಟಾಗುವುದಕ್ಕೆ ಕಾರಣವಾಗಬಹುದು. ರಕ್ತ ಪರೀಕ್ಷೆಯ ಮೂಲಕ ದೃಢೀಕರಿಸಿಕೊಳ್ಳಬೇಕು."
            ),
            "dietary_guidance": (
                "ಗರ್ಭಿಣಿಯರು ಮತ್ತು ಬಾಣಂತಿಯರಿಗೆ ವಿಟಮಿನ್ ಎ ಅವಶ್ಯಕ. ಆದರೆ ವೈದ್ಯರ ಸಲಹೆಯಿಲ್ಲದೆ "
                "ಹೆಚ್ಚುವರಿ ಸಪ್ಲಿಮೆಂಟ್ ತೆಗೆದುಕೊಳ್ಳಬಾರದು."
            )
        }
    },

    # ── VITAMIN B12 ────────────────────────────────────────────────────────
    "vitamin b12": {
        "English": {
            "title": "Vitamin B12 — Nutrition Information",
            "importance": (
                "Vitamin B12 is vital for nerve function, red blood cell production, "
                "and DNA synthesis. It is especially important during pregnancy."
            ),
            "food_sources": (
                "Rich Indian sources include:\n"
                "• Non-vegetarian: fish (mackerel, sardines), chicken, eggs, mutton.\n"
                "• Vegetarian/dairy: milk, paneer, curd (yoghurt), fortified foods. "
                "Strict vegetarians and vegans are at higher risk of deficiency."
            ),
            "deficiency_symptoms": (
                "Possible signs include fatigue, weakness, tingling in hands and feet, "
                "pale skin, memory difficulties, and mood changes. "
                "Confirm with a blood test and consult a doctor."
            ),
            "dietary_guidance": (
                "Pregnant and breastfeeding mothers need adequate B12. "
                "If you are vegetarian or vegan, discuss supplementation with your doctor."
            )
        },
        "Malayalam": {
            "title": "വിറ്റാമിൻ ബി12 — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": (
                "നാഡികളുടെ പ്രവർത്തനം, ചുവന്ന രക്താണുക്കളുടെ ഉത്പാദനം, ഡിഎൻഎ നിർമ്മാണം എന്നിവയ്ക്ക് "
                "വിറ്റാമിൻ ബി12 അത്യാവശ്യമാണ്. ഗർഭകാലത്ത് ഇത് വളരെ പ്രധാനമാണ്."
            ),
            "food_sources": (
                "പ്രധാന സ്രോതസ്സുകൾ:\n"
                "• മാംസാഹാരം: അയല, മത്തി തുടങ്ങിയ മത്സ്യങ്ങൾ, ചിക്കൻ, മുട്ട, മട്ടൺ.\n"
                "• സസ്യാഹാരം/ഡയറി: പാൽ, പനീർ, തൈര്. സസ്യാഹാരികൾക്ക് ബി12 കുറവ് വരാനുള്ള സാധ്യത കൂടുതലാണ്."
            ),
            "deficiency_symptoms": (
                "അമിതമായ ക്ഷീണം, കൈകാലുകളിൽ തരിപ്പ്, വിളർച്ച, തളർച്ച എന്നിവ ഇതിന്റെ ലക്ഷണങ്ങളാകാം. "
                "രക്തപരിശോധനയിലൂടെ മാത്രമേ ഇത് സ്ഥിരീകരിക്കാനാകൂ."
            ),
            "dietary_guidance": (
                "ഗർഭിണികളും മുലയൂട്ടുന്ന അമ്മമാരും ആവശ്യത്തിന് ബി12 ലഭിക്കുന്നുണ്ടെന്ന് ഉറപ്പാക്കണം. "
                "സസ്യാഹാരികൾ ഡോക്ടറുടെ നിർദ്ദേശപ്രകാരം സപ്ലിമെന്റുകൾ കഴിക്കുന്നത് ആലോചിക്കുക."
            )
        },
        "Hindi": {
            "title": "विटामिन बी12 — पोषण संबंधी जानकारी",
            "importance": (
                "विटामिन बी12 तंत्रिका तंत्र (नर्वस सिस्टम), लाल रक्त कोशिकाओं और डीएनए निर्माण के लिए आवश्यक है।"
            ),
            "food_sources": (
                "प्रमुख स्रोत:\n"
                "• मांसाहारी: मछली (मैकेरल, सार्डिन), चिकन, अंडे, मटन।\n"
                "• शाकाहारी: दूध, पनीर, दही। शुद्ध शाकाहारियों में इसकी कमी का जोखिम अधिक रहता है।"
            ),
            "deficiency_symptoms": (
                "थकान, कमजोरी, हाथ-पैरों में झनझनाहट और खून की कमी इसके सामान्य लक्षण हैं। डॉक्टर से जांच कराएं।"
            ),
            "dietary_guidance": (
                "गर्भवती और स्तनपान कराने वाली महिलाओं को पर्याप्त बी12 की आवश्यकता होती है। सप्लीमेंट्स के लिए डॉक्टर से परामर्श लें।"
            )
        },
        "Kannada": {
            "title": "ವಿಟಮಿನ್ ಬಿ12 — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": (
                "ನರಗಳ ಆರೋಗ್ಯ, ಕೆಂಪು ರಕ್ತ ಕಣಗಳ ಉತ್ಪಾದನೆ ಮತ್ತು ಡಿಎನ್‌ಎ ಸಂಶ್ಲೇಷಣೆಗೆ ವಿಟಮಿನ್ ಬಿ12 ಅತ್ಯಗತ್ಯ."
            ),
            "food_sources": (
                "ಪ್ರಮುಖ ಮೂಲಗಳು:\n"
                "• ಮಾಂಸಾಹಾರಿ: ಮೀನು, ಚಿಕನ್, ಮೊಟ್ಟೆ, ಮಟನ್.\n"
                "• ಸಸ್ಯಾಹಾರಿ: ಹಾಲು, ಮೊಸರು, ಪನೀರ್. ಶುದ್ಧ ಸಸ್ಯಾಹಾರಿಗಳಲ್ಲಿ ಬಿ12 ಕೊರತೆಯ ಸಾಧ್ಯತೆ ಹೆಚ್ಚು."
            ),
            "deficiency_symptoms": (
                "ಸುಸ್ತು, ದೌರ್ಬಲ್ಯ, ಕೈಕಾಲುಗಳಲ್ಲಿ ಜುಮ್ಮೆನಿಸುವಿಕೆ ಮತ್ತು ರಕ್ತಹೀನತೆ ಕಂಡುಬರಬಹುದು."
            ),
            "dietary_guidance": (
                "ಗರ್ಭಿಣಿಯರು ಮತ್ತು ಬಾಣಂತಿಯರು ವೈದ್ಯರ ಸಲಹೆಯೊಂದಿಗೆ ಸೂಕ್ತ ಪೌಷ್ಟಿಕಾಂಶ ಪಡೆಯಬೇಕು."
            )
        }
    },

    # ── FOLATE / FOLIC ACID ────────────────────────────────────────────────
    "folate": {
        "English": {
            "title": "Folate (Folic Acid) — Nutrition Information",
            "importance": (
                "Folate (Vitamin B9) is critical for cell division and preventing neural "
                "tube defects in the developing baby. It is essential before and during pregnancy."
            ),
            "food_sources": (
                "Rich Indian sources include:\n"
                "• Green leafy vegetables: spinach, fenugreek (methi), coriander.\n"
                "• Legumes: dal (lentils), rajma (kidney beans), chana (chickpeas), moong.\n"
                "• Other: beetroot, banana, oranges, peanuts."
            ),
            "deficiency_symptoms": (
                "Tiredness, mouth ulcers, and anaemia. In pregnancy, deficiency increases birth defect risks."
            ),
            "dietary_guidance": (
                "Folic acid supplements are routinely recommended in early pregnancy. Eat greens and dal daily."
            )
        },
        "Malayalam": {
            "title": "ഫോളേറ്റ് (ഫോളിക് ആസിഡ്) — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": (
                "ഗർഭസ്ഥ ശിശുവിന്റെ തലച്ചോറിന്റെയും സുഷുമ്നാ നാഡിയുടെയും വളർച്ചയ്ക്കും വൈകല്യങ്ങൾ തടയുന്നതിനും ഫോളേറ്റ് അത്യന്താപേക്ഷിതമാണ്."
            ),
            "food_sources": (
                "സ്രോതസ്സുകൾ:\n"
                "• ഇലക്കറികൾ: ചീര, ഉലുവയില, മുരിങ്ങയില, മല്ലിയില.\n"
                "• പയറുവർഗ്ഗങ്ങൾ: പരിപ്പ്, ചെറുപയർ, കടല, രാജ്മ.\n"
                "• മറ്റു ഭക്ഷണങ്ങൾ: ബീറ്റ്റൂട്ട്, ഏത്തപ്പഴം, ഓറഞ്ച്, നിലക്കടല."
            ),
            "deficiency_symptoms": (
                "വിളർച്ച, അമിത ക്ഷീണം, വായ്പ്പുണ്ണ് എന്നിവ ലക്ഷണങ്ങളാണ്."
            ),
            "dietary_guidance": (
                "ഗർഭധാരണത്തിന് മുമ്പും ആദ്യ മാസങ്ങളിലും ഫോളിക് ആസിഡ് ഗുളികകൾ ഡോക്ടർമാർ നിർദ്ദേശിക്കാറുണ്ട്. ദിവസവും ഇലക്കറികളും പരിപ്പും കഴിക്കുക."
            )
        },
        "Hindi": {
            "title": "फ़ोलेट (फ़ोलिक एसिड) — पोषण संबंधी जानकारी",
            "importance": (
                "शिशु के मस्तिष्क और रीढ़ की हड्डी के समुचित विकास (न्यूरल ट्यूब दोषों की रोकथाम) के लिए फ़ोलेट अति आवश्यक है।"
            ),
            "food_sources": (
                "स्रोत: हरी पत्तेदार सब्जियां (पालक, मेथी), दालें, राजमा, चना, मूंग, चुकंदर, संतरा, मूंगफली।"
            ),
            "deficiency_symptoms": (
                "कमजोरी, थकान और एनीमिया। गर्भावस्था में इसकी कमी से जन्म दोष हो सकते हैं।"
            ),
            "dietary_guidance": (
                "गर्भावस्था की शुरुआत में डॉक्टर द्वारा बताए गए फोलिक एसिड सप्लीमेंट्स अवश्य लें और रोज दाल व हरी सब्जियां खाएं।"
            )
        },
        "Kannada": {
            "title": "ಫೋಲೇಟ್ (ಫೋಲಿಕ್ ಆಮ್ಲ) — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": (
                "ಮಗುವಿನ ಮೆದುಳು ಮತ್ತು ಬೆನ್ನುಹುರಿಯ ಬೆಳವಣಿಗೆಗೆ ಹಾಗೂ ನ್ಯೂರಲ್ ಟ್ಯೂಬ್ ದೋಷಗಳನ್ನು ತಡೆಯಲು ಫೋಲೇಟ್ ಅತ್ಯಗತ್ಯ."
            ),
            "food_sources": (
                "ಮೂಲಗಳು: ಪಾಲಕ್, ಮೆಂತ್ಯ ಸೊಪ್ಪು, ತೊಗರಿಬೇಳೆ, ಕಡಲೆಕಾಳು, ಹೆಸರುಕಾಳು, ಬೀಟ್‌ರೂಟ್, ಕಿತ್ತಳೆ, ಕಡಲೆಕಾಯಿ."
            ),
            "deficiency_symptoms": (
                "ಆಯಾಸ, ಬಾಯಿಯ ಹುಣ್ಣು ಮತ್ತು ರಕ್ತಹೀನತೆ ಕಂಡುಬರಬಹುದು."
            ),
            "dietary_guidance": (
                "ಗರ್ಭಾವಸ್ಥೆಯ ಆರಂಭದಲ್ಲಿ ವೈದ್ಯರು ಸೂಚಿಸುವ ಫೋಲಿಕ್ ಆಮ್ಲ ಮಾತ್ರೆಗಳನ್ನು ನಿಯಮಿತವಾಗಿ ತೆಗೆದುಕೊಳ್ಳಿ."
            )
        }
    },

    # ── IRON ───────────────────────────────────────────────────────────────
    "iron": {
        "English": {
            "title": "Iron — Nutrition Information",
            "importance": (
                "Iron is needed to make haemoglobin, which carries oxygen in the blood. "
                "Essential during pregnancy, breastfeeding, and childhood."
            ),
            "food_sources": (
                "Rich Indian sources include:\n"
                "• Vegetarian: ragi (finger millet), spinach, drumstick leaves, rajma, chana dal, jaggery (gud), sesame seeds (til), dates.\n"
                "• Non-vegetarian: mutton liver, chicken, fish.\n"
                "• Tip: Vitamin C (amla, lemon) improves iron absorption. Avoid tea/coffee with meals."
            ),
            "deficiency_symptoms": (
                "Fatigue, weakness, pale skin, shortness of breath, dizziness. Confirm via blood test."
            ),
            "dietary_guidance": (
                "Iron deficiency anaemia is very common in Indian mothers. Never stop prescribed iron supplements without doctor's advice."
            )
        },
        "Malayalam": {
            "title": "ഇരുമ്പ് (അയൺ) — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": (
                "രക്തത്തിൽ ഓക്സിജൻ വഹിക്കുന്ന ഹീമോഗ്ലോബിൻ നിർമ്മിക്കാൻ ഇരുമ്പ് അത്യന്താപേക്ഷിതമാണ്. വിളർച്ച തടയാൻ ഇത് സഹായിക്കുന്നു."
            ),
            "food_sources": (
                "പ്രധാന ഭക്ഷണങ്ങൾ:\n"
                "• സസ്യഭക്ഷണം: റാഗി (പഞ്ഞപ്പുല്ല്), മുരിങ്ങയില, ചീര, രാജ്മ, കടല, ശർക്കര, എള്ള്, ഈന്തപ്പഴം.\n"
                "• മാംസാഹാരം: കരൾ, ചിക്കൻ, മത്സ്യം.\n"
                "• നുറുങ്ങുവിദ്യ: ഇരുമ്പ് ആഗിരണം ചെയ്യാൻ നെല്ലിക്ക, നാരങ്ങ പോലുള്ള വിറ്റാമിൻ സി ഭക്ഷണങ്ങൾ ഒപ്പം കഴിക്കുക. ഭക്ഷണത്തോടൊപ്പം ചായ/കാപ്പി ഒഴിവാക്കുക."
            ),
            "deficiency_symptoms": (
                "വിളർച്ച, കഠിനമായ ക്ഷീണം, കിതപ്പ്, തലകറക്കം, വിളറിയ ചർമ്മം. രക്തപരിശോധനയിലൂടെ ഹീമോഗ്ലോബിൻ പരിശോധിക്കുക."
            ),
            "dietary_guidance": (
                "ഗർഭിണികളിൽ അയൺ കുറവ് സാധാരണമാണ്. ഡോക്ടർ നിർദ്ദേശിച്ച അയൺ ഗുളികകൾ കൃത്യമായി കഴിക്കുക."
            )
        },
        "Hindi": {
            "title": "आयरन (लोहा) — पोषण संबंधी जानकारी",
            "importance": (
                "शरीर में हीमोग्लोबिन बनाने और खून की कमी (एनीमिया) को रोकने के लिए आयरन बहुत जरूरी है।"
            ),
            "food_sources": (
                "स्रोत:\n"
                "• शाकाहारी: रागी, पालक, सहजन के पत्ते, गुड़, राजमा, चना, तिल, खजूर।\n"
                "• मांसाहारी: कलेजी, चिकन, मछली।\n"
                "• सुझाव: आंवला या नींबू पानी साथ लेने से आयरन का अवशोषण बेहतर होता है। भोजन के साथ चाय-कॉफ़ी न पिएं।"
            ),
            "deficiency_symptoms": (
                "थकान, सांस फूलना, चक्कर आना, पीली त्वचा। हीमोग्लोबिन की जांच डॉक्टर से कराएं।"
            ),
            "dietary_guidance": (
                "गर्भावस्था में डॉक्टर द्वारा दी गई आयरन की गोलियां नियमित रूप से लें और पौष्टिक भोजन करें।"
            )
        },
        "Kannada": {
            "title": "ಕಬ್ಬಿಣಾಂಶ (ಐರನ್) — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": (
                "ರಕ್ತದಲ್ಲಿ ಹಿಮೋಗ್ಲೋಬಿನ್ ಹೆಚ್ಚಿಸಲು ಮತ್ತು ರಕ್ತಹೀನತೆ ತಡೆಯಲು ಕಬ್ಬಿಣದ ಅಂಶ ಅತ್ಯಗತ್ಯ."
            ),
            "food_sources": (
                "ಮೂಲಗಳು:\n"
                "• ಸಸ್ಯಾಹಾರಿ: ರಾಗಿ, ಪಾಲಕ್ ಸೊಪ್ಪು, ನುಗ್ಗೆ ಸೊಪ್ಪು, ಬೆಲ್ಲ, ರಾಜ್ಮಾ, ಕಡಲೆ, ಎಳ್ಳು, ಖರ್ಜೂರ.\n"
                "• ಮಾಂಸಾಹಾರಿ: ಲಿವರ್, ಚಿಕನ್, ಮೀನು.\n"
                "• ಸಲಹೆ: ನೆಲ್ಲಿಕಾಯಿ ಅಥವಾ ನಿಂಬೆ ರಸದೊಂದಿಗೆ ಸೇವಿಸಿದರೆ ಕಬ್ಬಿಣದ ಅಂಶ ದೇಹಕ್ಕೆ ಬೇಗ ಹೀರಿಕೊಳ್ಳುತ್ತದೆ."
            ),
            "deficiency_symptoms": (
                "ಸುಸ್ತು, ಉಸಿರಾಟದಲ್ಲಿ ತೊಂದರೆ, ತಲೆತಿರುಗುವಿಕೆ, ಮಸುಕಾದ ಚರ್ಮ."
            ),
            "dietary_guidance": (
                "ಗರ್ಭಿಣಿಯರು ರಕ್ತಹೀನತೆ ತಡೆಯಲು ವೈದ್ಯರು ನೀಡುವ ಐರನ್ ಮಾತ್ರೆಗಳನ್ನು ತಪ್ಪದೆ ತೆಗೆದುಕೊಳ್ಳಬೇಕು."
            )
        }
    },

    # ── CALCIUM ────────────────────────────────────────────────────────────
    "calcium": {
        "English": {
            "title": "Calcium — Nutrition Information",
            "importance": (
                "Essential for strong bones, teeth, muscle function, and nerve signaling. Protects mother and baby."
            ),
            "food_sources": (
                "Rich sources: milk, curd, paneer, ragi (finger millet), sesame seeds (til), drumstick leaves, small fish with bones."
            ),
            "deficiency_symptoms": (
                "Muscle cramps, brittle nails, dental issues, weak bones. Blood test confirms levels."
            ),
            "dietary_guidance": (
                "Ragi porridge is an outstanding, affordable Indian calcium food. Pair with Vitamin D for absorption."
            )
        },
        "Malayalam": {
            "title": "കാൽസ്യം — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": (
                "എല്ലുകളുടെയും പല്ലുകളുടെയും ബലത്തിനും പേശികളുടെ ശരിയായ പ്രവർത്തനത്തിനും കാൽസ്യം അത്യാവശ്യമാണ്."
            ),
            "food_sources": (
                "സ്രോതസ്സുകൾ: പാൽ, തൈര്, പനീർ, റാഗി (പഞ്ഞപ്പുല്ല് കുറുക്ക്), എള്ള്, മുരിങ്ങയില, ചെറിയ മീനുകൾ (മുള്ളോടുകൂടി കഴിക്കാവുന്നത്)."
            ),
            "deficiency_symptoms": (
                "പേശിവലിവ്, പല്ലുവേദന, നഖങ്ങൾ പൊട്ടൽ, എല്ലുകളുടെ ബലക്കുറവ്."
            ),
            "dietary_guidance": (
                "റാഗി കുറുക്ക് അമ്മമാർക്കും കുട്ടികൾക്കും കാൽസ്യം നൽകുന്ന ഉത്തമ ഭക്ഷണമാണ്. വിറ്റാമിൻ ഡിയും ഒപ്പം ഉറപ്പാക്കുക."
            )
        },
        "Hindi": {
            "title": "कैल्शियम — पोषण संबंधी जानकारी",
            "importance": (
                "मजबूत हड्डियों, दांतों और मांसपेशियों के संचालन के लिए कैल्शियम बहुत जरूरी है।"
            ),
            "food_sources": (
                "स्रोत: दूध, दही, पनीर, रागी, तिल, सहजन के पत्ते, छोटी मछलियां।"
            ),
            "deficiency_symptoms": (
                "मांसपेशियों में ऐंठन, कमजोर नाखून, हड्डियों में दर्द।"
            ),
            "dietary_guidance": (
                "रागी का दलिया या कांजी कैल्शियम का बहुत अच्छा भारतीय स्रोत है। साथ में धूप से विटामिन डी भी लें।"
            )
        },
        "Kannada": {
            "title": "ಕ್ಯಾಲ್ಸಿಯಂ — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": (
                "ಮೂಳೆಗಳು ಮತ್ತು ಹಲ್ಲುಗಳ ಬಲವರ್ಧನೆಗೆ ಹಾಗೂ ಸ್ನಾಯುಗಳ ಕಾರ್ಯಕ್ಷಮತೆಗೆ ಕ್ಯಾಲ್ಸಿಯಂ ಅತ್ಯಗತ್ಯ."
            ),
            "food_sources": (
                "ಮೂಲಗಳು: ಹಾಲು, ಮೊಸರು, ಪನೀರ್, ರಾಗಿ (ರಾಗಿ ಅಂಬಲಿ), ಎಳ್ಳು, ನುಗ್ಗೆ ಸೊಪ್ಪು."
            ),
            "deficiency_symptoms": (
                "ಸ್ನಾಯು ಸೆಳೆತ, ದುರ್ಬಲ ಮೂಳೆಗಳು ಮತ್ತು ಹಲ್ಲುಗಳ ತೊಂದರೆ."
            ),
            "dietary_guidance": (
                "ರಾಗಿ ಮುದ್ದೆ ಅಥವಾ ರಾಗಿ ಗಂಜಿ ತಾಯಿ ಮತ್ತು ಮಗುವಿಗೆ ಉತ್ತಮ ಕ್ಯಾಲ್ಸಿಯಂ ನೀಡುತ್ತದೆ."
            )
        }
    },

    # ── VITAMIN C ──────────────────────────────────────────────────────────
    "vitamin c": {
        "English": {
            "title": "Vitamin C — Nutrition Information",
            "importance": "Boosts immunity, enhances plant iron absorption, and aids tissue repair.",
            "food_sources": "Amla (Indian gooseberry), guava, orange, lemon, mosambi, papaya, capsicum, tomato.",
            "deficiency_symptoms": "Bleeding gums, slow wound healing, frequent infections, fatigue.",
            "dietary_guidance": "Eat amla or citrus fruits with iron-rich meals for optimal iron uptake."
        },
        "Malayalam": {
            "title": "വിറ്റാമിൻ സി — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": "രോഗപ്രതിരോധശേഷി വർദ്ധിപ്പിക്കുന്നതിനും ഭക്ഷണത്തിൽ നിന്നുള്ള ഇരുമ്പ് ശരീരം ആഗിരണം ചെയ്യുന്നതിനും സഹായിക്കുന്നു.",
            "food_sources": "നെല്ലിക്ക (ഏറ്റവും മികച്ച സ്രോതസ്സ്), പേരയ്ക്ക, ഓറഞ്ച്, നാരങ്ങ, പപ്പായ, തക്കാളി.",
            "deficiency_symptoms": "മോണയിൽ നിന്ന് രക്തം വരിക, മുറിവുകൾ ഉണങ്ങാൻ താമസം, അടിക്കടിയുള്ള രോഗങ്ങൾ.",
            "dietary_guidance": "നെല്ലിക്കയും നാരങ്ങയും ഭക്ഷണത്തിൽ ഉൾപ്പെടുത്തുന്നത് അയൺ ആഗിരണം ചെയ്യാൻ വളരെ നല്ലതാണ്."
        },
        "Hindi": {
            "title": "विटामिन सी — पोषण संबंधी जानकारी",
            "importance": "रोग प्रतिरोधक क्षमता बढ़ाता है और भोजन से आयरन सोखने में शरीर की मदद करता है।",
            "food_sources": "आंवला (सर्वोत्तम स्रोत), अमरूद, संतरा, नींबू, पपीता, शिमला मिर्च, टमाटर।",
            "deficiency_symptoms": "मसूड़ों से खून आना, घाव देर से भरना, बार-बार सर्दी-जुकाम होना।",
            "dietary_guidance": "आंवला या नींबू का रस भोजन के साथ शामिल करें जिससे आयरन अच्छे से पच सके।"
        },
        "Kannada": {
            "title": "ವಿಟಮಿನ್ ಸಿ — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": "ರೋಗನಿರೋಧಕ ಶಕ್ತಿ ಹೆಚ್ಚಿಸುತ್ತದೆ ಮತ್ತು ದೇಹವು ಕಬ್ಬಿಣದ ಅಂಶವನ್ನು ಹೀರಿಕೊಳ್ಳಲು ನೆರವಾಗುತ್ತದೆ.",
            "food_sources": "ನೆಲ್ಲಿಕಾಯಿ (ಅತ್ಯುತ್ತಮ ಮೂಲ), ಸೀಬೆಹಣ್ಣು (ಪೇರಲ), ಕಿತ್ತಳೆ, ನಿಂಬೆಹಣ್ಣು, ಟೊಮೆಟೊ.",
            "deficiency_symptoms": "ಒಸಡುಗಳಿಂದ ರಕ್ತಸ್ರಾವ, ಗಾಯಗಳು ತಡವಾಗಿ ಗುಣವಾಗುವುದು, ಸುಸ್ತು.",
            "dietary_guidance": "ನೆಲ್ಲಿಕಾಯಿ ಅಥವಾ ಸಿಟ್ರಸ್ ಹಣ್ಣುಗಳನ್ನು ಊಟದ ಜೊತೆಗೆ ಸೇವಿಸುವುದು ಉತ್ತಮ."
        }
    },

    # ── VITAMIN D ──────────────────────────────────────────────────────────
    "vitamin d": {
        "English": {
            "title": "Vitamin D — Nutrition Information",
            "importance": "Aids calcium absorption, bone strength, and immunity for mother and baby.",
            "food_sources": "Safe midday sunlight (15-30 mins), fatty fish (mackerel, sardines), egg yolks, fortified milk.",
            "deficiency_symptoms": "Bone pain, muscle weakness, rickets in infants. Blood test confirms.",
            "dietary_guidance": "Sunlight exposure is essential. Discuss pediatric Vitamin D drops with your doctor."
        },
        "Malayalam": {
            "title": "വിറ്റാമിൻ ഡി — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": "കാൽസ്യം ആഗിരണം ചെയ്യുന്നതിനും എല്ലുകളുടെ ബലത്തിനും വിറ്റാമിൻ ഡി അത്യന്താപേക്ഷിതമാണ്.",
            "food_sources": "സൂര്യപ്രകാശം (രാവിലെ/ഉച്ചയ്ക്ക് 15-20 മിനിറ്റ്), മത്തി, അയല, മുട്ടയുടെ മഞ്ഞക്കരു, പാൽ.",
            "deficiency_symptoms": "എല്ലുവേദന, പേശി ബലഹീനത, കുട്ടികളിലെ കണ രോഗം (റിക്കറ്റ്സ്).",
            "dietary_guidance": "കുഞ്ഞുങ്ങൾക്ക് വിറ്റാമിൻ ഡി തുള്ളിമരുന്ന് നൽകുന്നതിനെക്കുറിച്ച് ഡോക്ടറോട് ചോദിക്കുക."
        },
        "Hindi": {
            "title": "विटामिन डी — पोषण संबंधी जानकारी",
            "importance": "हड्डियों को मजबूत बनाने और कैल्शियम सोखने के लिए विटामिन डी आवश्यक है।",
            "food_sources": "धूप (15-20 मिनट), मछली, अंडे की जर्दी, फोर्टिफाइड दूध।",
            "deficiency_symptoms": "हड्डियों और जोड़ों में दर्द, मांसपेशियों में कमजोरी।",
            "dietary_guidance": "शिशुओं के लिए विटामिन डी ड्रॉप्स के बारे में बाल रोग विशेषज्ञ से सलाह लें।"
        },
        "Kannada": {
            "title": "ವಿಟಮಿನ್ ಡಿ — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": "ಕ್ಯಾಲ್ಸಿಯಂ ಹೀರಿಕೊಳ್ಳಲು ಮತ್ತು ಮೂಳೆಗಳ ಸದೃಢತೆಗೆ ವಿಟಮಿನ್ ಡಿ ಅತ್ಯಗತ್ಯ.",
            "food_sources": "ಬೆಳಗಿನ ಬಿಸಿಲು, ಮೀನು, ಮೊಟ್ಟೆಯ ಹಳದಿ ಭಾಗ, ಹಾಲು.",
            "deficiency_symptoms": "ಮೂಳೆ ನೋವು, ಸ್ನಾಯು ದೌರ್ಬಲ್ಯ, ಮಕ್ಕಳಲ್ಲಿ ಮೂಳೆ ಬಾಗುವಿಕೆ.",
            "dietary_guidance": "ಮಕ್ಕಳಿಗೆ ವಿಟಮಿನ್ ಡಿ ಹನಿಗಳ ಬಗ್ಗೆ ಮಕ್ಕಳ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ."
        }
    },

    # ── VITAMIN E ──────────────────────────────────────────────────────────
    "vitamin e": {
        "English": {
            "title": "Vitamin E — Nutrition Information",
            "importance": "Protects cellular health, supports healthy skin, eyes, and immune function.",
            "food_sources": "Sunflower seeds, peanuts, almonds, sesame oil, spinach.",
            "deficiency_symptoms": "Muscle weakness, numbness, impaired immune response.",
            "dietary_guidance": "A handful of mixed nuts and healthy traditional cooking oils usually provide enough."
        },
        "Malayalam": {
            "title": "വിറ്റാമിൻ ഇ — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": "കോശങ്ങളുടെ ആരോഗ്യം, തിളക്കമുള്ള ചർമ്മം, പ്രതിരോധശേഷി എന്നിവയ്ക്ക് സഹായിക്കുന്നു.",
            "food_sources": "നിലക്കടല, ബദാം, സൂര്യകാന്തി വിത്തുകൾ, എള്ളെണ്ണ, ചീര.",
            "deficiency_symptoms": "പേശി തളർച്ച, പ്രതിരോധശേഷിക്കുറവ്.",
            "dietary_guidance": "ദിവസവും കുറച്ച് നിലക്കടലയോ ബദാമോ കഴിക്കുന്നത് വിറ്റാമിൻ ഇ നൽകും."
        },
        "Hindi": {
            "title": "विटामिन ई — पोषण संबंधी जानकारी",
            "importance": "कोशिकाओं की सुरक्षा, त्वचा और आंखों की सेहत के लिए एंटीऑक्सीडेंट का काम करता है।",
            "food_sources": "मूंगफली, बादाम, सूरजमुखी के बीज, तिल का तेल, पालक।",
            "deficiency_symptoms": "मांसपेशियों में कमजोरी, सुन्नता।",
            "dietary_guidance": "सूखे मेवे (बादाम, मूंगफली) का संतुलित सेवन पर्याप्त विटामिन ई देता है।"
        },
        "Kannada": {
            "title": "ವಿಟಮಿನ್ ಇ — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": "ಕೋಶಗಳ ರಕ್ಷಣೆ, ಚರ್ಮದ ಕಾಂತಿ ಮತ್ತು ರೋಗನಿರೋಧಕ ಶಕ್ತಿಗೆ ಉಪಯುಕ್ತ.",
            "food_sources": "ಕಡಲೆಕಾಯಿ, ಬಾದಾಮಿ, ಸೂರ್ಯಕಾಂತಿ ಬೀಜಗಳು, ಎಳ್ಳೆಣ್ಣೆ, ಪಾಲಕ್.",
            "deficiency_symptoms": "ಸ್ನಾಯು ದೌರ್ಬಲ್ಯ.",
            "dietary_guidance": "ಬಾದಾಮಿ ಅಥವಾ ಕಡಲೆಕಾಯಿ ಸೇವನೆಯು ಉತ್ತಮ ಪೋಷಣೆ ನೀಡುತ್ತದೆ."
        }
    },

    # ── MAGNESIUM ──────────────────────────────────────────────────────────
    "magnesium": {
        "English": {
            "title": "Magnesium — Nutrition Information",
            "importance": "Regulates muscle and nerve function, blood pressure, blood sugar, and sleep.",
            "food_sources": "Almonds, cashews, peanuts, pumpkin seeds, whole wheat roti, bajra, ragi, dal, spinach, bananas.",
            "deficiency_symptoms": "Muscle twitches, cramps, insomnia, fatigue.",
            "dietary_guidance": "Eat whole millets, dals, and leafy greens for natural magnesium."
        },
        "Malayalam": {
            "title": "മഗ്നീഷ്യം — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": "പേശികളുടെയും നാഡികളുടെയും ആരോഗ്യം, രക്തസമ്മർദ്ദം നിയന്ത്രിക്കൽ, നല്ല ഉറക്കം എന്നിവയ്ക്ക് ആവശ്യമാണ്.",
            "food_sources": "ബദാം, കശുവണ്ടി, നിലക്കടല, മത്തങ്ങാവിത്ത്, റാഗി, പരിപ്പ്, ചീര, ഏത്തപ്പഴം.",
            "deficiency_symptoms": "പേശിവലിവ്, ഉറക്കമില്ലായ്മ, അമിത ക്ഷീണം.",
            "dietary_guidance": "റാഗിയും പയറുവർഗ്ഗങ്ങളും ഭക്ഷണത്തിൽ ഉൾപ്പെടുത്തുന്നത് ആവശ്യത്തിന് മഗ്നീഷ്യം നൽകും."
        },
        "Hindi": {
            "title": "मैग्नीशियम — पोषण संबंधी जानकारी",
            "importance": "मांसपेशियों के खिंचाव को कम करने, अच्छी नींद और रक्तचाप नियंत्रण के लिए आवश्यक है।",
            "food_sources": "बादाम, काजू, मूंगफली, कद्दू के बीज, रागी, बाजरा, दालें, पालक, केला।",
            "deficiency_symptoms": "मांसपेशियों में ऐंठन, अनिद्रा, थकान।",
            "dietary_guidance": "मोटे अनाज (बाजरा, रागी) और हरी सब्जियां मैग्नीशियम से भरपूर होती हैं।"
        },
        "Kannada": {
            "title": "ಮ್ಯಾಗ್ನೀಸಿಯಮ್ — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": "ಸ್ನಾಯುಗಳ ಶಾಂತತೆ, ನಿದ್ರೆ ಮತ್ತು ರಕ್ತದೊತ್ತಡ ನಿಯಂತ್ರಣಕ್ಕೆ ಸಹಕಾರಿ.",
            "food_sources": "ಬಾದಾಮಿ, ಗೋಡಂಬಿ, ಕಡಲೆಕಾಯಿ, ರಾಗಿ, ಸಿರಿಧಾನ್ಯಗಳು, ಬೇಳೆಕಾಳುಗಳು, ಬಾಳೆಹಣ್ಣು.",
            "deficiency_symptoms": "ಸ್ನಾಯು ಸೆಳೆತ, ನಿದ್ರಾಹೀನತೆ.",
            "dietary_guidance": "ಸಿರಿಧಾನ್ಯಗಳು ಮತ್ತು ಹಸಿರು ಸೊಪ್ಪುಗಳನ್ನು ನಿಯಮಿತವಾಗಿ ಸೇವಿಸಿ."
        }
    },

    # ── ZINC ───────────────────────────────────────────────────────────────
    "zinc": {
        "English": {
            "title": "Zinc — Nutrition Information",
            "importance": "Crucial for immune defense, wound healing, taste sensation, and healthy growth.",
            "food_sources": "Chickpeas (chana), lentils, pumpkin seeds, sesame seeds, cashews, dairy, eggs, meat.",
            "deficiency_symptoms": "Poor immunity, slow healing, loss of taste/appetite, growth faltering in children.",
            "dietary_guidance": "Soaking and sprouting legumes improves zinc absorption."
        },
        "Malayalam": {
            "title": "സിങ്ക് — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": "രോഗപ്രതിരോധശേഷി, മുറിവുകൾ ഉണങ്ങൽ, കുഞ്ഞുങ്ങളുടെ വളർച്ച എന്നിവയ്ക്ക് സിങ്ക് ആവശ്യമാണ്.",
            "food_sources": "കടല, പയറുവർഗ്ഗങ്ങൾ, മത്തങ്ങാവിത്ത്, എള്ള്, കശുവണ്ടി, പാൽ ഉൽപന്നങ്ങൾ, മുട്ട, ഇറച്ചി.",
            "deficiency_symptoms": "അടിക്കടി വരുന്ന അസുഖങ്ങൾ, മുറിവുകൾ ഉണങ്ങാതിരിക്കുക, വിശപ്പില്ലായ്മ.",
            "dietary_guidance": "പയർ മുളപ്പിച്ച് കഴിക്കുന്നത് സിങ്ക് ശരീരം ആഗിരണം ചെയ്യുന്നത് എളുപ്പമാക്കുന്നു."
        },
        "Hindi": {
            "title": "जिंक (जस्ता) — पोषण संबंधी जानकारी",
            "importance": "प्रतिरोधक क्षमता बढ़ाने, घाव भरने और बच्चों के समुचित शारीरिक विकास के लिए जरूरी है।",
            "food_sources": "चना, दालें, कद्दू के बीज, तिल, काजू, दूध, पनीर, अंडे, चिकन।",
            "deficiency_symptoms": "बार-बार बीमार पड़ना, भूख न लगना, बच्चों का विकास धीमा होना।",
            "dietary_guidance": "दालों और चने को अंकुरित (स्प्राउट) करके खाने से जिंक भरपूर मिलता है।"
        },
        "Kannada": {
            "title": "ಜಿಂಕ್ (ಸತು) — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": "ರೋಗನಿರೋಧಕ ಶಕ್ತಿ ಮತ್ತು ಮಕ್ಕಳ ಆರೋಗ್ಯಕರ ಬೆಳವಣಿಗೆಗೆ ಜಿಂಕ್ ಅತ್ಯಗತ್ಯ.",
            "food_sources": "ಕಡಲೆಕಾಳು, ಬೇಳೆಗಳು, ಕುಂಬಳಕಾಯಿ ಬೀಜಗಳು, ಎಳ್ಳು, ಹಾಲು, ಮೊಟ್ಟೆ.",
            "deficiency_symptoms": "ಆಗಾಗ ಅನಾರೋಗ್ಯ, ಹಸಿವಾಗದಿರುವುದು.",
            "dietary_guidance": "ಕಾಳುಗಳನ್ನು ಮೊಳಕೆ ಕಟ್ಟಿ ತಿನ್ನುವುದರಿಂದ ಜಿಂಕ್ ಅಂಶ ಸುಲಭವಾಗಿ ಸಿಗುತ್ತದೆ."
        }
    },

    # ── PROTEIN ────────────────────────────────────────────────────────────
    "protein": {
        "English": {
            "title": "Protein — Nutrition Information",
            "importance": "The building block for cells, muscles, hormones, and infant tissue growth.",
            "food_sources": "Dals (moong, toor, masoor), paneer, curd, eggs, chicken, fish, soya, rajma, peanuts.",
            "deficiency_symptoms": "Muscle loss, chronic weakness, hair thinning, poor growth in children.",
            "dietary_guidance": "Pair dal + rice or dal + roti for a complete amino acid profile at every meal."
        },
        "Malayalam": {
            "title": "പ്രോട്ടീൻ — പോഷകാഹാര വിവരങ്ങൾ",
            "importance": "ശരീരകോശങ്ങളുടെയും പേശികളുടെയും നിർമ്മാണത്തിനും കുഞ്ഞിന്റെ വളർച്ചയ്ക്കും പ്രോട്ടീൻ ഒഴിച്ചുകൂടാനാവാത്തതാണ്.",
            "food_sources": "ചെറുപയർ, തുവരപ്പരിപ്പ്, പനീർ, തൈര്, മുട്ട, മത്സ്യം, ചിക്കൻ, സോയാബീൻ, നിലക്കടല.",
            "deficiency_symptoms": "പേശീക്ഷയം, അമിതമായ ക്ഷീണം, കുട്ടികളിലെ ഭാരക്കുറവ്.",
            "dietary_guidance": "പരിപ്പും ചോറും അല്ലെങ്കിൽ റൊട്ടിയും പരിപ്പും ചേർത്തുകഴിക്കുന്നത് സമ്പൂർണ്ണ പ്രോട്ടീൻ നൽകുന്നു."
        },
        "Hindi": {
            "title": "प्रोटीन — पोषण संबंधी जानकारी",
            "importance": "मांसपेशियों के निर्माण, शरीर की मरम्मत और बच्चे के समुचित विकास के लिए सबसे महत्वपूर्ण है।",
            "food_sources": "मूंग/तूर दाल, पनीर, दही, अंडे, चिकन, मछली, सोयाबीन, राजमा, मूंगफली।",
            "deficiency_symptoms": "कमजोरी, मांसपेशियों में कमी, बच्चों का वजन न बढ़ना।",
            "dietary_guidance": "दाल-चावल या दाल-रोटी का संयोजन संपूर्ण प्रोटीन (सभी अमीनो एसिड) प्रदान करता है।"
        },
        "Kannada": {
            "title": "ಪ್ರೋಟೀನ್ — ಪೌಷ್ಟಿಕಾಂಶದ ಮಾಹಿತಿ",
            "importance": "ದೇಹದ ಕೋಶಗಳು ಮತ್ತು ಸ್ನಾಯುಗಳ ಬೆಳವಣಿಗೆಗೆ ಪ್ರೋಟೀನ್ ಅತ್ಯಗತ್ಯ.",
            "food_sources": "ತೊಗರಿಬೇಳೆ, ಹೆಸರುಬೇಳೆ, ಪನೀರ್, ಮೊಸರು, ಮೊಟ್ಟೆ, ಮೀನು, ಚಿಕನ್, ಕಡಲೆಕಾಯಿ.",
            "deficiency_symptoms": "ದೌರ್ಬಲ್ಯ, ಸ್ನಾಯುಗಳ ಕ್ಷೀಣತೆ, ಮಕ್ಕಳ ತೂಕ ಕಡಿಮೆಯಾಗುವುದು.",
            "dietary_guidance": "ಬೇಳೆ-ಅನ್ನ ಅಥವಾ ಬೇಳೆ-ರೊಟ್ಟಿ ಸೇವನೆಯು ಸಮತೋಲಿತ ಪ್ರೋಟೀನ್ ಒದಗಿಸುತ್ತದೆ."
        }
    }
}

# =============================================================================
# Multilingual Context-Specific Guidance (Pregnancy, Postnatal, Child, General)
# =============================================================================

CONTEXT_GUIDANCE = {
    "English": {
        "pregnancy": (
            "## Nutrition Guidance During Pregnancy (Indian Diet)\n\n"
            "A balanced Indian meal plan meets maternal and fetal needs:\n"
            "• **Key Nutrients:** Folic acid for neural development, iron to prevent anaemia, calcium & Vitamin D for bone growth, and protein at every meal.\n"
            "• **Meal Ideas:** Ragi porridge or idli/sambar for breakfast; roti + dal + seasonal greens + curd for lunch; fruit or roasted chana as snacks.\n"
            "• **Avoid:** Raw/undercooked meat/eggs, unpasteurised milk, excessive caffeine, and unwashed produce."
        ),
        "postnatal": (
            "## Nutrition Guidance After Delivery (Postnatal & Lactation)\n\n"
            "Promotes recovery and supports healthy breast milk production:\n"
            "• **Hydration & Fluids:** Drink plenty of warm water, dal soup, buttermilk, or kanji.\n"
            "• **Traditional Indian Foods:** Ragi porridge (calcium & iron), dink/methi ladoo, ajwain water, and halim seeds.\n"
            "• **Nutrient Focus:** Protein (dals, paneer, eggs), iron-rich greens, and calcium."
        ),
        "general": (
            "## General Maternal Nutrition Principles\n\n"
            "• Include a portion of dal or pulse at every major meal.\n"
            "• Eat colorful vegetables and fresh fruits daily.\n"
            "• Drink adequate water throughout the day.\n"
            "• Choose whole grains (whole wheat, ragi, bajra) over refined flour."
        )
    },
    "Malayalam": {
        "pregnancy": (
            "## ഗർഭകാല പോഷകാഹാര നിർദ്ദേശങ്ങൾ (കേരള/ഇന്ത്യൻ ഭക്ഷണം)\n\n"
            "അമ്മയുടെയും കുഞ്ഞിന്റെയും ആരോഗ്യത്തിന് സമീകൃതാഹാരം ഉറപ്പാക്കാം:\n"
            "• **പ്രധാന പോഷകങ്ങൾ:** തലച്ചോറിന്റെ വളർച്ചയ്ക്ക് ഫോളിക് ആസിഡ്, വിളർച്ച തടയാൻ അയൺ, എല്ലുകളുടെ ബലത്തിന് കാൽസ്യവും വിറ്റാമിൻ ഡിയും, ശരീരപുഷ്ടിക്ക് പ്രോട്ടീൻ.\n"
            "• **ഭക്ഷണ ക്രമം:** പ്രഭാതഭക്ഷണത്തിന് റാഗി കുറുക്ക് അല്ലെങ്കിൽ ഇഡ്ഡലിയും സാമ്പാറും; ഉച്ചയ്ക്ക് ചോറ് + പരിപ്പ്/പയർ + ഇലക്കറി + തൈര്; വൈകുന്നേരം പഴങ്ങളോ പുഴുങ്ങിയ പയറോ.\n"
            "• **ശ്രദ്ധിക്കുക:** പച്ചമുട്ട, വേവിക്കാത്ത മാംസം, അമിതമായ ചായ/കാപ്പി എന്നിവ ഒഴിവാക്കുക."
        ),
        "postnatal": (
            "## പ്രസവാനന്തര പോഷകാഹാരം (മുലയൂട്ടുന്ന അമ്മമാർക്ക്)\n\n"
            "ശരീര സൗഖ്യത്തിനും മുലപ്പാൽ വർദ്ധനവിനും ഉചിതമായ ഭക്ഷണങ്ങൾ:\n"
            "• **ദ്രവരൂപത്തിലുള്ള ആഹാരം:** ധാരാളം തിളപ്പിച്ചാറിയ വെള്ളം, കഞ്ഞിവെള്ളം, സംഭാരം, പരിപ്പ് സൂപ്പ് എന്നിവ കുടിക്കുക.\n"
            "• **പരമ്പരാഗത ഭക്ഷണങ്ങൾ:** റാഗി കുറുക്ക് (കാൽസ്യവും അയണും), അയമോദക വെള്ളം, ഉലുവക്കഞ്ഞി, ഇലക്കറികൾ.\n"
            "• **പ്രോട്ടീൻ:** ചെറുപയർ, മുട്ട, പാൽ, മത്സ്യം എന്നിവ ഭക്ഷണത്തിൽ ഉൾപ്പെടുത്തുക."
        ),
        "general": (
            "## അമ്മമാർക്കുള്ള പൊതുവായ പോഷകാഹാര തത്വങ്ങൾ\n\n"
            "• ഓരോ നേരത്തെ ഭക്ഷണത്തിലും പരിപ്പോ പയറോ ഉൾപ്പെടുത്തുക.\n"
            "• ദിവസവും പച്ചക്കറികളും നാടൻ പഴങ്ങളും കഴിക്കുക.\n"
            "• മൈദയ്ക്ക് പകരം റാഗി, തവിടുള്ള അരി, ഗോതമ്പ് എന്നിവ ഉപയോഗിക്കുക.\n"
            "• ദിവസവും ആവശ്യത്തിന് ശുദ്ധജലം കുടിക്കുക."
        )
    },
    "Hindi": {
        "pregnancy": (
            "## गर्भावस्था के दौरान पोषण संबंधी मार्गदर्शन (भारतीय आहार)\n\n"
            "मां और गर्भस्थ शिशु के संपूर्ण स्वास्थ्य के लिए संतुलित आहार लें:\n"
            "• **महत्वपूर्ण पोषक तत्व:** न्यूरल ट्यूब विकास के लिए फोलिक एसिड, एनीमिया से बचाव के लिए आयरन, मजबूत हड्डियों के लिए कैल्शियम और विटामिन डी, तथा कोशिकाओं के लिए प्रोटीन।\n"
            "• **आहार सुझाव:** नाश्ते में रागी दलिया, पोहा या इडली-सांभर; दोपहर के भोजन में रोटी + दाल + हरी पत्तेदार सब्जी + दही; शाम को भुना चना या फल।\n"
            "• **परहेज करें:** अधपका मांस या अंडा, बासी खाना, अधिक चाय-कॉफ़ी और जंक फ़ूड।"
        ),
        "postnatal": (
            "## प्रसवोत्तर पोषण और स्तनपान कराने वाली माताओं के लिए मार्गदर्शन\n\n"
            "प्रसव के बाद शरीर की रिकवरी और पर्याप्त दूध बनने के लिए:\n"
            "• **तरल पदार्थ:** खूब गुनगुना पानी, दाल का पानी, छाछ और दलिया लें।\n"
            "• **पारंपरिक खाद्य पदार्थ:** रागी, मेथी/गोंद के लड्डू, अजवाइन का पानी, और हरी सब्जियां।\n"
            "• **प्रोटीन और कैल्शियम:** दालें, पनीर, दूध, और उबला अंडा शामिल करें।"
        ),
        "general": (
            "## स्वस्थ पोषण के मूल सिद्धांत\n\n"
            "• प्रत्येक भोजन में दाल या दाल उत्पाद शामिल करें।\n"
            "• मौसमी ताजे फल और हरी सब्जियां रोजाना खाएं।\n"
            "• पूरे दिन पर्याप्त मात्रा में पानी पिएं।\n"
            "• मैदा के स्थान पर साबुत अनाज (गेहूं, रागी, बाजरा) का प्रयोग करें।"
        )
    },
    "Kannada": {
        "pregnancy": (
            "## ಗರ್ಭಾವಸ್ಥೆಯ ಪೌಷ್ಟಿಕಾಂಶದ ಮಾರ್ಗದರ್ಶನ (ಭಾರತೀಯ ಆಹಾರ)\n\n"
            "ತಾಯಿ ಮತ್ತು ಮಗುವಿನ ಆರೋಗ್ಯಕ್ಕಾಗಿ ಸಮತೋಲಿತ ಆಹಾರವನ್ನು ಸೇವಿಸಿ:\n"
            "• **ಮುಖ್ಯ ಪೋಷಕಾಂಶಗಳು:** ಮೆದುಳಿನ ಬೆಳವಣಿಗೆಗೆ ಫೋಲಿಕ್ ಆಮ್ಲ, ರಕ್ತಹೀನತೆ ತಡೆಯಲು ಐರನ್, ಮೂಳೆಗಳಿಗೆ ಕ್ಯಾಲ್ಸಿಯಂ ಮತ್ತು ವಿಟಮಿನ್ ಡಿ, ಹಾಗೂ ಪ್ರೋಟೀನ್.\n"
            "• **ಆಹಾರ ಕ್ರಮ:** ಉಪಾಹಾರಕ್ಕೆ ರಾಗಿ ಗಂಜಿ ಅಥವಾ ಇಡ್ಲಿ-ಸಾಂಬಾರ್; ಮಧ್ಯಾಹ್ನದ ಊಟಕ್ಕೆ ರೊಟ್ಟಿ/ಅನ್ನ + ಬೇಳೆಕಾಳು + ಹಸಿರು ಸೊಪ್ಪು + ಮೊಸರು; ಸಂಜೆ ಹಣ್ಣುಗಳು.\n"
            "• **ತ್ಯಜಿಸಬೇಕಾದವು:** ಬೇಯಿಸದ ಆಹಾರ, ಅತಿಯಾದ ಕಾಫಿ/ಟೀ, ಹೊರಗಿನ ಜಂಕ್ ಫುಡ್."
        ),
        "postnatal": (
            "## ಹೆರಿಗೆಯ ನಂತರದ ಆಹಾರ ಮತ್ತು ಬಾಣಂತನದ ಆರೈಕೆ\n\n"
            "ತಾಯಿಯ ಚೇತರಿಕೆ ಮತ್ತು ಎದೆಹಾಲಿನ ಉತ್ಪಾದನೆಗೆ:\n"
            "• **ದ್ರವಾಹಾರ:** ಸಾಕಷ್ಟು ಉಗುರುಬೆಚ್ಚಗಿನ ನೀರು, ಮಜ್ಜಿಗೆ, ಬೇಳೆ ಸಾರು ಸೇವಿಸಿ.\n"
            "• **ಸಾಂಪ್ರದಾಯಿಕ ಆಹಾರ:** ರಾಗಿ ಅಂಬಲಿ, ಮೆಂತ್ಯದ ಲಾಡು, ಓಂಕಾಳು ನೀರು, ಸೊಪ್ಪಿನ ಸಾರು.\n"
            "• **ಪೋಷಕಾಂಶಗಳು:** ತೊಗರಿಬೇಳೆ, ಹಾಲು, ಮೊಟ್ಟೆ ಮತ್ತು ಹಣ್ಣುಗಳನ್ನು ಸೇವಿಸಿ."
        ),
        "general": (
            "## ತಾಯಂದಿರಿಗಾಗಿ ಸಾಮಾನ್ಯ ಪೌಷ್ಟಿಕಾಂಶದ ನಿಯಮಗಳು\n\n"
            "• ಪ್ರತಿದಿನ ಊಟದಲ್ಲಿ ಬೇಳೆ ಅಥವಾ ಕಾಳುಗಳನ್ನು ಸೇರಿಸಿ.\n"
            "• ತಾಜಾ ಸೊಪ್ಪು ಮತ್ತು ಹಣ್ಣುಗಳನ್ನು ಸೇವಿಸಿ.\n"
            "• ದಿನವಿಡೀ ಸಾಕಷ್ಟು ನೀರು ಕುಡಿಯಿರಿ.\n"
            "• ರಾಗಿ, ಜೋಳ, ಸಜ್ಜೆ ಮುಂತಾದ ಸಿರಿಧಾನ್ಯಗಳನ್ನು ಬಳಸಿ."
        )
    }
}

# =============================================================================
# Child Age Milestones Guidance
# =============================================================================

def get_child_age_guidance(age_months, language='English'):
    """Returns child age guidance in the requested language."""
    if language == 'Malayalam':
        if age_months < 6:
            return (
                "## ശിശു പോഷകാഹാരം: ജനനം മുതൽ 6 മാസം വരെ\n\n"
                "• **മുലപ്പാൽ മാത്രം നൽകുക (Exclusive Breastfeeding):** ആദ്യ 6 മാസം മുലപ്പാൽ അല്ലാതെ വെള്ളമോ മറ്റ് പാനീയങ്ങളോ ആഹാരമോ നൽകരുത്.\n"
                "• കുഞ്ഞിന് ആവശ്യമായ എല്ലാ പോഷകങ്ങളും വെള്ളവും മുലപ്പാലിൽ അടങ്ങിയിട്ടുണ്ട്."
            )
        elif age_months < 12:
            return (
                f"## ശിശു പോഷകാഹാരം: 6 മുതൽ 12 മാസം വരെ (പ്രായം: ഏകദേശം {age_months} മാസം)\n\n"
                "• മുലപ്പാലിനൊപ്പം കുറുക്കുകൾ നൽകിത്തുടങ്ങാം.\n"
                "• റാഗി കുറുക്ക്, നന്നായി വെന്ത ചോറും ചെറുപയറും ചേർത്ത കിച്ച്ഡി, ഉടച്ച ഏത്തപ്പഴം, പുഴുങ്ങിയ മത്തങ്ങ.\n"
                "• ഒരു വയസ്സുവരെ ഉപ്പും പഞ്ചസാരയും തേനും കുഞ്ഞുങ്ങൾക്ക് നൽകരുത്."
            )
        elif age_months < 24:
            return (
                f"## ശിശു പോഷകാഹാരം: 12 മുതൽ 24 മാസം വരെ (പ്രായം: ഏകദേശം {age_months} മാസം)\n\n"
                "• വീട്ടിലെ സാധാരണ സമീകൃതാഹാരം മൃദുവാക്കി നൽകാം (ചോറ്, പരിപ്പ്, ഇഡ്ഡലി, റാഗി, തൈര്, പുഴുങ്ങിയ മുട്ട).\n"
                "• രണ്ടു വയസ്സുവരെ മുലപ്പാൽ നൽകുന്നത് തുടരുക.\n"
                "• പച്ചക്കറികളും പഴങ്ങളും ദിവസവും നൽകുക."
            )
        elif age_months < 60:
            years = age_months // 12
            return (
                f"## ബാല്യകാല പോഷകാഹാരം: 2 മുതൽ 5 വയസ്സ് വരെ (പ്രായം: ഏകദേശം {years} വയസ്സ്)\n\n"
                "• സമീകൃതാഹാരം നൽകുക: ചോറ്, റൊട്ടി, പയറുവർഗ്ഗങ്ങൾ, ഇലക്കറികൾ, പാൽ, മുട്ട, പഴങ്ങൾ.\n"
                "• ചിപ്സ്, മിഠായികൾ തുടങ്ങിയ ജങ്ക് ഫുഡുകൾ ഒഴിവാക്കുക."
            )
        else:
            years = age_months // 12
            return (
                f"## സ്കൂൾ പ്രായത്തിലുള്ള കുട്ടികളുടെ പോഷകാഹാരം: 5 വയസ്സിനു മുകളിൽ (പ്രായം: ഏകദേശം {years} വയസ്സ്)\n\n"
                "• വളർച്ചയ്ക്കും പഠനത്തിനും ആവശ്യമായ ഊർജ്ജസ്വലമായ സമീകൃതാഹാരം നൽകുക.\n"
                "• പ്രഭാതഭക്ഷണം മുടക്കരുത്. നട്സ്, പഴങ്ങൾ, പച്ചക്കറികൾ ശീലമാക്കുക."
            )
    elif language == 'Hindi':
        if age_months < 6:
            return (
                "## शिशु पोषण: जन्म से 6 महीने तक\n\n"
                "• **केवल स्तनपान (Exclusive Breastfeeding):** पहले 6 महीने शिशु को केवल मां का दूध दें। पानी, घुट्टी या अन्य आहार बिल्कुल न दें।"
            )
        elif age_months < 12:
            return (
                f"## शिशु पोषण: 6 से 12 महीने (उम्र: लगभग {age_months} माह)\n\n"
                "• स्तनपान के साथ नरम पूरक आहार शुरू करें।\n"
                "• पतली मूंग दाल-चावल की खिचड़ी, रागी का दलिया, मसला हुआ केला, उबला कद्दू।\n"
                "• 1 वर्ष से कम उम्र के बच्चों को नमक, चीनी और शहद न दें।"
            )
        elif age_months < 24:
            return (
                f"## शिशु पोषण: 12 से 24 महीने (उम्र: लगभग {age_months} माह)\n\n"
                "• घर का बना नरम पौष्टिक खाना (दाल-खिचड़ी, सूजी खीर, इडली, दही, उबला अंडा) दें।\n"
                "• 2 वर्ष तक स्तनपान जारी रखें और दिन में 3 बार खाना व 2 बार स्वस्थ स्नैक्स दें।"
            )
        elif age_months < 60:
            years = age_months // 12
            return (
                f"## बाल पोषण: 2 से 5 वर्ष (उम्र: लगभग {years} वर्ष)\n\n"
                "• दाल, रोटी, चावल, हरी सब्जियां, फल और दूध से भरपूर संतुलित आहार दें।"
            )
        else:
            years = age_months // 12
            return (
                f"## स्कूली बच्चों का पोषण: 5 वर्ष से अधिक (उम्र: लगभग {years} वर्ष)\n\n"
                "• पढ़ाई और खेलकूद के लिए ऊर्जावान पौष्टिक भोजन दें। नाश्ता कभी न छोड़ें।"
            )
    elif language == 'Kannada':
        if age_months < 6:
            return (
                "## ಶಿಶು ಪೌಷ್ಟಿಕಾಂಶ: ಹುಟ್ಟಿನಿಂದ 6 ತಿಂಗಳವರೆಗೆ\n\n"
                "• **ಕೇವಲ ತಾಯಿಯ ಹಾಲು (Exclusive Breastfeeding):** ಮೊದಲ 6 ತಿಂಗಳು ಮಗುವಿಗೆ ಕೇವಲ ಎದೆಹಾಲು ಮಾತ್ರ ನೀಡಿ. ನೀರು ಅಥವಾ ಇತರೆ ಯಾವುದೇ ಆಹಾರ ಬೇಡ."
            )
        elif age_months < 12:
            return (
                f"## ಶಿಶು ಪೌಷ್ಟಿಕಾಂಶ: 6 ರಿಂದ 12 ತಿಂಗಳು (ವಯಸ್ಸು: ಸುಮಾರು {age_months} ತಿಂಗಳು)\n\n"
                "• ಎದೆಹಾಲಿನ ಜೊತೆಗೆ ಮೃದುವಾದ ಪೂರಕ ಆಹಾರ ಪ್ರಾರಂಭಿಸಿ.\n"
                "• ರಾಗಿ ಸರಿ, ಮೃದುವಾದ ಬೇಳೆ-ಅನ್ನದ ಕಿಚಡಿ, ಹಿಸುಕಿದ ಬಾಳೆಹಣ್ಣು.\n"
                "• ಒಂದು ವರ್ಷದವರೆಗೆ ಸಕ್ಕರೆ, ಉಪ್ಪು ಮತ್ತು ಜೇನುತುಪ್ಪ ನೀಡಬೇಡಿ."
            )
        elif age_months < 24:
            return (
                f"## ಶಿಶು ಪೌಷ್ಟಿಕಾಂಶ: 12 ರಿಂದ 24 ತಿಂಗಳು (ವಯಸ್ಸು: ಸುಮಾರು {age_months} ತಿಂಗಳು)\n\n"
                "• ಮನೆಯ ಮೃದುವಾದ ಸಮತೋಲಿತ ಆಹಾರ (ಕಿಚಡಿ, ಇಡ್ಲಿ, ಮೊಸರು, ಹಿಸುಕಿದ ಹಣ್ಣುಗಳು) ನೀಡಿ.\n"
                "• 2 ವರ್ಷಗಳವರೆಗೆ ಎದೆಹಾಲು ಮುಂದುವರಿಸಿ."
            )
        elif age_months < 60:
            years = age_months // 12
            return (
                f"## ಮಕ್ಕಳ ಪೌಷ್ಟಿಕಾಂಶ: 2 ರಿಂದ 5 ವರ್ಷ (ವಯಸ್ಸು: ಸುಮಾರು {years} ವರ್ಷ)\n\n"
                "• ಬೇಳೆ, ಅನ್ನ, ರಾಗಿ ಮುದ್ದೆ, ಹಸಿರು ತರಕಾರಿಗಳು, ಮೊಟ್ಟೆ ಮತ್ತು ಹಾಲು ನೀಡಿ."
            )
        else:
            years = age_months // 12
            return (
                f"## ಶಾಲಾ ಮಕ್ಕಳ ಪೌಷ್ಟಿಕಾಂಶ: 5 ವರ್ಷ ಮೇಲ್ಪಟ್ಟ ಮಕ್ಕಳಿಗೆ (ವಯಸ್ಸು: ಸುಮಾರು {years} ವರ್ಷ)\n\n"
                "• ಬೆಳವಣಿಗೆ ಮತ್ತು ವಿದ್ಯಾಭ್ಯಾಸಕ್ಕಾಗಿ ಪೌಷ್ಟಿಕ ಸಮತೋಲಿತ ಆಹಾರ ನೀಡಿ. ಜಂಕ್ ಫುಡ್ ಕಡಿಮೆ ಮಾಡಿ."
            )
    else:  # English default
        if age_months < 6:
            return (
                "## Infant Nutrition: Birth to 6 Months\n\n"
                "• **Exclusive Breastfeeding:** Only breast milk for the first 6 months. No water, formula (unless medically advised), or solid food."
            )
        elif age_months < 12:
            return (
                f"## Complementary Feeding: 6 to 12 Months (Age: approx {age_months} months)\n\n"
                "• Introduce soft purees alongside continued breastfeeding.\n"
                "• Ragi porridge, mashed moong dal khichdi, mashed banana, cooked sweet potato.\n"
                "• Avoid salt, sugar, and honey before 1 year."
            )
        elif age_months < 24:
            return (
                f"## Toddler Nutrition: 12 to 24 Months (Age: approx {age_months} months)\n\n"
                "• Transition to modified family food: khichdi, soft idli, curd, mashed fruits.\n"
                "• Continue breastfeeding on demand up to 2 years and beyond.\n"
                "• Offer 3 small meals and 2 healthy snacks daily."
            )
        elif age_months < 60:
            years = age_months // 12
            return (
                f"## Young Child Nutrition: 2 to 5 Years (Age: approx {years} years)\n\n"
                "• Diverse family meals: dal, rice/roti, seasonal vegetables, milk/curd, eggs.\n"
                "• Encourage independent eating and healthy eating habits."
            )
        else:
            years = age_months // 12
            return (
                f"## School-age Child Nutrition: 5+ Years (Age: approx {years} years)\n\n"
                "• Balanced diet for school growth, learning, and physical activity.\n"
                "• Wholesome breakfasts, fruits, nuts, pulses, and greens. Limit processed junk foods."
            )

# =============================================================================
# Multilingual Disclaimers
# =============================================================================

DISCLAIMERS = {
    "English": (
        "> **Health Notice:** This information is for general nutrition awareness only. "
        "It is not a medical diagnosis. If you have concerns about deficiency symptoms, pregnancy, "
        "or infant feeding, please consult a qualified healthcare professional. Blood tests are needed to confirm deficiencies."
    ),
    "Malayalam": (
        "> **ആരോഗ്യ മുന്നറിയിപ്പ്:** ഈ വിവരങ്ങൾ പൊതുവായ പോഷകാഹാര അവബോധത്തിന് മാത്രമുള്ളതാണ്. "
        "ഇത് ഒരു മെഡിക്കൽ രോഗനിർണയമല്ല. എന്തെങ്കിലും ലക്ഷണങ്ങളോ സംശയങ്ങളോ ഉണ്ടെങ്കിൽ ഒരു ഡോക്ടറെ സമീപിക്കുക. "
        "പോഷകക്കുറവ് സ്ഥിരീകരിക്കാൻ രക്തപരിശോധന ആവശ്യമാണ്."
    ),
    "Hindi": (
        "> **स्वास्थ्य सूचना:** यह जानकारी केवल सामान्य पोषण जागरूकता के लिए है, यह कोई चिकित्सीय निदान नहीं है। "
        "किसी भी लक्षण या समस्या के लिए योग्य डॉक्टर से परामर्श करें। पोषण की कमी की पुष्टि के लिए रक्त परीक्षण आवश्यक है।"
    ),
    "Kannada": (
        "> **ಆರೋಗ್ಯ ಸೂಚನೆ:** ಈ ಮಾಹಿತಿಯು ಸಾಮಾನ್ಯ ಪೌಷ್ಟಿಕಾಂಶದ ಅರಿವಿಗಾಗಿ ಮಾತ್ರ. ಇದು ಯಾವುದೇ ವೈದ್ಯಕೀಯ ರೋಗನಿರ್ಣಯವಲ್ಲ. "
        "ಯಾವುದೇ ರೋಗಲಕ್ಷಣಗಳಿದ್ದರೆ ಅರ್ಹ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ. ಪೌಷ್ಟಿಕಾಂಶದ ಕೊರತೆಯನ್ನು ದೃಢೀಕರಿಸಲು ರಕ್ತ ಪರೀಕ್ಷೆ ಅಗತ್ಯ."
    )
}

# =============================================================================
# Multilingual Keyword Normalization & Detection
# =============================================================================

NUTRIENT_KEYWORDS = {
    "iron": ["iron", "ഇരുമ്പ്", "അയൺ", "ആയൺ", "आयरन", "लोहा", "ಕಬ್ಬಿಣ", "ಕಬ್ಬಿಣಾಂಶ", "ಐರನ್"],
    "calcium": ["calcium", "കാൽസ്യം", "ക്യാൽസ്യം", "कैल्शियम", "कैलशियम", "ಕ್ಯಾಲ್ಸಿಯಂ", "ಸುಣ್ಣ"],
    "vitamin a": ["vitamin a", "വിറ്റാമിൻ എ", "ജീവകം എ", "विटामिन ए", "ವಿಟಮಿನ್ ಎ"],
    "vitamin b12": ["vitamin b12", "b12", "വിറ്റാമിൻ ബി12", "ജീവകം ബി12", "विटामिन बी12", "ವಿಟಮಿನ್ ಬಿ12"],
    "folate": ["folate", "folic", "ഫോളേറ്റ്", "ഫോളിക്", "फ़ोलेट", "फोलिक", "ಫೋಲೇಟ್", "ಫೋಲಿಕ್"],
    "vitamin c": ["vitamin c", "വിറ്റാമിൻ സി", "ജീവകം സി", "विटामिन सी", "ವಿಟಮಿನ್ ಸಿ"],
    "vitamin d": ["vitamin d", "വിറ്റാമിൻ ഡി", "ജീവകം ഡി", "विटामिन डी", "ವಿಟಮಿನ್ ಡಿ"],
    "vitamin e": ["vitamin e", "വിറ്റാമിൻ ഇ", "ജീവകം ഇ", "विटामिन ई", "ವಿಟಮಿನ್ ಇ"],
    "magnesium": ["magnesium", "മഗ്നീഷ്യം", "मैग्नीशियम", "ಮ್ಯಾಗ್ನೀಸಿಯಮ್"],
    "zinc": ["zinc", "സിങ്ക്", "जिंक", "ಜಸದ ಅಂಶ", "ಜಿಂಕ್"],
    "protein": ["protein", "പ്രോട്ടീൻ", "മാംസ്യം", "प्रोटीन", "ಪ್ರೋಟೀನ್"]
}

def _normalize(text):
    return re.sub(r'\s+', ' ', text.lower().strip())

def find_nutrient_match(question):
    """Detects nutrient from English, Malayalam, Hindi, or Kannada query."""
    q = _normalize(question)
    for nutrient, kws in NUTRIENT_KEYWORDS.items():
        for kw in kws:
            if kw.lower() in q:
                return nutrient
    return None

def build_fallback_response(question, context, language='English', child_age_months=None):
    """
    Generates an evidence-based knowledge-base answer in the chosen language.
    """
    if language not in ('English', 'Malayalam', 'Hindi', 'Kannada'):
        language = 'English'

    q = _normalize(question)
    nutrient = find_nutrient_match(q)

    # Detect context keywords in multiple scripts
    is_pregnancy = any(w in q for w in [
        'pregnant', 'pregnancy', 'trimester', 'antenatal', 'prenatal',
        'ഗർഭം', 'ഗർഭിണി', 'പ്രസവം', 'गर्भावस्था', 'गर्भवती', 'गर्भ', 'ಗರ್ಭಾವಸ್ಥೆ', 'ಗರ್ಭಿಣಿ'
    ]) or context == 'Pregnancy'

    is_postnatal = any(w in q for w in [
        'breastfeed', 'postnatal', 'after delivery', 'lactation', 'postpartum',
        'മുലയൂട്ടൽ', 'പ്രസവശേഷം', 'സ്തനपान', 'प्रसवोत्तर', 'ಹಾಲುಣಿಸುವಿಕೆ', 'ಹೆರಿಗೆಯ ನಂತರ'
    ]) or context == 'Postnatal Care'

    is_child = (child_age_months is not None) and (
        any(w in q for w in [
            'child', 'baby', 'infant', 'toddler', 'feed', 'solid', 'food', 'eat',
            'കുഞ്ഞ്', 'കുട്ടി', 'ശിശു', 'ഭക്ഷണം', 'बच्चा', 'शिशु', 'बाल', 'ಆಹಾರ', 'ಮಗು', 'ಕೂಸು'
        ]) or context == 'Child Nutrition'
    )

    base = None
    lang_ctx = CONTEXT_GUIDANCE.get(language, CONTEXT_GUIDANCE['English'])

    if is_child and child_age_months is not None:
        base = get_child_age_guidance(child_age_months, language)
    elif is_pregnancy:
        base = lang_ctx.get('pregnancy')
    elif is_postnatal:
        base = lang_ctx.get('postnatal')
    elif context == 'General Nutrition' and not nutrient:
        base = lang_ctx.get('general')

    parts = []

    # Nutrient specific information
    if nutrient and nutrient in NUTRIENT_KB:
        kb_entry = NUTRIENT_KB[nutrient].get(language, NUTRIENT_KB[nutrient]['English'])
        parts.append(f"## {kb_entry['title']}\n")
        
        # Localized field labels
        if language == 'Malayalam':
            parts.append(f"**പ്രാധാന്യം:**\n{kb_entry['importance']}\n")
            parts.append(f"**ഭക്ഷണ സ്രോതസ്സുകൾ:**\n{kb_entry['food_sources']}\n")
            parts.append(f"**കുറവിന്റെ ലക്ഷണങ്ങൾ:**\n{kb_entry['deficiency_symptoms']}\n")
            parts.append(f"**പൊതുവായ മാർഗ്ഗനിർദ്ദേശം:**\n{kb_entry['dietary_guidance']}")
        elif language == 'Hindi':
            parts.append(f"**महत्व:**\n{kb_entry['importance']}\n")
            parts.append(f"**खाद्य स्रोत:**\n{kb_entry['food_sources']}\n")
            parts.append(f"**कमी के लक्षण:**\n{kb_entry['deficiency_symptoms']}\n")
            parts.append(f"**सामान्य मार्गदर्शन:**\n{kb_entry['dietary_guidance']}")
        elif language == 'Kannada':
            parts.append(f"**ಪ್ರಾಮುಖ್ಯತೆ:**\n{kb_entry['importance']}\n")
            parts.append(f"**ಆಹಾರ ಮೂಲಗಳು:**\n{kb_entry['food_sources']}\n")
            parts.append(f"**ಕೊರತೆಯ ಲಕ್ಷಣಗಳು:**\n{kb_entry['deficiency_symptoms']}\n")
            parts.append(f"**ಸಾಮಾನ್ಯ ಮಾರ್ಗದರ್ಶನ:**\n{kb_entry['dietary_guidance']}")
        else:
            parts.append(f"**Why it matters:**\n{kb_entry['importance']}\n")
            parts.append(f"**Indian food sources:**\n{kb_entry['food_sources']}\n")
            parts.append(f"**Signs that may suggest low intake:**\n{kb_entry['deficiency_symptoms']}\n")
            parts.append(f"**General dietary guidance:**\n{kb_entry['dietary_guidance']}")

    if base:
        parts.append(base)

    if not parts:
        parts.append(lang_ctx.get('general', CONTEXT_GUIDANCE['English']['general']))

    # Append disclaimer
    parts.append(f"\n---\n{DISCLAIMERS.get(language, DISCLAIMERS['English'])}")
    return "\n\n".join(parts)

# =============================================================================
# Google Gemini API Call with Safe Multilingual Fallback
# =============================================================================

def get_ai_response(question, context, language='English', chat_history=None, child_age_months=None, child_name=None):
    """
    Calls Gemini API if GEMINI_API_KEY is configured.
    Falls back gracefully to the built-in multilingual knowledge base.
    """
    if language not in ('English', 'Malayalam', 'Hindi', 'Kannada'):
        language = 'English'

    api_key = os.environ.get('GEMINI_API_KEY', '').strip()

    if not api_key:
        return build_fallback_response(question, context, language, child_age_months), False

    try:
        from google import genai
        from google.genai import types as genai_types

        client = genai.Client(api_key=api_key)

        context_note = f"Context: {context}"
        if child_age_months is not None:
            context_note += f" | Child Age: {child_age_months} months"
        language_note = (
            f"CRITICAL: The user has chosen {language}. You MUST formulate the entire reply in "
            f"{language} using proper script. Do NOT reply in English unless English was requested."
        )

        full_prompt = f"{context_note}\n{language_note}\n\nQuestion: {question}"

        history = []
        if chat_history:
            for msg in chat_history[-6:]:
                role = 'user' if msg['role'] == 'user' else 'model'
                history.append(genai_types.Content(
                    role=role,
                    parts=[genai_types.Part(text=msg['content'])]
                ))

        system_instruction = (
            "You are MomCare Nutrition Assistant, a maternal and child nutrition expert for India. "
            f"You provide accurate, culturally relevant Indian food advice. Answer in {language}. "
            "Never diagnose deficiencies from symptoms alone; always suggest consulting a doctor or blood test. "
            "Never prescribe supplement doses or advise stopping doctor medications."
        )

        chat = client.chats.create(
            model='gemini-2.0-flash',
            config=genai_types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.6,
                max_output_tokens=1024,
            ),
            history=history
        )

        response = chat.send_message(full_prompt)
        return response.text, True

    except Exception:
        fallback = build_fallback_response(question, context, language, child_age_months)
        return fallback, False
