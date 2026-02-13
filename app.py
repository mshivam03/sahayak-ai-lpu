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

st.set_page_config(page_title="Sahayak AI Pro", layout="wide")

# 2. SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None
if "use_camera" not in st.session_state: st.session_state.use_camera = False

# 3. SIDEBAR: PRIVACY & CONTROLS
with st.sidebar:
    st.title("🛠️ Sahayak Settings")
    st.write(f"**Dev:** Shivam Kumar (12514900)")
    
    # CAMERA TOGGLE
    st.subheader("📸 Privacy Control")
    st.session_state.use_camera = st.toggle("Enable AI Vision (Camera)", value=st.session_state.use_camera)
    
    if st.session_state.use_camera:
        img_file = st.camera_input("Snap issue photo")
        if img_file:
            img = Image.open(img_file)
            with st.spinner("Gemini is analyzing..."):
                v_res = vision_model.generate_content(["Identify the service needed from this image. Return ONLY the service name.", img])
                st.session_state.voice_input = f"I need a {v_res.text} service."
                st.success(f"Detected: {v_res.text}")
    else:
        st.info("Camera is currently OFF for your privacy.")

    st.divider()
    st.subheader("📍 Real-time Location")
    # Simulation of Dynamic Location (LPU default)
    u_lat = st.number_input("Your Latitude", value=31.254, format="%.4f")
    u_lon = st.number_input("Your Longitude", value=75.705, format="%.4f")

# 4. BRAIN: INTENT CLASSIFICATION
input_text = None
if "voice_input" in st.session_state:
    input_text = st.session_state.voice_input
    del st.session_state.voice_input
elif p := st.chat_input("Ask Sahayak anything..."):
    input_text = p

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are Sahayak AI by Shivam Kumar. Categorize: 1. Service Request (JSON) 2. General Chat (JSON)."},
            {"role": "user", "content": input_text}
        ],
        response_format={"type": "json_object"}
    )
    res = json.loads(completion.choices[0].message.content)

    if res.get("type") == "chat":
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
    else:
        service = res.get('service', 'General').title()
        # DYNAMIC DISTANCE CALCULATION
        agent_lat, agent_lon = 31.280, 75.720 
        dist = calculate_distance(u_lat, u_lon, agent_lat, agent_lon)
        
        st.session_state.last_booking = {
            "service": service,
            "dist": dist,
            "total": 299 + round(dist * 15, 2),
            "otp": "4900",
            "agent": "Rajesh Kumar (LPU)"
        }
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
        requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

# 5. MAIN UI
st.title("🤖 Sahayak AI: Pro")
c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("💬 Chat Session")
    for msg in st.session_state.messages[-3:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])

with c2:
    if b := st.session_state.last_booking:
        st.success(f"### {b['service']} Dispatched!")
        st.metric("Total Payable", f"₹{b['total']}")
        st.write(f"📍 Distance: {b['dist']} km | **OTP: {b['otp']}**")
        
        m = folium.Map(location=[u_lat, u_lon], zoom_start=13)
        folium.Marker([u_lat, u_lon], icon=folium.Icon(color='blue', icon='user')).add_to(m)
        folium.Marker([31.280, 75.720], icon=folium.Icon(color='red', icon='wrench')).add_to(m)
        st_folium(m, height=300, width=550, key="dynamic_map")
        st.balloons()