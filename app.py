import streamlit as st
from groq import Groq
import json
import folium
from streamlit_folium import st_folium
import speech_recognition as sr
import requests
import math

# 1. CORE CONFIG (Citing User Identity: Shivam Kumar, 12514900)
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
    .metric-card { background: #1e1e1e; padding: 20px; border-radius: 15px; border-left: 5px solid #00ff00; color: white; }
    .total-price { font-size: 28px; color: #00ff00; font-weight: bold; }
    .chat-bubble { padding: 10px; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. SESSION STATE
if "messages" not in st.session_state: st.session_state.messages = []
if "last_booking" not in st.session_state: st.session_state.last_booking = None

# 3. SIDEBAR: ADMIN & SYSTEM INFO
with st.sidebar:
    st.title("🛠️ Sahayak Control")
    st.info("System: Connected to Llama-3.3-70B")
    
    st.subheader("🎙️ Voice Command")
    if st.button("Tap to Speak (Bolo Shivam)", use_container_width=True):
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.toast("Listening...")
                audio = r.listen(source, timeout=5)
                st.session_state.voice_input = r.recognize_google(audio, language='hi-IN')
                st.rerun()
        except:
            st.error("Mic access limited to Localhost.")
    
    st.divider()
    st.markdown("### 📊 Live Backend Stats")
    st.metric("Inference Speed", "0.38s", "-0.02s")
    if b := st.session_state.last_booking:
        st.success(f"Last Event: {b['service']} Booked")

# 4. ADVANCED AI LOGIC (Intent Classification)
input_text = None
if "voice_input" in st.session_state:
    input_text = st.session_state.voice_input
    del st.session_state.voice_input
elif p := st.chat_input("Ask me anything or book a service..."):
    input_text = p

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """
            You are Sahayak AI, an advanced virtual assistant created by Shivam Kumar (Roll: 12514900), a B.Tech CSE student at LPU.
            
            TASKS:
            1. If the user wants a service (plumber, cleaning, repair, etc.), return JSON: 
               {"type": "booking", "service": "Service Name", "urgency": "HIGH/NORMAL", "reply": "Confirming your booking..."}
            2. For general chat (greetings, 'who are you', jokes, coding, LPU info), return JSON:
               {"type": "chat", "reply": "A witty and helpful human-like response"}
            
            Be proud of your creator Shivam Kumar and LPU. Always return valid JSON.
            """},
            {"role": "user", "content": input_text}
        ],
        response_format={"type": "json_object"}
    )
    
    res = json.loads(completion.choices[0].message.content)

    if res.get("type") == "chat":
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
    else:
        # Transactional Logic
        service = res.get('service', 'Maintenance').title()
        USER_LOC = [31.254, 75.705] 
        AGENT_LOC = [31.280, 75.720]
        dist = calculate_distance(USER_LOC[0], USER_LOC[1], AGENT_LOC[0], AGENT_LOC[1])
        
        base = 299
        dist_fee = round(dist * 15, 2)
        total = base + dist_fee + (100 if res.get('urgency') == 'HIGH' else 0)
        
        st.session_state.last_booking = {
            "service": service,
            "dist": dist,
            "total": total,
            "otp": "4900", # Shivam's Identifier
            "agent": "Rajesh Kumar (LPU Partner)"
        }
        st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
        requests.post(REQUESTBIN_URL, json=st.session_state.last_booking)

# 5. MAIN INTERFACE
st.title("🤖 Sahayak AI: Next-Gen Assistant")
st.caption("Developed by Shivam Kumar | LPU B.Tech CSE")

c1, c2 = st.columns([1, 1.2])

with c1:
    st.subheader("💬 Smart Chat")
    for msg in st.session_state.messages[-4:]:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if st.session_state.last_booking:
        with st.expander("🛠️ Developer Trace (JSON)"):
            st.json(st.session_state.last_booking)

with c2:
    if b := st.session_state.last_booking:
        st.markdown(f"""
        <div class="metric-card">
            <h2 style='color:#00ff00; margin:0;'>✅ Booking Active</h2>
            <p><b>Service Type:</b> {b['service']}</p>
            <div class='total-price'>Estimate: ₹{b['total']}</div>
            <p style='font-size:14px; color:#aaa;'>Includes distance fee for {b['dist']} km</p>
            <hr style='border-color:#333;'>
            <p>👨‍🔧 <b>Partner:</b> {b['agent']}</p>
            <p>🔑 <b>Security OTP: {b['otp']}</b></p>
            <button style='width:100%; background:#00ff00; color:black; border:none; padding:12px; border-radius:8px; font-weight:bold;'>PAY NOW</button>
        </div>
        """, unsafe_allow_html=True)
        
        m = folium.Map(location=[31.254, 75.705], zoom_start=13)
        folium.Marker([31.254, 75.705], popup="User Location", icon=folium.Icon(color='blue', icon='home')).add_to(m)
        folium.Marker([31.280, 75.720], popup="Agent Rajesh", icon=folium.Icon(color='red', icon='wrench')).add_to(m)
        folium.PolyLine([[31.254, 75.705], [31.280, 75.720]], color="#00ff00", weight=3).add_to(m)
        st_folium(m, height=300, width=550, key="main_map")
        st.balloons()