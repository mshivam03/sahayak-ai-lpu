import streamlit as st
from groq import Groq
import json
import folium
from streamlit_folium import st_folium
import speech_recognition as sr
import requests
import math

# 1. CORE CONFIG (Shivam Kumar - 12514900)
GROQ_API_KEY = "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"
REQUESTBIN_URL = "https://eowayl2i7ckb9xd.m.pipedream.net"
client = Groq(api_key=GROQ_API_KEY)

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)

st.set_page_config(page_title="Sahayak AI Pro", layout="wide")

# UI Styling
st.markdown("""
    <style>
    .backend-box { background: #0e1117; padding: 15px; border-radius: 10px; border: 1px solid #333; font-family: monospace; }
    .metric-card { background: #1e1e1e; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff00; }
    .total-price { font-size: 30px; color: #00ff00; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None

# 3. SIDEBAR: THE DASHING BACKEND DASHBOARD
with st.sidebar:
    st.title("🛠️ Admin Dashboard")
    
    # Live Metrics
    st.markdown("### 📊 System Health")
    c1, c2 = st.columns(2)
    c1.metric("API Latency", "320ms", "-20ms")
    c2.metric("Uptime", "99.9%", "Stable")
    
    st.divider()
    
    # Voice Control with Error Handling
    st.subheader("🎙️ Voice Command")
    if st.button("Tap to Speak (Bolo Shivam)", use_container_width=True):
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.toast("Listening...")
                audio = r.listen(source, timeout=5)
                st.session_state.voice_input = r.recognize_google(audio, language='hi-IN')
                st.rerun()
        except Exception as e:
            st.error("Mic access limited to Localhost. Use Text Input for Cloud Demo.")
    
    st.divider()
    st.markdown("#### 📟 SMS Dispatch Center")
    if b := st.session_state.last_booking:
        st.code(f"DEST: +91 98XXX-XXXXX\nBODY: New {b['service']} OTP: {b['otp']}", language="bash")
    else:
        st.caption("Waiting for trigger...")

# 4. INPUT LOGIC
input_text = None
if "voice_input" in st.session_state:
    input_text = st.session_state.voice_input
    del st.session_state.voice_input
elif p := st.chat_input("Kaun si service chahiye?"):
    input_text = p

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    # AI Processing
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": "Extract JSON: {'service', 'urgency'}"}, {"role": "user", "content": input_text}],
        response_format={"type": "json_object"}
    )
    res = json.loads(completion.choices[0].message.content)
    
    # LOGISTICS
    USER_LOC = [31.254, 75.705] 
    AGENT_LOC = [31.280, 75.720]
    dist = calculate_distance(USER_LOC[0], USER_LOC[1], AGENT_LOC[0], AGENT_LOC[1])
    
    base = 299
    dist_fee = round(dist * 15, 2)
    
    st.session_state.last_booking = {
        "service": res.get('service', 'General'),
        "dist": dist,
        "total": base + dist_fee,
        "otp": "4900",
        "raw_ai_data": res
    }
    requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

# 5. MAIN UI
st.title("🤖 Sahayak AI Pro")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("💬 Active Session")
    for msg in st.session_state.messages[-2:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if st.session_state.last_booking:
        st.write("---")
        st.subheader("🛠️ Backend Trace")
        with st.expander("View Raw JSON Payload", expanded=True):
            st.json(st.session_state.last_booking)

with col2:
    if b := st.session_state.last_booking:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='color:#00ff00;'>✅ Booking Confirmed</h2>
            <p><b>Service:</b> {b['service']} | <b>Distance:</b> {b['dist']} km</p>
            <div class='total-price'>Total Payable: ₹{b['total']}</div>
            <hr>
            <p>🔑 <b>Verification OTP: {b['otp']}</b></p>
            <button style='width:100%; background:#00ff00; border:none; padding:10px; border-radius:5px; font-weight:bold;'>PROCEED TO PAYMENT</button>
        </div>
        """, unsafe_allow_html=True)
        
        m = folium.Map(location=[31.254, 75.705], zoom_start=13)
        folium.Marker([31.254, 75.705], icon=folium.Icon(color='blue')).add_to(m)
        folium.Marker([31.280, 75.720], icon=folium.Icon(color='red')).add_to(m)
        folium.PolyLine([[31.254, 75.705], [31.280, 75.720]], color="#00ff00").add_to(m)
        st_folium(m, height=300, width=500)
        st.balloons()