import streamlit as st
import requests
import json
import os
from datetime import datetime, date, timedelta

# --- Configuration ---
st.set_page_config(page_title="CIA Booking Shared", page_icon="🏗️", layout="wide")

# ใส่ API Key ของคุณที่นี่
API_KEY = "" 
DB_FILE = "bookings_db.json"

# --- Database Functions (ระบบเก็บข้อมูลส่วนกลาง) ---
def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Custom Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    .stApp { background-color: #f8fafc; }
    .room-card { background-color: white; border-radius: 15px; border: 1px solid #e2e8f0; padding: 10px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .tag { padding: 2px 8px; border-radius: 5px; font-size: 10px; font-weight: bold; color: white; }
    .tag-theater { background-color: #f97316; }
    .tag-meeting { background-color: #3b82f6; }
    .tag-table { background-color: #10b981; }
    </style>
""", unsafe_allow_html=True)

# --- Room Data ---
ROOM_DATA = [
    {"id": "tr1", "name": "Theater Room 1", "type": "theater", "cap": 10, "img": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400"},
    {"id": "tr2", "name": "Theater Room 2", "type": "theater", "cap": 10, "img": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=400"},
]
for i in range(1, 6):
    ROOM_DATA.append({"id": f"mr{i}", "name": f"Meeting Room {i}", "type": "meeting", "cap": 8, "img": "https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=400"})
for i in range(1, 7):
    ROOM_DATA.append({"id": f"et{i}", "name": f"Table {i}", "type": "table", "cap": 6, "img": "https://images.unsplash.com/photo-1529148482759-b35b25c5f217?w=400"})

# --- Helper Functions ---
def is_conflict(room_id, booking_date, start, duration):
    all_bookings = load_db()
    req_slots = set(range(start, start + duration))
    for b in all_bookings:
        if b['room_id'] == room_id and b['date'] == str(booking_date):
            booked_slots = set(range(b['start'], b['start'] + b['duration']))
            if req_slots.intersection(booked_slots):
                return True
    return False

def call_gemini(prompt):
    if not API_KEY: return "กรุณาใส่ API Key"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    payload = {"contents": [{"parts": [{"text": f"You are a Civil Engineering AI. Give 3 steps for: {prompt} in Thai language."}]}]}
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "AI ไม่พร้อมใช้งานในขณะนี้"

# --- Main App ---
st.title("🏗️ CIA SHARED BOOKING")
st.caption("ระบบจองพื้นที่ส่วนกลาง - ข้อมูลอัปเดตเรียลไทม์สำหรับทุกคน")

# Initialize Local State for AI only
if 'ai_res' not in st.session_state: st.session_state.ai_res = ""
if 'sel_room' not in st.session_state: st.session_state.sel_room = None

tabs = st.tabs(["🔍 ค้นหาและจอง", "📋 ประวัติการจองทั้งหมด"])

# --- TAB 1: Booking ---
with tabs[0]:
    # AI Assistant (Optional)
    with st.expander("✨ ปรึกษา AI วางแผนงานก่อนจอง"):
        ai_q = st.text_input("ระบุโปรเจกต์ของคุณ")
        if st.button("ถาม AI"):
            st.session_state.ai_res = call_gemini(ai_q)
        if st.session_state.ai_res: st.info(st.session_state.ai_res)

    st.divider()

    # แสดงแบบฟอร์มเมื่อเลือกห้อง
    if st.session_state.sel_room:
        room = next(r for r in ROOM_DATA if r['id'] == st.session_state.sel_room)
        st.success(f"📍 กำลังจอง: **{room['name']}**")
        with st.form("book_form"):
            col1, col2 = st.columns(2)
            u_name = col1.text_input("ชื่อผู้จอง")
            u_sid = col2.text_input("รหัสนักศึกษา")
            
            col3, col4, col5 = st.columns(3)
            # จองล่วงหน้าได้ 1 วัน
            u_date = col3.date_input("วันที่จอง", min_value=date.today(), max_value=date.today() + timedelta(days=1))
            u_start = col4.selectbox("เริ่มเวลา", range(9, 17), format_func=lambda x: f"{x:02d}:00 น.")
            u_dur = col5.selectbox("ระยะเวลา (ชม.)", [1, 2, 3, 4])
            
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.form_submit_button("ยืนยันการจอง", use_container_width=True):
                if not u_name or not u_sid:
                    st.error("กรุณากรอกข้อมูลให้ครบ")
                elif u_start + u_dur > 17:
                    st.error("เวลาที่เลือกเกิน 17:00 น.")
                elif is_conflict(room['id'], u_date, u_start, u_dur):
                    st.error("❌ มีคนจองเวลานี้ไปแล้ว! โปรดตรวจสอบตารางการจอง")
                else:
                    current_db = load_db()
                    current_db.append({
                        "room_id": room['id'], "room_name": room['name'],
                        "name": u_name, "sid": u_sid, "date": str(u_date),
                        "start": u_start, "duration": u_dur, "timestamp": str(datetime.now())
                    })
                    save_db(current_db)
                    st.balloons()
                    st.session_state.sel_room = None
                    st.rerun()
            
            if c_btn2.form_submit_button("ยกเลิก"):
                st.session_state.sel_room = None
                st.rerun()
    
    # Filter
    f_col1, f_col2 = st.columns([2, 1])
    search = f_col1.text_input("🔍 ค้นหาห้อง...")
    f_type = f_col2.selectbox("ประเภท", ["ทั้งหมด", "theater", "meeting", "table"])
    
    # Grid
    filtered = [r for r in ROOM_DATA if (f_type == "ทั้งหมด" or r['type'] == f_type) and (search.lower() in r['name'].lower())]
    
    for i in range(0, len(filtered), 4):
        cols = st.columns(4)
        for j, room in enumerate(filtered[i:i+4]):
            with cols[j]:
                st.markdown(f"""
                <div class="room-card">
                    <img src="{room['img']}" style="width:100%; border-radius:10px; height:100px; object-fit:cover;">
                    <h5 style="margin:5px 0 0 0;">{room['name']}</h5>
                    <span class="tag tag-{room['type']}">{room['type'].upper()}</span>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"เลือก {room['name']}", key=room['id']):
                    st.session_state.sel_room = room['id']
                    st.rerun()

# --- TAB 2: Shared History ---
with tabs[1]:
    st.subheader("📋 ตารางการใช้งานทั้งหมด")
    all_data = load_db()
    
    if not all_data:
        st.write("ยังไม่มีข้อมูลการจอง")
    else:
        # เรียงลำดับตามวันที่และเวลา
        sorted_data = sorted(all_data, key=lambda x: (x['date'], x['start']))
        
        # กรองเฉพาะวันนี้และอนาคต (ลบประวัติเก่าอัตโนมัติในการแสดงผล)
        today_str = str(date.today())
        
        for b in sorted_data:
            is_today = "วันนี้" if b['date'] == today_str else "พรุ่งนี้"
            with st.expander(f"📅 {b['date']} ({is_today}) | 🕒 {b['start']:02d}:00 | 📍 {b['room_name']}"):
                st.write(f"**ผู้จอง:** {b['name']} ({b['sid']})")
                st.write(f"**เวลา:** {b['start']:02d}:00 - {b['start']+b['duration']:02d}:00 น.")
                if st.button("ยกเลิกการจองนี้ (Admin/User)", key=f"del_{b['timestamp']}"):
                    new_db = [x for x in all_data if x['timestamp'] != b['timestamp']]
                    save_db(new_db)
                    st.rerun()

st.sidebar.info("💡 ข้อมูลจะถูกบันทึกลงไฟล์ bookings_db.json ทำให้ทุกคนเห็นข้อมูลเดียวกัน")
