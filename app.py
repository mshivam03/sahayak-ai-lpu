import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
import os
import json
import uuid
import math
import requests
from datetime import datetime
from streamlit_folium import st_folium
from groq import Groq
import google.generativeai as genai
from PIL import Image
from streamlit_mic_recorder import mic_recorder

# ==========================================
# 1. UNIVERSAL CONFIGURATION
# ==========================================
# Developer: Shivam Kumar (12514900)
REQUESTBIN_URL = "https://eoedejtm2wdnwrz.m.pipedream.net"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCXhGXTZPrtr4lDFvjJifgUubritqDT--M")

client = Groq(api_key=GROQ_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return round(R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a))), 2)

# ==========================================
# 2. UI GLOBAL STYLING
# ==========================================
st.set_page_config(page_title="Nexus Master AI", layout="wide")

# Global CSS for Premium Dark Feel
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: white; }
    .st-emotion-cache-1kyx06y { background: #111; border: 1px solid #00ff00; border-radius: 15px; }
    .neon-card { background: rgba(0, 255, 0, 0.05); border: 1px solid #00ff00; padding: 20px; border-radius: 15px; box-shadow: 0 0 20px rgba(0,255,0,0.1); }
    .neon-text { color: #00ff00; font-weight: bold; text-shadow: 0 0 10px #00ff00; }
    .stButton>button { background-color: #00ff00; color: black; font-weight: bold; border-radius: 10px; border: none; }
    </style>
    """, unsafe_allow_html=True)

if "bookings" not in st.session_state: 
    st.session_state.bookings = []

# ==========================================
# 3. SIDEBAR (Persistent Info)
# ==========================================
with st.sidebar:
    st.markdown("<h2 class='neon-text'>NEXUS CONTROL</h2>", unsafe_allow_html=True)
    st.write(f"**Dev:** Shivam Kumar")
    st.write(f"**ID:** 12514900")
    st.divider()
    nav = st.radio("Navigation", ["Dashboard", "Service Booking", "Analytics"])
    st.divider()
    u_lat = st.number_input("User Lat", value=31.254, format="%.4f")
    u_lon = st.number_input("User Lon", value=75.705, format="%.4f")
    st.success("System: Open Access Mode")

# ==========================================
# 4. MAIN NAVIGATION MODULES
# ==========================================

# --- DASHBOARD MODULE ---
if nav == "Dashboard":
    st.markdown("<h1 class='neon-text'>📊 System Overview</h1>", unsafe_allow_html=True)
    if not st.session_state.bookings:
        st.info("System Ready. Waiting for first booking trigger...")
    else:
        c1, c2, c3 = st.columns(3)
        rev = sum(b['price'] for b in st.session_state.bookings)
        c1.metric("Total Bookings", len(st.session_state.bookings))
        c2.metric("Gross Revenue", f"₹{rev}")
        c3.metric("Uptime", "100.0%")
        
        df = pd.DataFrame(st.session_state.bookings)
        st.plotly_chart(px.bar(df, x='service', y='price', color='service', template="plotly_dark", title="Revenue Per Service Type"))

# --- SERVICE BOOKING MODULE (DYNAMIC) ---
elif nav == "Service Booking":
    st.markdown("<h1 class='neon-text'>🎙️ High-Speed Service Engine</h1>", unsafe_allow_html=True)
    col_l, col_r = st.columns([1, 1.2])

    with col_l:
        st.write("Instant Detection (Voice or Text):")
        audio_data = mic_recorder(start_prompt="⚡ CLICK & SPEAK", stop_prompt="⏹️ STOP", key='universal_mic')
        user_text = st.chat_input("Explain your problem...")

        if audio_data or user_text:
            query = user_text if user_text else "Voice/Image Intent Triggered"
            with st.spinner("⚡ NEXUS ANALYZING..."):
                # DYNAMIC INTENT DETECTION
                comp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{
                        "role": "system", 
                        "content": f"Analyze: '{query}'. Detect service: Plumber, Electrician, or Cleaning. Return JSON ONLY: {{'service': 'NAME', 'reply': 'MSG'}}"
                    }],
                    response_format={"type": "json_object"}
                )
                res = json.loads(comp.choices[0].message.content)
                
                # Logistics & Cloud Update
                dist = haversine(u_lat, u_lon, 31.281, 75.721)
                booking = {
                    "id": str(uuid.uuid4())[:6].upper(),
                    "service": res['service'],
                    "price": 299 + (dist * 15),
                    "dist": dist,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                st.session_state.bookings.append(booking)
                
                # Update Pipedream Everywhere
                try: requests.post(REQUESTBIN_URL, json=booking, timeout=1)
                except: pass
                
                st.session_state.last_b = booking
                st.rerun()

    with col_r:
        if "last_b" in st.session_state:
            lb = st.session_state.last_b
            st.markdown(f"""
            <div class='neon-card'>
                <h2 class='neon-text'>✅ {lb['service']} DISPATCHED</h2>
                <p>Booking ID: <b>{lb['id']}</b></p>
                <p>Status: <span style='color:#00ff00;'>En-route</span></p>
                <p>Distance: <b>{lb['dist']} km</b> | Bill: <b>₹{round(lb['price'],2)}</b></p>
                <hr style='border: 0.5px solid #00ff00;'>
                <p>Verification Code: <span style='font-size:24px; color:yellow;'>4900</span></p>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()

# --- ANALYTICS MODULE ---
elif nav == "Analytics":
    st.markdown("<h1 class='neon-text'>📈 Advanced Performance</h1>", unsafe_allow_html=True)
    if st.session_state.bookings:
        df = pd.DataFrame(st.session_state.bookings)
        st.plotly_chart(px.line(df, x='timestamp', y='price', markers=True, template="plotly_dark", title="Transaction Trend"))
        
        m = folium.Map(location=[u_lat, u_lon], zoom_start=14, tiles="CartoDB dark_matter")
        folium.Marker([u_lat, u_lon], icon=folium.Icon(color='green', icon='user')).add_to(m)
        st_folium(m, height=450, width=1100)