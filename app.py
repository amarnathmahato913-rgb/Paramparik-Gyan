import streamlit as st
from google import genai
from google.genai import types
import urllib.parse
from gtts import gTTS
import io

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

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("🪔 अपना गुरु जी")
    st.write("भारतीय दर्शन और आधुनिक मनोविज्ञान के माध्यम से जीवन की समस्याओं का समाधान।")
    if st.button("नई बातचीत शुरू करें (Clear Chat)"):
        st.session_state.messages = []
        st.rerun()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image_url" in message:
            st.image(message["image_url"], use_container_width=True)
        if "audio_bytes" in message:
            st.audio(message["audio_bytes"], format="audio/mp3")

# Prompt Definition
system_instruction = (
    "आप 'अपना गुरु जी' हैं—एक आत्मीय, ज्ञानी और धैर्यवान मार्गदर्शक। "
    "यूज़र को जीवन की दुविधाओं, तनाव और मानसिक उलझनों में सही रास्ता दिखाएँ।\n\n"
    "नियम:\n"
    "1. उत्तर में भारतीय दर्शन (गीता, उपनिषद) और आधुनिक मनोविज्ञान (Cognitive Science) का व्यावहारिक संतुलन रखें।\n"
    "2. भाषा सरल, सम्मानजनक, स्नेहपूर्ण और प्रेरणादायक हिंदी रखें।\n"
    "3. उत्तर के अंत में 1 छोटी अंग्रेजी लाइन जोड़ें जो इस उत्तर का दृश्य (Visual Prompt) बताए, "
    "फॉर्मेट: [IMAGE_PROMPT: serene Indian meditation art with golden glowing light, high quality]"
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
            
            # 1. Extract Image Prompt & URL
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

            if image_url:
                st.image(image_url, use_container_width=True)

            # 2. Text-to-Speech (Hindi Audio)
            tts = gTTS(text=reply_text, lang='hi', slow=False)
            audio_fp = io.BytesIO()
            tts.write_to_fp(audio_fp)
            audio_fp.seek(0)
            audio_bytes = audio_fp.read()
            st.audio(audio_bytes, format="audio/mp3")

            msg_data = {"role": "assistant", "content": reply_text, "audio_bytes": audio_bytes}
            if image_url:
                msg_data["image_url"] = image_url
            st.session_state.messages.append(msg_data)

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

# Voice Input (Mic)
st.write("---")
mic_audio = st.audio_input("🎙️ बोलकर पूछें (माइक पर टैप करके रिकॉर्ड करें)")
if mic_audio:
    audio_data = mic_audio.read()
    with st.spinner("आपकी आवाज़ समझी जा रही है..."):
        try:
            transcription_resp = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=[
                    "इस ऑडियो में कही गई बात को ठीक-ठीक हिंदी टेक्स्ट में लिखें। केवल वही टेक्स्ट लौटाएँ, कोई अतिरिक्त टिप्पणी नहीं।",
                    types.Part.from_bytes(data=audio_data, mime_type="audio/wav")
                ]
            )
            spoken_text = transcription_resp.text.strip()
            if spoken_text:
                process_query(spoken_text)
        except Exception as e:
            st.error(f"ऑडियो समझने में त्रुटि: {e}")

# Text Input
user_query = st.chat_input("गुरु जी से अपनी दुविधा लिखकर साझा करें...")
if user_query:
    process_query(user_query)
