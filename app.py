import streamlit as st
from groq import Groq
import json
import folium
from streamlit_folium import st_folium
import speech_recognition as sr
import requests
import math

# 1. FIXED CONFIGURATION
GROQ_API_KEY = "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"
REQUESTBIN_URL = "https://eowayl2i7ckb9xd.m.pipedream.net"
client = Groq(api_key=GROQ_API_KEY)

# Haversine Formula for Distance Calculation
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

st.set_page_config(page_title="Sahayak AI Premium", layout="wide")

# CSS for Stylish UI
st.markdown("""
    <style>
    .booking-card { background: #1e1e1e; padding: 20px; border-radius: 15px; border: 2px solid #00ff00; color: white; }
    .price-details { background: #2d2d2d; padding: 10px; border-radius: 8px; margin: 10px 0; font-size: 14px; }
    .total-price { font-size: 26px; color: #00ff00; font-weight: bold; }
    .otp-badge { background:#00ff00; color:black; padding:5px 10px; border-radius:5px; font-weight:bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. VOICE ENGINE (Ye wapas add kar diya hai)
def start_listening():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.sidebar.info("🎙️ Listening... Bolo Shivam!")
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio, language='hi-IN')
        except: 
            st.sidebar.error("Nahi suna, fir se try karo!")
            return None

# 3. SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None

# 4. LOCATIONS (LPU Coordinates)
USER_LOC = [31.254, 75.705] 
AGENT_LOC = [31.280, 75.720] 

# 5. SIDEBAR (Voice Control wapas yahan hai)
with st.sidebar:
    st.title("🎙️ Voice Booking")
    if st.button("Tap to Speak", use_container_width=True):
        voice_data = start_listening()
        if voice_data:
            st.session_state.voice_input = voice_data
            st.rerun()
    st.divider()
    st.info("Status: System Online ✅")

# 6. INPUT LOGIC
input_text = None
if "voice_input" in st.session_state:
    input_text = st.session_state.voice_input
    del st.session_state.voice_input
elif p := st.chat_input("Kaun si service chahiye?"):
    input_text = p

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    # AI Brain (Groq)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "Extract JSON: {'service', 'urgency'}"}, {"role": "user", "content": input_text}],
        response_format={"type": "json_object"}
    )
    res = json.loads(completion.choices[0].message.content)
    
    # PRICING + DISTANCE
    dist = calculate_distance(USER_LOC[0], USER_LOC[1], AGENT_LOC[0], AGENT_LOC[1])
    base_prices = {"Cleaning": 499, "Plumbing": 299, "Electrical": 399}
    base = base_prices.get(res.get('service', 'General'), 199)
    dist_charge = round(dist * 15, 2) 
    urgency_fee = 100 if res.get('urgency') == 'HIGH' else 0
    
    st.session_state.last_booking = {
        "service": res.get('service'),
        "dist": dist,
        "total": base + dist_charge + urgency_fee,
        "breakdown": {"Base": base, "Distance": dist_charge, "Urgency": urgency_fee},
        "otp": "4900" # Based on your Roll No
    }
    # Sync to Pipedream
    requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

# 7. DISPLAY
st.title("🤖 Sahayak AI Premium")

col1, col2 = st.columns([1, 1])
with col1:
    for msg in st.session_state.messages[-3:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])

with col2:
    if st.session_state.last_booking:
        b = st.session_state.last_booking
        st.markdown(f"""
        <div class="booking-card">
            <h2 style='color:#00ff00;'>Booking Confirmed</h2>
            <p>📍 <b>Distance:</b> {b['dist']} km</p>
            <div class="price-details">
                Base Price: ₹{b['breakdown']['Base']}<br>
                Travel Fee: ₹{b['breakdown']['Distance']}<br>
                Urgency Fee: ₹{b['breakdown']['Urgency']}
            </div>
            <p class="total-price">Total: ₹{b['total']}</p>
            <p>🔑 <span class="otp-badge">OTP: {b['otp']}</span> | Agent: Rajesh Kumar</p>
        </div>
        """, unsafe_allow_html=True)
        
        m = folium.Map(location=USER_LOC, zoom_start=13)
        folium.Marker(USER_LOC, popup="You", icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker(AGENT_LOC, popup="Agent", icon=folium.Icon(color='red')).add_to(m)
        folium.PolyLine([USER_LOC, AGENT_LOC], color="green", weight=3).add_to(m)
        st_folium(m, height=300, width=500, key="final_map")
        st.balloons()