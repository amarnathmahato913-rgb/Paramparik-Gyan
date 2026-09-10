import streamlit as st
from google import genai
from google.genai import types
import urllib.parse
import requests
import json
import base64

st.set_page_config(page_title="Apna Guru Ji", page_icon="🪔", layout="centered")

st.title("🪔 अपना गुरु जी (Apna Guru Ji)")
st.caption("उपनिषदों का विवेक, गीता का दर्शन और आधुनिक मनोविज्ञान का व्यावहारिक तालमेल")

# API Keys Setup
try:
    gemini_key = str(st.secrets["GEMINI_API_KEY"]).strip().replace('"', '').replace("'", "")
    client = genai.Client(api_key=gemini_key)
except Exception:
    st.error("कृपया Streamlit Secrets में 'GEMINI_API_KEY' सेट करें।")
    st.stop()

# Function to generate ElevenLabs Brian Voice
def get_brian_voice(text):
    if "ELEVENLABS_API_KEY" not in st.secrets:
        return None
    
    clean_key = str(st.secrets["ELEVENLABS_API_KEY"]).strip().replace('"', '').replace("'", "")
    voice_id = "nPczCjzI2devNBz1zQrb"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json; charset=utf-8",
        "xi-api-key": clean_key,
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.85
        }
    }

    try:
        response = requests.post(
            url, 
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), 
            headers=headers, 
            timeout=30
        )
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception:
        return None

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("🪔 अपना गुरु जी")
    st.write("शांत, गंभीर और प्रामाणिक दार्शनिक वाणी।")
    if st.button("नई बातचीत शुरू करें (Clear Chat)"):
        st.session_state.messages = []
        st.rerun()

system_instruction = (
    "You are 'Apna Guru Ji', an authentic, compassionate Vedic sage and psychological mentor. "
    "Guide the seeker with wisdom from Bhagavad Gita, Upanishads, and modern psychology. "
    "Always reply in respectful, pure, and soothing Hindi. "
    "Keep answers concise (2-3 short paragraphs). "
    "At the very end, append one line specifying an image prompt: "
    "[IMAGE_PROMPT: serene Indian Vedic sage meditating in Himalayas, cinematic lighting, ultra realistic]"
)

def process_query(prompt_text):
    if not prompt_text:
        return

    st.session_state.messages.append({"role": "user", "content": prompt_text})

    with st.chat_message("user"):
        st.markdown(prompt_text)

    with st.chat_message("assistant"):
        with st.spinner("गुरु जी चिंतन कर रहे हैं..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[system_instruction, f"Seeker's question: {prompt_text}"]
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

                audio_bytes = get_brian_voice(reply_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

                if image_url:
                    st.image(image_url, use_container_width=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": reply_text,
                    "audio_bytes": audio_bytes,
                    "image_url": image_url
                })

            except Exception as e:
                st.error(f"त्रुटि: {e}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("audio_bytes"):
            st.audio(message["audio_bytes"], format="audio/mp3")
        if message.get("image_url"):
            st.image(message["image_url"], use_container_width=True)

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

user_typed_query = st.chat_input("गुरु जी से अपनी दुविधा साझा करें...")
if user_typed_query:
    process_query(user_typed_query)

audio_mic = st.audio_input("🎙️ बोलकर पूछें (Mic)")
if audio_mic is not None:
    try:
        raw_audio = audio_mic.getvalue()
        # Clean inline data upload via Part
        part = types.Part(
            inline_data=types.Blob(
                mime_type="audio/wav",
                data=raw_audio
            )
        )
        transcription_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                part,
                "Transcribe this spoken audio accurately into Devanagari Hindi text. Output ONLY the transcribed Hindi words without explanations."
            ]
        )
        voice_query = transcription_response.text.strip()
        if voice_query:
            process_query(voice_query)
    except Exception as e:
        st.error(f"माइक से आवाज़ समझने में समस्या: {e}")
        
