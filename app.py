import streamlit as st
from groq import Groq
import google.generativeai as genai
import json
import folium
from streamlit_folium import st_folium
import speech_recognition as sr
import requests
import math
from PIL import Image

# 1. CORE CONFIG (Shivam Kumar - 12514900)
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyCXhGXTZPrtr4lDFvjJifgUubritqDT--M"
REQUESTBIN_URL = "https://eowayl2i7ckb9xd.m.pipedream.net"

# Setup Clients
client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-1.5-flash')

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

st.set_page_config(page_title="Sahayak AI Multimodal", layout="wide")

# 2. SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None

# 3. SIDEBAR: VISION & VOICE
with st.sidebar:
    st.title("🛠️ Advanced Controls")
    st.write(f"**Developer:** Shivam Kumar")
    
    # --- VISION SECTION ---
    st.subheader("👁️ AI Vision (Gemini)")
    img_file = st.camera_input("Snap a photo of the problem")
    
    if img_file:
        img = Image.open(img_file)
        with st.spinner("Analyzing image..."):
            # Gemini analyzes the image
            v_res = vision_model.generate_content([
                "Look at this image. If there is a repair or cleaning issue, name the service needed in 1-2 words (e.g. Plumber, Electrician, Cleaning). If no issue, say 'General'.", 
                img
            ])
            st.session_state.voice_input = f"I need a {v_res.text} service for this issue."
            st.success(f"Detected: {v_res.text}")

    st.divider()
    
    # --- VOICE SECTION ---
    st.subheader("🎙️ Voice Command")
    if st.button("Speak Now", use_container_width=True):
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.toast("Listening...")
                audio = r.listen(source, timeout=5)
                st.session_state.voice_input = r.recognize_google(audio, language='hi-IN')
                st.rerun()
        except:
            st.error("Mic access limited to Localhost.")

# 4. BRAIN: GROQ + DEEPSEEK REASONING
input_text = None
if "voice_input" in st.session_state:
    input_text = st.session_state.voice_input
    del st.session_state.voice_input
elif p := st.chat_input("How can Sahayak help you today?"):
    input_text = p

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    # Intelligent Routing (DeepSeek reasoning style)
    completion = client.chat.completions.create(
        model="deepseek-r1-distill-llama-70b",
        messages=[
            {"role": "system", "content": """You are Sahayak AI by Shivam Kumar. 
            Analyze intent: 
            1. Service Request -> JSON: {"type": "booking", "service": "Name", "reply": "msg"}
            2. General Chat -> JSON: {"type": "chat", "reply": "msg"}"""},
            {"role": "user", "content": input_text}
        ],
        response_format={"type": "json_object"}
    )
    res = json.loads(completion.choices[0].message.content)

    if res.get("type") == "chat":
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
    else:
        # Booking Engine
        service = res.get('service', 'General').title()
        dist = calculate_distance(31.254, 75.705, 31.280, 75.720) # LPU Campus
        st.session_state.last_booking = {
            "service": service,
            "dist": dist,
            "total": 299 + round(dist * 15, 2),
            "otp": "4900",
            "agent": "Rajesh Kumar (LPU Partner)"
        }
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
        requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

# 5. UI DISPLAY
st.title("🤖 Sahayak AI: Vision & Voice")
c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("💬 Smart Chat")
    for msg in st.session_state.messages[-3:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])

with c2:
    if b := st.session_state.last_booking:
        st.success(f"### {b['service']} Booked!")
        st.metric("Total Bill", f"₹{b['total']}")
        st.write(f"📍 Agent is {b['dist']} km away. **OTP: {b['otp']}**")
        
        m = folium.Map(location=[31.254, 75.705], zoom_start=13)
        folium.Marker([31.254, 75.705], icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker([31.280, 75.720], icon=folium.Icon(color='red')).add_to(m)
        st_folium(m, height=300, width=500, key="multimodal_map")
        st.balloons()