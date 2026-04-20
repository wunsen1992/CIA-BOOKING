import streamlit as st
import requests
import json
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="CIA Booking System", page_icon="🏗️", layout="wide")

# ใส่ API Key ของคุณที่นี่
API_KEY = "" 

# --- Custom Styling (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f1f5f9; }
    
    /* Card Design */
    .room-card {
        background-color: white;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    
    /* AI Section */
    .ai-panel {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: white;
        padding: 25px;
        border-radius: 20px;
        margin-bottom: 25px;
    }

    /* Status Tags */
    .tag { padding: 3px 10px; border-radius: 8px; font-size: 11px; font-weight: bold; color: white; }
    .tag-theater { background-color: #f97316; }
    .tag-meeting { background-color: #3b82f6; }
    .tag-table { background-color: #10b981; }
    </style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'bookings' not in st.session_state:
    st.session_state.bookings = []
if 'selected_room_id' not in st.session_state:
    st.session_state.selected_room_id = None
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""

# --- Room Data ---
ROOM_DATA = [
    {"id": "tr1", "name": "Theater Room 1", "type": "theater", "cap": 10, "desc": "ห้องประชุมขนาดใหญ่ เหมาะสำหรับการสัมมนา", "img": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400"},
    {"id": "tr2", "name": "Theater Room 2", "type": "theater", "cap": 10, "desc": "ห้องเอนกประสงค์พร้อมเครื่องเสียงครบครัน", "img": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=400"},
]
for i in range(1, 6):
    ROOM_DATA.append({"id": f"mr{i}", "name": f"Meeting Room {i}", "type": "meeting", "cap": 8, "desc": "ห้องทำงานกลุ่มขนาดกลาง สำหรับระดมสมอง", "img": "https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=400"})
for i in range(1, 7):
    ROOM_DATA.append({"id": f"et{i}", "name": f"Table {i}", "type": "table", "cap": 6, "desc": "พื้นที่เปิดโล่งสำหรับนั่งทำงานกลุ่ม", "img": "https://images.unsplash.com/photo-1529148482759-b35b25c5f217?w=400"})

# --- Helper Functions ---
def call_gemini(prompt):
    if not API_KEY: return "กรุณาใส่ API Key ในโค้ดก่อนใช้งาน"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    system_prompt = "You are a Civil Engineering AI. Recommend a CIA room and 3 project steps. Respond in Thai."
    payload = {"contents": [{"parts": [{"text": f"{system_prompt}\nProject: {prompt}"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "ขออภัย ระบบ AI ขัดข้อง"

def is_conflict(room_id, start, duration):
    req_slots = set(range(start, start + duration))
    for b in st.session_state.bookings:
        if b['room_id'] == room_id:
            booked_slots = set(range(b['start'], b['start'] + b['duration']))
            if req_slots.intersection(booked_slots):
                return True
    return False

# --- App Layout ---
st.title("🏗️ CIA BOOKING SYSTEM")
st.markdown("<p style='margin-top:-20px; color:orange;'>ระบบจองพื้นที่คณะวิศวกรรมศาสตร์ (09:00 - 17:00)</p>", unsafe_allow_html=True)

# Navigation Menu
menu = st.tabs(["🔍 ค้นหาและจองพื้นที่", "📅 รายการจองของฉัน"])

# --- TAB 1: Search & Book ---
with menu[0]:
    # AI Assistant Section
    st.markdown("""<div class="ai-panel"><h3>✨ AI Civil Consultant</h3><p>ให้ AI ช่วยวางแผนโปรเจกต์และเลือกห้อง</p></div>""", unsafe_allow_html=True)
    ai_q = st.text_input("ระบุหัวข้อโปรเจกต์ของคุณ...")
    if st.button("ขอคำแนะนำจาก AI"):
        with st.spinner("AI กำลังวิเคราะห์..."):
            st.session_state.ai_response = call_gemini(ai_q)
    
    if st.session_state.ai_response:
        st.info(st.session_state.ai_response)
        if st.button("ล้างคำแนะนำ"):
            st.session_state.ai_response = ""
            st.rerun()

    st.divider()

    # --- Booking Form Section (จะแสดงผลเมื่อมีการเลือกห้อง) ---
    if st.session_state.selected_room_id:
        room = next((r for r in ROOM_DATA if r['id'] == st.session_state.selected_room_id), None)
        if room:
            st.warning(f"📍 คุณกำลังทำรายการจอง: **{room['name']}**")
            with st.form("booking_form", clear_on_submit=True):
                col_f1, col_f2 = st.columns(2)
                name = col_f1.text_input("ชื่อ-นามสกุล")
                sid = col_f2.text_input("รหัสนักศึกษา")
                
                col_f3, col_f4 = st.columns(2)
                t_start = col_f3.selectbox("เริ่มเวลา", range(9, 17), format_func=lambda x: f"{x:02d}:00 น.")
                dur = col_f4.select_slider("ระยะเวลา (ชั่วโมง)", options=[1, 2, 3, 4])
                
                c1, c2 = st.columns(2)
                submit = c1.form_submit_button("ยืนยันการจอง")
                cancel = c2.form_submit_button("ยกเลิกการเลือก")
                
                if submit:
                    if not name or not sid:
                        st.error("❌ กรุณากรอกข้อมูลให้ครบถ้วน")
                    elif t_start + dur > 17:
                        st.error("❌ เวลาที่จองเกินเวลาทำการ (ปิด 17:00)")
                    elif is_conflict(room['id'], t_start, dur):
                        st.error("❌ ช่วงเวลานี้มีการจองแล้ว")
                    else:
                        st.session_state.bookings.append({
                            "room_id": room['id'], "room_name": room['name'],
                            "name": name, "sid": sid, "start": t_start, "duration": dur
                        })
                        st.success(f"✅ จอง {room['name']} สำเร็จ!")
                        st.session_state.selected_room_id = None
                        st.rerun()
                
                if cancel:
                    st.session_state.selected_room_id = None
                    st.rerun()
            st.divider()

    # --- Room Browser Section ---
    st.subheader("เลือกพื้นที่ที่คุณต้องการ")
    
    # Filter & Search UI
    f_col1, f_col2 = st.columns([2, 1])
    search_q = f_col1.text_input("🔍 ค้นหาห้อง...", placeholder="พิมพ์ชื่อห้อง...")
    filter_t = f_col2.selectbox("ประเภท", ["ทั้งหมด", "theater", "meeting", "table"])
    
    # Filter Logic
    filtered = [r for r in ROOM_DATA if (filter_t == "ทั้งหมด" or r['type'] == filter_t) and (search_q.lower() in r['name'].lower())]
    
    # Display Grid
    rows = [filtered[i:i + 4] for i in range(0, len(filtered), 4)]
    for row in rows:
        cols = st.columns(4)
        for idx, room in enumerate(row):
            with cols[idx]:
                st.markdown(f"""
                <div class="room-card">
                    <img src="{room['img']}" style="width:100%; border-radius:15px 15px 0 0; height:120px; object-fit:cover;">
                    <div style="padding:10px">
                        <span class="tag tag-{room['type']}">{room['type'].upper()}</span>
                        <h4 style="margin:8px 0 2px 0; font-size:14px;">{room['name']}</h4>
                        <p style="font-size:11px; color:gray; margin-bottom:5px;">👥 {room['cap']} Seats</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # ปุ่มเลือกห้อง
                if st.button(f"เลือก {room['name']}", key=f"btn_{room['id']}", use_container_width=True):
                    st.session_state.selected_room_id = room['id']
                    st.rerun()

# --- TAB 2: My Bookings ---
with menu[1]:
    st.subheader("การจองทั้งหมดของคุณ")
    if not st.session_state.bookings:
        st.info("คุณยังไม่มีรายการจองในขณะนี้")
    else:
        for i, b in enumerate(st.session_state.bookings):
            with st.container():
                c1, c2, c3 = st.columns([1, 4, 1])
                c1.markdown(f"<div style='background:#f97316; color:white; padding:10px; border-radius:10px; text-align:center;'>{b['start']:02d}:00</div>", unsafe_allow_html=True)
                c2.write(f"**{b['room_name']}** | {b['name']} ({b['sid']}) - {b['duration']} ชั่วโมง")
                if c3.button("ยกเลิก", key=f"del_{i}"):
                    st.session_state.bookings.pop(i)
                    st.rerun()
                st.divider()

st.markdown("<p style='text-align:center; color:gray; font-size:10px; margin-top:50px;'>CIA BOOKING • CIVIL ENGINEERING PROJECT</p>", unsafe_allow_html=True)
