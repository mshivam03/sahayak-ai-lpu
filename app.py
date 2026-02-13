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

# 1. CONFIG & IDENTITY (Shivam Kumar - 12514900)
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyCXhGXTZPrtr4lDFvjJifgUubritqDT--M"
REQUESTBIN_URL = "https://eowayl2i7ckb9xd.m.pipedream.net"

client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-1.5-flash')

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = math.radians(lat2 - lat1); dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 2)

st.set_page_config(page_title="Sahayak AI Premium", layout="wide")

# 2. ADVANCED CSS & BOOTSTRAP INJECTION
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; background-color: #0e1117; color: #ffffff; }
    .react-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 25px; transition: 0.3s; }
    .react-card:hover { border: 1px solid #00ff00; box-shadow: 0 0 20px rgba(0, 255, 0, 0.2); }
    .neon-text { color: #00ff00; text-shadow: 0 0 10px rgba(0, 255, 0, 0.5); font-weight: 800; }
    .stButton>button { background: linear-gradient(90deg, #00ff00, #008000); color: black; border: none; border-radius: 10px; font-weight: bold; width: 100%; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(0, 255, 0, 0.4); }
    </style>
    """, unsafe_allow_html=True)

# 3. NAVBAR & STATUS
st.markdown(f"""
    <div class="d-flex justify-content-between align-items-center mb-4 p-3 react-card">
        <h2 class="neon-text m-0">🤖 Sahayak AI Pro</h2>
        <div class="text-end">
            <span class="badge bg-success">Online</span><br>
            <small class="text-secondary">Dev: Shivam Kumar (12514900)</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None
if "use_camera" not in st.session_state: st.session_state.use_camera = False

# 4. SIDEBAR (React-Style Navigation)
with st.sidebar:
    st.markdown("<h4 class='neon-text'>Control Panel</h4>", unsafe_allow_html=True)
    st.session_state.use_camera = st.toggle("Enable AI Vision", value=st.session_state.use_camera)
    if st.session_state.use_camera:
        img_file = st.camera_input("Scanner")
        if img_file:
            img = Image.open(img_file)
            v_res = vision_model.generate_content(["Identify service needed. One word only.", img])
            st.session_state.voice_input = f"I need a {v_res.text}."
    
    st.divider()
    st.markdown("📍 **Location Config**")
    u_lat = st.number_input("Lat", value=31.254, format="%.4f")
    u_lon = st.number_input("Lon", value=75.705, format="%.4f")

# 5. MAIN CONTENT (Bootstrap Grid)
col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.markdown("<div class='react-card'>", unsafe_allow_html=True)
    st.markdown("<h5>💬 Conversation Engine</h5>", unsafe_allow_html=True)
    
    if st.button("🎙️ Tap to Speak (Bolo Shivam)"):
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.toast("Listening...")
                audio = r.listen(source, timeout=5)
                st.session_state.voice_input = r.recognize_google(audio, language='hi-IN')
                st.rerun()
        except: st.error("Mic restricted on Cloud.")

    # Chat logic
    input_text = None
    if "voice_input" in st.session_state:
        input_text = st.session_state.voice_input; del st.session_state.voice_input
    elif p := st.chat_input("Ask me anything..."): input_text = p

    if input_text:
        st.session_state.messages.append({"role": "user", "content": input_text})
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "You are Sahayak AI by Shivam Kumar. Categorize: Service or Chat (JSON)."}, {"role": "user", "content": input_text}],
            response_format={"type": "json_object"}
        )
        res = json.loads(completion.choices[0].message.content)
        if res.get("type") == "chat":
            st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
        else:
            service = res.get('service', 'General').title()
            dist = calculate_distance(u_lat, u_lon, 31.280, 75.720)
            st.session_state.last_booking = {"service": service, "dist": dist, "total": 299 + round(dist * 15, 2), "otp": "4900"}
            st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
            requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

    for msg in st.session_state.messages[-3:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    if b := st.session_state.last_booking:
        st.markdown(f"""
            <div class="react-card border-success">
                <h3 class="neon-text">✅ Booking Confirmed</h3>
                <div class="row mt-3">
                    <div class="col-6"><p class="text-secondary m-0">Service</p><b>{b['service']}</b></div>
                    <div class="col-6"><p class="text-secondary m-0">Distance</p><b>{b['dist']} km</b></div>
                </div>
                <div class="mt-3"><span class="h1 neon-text">₹{b['total']}</span></div>
                <hr style="border-color: rgba(255,255,255,0.1)">
                <div class="d-flex justify-content-between align-items-center">
                    <span>Verification OTP: <b>{b['otp']}</b></span>
                    <button class="btn btn-outline-success btn-sm">Pay Now</button>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        m = folium.Map(location=[u_lat, u_lon], zoom_start=13, tiles="CartoDB dark_matter")
        folium.Marker([u_lat, u_lon], icon=folium.Icon(color='green', icon='user')).add_to(m)
        folium.Marker([31.280, 75.720], icon=folium.Icon(color='red', icon='wrench')).add_to(m)
        st_folium(m, height=350, width=650, key="react_map")
        st.balloons()