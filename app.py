import streamlit as st
from google import genai
from google.genai import types
import urllib.parse
import edge_tts
import asyncio
import re

st.set_page_config(page_title="Apna Guru Ji", page_icon="🪔", layout="centered")

st.title("🪔 अपना गुरु जी (Apna Guru Ji)")
st.caption("सकल धर्मग्रंथों का शाश्वत विवेक और आधुनिक जीवन का व्यावहारिक तालमेल")

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

# Helper function with active models fallback
def generate_gemini_response(contents):
    models_to_try = ["gemini-3.6-flash", "gemini-3.1-pro-preview"]
    last_err = None
    for m in models_to_try:
        try:
            res = client.models.generate_content(
                model=m,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.6,
                    top_p=0.9
                )
            )
            if res and res.text:
                return res.text
        except Exception as err:
            last_err = err
            continue
    raise last_err

# 100% Free, Unlimited Deep Sage Voice
async def create_guru_audio(text, output_file="guru_voice.mp3"):
    communicate = edge_tts.Communicate(
        text=text,
        voice="hi-IN-MadhurNeural",
        rate="-4%",
        pitch="-7Hz"
    )
    await communicate.save(output_file)

def get_free_guru_voice(text):
    try:
        clean_text = text.replace("*", "").replace("#", "").strip()
        asyncio.run(create_guru_audio(clean_text))
        with open("guru_voice.mp3", "rb") as f:
            return f.read()
    except Exception:
        return None

# Clean No-Logo Image Generator
def get_clean_image_url(prompt):
    clean_desc = urllib.parse.quote(prompt.strip())
    return f"https://image.pollinations.ai/prompt/{clean_desc}?width=1024&height=576&seed=42&nologo=true"

# Session State for History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("🪔 अपना गुरु जी")
    st.write("सकल धर्मग्रंथों (गीता, उपनिषद, सूफ़ी, बाइबिल, गुरबाणी, बौद्ध) का साझा ज्ञान।")
    if st.button("नई बातचीत शुरू करें (Clear Chat)"):
        st.session_state.messages = []
        st.rerun()

# Multi-Faith Heading-Wise System Instruction
system_instruction = (
    "आप 'अपना गुरु जी' हैं—एक अत्यंत प्रबुद्ध, तटस्थ और स्नेही आध्यात्मिक मार्गदर्शक। "
    "आपका उद्देश्य संसार के सभी प्रमुख धर्मग्रंथों के मूल सत्य को मिलाकर जिज्ञासु का मार्गदर्शन करना है।\n\n"
    "अनिवार्य निर्देश:\n"
    "प्रत्येक उत्तर को स्पष्ट रूप से निम्नलिखित 4 हेडिंग्स में बाँटकर लिखें:\n\n"
    "*1. आत्मिक दृष्टि (मूल सार):*\n"
    "जिज्ञासु की मनःस्थिति को समझें और 2-3 पंक्तियों में सांत्वना व दृष्टिकोण दें।\n\n"
    "*2. सनातन विवेक (गीता व उपनिषद):*\n"
    "गीता/उपनिषद का दार्शनिक सूत्र या श्लोक का अर्थ समझाएँ।\n\n"
    "*3. विश्व धर्मों का साझा प्रकाश (सूफी, बाइबिल, गुरबाणी व बौद्ध दर्शन):*\n"
    "अन्य धर्मग्रंथों (जैसे कुरान/सूफीवाद, ईसा मसीह के उपदेश, श्री गुरु ग्रंथ साहिब या बुद्ध के धम्मपद) से मिलती-जुलती अमूल्य सीख प्रस्तुत करें ताकि सिद्ध हो सके कि सत्य एक है।\n\n"
    "*4. दैनिक जीवन में व्यावहारिक समाधान:*\n"
    "आधुनिक जीवन में तुरंत अपनाने योग्य 2-3 ठोस कदम बुलेट पॉइंट्स में लिखें।\n\n"
    "भाषा अत्यंत गरिमामयी, शुद्ध, सौम्य और शांत हिंदी हो।\n"
    "उत्तर के अंत में यह टैग जोड़ें:\n"
    "[IMAGE_PROMPT: peaceful enlightened multi faith spiritual teacher radiating golden light, sacred texts, mountain sanctuary, cinematic ultra realistic, 8k]"
)

# Process User Query
def process_query(prompt_text):
    if not prompt_text:
        return

    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)

    with st.chat_message("assistant"):
        with st.spinner("गुरु जी सभी धर्मग्रंथों के मर्म का मंथन कर रहे हैं..."):
            try:
                raw_text = generate_gemini_response([system_instruction, f"जिज्ञासु का प्रश्न: {prompt_text}"])

                image_url = None
                if "[IMAGE_PROMPT:" in raw_text:
                    parts = raw_text.split("[IMAGE_PROMPT:")
                    reply_text = parts[0].strip()
                    img_desc = parts[1].replace("]", "").strip()
                    image_url = get_clean_image_url(img_desc)
                else:
                    reply_text = raw_text.strip()

                st.markdown(reply_text)

                # Free Deep Voice
                audio_bytes = get_free_guru_voice(reply_text)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

                # Watermark-Free AI Image
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
        process_query("मुझे अशांति और तनाव से मुक्ति पाने का मार्ग सभी धर्मों की दृष्टि से समझाएं।")
with col2:
    if st.button("🎯 एकाग्रता व उद्देश्य"):
        process_query("जीवन का उद्देश्य और कर्म में मन एकाग्र करने का मर्म क्या है?")
with col3:
    if st.button("⚖️ क्षमा और प्रेम"):
        process_query("क्रोध पर विजय, क्षमा और निःस्वार्थ प्रेम का महत्व क्या है?")

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
        transcription_text = generate_gemini_response([audio_part, "Transcribe this spoken audio into Hindi text accurately. Return ONLY the transcribed text."])
        voice_query = transcription_text.strip() if transcription_text else ""
        if voice_query:
            process_query(voice_query)
    except Exception as e:
        st.error(f"माइक ट्रांसक्रिप्शन में त्रुटि: {e}")
