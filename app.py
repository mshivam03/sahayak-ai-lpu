import streamlit as st
from groq import Groq
import google.generativeai as genai
import json, requests, math
from PIL import Image
import speech_recognition as sr
import folium
from streamlit_folium import st_folium

# 1. AUTHENTICATION CONFIG (Shivam Kumar - 12514900)
USER_ID = "shivam12514900"
USER_PASS = "lpu@2026"

# 2. CORE API CONFIG
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

st.set_page_config(page_title="Nexus AI Secure", layout="wide")

# 3. LOGIN GATEWAY
def login():
    if 'auth' not in st.session_state: st.session_state.auth = False
    if not st.session_state.auth:
        st.markdown("<h1 style='text-align:center; color:#00ff00;'>🛡️ Nexus AI Gateway</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            u = st.text_input("User ID")
            p = st.text_input("Password", type="password")
            if st.button("Unlock System", use_container_width=True):
                if u == USER_ID and p == USER_PASS:
                    st.session_state.auth = True
                    st.rerun()
                else: st.error("Access Denied")
        return False
    return True

if login():
    # --- UI STYLING ---
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; }
        .main-card { background: rgba(255, 255, 255, 0.05); border: 1px solid #00ff00; border-radius: 15px; padding: 20px; }
        .neon-txt { color: #00ff00; text-shadow: 0 0 5px #00ff00; }
        </style>
    """, unsafe_allow_html=True)

    # --- SIDEBAR CONTROLS ---
    with st.sidebar:
        st.title("⚙️ Controls")
        st.write(f"**Dev:** Shivam Kumar (12514900)")
        if st.button("Logout"): 
            st.session_state.auth = False
            st.rerun()
        
        st.divider()
        st.subheader("📸 Privacy & Vision")
        use_cam = st.toggle("Enable AI Eyes (Camera)")
        if use_cam:
            img_file = st.camera_input("Scanner")
            if img_file:
                img = Image.open(img_file)
                v_res = vision_model.generate_content(["Identify service needed. One word.", img])
                st.session_state.v_input = f"I need a {v_res.text}."
        
        st.divider()
        st.subheader("📍 Location")
        u_lat = st.number_input("Lat", value=31.254, format="%.4f")
        u_lon = st.number_input("Lon", value=75.705, format="%.4f")

    # --- MAIN DASHBOARD ---
    st.markdown("<h2 class='neon-txt'>🤖 Nexus AI: Next-Gen Assistant</h2>", unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 1.2])

    with col_a:
        st.subheader("💬 Smart Chat")
        if st.button("🎙️ Tap to Speak"):
            try:
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    audio = r.listen(source, timeout=5)
                    st.session_state.v_input = r.recognize_google(audio, language='hi-IN')
                    st.rerun()
            except: st.error("Mic issue. Use text input.")

        if "messages" not in st.session_state: st.session_state.messages = []
        
        user_msg = None
        if "v_input" in st.session_state:
            user_msg = st.session_state.v_input; del st.session_state.v_input
        elif p := st.chat_input("Ask Nexus..."): user_msg = p

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            comp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "You are Nexus AI by Shivam Kumar. Return JSON: {type: 'chat'/'booking', service: 'NAME', reply: 'MSG'}"}],
                response_format={"type": "json_object"}
            )
            res = json.loads(comp.choices[0].message.content)
            st.session_state.messages.append({"role": "assistant", "content": res.get("reply")})
            
            if res.get("type") == "booking":
                dist = calculate_distance(u_lat, u_lon, 31.280, 75.720)
                st.session_state.last_book = {"service": res.get('service'), "dist": dist, "total": 299 + (dist*15), "otp": "4900"}
                requests.post(REQUESTBIN_URL, json=st.session_state.last_book)

        for m in st.session_state.messages[-3:]:
            with st.chat_message(m["role"]): st.write(m["content"])

    with col_b:
        if "last_book" in st.session_state:
            b = st.session_state.last_book
            st.markdown(f"""
                <div class="main-card">
                    <h3 style="color:#00ff00;">✅ {b['service']} Dispatched</h3>
                    <p>Bill: <b>₹{round(b['total'],2)}</b> | Dist: <b>{b['dist']} km</b></p>
                    <p>Security OTP: <b style="font-size:24px;">{b['otp']}</b></p>
                </div>
            """, unsafe_allow_html=True)
            
            m = folium.Map(location=[u_lat, u_lon], zoom_start=13, tiles="CartoDB dark_matter")
            folium.Marker([u_lat, u_lon], icon=folium.Icon(color='green')).add_to(m)
            folium.Marker([31.280, 75.720], icon=folium.Icon(color='red')).add_to(m)
            st_folium(m, height=350, width=550, key="nexus_map")
            st.balloons()