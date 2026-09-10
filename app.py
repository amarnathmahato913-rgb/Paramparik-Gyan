import streamlit as st
from google import genai
from google.genai import types
import urllib.parse
import requests
import json
import re

st.set_page_config(page_title="Apna Guru Ji", page_icon="🪔", layout="centered")

st.title("🪔 अपना गुरु जी (Apna Guru Ji)")
st.caption("उपनिषदों का विवेक, गीता का दर्शन और आधुनिक मनोविज्ञान का व्यावहारिक तालमेल")

# Safe Key Cleaning Function
def clean_ascii_key(raw_val):
    if not raw_val:
        return ""
    # Remove smart quotes, extra spaces, and any non-ascii characters
    val_str = str(raw_val).strip().strip("'\"“”‘’")
    return re.sub(r'[^\x00-\x7F]+', '', val_str)

# API Keys Setup
try:
    gemini_key = clean_ascii_key(st.secrets.get("GEMINI_API_KEY", ""))
    client = genai.Client(api_key=gemini_key)
except Exception as e:
    st.error(f"Gemini API सेटअप त्रुटि: {e}")
    st.stop()

# Safe ElevenLabs Brian Voice Generator
def get_brian_voice(text):
    raw_key = st.secrets.get("ELEVENLABS_API_KEY", None)
    if not raw_key:
        return None
    
    clean_key = clean_ascii_key(raw_key)
    voice_id = "nPczCjzI2devNBz1zQrb"  # Brian Voice ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": clean_key,
    }

    # Shorten text to prevent timeouts
    clean_text = text[:500] if len(text) > 500 else text

    payload = {
        "text": clean_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.85
        }
    }

    try:
        # Strictly encode JSON body as pure UTF-8 bytes
        req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        response = requests.post(url, data=req_body, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None

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

# System Prompt
system_instruction = (
    "You are 'Apna Guru Ji', an authentic Vedic sage and life coach. "
    "Provide guidance using wisdom from Bhagavad Gita and modern psychology. "
    "Reply in calm, respectful, and soothing Hindi. "
    "Keep replies concise (2 short paragraphs). "
    "At the end, add: [IMAGE_PROMPT: serene Indian Vedic sage meditating in Himalayas, cinematic lighting]"
)

# Function to Process Query
def process_query(prompt_text):
    if not prompt_text:
        return

    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    with st.chat_message("assistant"):
        with st.spinner("गुरु जी चिंतन कर रहे हैं..."):
            try:
                # 1. Generate text from Gemini
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[system_instruction, f"Question: {prompt_text}"]
                )
                raw_text = response.text or ""

                # 2. Extract visual prompt
                image_url = None
                if "[IMAGE_PROMPT:" in raw_text:
                    parts = raw_text.split("[IMAGE_PROMPT:")
                    reply_text = parts[0].strip()
                    img_desc = parts[1].replace("]", "").strip()
                    encoded_desc = urllib.parse.quote(img_desc)
                    image_url = f"https://image.pollinations.ai/prompt/{encoded_desc}?width=800&height=450&nologo=true"
                else:
                    reply_text = raw_text.strip()

                # Display Text
                st.markdown(reply_text)

                # 3. Audio generation
                audio_bytes = get_brian_voice(reply_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

                # 4. Display Image
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

# Display Past History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("audio_bytes"):
            st.audio(message["audio_bytes"], format="audio/mp3")
        if message.get("image_url"):
            st.image(message["image_url"], use_container_width=True)

# Quick Prompts
st.write("*त्वरित प्रश्न चुनें:*")
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🧘 मानसिक शांति"):
        process_query("मुझे मानसिक अशांति महसूस हो रही है, क्या करूँ?")
with col2:
    if st.button("🎯 एकाग्रता"):
        process_query("काम और पढ़ाई में मन एकाग्र कैसे करें?")
with col3:
    if st.button("⚖️ कर्म का मर्म"):
        process_query("कर्म और उसके फल का सही मर्म क्या है?")

# Chat Text Input
user_typed_query = st.chat_input("गुरु जी से अपनी दुविधा साझा करें...")
if user_typed_query:
    process_query(user_typed_query)

# Mic Audio Input
audio_mic = st.audio_input("🎙️ बोलकर पूछें (Mic)")
if audio_mic is not None:
    try:
        raw_audio = audio_mic.read()
        audio_part = types.Part.from_bytes(
            data=raw_audio,
            mime_type="audio/wav"
        )
        transcription_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[audio_part, "Transcribe this spoken audio into text. Return ONLY the transcribed text."]
        )
        voice_query = transcription_response.text.strip() if transcription_response.text else ""
        if voice_query:
            process_query(voice_query)
    except Exception as e:
        st.error(f"माइक ट्रांसक्रिप्शन में त्रुटि: {e}")
