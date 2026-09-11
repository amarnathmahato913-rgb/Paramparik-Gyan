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
    val_str = str(raw_val).strip().strip("'\"“”‘’")
    return re.sub(r'[^\x00-\x7F]+', '', val_str)

# API Keys Setup
try:
    gemini_key = clean_ascii_key(st.secrets.get("GEMINI_API_KEY", ""))
    client = genai.Client(api_key=gemini_key)
except Exception as e:
    st.error(f"Gemini API सेटअप त्रुटि: {e}")
    st.stop()

# Helper function to generate content with fallback on 503
def generate_gemini_response(contents):
    models_to_try = ["gemini-2.5-flash", "gemini-2.5-pro"]
    last_err = None
    for m in models_to_try:
        try:
            res = client.models.generate_content(model=m, contents=contents)
            if res and res.text:
                return res.text
        except Exception as err:
            last_err = err
            continue
    raise last_err

# ElevenLabs Brian Voice Generator (Long Audio Support)
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

    # Increased character limit for longer ~1.5 to 2 minute audio
    clean_text = text.replace("*", "").replace("#", "")[:1600]

    payload = {
        "text": clean_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.85
        }
    }

    try:
        req_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        response = requests.post(url, data=req_body, headers=headers, timeout=60)
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None

# Session State for History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("🪔 अपना गुरु जी")
    st.write("शांत, गंभीर और प्रामाणिक दार्शनिक वाणी (Brian Voice)।")
    if st.button("नई बातचीत शुरू करें (Clear Chat)"):
        st.session_state.messages = []
        st.rerun()

# Comprehensive Guidance System Instruction
system_instruction = (
    "आप 'अपना गुरु जी' हैं—एक अत्यंत प्रबुद्ध, शांत, गंभीर और स्नेही वैदिक आचार्य। "
    "यूज़र के प्रश्नों का उत्तर संक्षेप में नहीं, बल्कि बहुत विस्तार और गहराई से दें (कम से कम 3 से 4 विस्तृत अनुच्छेद)।\n\n"
    "निर्देश:\n"
    "1. उत्तर में श्रीमद्भगवद्गीता के सिद्धांत, उपनिषदों की सीख और आधुनिक जीवन में उसके व्यावहारिक उपयोग को स्पष्ट करें।\n"
    "2. जीवन के वास्तविक उदाहरण दें और मार्गदर्शन ऐसा हो जो मन को शांत और स्पष्ट दृष्टि दे।\n"
    "3. भाषा अत्यंत शुद्ध, सम्मानजनक, गंभीर और प्रेरणादायी हिंदी हो।\n"
    "4. उत्तर के अंत में यह इमेज टैग अवश्य जोड़ें: "
    "[IMAGE_PROMPT: serene Indian Vedic sage meditating in Himalayas near sacred fire, golden sunrise, cinematic 8k ultra realistic]"
)

# Process Query
def process_query(prompt_text):
    if not prompt_text:
        return

    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    with st.chat_message("assistant"):
        with st.spinner("गुरु जी गहराई से चिंतन कर रहे हैं..."):
            try:
                # 1. Text Generation with Automatic Retry/Fallback
                raw_text = generate_gemini_response([system_instruction, f"प्रश्न: {prompt_text}"])

                # 2. Visual Prompt Extraction
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

                # 3. Longer Brian Voice Generation
                audio_bytes = get_brian_voice(reply_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

                # 4. Image Display
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

# Render History
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
        process_query("मुझे मानसिक अशांति महसूस हो रही है, मन को शांत करने का गहरा मार्ग बताएं।")
with col2:
    if st.button("🎯 एकाग्रता"):
        process_query("काम और अध्ययन में मन एकाग्र करने के व्यावहारिक सूत्र क्या हैं?")
with col3:
    if st.button("⚖️ कर्म का मर्म"):
        process_query("कर्म और निष्काम कर्म योग का वास्तविक मर्म क्या है?")

# Inputs
user_typed_query = st.chat_input("गुरु जी से अपनी दुविधा साझा करें...")
if user_typed_query:
    process_query(user_typed_query)

audio_mic = st.audio_input("🎙️ बोलकर पूछें (Mic)")
if audio_mic is not None:
    try:
        raw_audio = audio_mic.read()
        audio_part = types.Part.from_bytes(
            data=raw_audio,
            mime_type="audio/wav"
        )
        transcription_text = generate_gemini_response([audio_part, "Transcribe this spoken audio into Hindi text. Return ONLY the transcribed text."])
        voice_query = transcription_text.strip() if transcription_text else ""
        if voice_query:
            process_query(voice_query)
    except Exception as e:
        st.error(f"माइक ट्रांसक्रिप्शन में त्रुटि: {e}")
