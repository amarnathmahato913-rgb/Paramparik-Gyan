import streamlit as st
from google import genai

st.set_page_config(page_title="Paramparik Gyan", page_icon="🕉️", layout="centered")

st.title("🕉️ पारंपरिक ज्ञान (Paramparik Gyan)")
st.caption("उपनिषदों का विवेक, गीता का दर्शन और आधुनिक मनोविज्ञान का व्यावहारिक तालमेल")

# API Key Streamlit Secrets se aayegi
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("कृपया Streamlit Secrets में 'GEMINI_API_KEY' सेट करें।")
    st.stop()

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Purane messages display karein
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input box
user_query = st.chat_input("अपनी दुविधा या प्रश्न यहाँ लिखें...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    # Prompt System
    system_instruction = """
    आप 'पारंपरिक ज्ञान' के मार्गदर्शक हैं। आपका उद्देश्य लोगों की मानसिक और व्यावहारिक समस्याओं का समाधान करना है।
    उत्तर देते समय:
    1. उपनिषदों, भगवद्गीता और भारतीय दर्शन के मूल सिद्धांतों को आधार बनाएँ।
    2. आधुनिक मनोविज्ञान (Cognitive Science) के व्यावहारिक समाधान जोड़ें।
    3. भाषा सरल, स्पष्ट, आदरपूर्ण और प्रेरणादायक हिंदी रखें।
    """

    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"{system_instruction}\n\nयूज़र का प्रश्न: {user_query}"
            )
            reply = response.text
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except Exception as e:
            st.error(f"त्रुटि: {e}")
