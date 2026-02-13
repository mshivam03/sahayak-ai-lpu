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

# 1. CORE CONFIGURATION
# Shivam Kumar (12514900) - B.Tech CSE (LPU)
GROQ_API_KEY = "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"
GEMINI_API_KEY = "AIzaSyCXhGXTZPrtr4lDFvjJifgUubritqDT--M"
REQUESTBIN_URL = "https://eowayl2i7ckb9xd.m.pipedream.net"

# Client Setup
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

# CSS for Dashing Backend UI
st.markdown("""
    <style>
    .metric-card { background: #1e1e1e; padding: 20px; border-radius: 15px; border-left: 5px solid #00ff00; color: white; }
    .total-price { font-size: 28px; color: #00ff00; font-weight: bold; }
    .backend-trace { font-family: monospace; background: #000; padding: 10px; border-radius: 5px; color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# 2. SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None

# 3. SIDEBAR: VISION, VOICE & ANALYTICS
with st.sidebar:
    st.title("🛠️ Sahayak Control")
    st.write(f"**Dev:** Shivam Kumar (12514900)")
    
    # Vision Module
    st.subheader("👁️ AI Vision (Gemini)")
    img_file = st.camera_input("Snap issue photo")
    if img_file:
        img = Image.open(img_file)
        with st.spinner("Analyzing with Gemini..."):
            v_res = vision_model.generate_content([
                "Identify the home service needed (e.g. Plumber, Electrician) based on this image. Return ONLY the service name.", 
                img
            ])
            st.session_state.voice_input = f"I need a {v_res.text} for the issue in this photo."
            st.success(f"Detected: {v_res.text}")

    st.divider()
    
    # Analytics
    st.markdown("### 📊 Backend Health")
    st.metric("Model", "Llama 3.3-70B", "Active")
    st.metric("Vision API", "Gemini 1.5", "Connected")

# 4. BRAIN: INTENT CLASSIFICATION
input_text = None
if "voice_input" in st.session_state:
    input_text = st.session_state.voice_input
    del st.session_state.voice_input
elif p := st.chat_input("Ask Sahayak or book a service..."):
    input_text = p

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    # Routing Logic using Llama 3.3 Versatile
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are Sahayak AI by Shivam Kumar.
            Categorize input:
            1. Service Request -> JSON: {"type": "booking", "service": "Name", "urgency": "HIGH", "reply": "msg"}
            2. General Chat/Identity -> JSON: {"type": "chat", "reply": "msg"}
            Always mention you are created by Shivam Kumar if asked about identity."""},
            {"role": "user", "content": input_text}
        ],
        response_format={"type": "json_object"}
    )
    res = json.loads(completion.choices[0].message.content)

    if res.get("type") == "chat":
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
    else:
        # Service Logistics
        service = res.get('service', 'General').title()
        dist = calculate_distance(31.254, 75.705, 31.280, 75.720)
        st.session_state.last_booking = {
            "service": service,
            "dist": dist,
            "total": 299 + round(dist * 15, 2),
            "otp": "4900",
            "agent": "Rajesh Kumar (LPU)"
        }
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
        requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

# 5. MAIN INTERFACE
st.title("🤖 Sahayak AI: Pro Assistant")
st.caption("B.Tech CSE Hackathon Build | Shivam Kumar")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("💬 Active Chat")
    for msg in st.session_state.messages[-3:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if st.session_state.last_booking:
        with st.expander("🛠️ Backend Trace (JSON)"):
            st.json(st.session_state.last_booking)

with col2:
    if b := st.session_state.last_booking:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='color:#00ff00; margin:0;'>✅ Service Dispatched</h2>
            <p><b>Request:</b> {b['service']} | <b>Distance:</b> {b['dist']} km</p>
            <div class='total-price'>Est. Total: ₹{b['total']}</div>
            <hr style='border-color:#444;'>
            <p>👨‍🔧 <b>Agent:</b> {b['agent']}</p>
            <p>🔑 <b>Security OTP: {b['otp']}</b></p>
            <button style='width:100%; background:#00ff00; color:black; border:none; padding:12px; border-radius:8px; font-weight:bold;'>PROCEED TO PAY</button>
        </div>
        """, unsafe_allow_html=True)
        
        m = folium.Map(location=[31.254, 75.705], zoom_start=13)
        folium.Marker([31.254, 75.705], popup="User", icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker([31.280, 75.720], popup="Agent", icon=folium.Icon(color='red')).add_to(m)
        folium.PolyLine([[31.254, 75.705], [31.280, 75.720]], color="#00ff00").add_to(m)
        st_folium(m, height=300, width=550, key="final_map")
        st.balloons()