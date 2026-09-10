
import streamlit as st
from google import genai
import urllib.parse
import edge_tts
import asyncio

st.set_page_config(page_title="Apna Guru Ji", page_icon="🪔", layout="centered")

st.title("🪔 अपना गुरु जी (Apna Guru Ji)")
st.caption("उपनिषदों का विवेक, गीता का दर्शन और आधुनिक मनोविज्ञान का व्यावहारिक तालमेल")

# API Key Setup
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("कृपया Streamlit Secrets में 'GEMINI_API_KEY' सेट करें।")
    st.stop()

# Async Function for Rishi/Guru Voice
async def generate_guru_audio(text, output_file="guru_voice.mp3"):
    voice = "hi-IN-MadhurNeural"
    communicate = edge_tts.Communicate(text, voice, rate="-10%", pitch="-5Hz")
    await communicate.save(output_file)

def get_audio(text):
    asyncio.run(generate_guru_audio(text))
    with open("guru_voice.mp3", "rb") as audio_file:
        return audio_file.read()

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("🪔 अपना गुरु जी")
    st.write("शांत, गंभीर और प्रामाणिक दार्शनिक वाणी।")
    if st.button("नई बातचीत शुरू करें (Clear Chat)"):
        st.session_state.messages = []
        st.rerun()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "audio_bytes" in message:
            st.audio(message["audio_bytes"], format="audio/mp3")
        if "image_url" in message:
            st.image(message["image_url"], use_container_width=True)

# Prompt Definition
system_instruction = (
    "आप 'अपना गुरु जी' हैं—एक प्रबुद्ध, शांत, गंभीर और स्नेही ऋषि-तुल्य आचार्य। "
    "यूज़र को जीवन की दुविधाओं, तनाव और उलझनों में सही रास्ता दिखाएँ।\n\n"
    "नियम:\n"
    "1. उत्तर में भारतीय दर्शन (गीता, उपनिषद) और आधुनिक मनोविज्ञान का व्यावहारिक संतुलन रखें।\n"
    "2. भाषा बहुत सरल, सम्मानजनक, शांत और प्रेरणादायक हिंदी रखें।\n"
    "3. उत्तर के अंत में 1 छोटी अंग्रेजी लाइन जोड़ें जो इस उत्तर का दृश्य (Visual Prompt) बताए, "
    "फॉर्मेट: [IMAGE_PROMPT: serene Indian Vedic sage meditating in Himalayas, cinematic lighting, ultra realistic]"
)

# Function to Process Query
def process_query(prompt_text):
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    st.chat_message("user").markdown(prompt_text)

    with st.chat_message("assistant"):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"{system_instruction}\n\nशिष्य का प्रश्न: {prompt_text}"
            )
            raw_text = response.text
            
            image_url = None
            if "[IMAGE_PROMPT:" in raw_text:
                parts = raw_text.split("[IMAGE_PROMPT:")
                reply_text = parts[0].strip()
                img_desc = parts[1].replace("]", "").strip()
                encoded_desc = urllib.parse.quote(img_desc)
                image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=800&height=450&nologo=true"
            else:
                reply_text = raw_text.strip()

            st.markdown(reply_text)
            
            # Audio Generation
            audio_bytes = get_audio(reply_text)
            st.audio(audio_bytes, format="audio/mp3")

            if image_url:
                st.image(image_url, use_container_width=True)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": reply_text, 
                    "audio_bytes": audio_bytes,
                    "image_url": image_url
                })
            else:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": reply_text, 
                    "audio_bytes": audio_bytes
                })

        except Exception as e:
            st.error(f"त्रुटि: {e}")

# Quick Prompt Buttons
st.write("*त्वरित प्रश्न चुनें:*")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🧘 मानसिक शांति"):
        process_query("मुझे मानसिक अशांति और तनाव महसूस हो रहा है, क्या करूँ?")
with col2:
    if st.button("🎯 एकाग्रता"):
        process_query("काम और पढ़ाई में मन एकाग्र कैसे करें?")
with col3:
    if st.button("⚖️ कर्म का मर्म"):
        process_query("कर्म और उसके फल को सही तरह कैसे समझें?")

# Chat Input
user_query = st.chat_input("गुरु जी से अपनी दुविधा साझा करें...")
if user_query:
    process_query(user_query)
