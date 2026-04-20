import streamlit as st
import requests
import json
import os
from datetime import datetime, date, timedelta

# --- Configuration ---
st.set_page_config(page_title="CIA Shared Booking (Hidden ID)", page_icon="🏗️", layout="wide")

DB_FILE = "bookings_db.json"

# --- Database Functions ---
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

# --- App Layout ---
st.title("🏗️ CIA SHARED BOOKING")
st.caption("ระบบส่วนกลาง | จองล่วงหน้าได้ 1 วัน | ความปลอดภัยสูง")

if 'sel_room' not in st.session_state: st.session_state.sel_room = None

tabs = st.tabs(["🔍 ค้นหาและจอง", "📋 ตารางการจองทั้งหมด"])

# --- TAB 1: Booking ---
with tabs[0]:
    if st.session_state.sel_room:
        room = next(r for r in ROOM_DATA if r['id'] == st.session_state.sel_room)
        st.info(f"📍 กำลังจอง: **{room['name']}**")
        with st.form("book_form"):
            col1, col2 = st.columns(2)
            u_name = col1.text_input("ชื่อผู้จอง")
            u_sid = col2.text_input("รหัสนักศึกษา (ใช้ยกเลิกรายการ)", type="password", help="รหัสนี้จะถูกใช้เพื่อยืนยันตอนยกเลิกรายการ และจะไม่ถูกแสดงให้ผู้อื่นเห็น")
            
            col3, col4, col5 = st.columns(3)
            u_date = col3.date_input("วันที่จอง", min_value=date.today(), max_value=date.today() + timedelta(days=1))
            u_start = col4.selectbox("เริ่มเวลา", range(9, 17), format_func=lambda x: f"{x:02d}:00 น.")
            u_dur = col5.selectbox("ระยะเวลา (ชม.)", [1, 2, 3, 4])
            
            sub_col1, sub_col2 = st.columns(2)
            if sub_col1.form_submit_button("ยืนยันการจอง", use_container_width=True):
                if not u_name or not u_sid:
                    st.error("กรุณากรอกข้อมูลให้ครบถ้วน")
                elif u_start + u_dur > 17:
                    st.error("เวลาที่เลือกเกิน 17:00 น.")
                elif is_conflict(room['id'], u_date, u_start, u_dur):
                    st.error("❌ มีคนจองเวลานี้แล้ว โปรดเลือกเวลาอื่น")
                else:
                    db = load_db()
                    db.append({
                        "room_id": room['id'], "room_name": room['name'],
                        "name": u_name, "sid": str(u_sid), "date": str(u_date),
                        "start": u_start, "duration": u_dur, "timestamp": str(datetime.now())
                    })
                    save_db(db)
                    st.success("✅ จองสำเร็จ!")
                    st.session_state.sel_room = None
                    st.rerun()
            if sub_col2.form_submit_button("ยกเลิก"):
                st.session_state.sel_room = None
                st.rerun()

    # Search Grid
    search = st.text_input("🔍 ค้นหาห้องหรือโต๊ะ...")
    filtered = [r for r in ROOM_DATA if search.lower() in r['name'].lower()]
    
    for i in range(0, len(filtered), 4):
        cols = st.columns(4)
        for j, room in enumerate(filtered[i:i+4]):
            with cols[j]:
                st.markdown(f"""
                <div class="room-card">
                    <img src="{room['img']}" style="width:100%; border-radius:10px; height:80px; object-fit:cover;">
                    <h6 style="margin:5px 0 0 0; font-size:14px;">{room['name']}</h6>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"เลือก {room['name']}", key=room['id']):
                    st.session_state.sel_room = room['id']
                    st.rerun()

# --- TAB 2: History (No ID Display) ---
with tabs[1]:
    st.subheader("📋 ตารางการใช้งานทั้งหมด")
    all_data = load_db()
    
    if not all_data:
        st.info("ยังไม่มีข้อมูลการจองในระบบ")
    else:
        # กรองเอาเฉพาะรายการที่ยังไม่หมดวัน (วันนี้และอนาคต)
        today = date.today()
        current_data = [b for b in all_data if datetime.strptime(b['date'], '%Y-%m-%d').date() >= today]
        
        # เรียงลำดับ วันที่ และ เวลา
        sorted_data = sorted(current_data, key=lambda x: (x['date'], x['start']))
        
        for idx, b in enumerate(sorted_data):
            is_today = " (วันนี้)" if b['date'] == str(today) else " (พรุ่งนี้)"
            header = f"📅 {b['date']}{is_today} | 🕒 {b['start']:02d}:00 น. | 📍 {b['room_name']}"
            
            with st.expa
