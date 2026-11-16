"""A few key replies in Hindi and Kannada. Other replies fall back to English.
These translations must be reviewed by a native speaker before real use."""

T = {
    "saved": {
        "en": "Saved. {party}, {total}.",
        "hi": "सेव हो गया। {party}, {total}.",
        "kn": "ಉಳಿಸಲಾಗಿದೆ. {party}, {total}.",
    },
    "eway_needed": {
        "en": "This needs an e-way bill ({value} is above the {limit} limit). Draft is ready, send the vehicle number.",
        "hi": "इसके लिए ई-वे बिल ज़रूरी है ({value}, सीमा {limit})। ड्राफ्ट तैयार है, गाड़ी का नंबर भेजें।",
        "kn": "ಇದಕ್ಕೆ ಇ-ವೇ ಬಿಲ್ ಅಗತ್ಯವಿದೆ ({value}, ಮಿತಿ {limit}). ಡ್ರಾಫ್ಟ್ ಸಿದ್ಧವಾಗಿದೆ, ವಾಹನ ಸಂಖ್ಯೆ ಕಳುಹಿಸಿ.",
    },
    "eway_ready": {
        "en": "E-way bill draft is complete for vehicle {vehicle}. You or your accountant can now generate it on the portal. I do not generate or file anything myself.",
        "hi": "गाड़ी {vehicle} के लिए ई-वे बिल ड्राफ्ट पूरा है। अब आप या आपके अकाउंटेंट पोर्टल पर इसे बना सकते हैं। मैं खुद कुछ फाइल नहीं करता।",
        "kn": "ವಾಹನ {vehicle} ಗಾಗಿ ಇ-ವೇ ಬಿಲ್ ಡ್ರಾಫ್ಟ್ ಪೂರ್ಣವಾಗಿದೆ. ಈಗ ನೀವು ಅಥವಾ ನಿಮ್ಮ ಅಕೌಂಟೆಂಟ್ ಪೋರ್ಟಲ್‌ನಲ್ಲಿ ಇದನ್ನು ರಚಿಸಬಹುದು. ನಾನು ಏನನ್ನೂ ಫೈಲ್ ಮಾಡುವುದಿಲ್ಲ.",
    },
    "itc_risk": {
        "en": "{supplier} has not reported {n} invoice(s) correctly. {amount} of your credit is at risk. Shall I draft a reminder? (yes / no)",
        "hi": "{supplier} ने {n} बिल सही रिपोर्ट नहीं किए। आपका {amount} क्रेडिट खतरे में है। क्या मैं रिमाइंडर ड्राफ्ट करूँ? (yes / no)",
        "kn": "{supplier} ಅವರು {n} ಬಿಲ್‌ಗಳನ್ನು ಸರಿಯಾಗಿ ವರದಿ ಮಾಡಿಲ್ಲ. ನಿಮ್ಮ {amount} ಕ್ರೆಡಿಟ್ ಅಪಾಯದಲ್ಲಿದೆ. ನಾನು ರಿಮೈಂಡರ್ ಡ್ರಾಫ್ಟ್ ಮಾಡಲೇ? (yes / no)",
    },
    "credit_safe": {
        "en": "Good news: {supplier} has now reported {invoice}. {amount} of credit is safe.",
        "hi": "अच्छी खबर: {supplier} ने अब {invoice} रिपोर्ट कर दिया है। {amount} क्रेडिट सुरक्षित है।",
        "kn": "ಒಳ್ಳೆಯ ಸುದ್ದಿ: {supplier} ಈಗ {invoice} ವರದಿ ಮಾಡಿದ್ದಾರೆ. {amount} ಕ್ರೆಡಿಟ್ ಸುರಕ್ಷಿತವಾಗಿದೆ.",
    },
}


def t(lang, key, **kw):
    return T[key].get(lang, T[key]["en"]).format(**kw)
