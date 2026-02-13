import streamlit as st
from groq import Groq
import json
import folium
from streamlit_folium import st_folium
import speech_recognition as sr
import requests
import math

# 1. CONFIGURATION
GROQ_API_KEY = "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"
REQUESTBIN_URL = "https://eowayl2i7ckb9xd.m.pipedream.net"
client = Groq(api_key=GROQ_API_KEY)

# Haversine Formula for Logistics
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

st.set_page_config(page_title="Sahayak AI Premium", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main-card { background: #1e1e1e; padding: 25px; border-radius: 15px; border: 2px solid #00ff00; color: white; margin-bottom: 20px; }
    .payment-box { background: #262730; padding: 15px; border-radius: 10px; border: 1px dashed #00ff00; margin-top: 15px; }
    .total-price { font-size: 32px; color: #00ff00; font-weight: bold; }
    .sms-log { font-family: 'Courier New', monospace; font-size: 12px; color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# 2. SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None

# 3. LOCATIONS (LPU Focused)
USER_LOC = [31.254, 75.705] 
AGENT_LOC = [31.280, 75.720] 

# 4. SIDEBAR (SMS & VOICE)
with st.sidebar:
    st.title("📲 Admin Center")
    if st.button("🎙️ Tap to Speak (Bolo Shivam)", use_container_width=True):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.toast("Listening...")
            try:
                audio = r.listen(source, timeout=5)
                st.session_state.voice_input = r.recognize_google(audio, language='hi-IN')
                st.rerun()
            except: st.error("Mic issue!")

    st.divider()
    st.subheader("📟 SMS Dispatch Log")
    if st.session_state.last_booking:
        b = st.session_state.last_booking
        st.markdown(f"""<div class='sms-log'>
        SENT TO: +91 98765-43210<br>
        MSG: New {b['service']} request at LPU. OTP: {b['otp']}. Fee: ₹{b['total']}.
        </div>""", unsafe_allow_html=True)
    else:
        st.caption("No active dispatches")

# 5. INPUT ENGINE
input_text = None
if "voice_input" in st.session_state:
    input_text = st.session_state.voice_input
    del st.session_state.voice_input
elif p := st.chat_input("Ex: Carpenter chahiye urgent LPU Gate 1 pe"):
    input_text = p

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "Extract JSON: {'service', 'urgency'}"}, {"role": "user", "content": input_text}],
        response_format={"type": "json_object"}
    )
    res = json.loads(completion.choices[0].message.content)
    
    # ADVANCED PRICING
    dist = calculate_distance(USER_LOC[0], USER_LOC[1], AGENT_LOC[0], AGENT_LOC[1])
    base_prices = {"Cleaning": 499, "Plumbing": 299, "Electrical": 399, "Carpenter": 350}
    service = res.get('service', 'General').title()
    base = base_prices.get(service, 199)
    dist_fee = round(dist * 15, 2)
    urgency = 100 if res.get('urgency') == 'HIGH' else 0
    
    st.session_state.last_booking = {
        "service": service,
        "dist": dist,
        "total": base + dist_fee + urgency,
        "base": base, "dist_fee": dist_fee, "urgency": urgency,
        "otp": "4900",
        "agent": "Rajesh Kumar (LPU Partner)"
    }
    requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

# 6. MAIN INTERFACE
st.title("🤖 Sahayak AI Premium")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("💬 Conversation")
    for msg in st.session_state.messages[-3:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])

with c2:
    if b := st.session_state.last_booking:
        st.markdown(f"""
        <div class="main-card">
            <h2 style='color:#00ff00; margin:0;'>Booking Confirmed!</h2>
            <p>🛠 <b>Service:</b> {b['service']} | 📍 <b>Dist:</b> {b['dist']} km</p>
            <hr>
            <div style='display:flex; justify-content:space-between;'>
                <span>Base Price:</span> <span>₹{b['base']}</span>
            </div>
            <div style='display:flex; justify-content:space-between;'>
                <span>Travel Fee:</span> <span>₹{b['dist_fee']}</span>
            </div>
            <div style='display:flex; justify-content:space-between; color:#ff4b4b;'>
                <span>Urgency Fee:</span> <span>₹{b['urgency']}</span>
            </div>
            <div class='total-price'>Total: ₹{b['total']}</div>
            <div class='payment-box'>
                <b>💳 Secure Checkout</b><br>
                <small>Pay via UPI, GPay or Card on arrival</small><br>
                <button style='width:100%; background:#00ff00; border:none; padding:10px; border-radius:5px; font-weight:bold; margin-top:10px;'>PROCEED TO PAY</button>
            </div>
            <p style='text-align:center; margin-top:15px;'><b>Verification OTP: <span style='color:#00ff00;'>{b['otp']}</span></b></p>
        </div>
        """, unsafe_allow_html=True)
        
        m = folium.Map(location=USER_LOC, zoom_start=13)
        folium.Marker(USER_LOC, popup="Shivam (LPU)", icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker(AGENT_LOC, popup="Agent Rajesh", icon=folium.Icon(color='red')).add_to(m)
        folium.PolyLine([USER_LOC, AGENT_LOC], color="#00ff00", weight=4).add_to(m)
        st_folium(m, height=250, width=550, key="pro_map_final")
        st.balloons()