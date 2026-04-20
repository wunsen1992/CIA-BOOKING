import streamlit as st
import requests
import json
from datetime import datetime

# --- Configuration ---
st.set_page_config(page_title="CIA Booking System", page_icon="🏗️", layout="wide")

# ใส่ API Key ของคุณตรงนี้
API_KEY = "" 

# --- Custom Styling (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Kanit', sans-serif; }
    
    .stApp { background-color: #f8fafc; }
    
    /* Card Styling */
    .room-card {
        background-color: white;
        border-radius: 20px;
        padding: 0px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        margin-bottom: 20px;
    }
    .room-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    
    /* AI Panel */
    .ai-panel {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        color: white;
        padding: 40px;
        border-radius: 30px;
        margin-bottom: 30px;
        border: 4px solid white;
    }
    
    /* Tag Colors */
    .tag-theater { background-color: #ea580c; color: white; padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    .tag-meeting { background-color: #2563eb; color: white; padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    .tag-table { background-color: #10b981; color: white; padding: 2px 10px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- Data Definition ---
ROOM_DATA = [
    {"id": "tr1", "name": "Theater Room 1", "type": "theater", "cap": 10, "desc": "ห้องประชุมขนาดใหญ่ เหมาะสำหรับการสัมมนา", "img": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=400"},
    {"id": "tr2", "name": "Theater Room 2", "type": "theater", "cap": 10, "desc": "ห้องเอนกประสงค์พร้อมเครื่องเสียงครบครัน", "img": "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=400"},
]
for i in range(1, 6):
    ROOM_DATA.append({"id": f"mr{i}", "name": f"Meeting Room {i}", "type": "meeting", "cap": 8, "desc": "ห้องทำงานกลุ่มขนาดกลาง สำหรับระดมสมอง", "img": "https://images.unsplash.com/photo-1431540015161-0bf868a2d407?w=400"})
for i in range(1, 7):
    ROOM_DATA.append({"id": f"et{i}", "name": f"Table {i}", "type": "table", "cap": 6, "desc": "พื้นที่เปิดโล่งสำหรับนั่งทำงานกลุ่ม", "img": "https://images.unsplash.com/photo-1529148482759-b35b25c5f217?w=400"})

# --- Session State Management ---
if 'bookings' not in st.session_state:
    st.session_state.bookings = []
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = None

# --- Logic Functions ---
def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    system_prompt = "You are an AI Assistant for Civil Engineering students. Opening Hours: 09:00 - 17:00. Recommend a room and 3 technical steps. Respond in Thai language."
    payload = {"contents": [{"parts": [{"text": f"{system_prompt}\nคำถาม: {prompt}"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except:
        return "ขออภัย ระบบขัดข้อง กรุณาเช็ค API Key"

def is_conflict(room_id, start, duration):
    req_slots = set(range(start, start + duration))
    for b in st.session_state.bookings:
        if b['room_id'] == room_id:
            booked_slots = set(range(b['start'], b['start'] + b['duration']))
            if req_slots.intersection(booked_slots):
                return True
    return False

# --- UI Header ---
col_logo, col_nav = st.columns([2, 2])
with col_logo:
    st.markdown("### 🏗️ CIA BOOKING <span style='font-size:12px; color:orange;'>Civil Eng • 09:00-17:00</span>", unsafe_allow_html=True)

menu = st.radio("Navigation", ["ค้นหาพื้นที่", "การจองของฉัน"], horizontal=True, label_visibility="collapsed")

st.divider()

# --- Browse View ---
if menu == "ค้นหาพื้นที่":
    # AI Panel
    st.markdown("""
        <div class="ai-panel">
            <h2 style='margin-top:0'>✨ ผู้ช่วย AI วิศวกรโยธา</h2>
            <p style='color:#cbd5e1'>พิมพ์ชื่อโปรเจกต์เพื่อให้ AI ช่วยวางแผนงานและเลือกห้องที่เหมาะสม</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        ai_col1, ai_col2 = st.columns([1, 1])
        with ai_col1:
            user_input = st.text_area("บอกหัวข้อโปรเจกต์ของคุณ...", placeholder="เช่น การออกแบบคานสะพาน...")
            if st.button("ขอคำแนะนำจาก AI ✨", use_container_width=True):
                with st.spinner("AI กำลังวิเคราะห์แผนงาน..."):
                    st.session_state.ai_response = call_gemini(user_input)
        
        with ai_col2:
            st.markdown("**📋 แผนงานที่แนะนำโดย AI:**")
            if st.session_state.ai_response:
                st.info(st.session_state.ai_response)
            else:
                st.markdown("<p style='color:gray; font-style:italic;'>คำแนะนำจะปรากฏที่นี่...</p>", unsafe_allow_html=True)

    st.divider()

    # Search and Filter
    f_col1, f_col2 = st.columns([2, 1])
    search_q = f_col1.text_input("🔍 ค้นหาห้องหรือโต๊ะ...", placeholder="พิมพ์ชื่อห้อง...")
    filter_t = f_col2.selectbox("ประเภทพื้นที่", ["ทั้งหมด", "theater", "meeting", "table"])

    # Rooms Grid
    filtered = [r for r in ROOM_DATA if (filter_t == "ทั้งหมด" or r['type'] == filter_t) and (search_q.lower() in r['name'].lower())]
    
    cols = st.columns(4)
    for idx, room in enumerate(filtered):
        with cols[idx % 4]:
            tag_class = f"tag-{room['type']}"
            st.markdown(f"""
                <div class="room-card">
                    <img src="{room['img']}" style="width:100%; border-radius:20px 20px 0 0; height:150px; object-fit:cover;">
                    <div style="padding:15px">
                        <span class="{tag_class}">{room['type'].upper()}</span>
                        <h4 style="margin:10px 0 5px 0">{room['name']}</h4>
                        <p style="font-size:11px; color:gray; height:35px; overflow:hidden;">{room['desc']}</p>
                        <p style="font-size:12px; font-weight:bold;">👥 {room['cap']} ที่นั่ง</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"จอง {room['name']}", key=room['id'], use_container_width=True):
                st.session_state.selected_room = room

    # Booking Dialog
    if 'selected_room' in st.session_state:
        room = st.session_state.selected_room
        st.markdown("---")
        with st.form("booking_form"):
            st.subheader(f"📝 แบบฟอร์มจอง: {room['name']}")
            c1, c2 = st.columns(2)
            name = c1.text_input("ชื่อ-นามสกุล")
            sid = c2.text_input("รหัสนักศึกษา")
            
            c3, c4 = st.columns(2)
            t_start = c3.selectbox("เริ่มเวลา", range(9, 17), format_func=lambda x: f"{x:02d}:00 น.")
            dur = c4.select_slider("ระยะเวลา (ชั่วโมง)", options=[1, 2, 3, 4])
            
            if st.form_submit_button("ยืนยันการจองพื้นที่", use_container_width=True):
                if not name or not sid:
                    st.error("❌ กรุณากรอกชื่อและรหัสนักศึกษา")
                elif t_start + dur > 17:
                    st.error("❌ เวลาที่จองเกินเวลาทำการ (ปิด 17:00)")
                elif is_conflict(room['id'], t_start, dur):
                    st.error("❌ ช่วงเวลานี้มีการจองแล้ว")
                elif any(b['sid'] == sid for b in st.session_state.bookings):
                    st.error("❌ คุณมีรายการจองค้างอยู่แล้ว (1 คน/1 สิทธิ์)")
                else:
                    st.session_state.bookings.append({
                        "id": datetime.now().timestamp(),
                        "room_name": room['name'],
                        "room_id": room['id'],
                        "name": name,
                        "sid": sid,
                        "start": t_start,
                        "duration": dur
                    })
                    st.success("✅ จองสำเร็จ! ไปที่หน้า 'การจองของฉัน' เพื่อดูรายละเอียด")
                    del st.session_state.selected_room
                    st.rerun()
            if st.form_submit_button("ยกเลิก"):
                del st.session_state.selected_room
                st.rerun()

# --- My Bookings View ---
else:
    st.title("📅 รายการจองของฉัน")
    if not st.session_state.bookings:
        st.info("ยังไม่มีข้อมูลการจอง เริ่มจองได้ที่เมนู 'ค้นหาพื้นที่'")
    else:
        for idx, b in enumerate(st.session_state.bookings):
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 1])
                col1.markdown(f"<div style='background:#ea580c; color:white; padding:15px; border-radius:15px; text-align:center;'><b>{b['start']:02d}:00</b></div>", unsafe_allow_html=True)
                col2.markdown(f"**{b['room_name']}**<br><small>{b['name']} ({b['sid']}) | ระยะเวลา {b['duration']} ชม.</small>", unsafe_allow_html=True)
                if col3.button("🗑️", key=f"del_{idx}"):
                    st.session_state.bookings.pop(idx)
                    st.rerun()
                st.divider()

# --- Footer ---
st.markdown("<br><p style='text-align:center; color:gray; font-size:10px;'>CIA BOOKING SYSTEM • YEAR 2 CIVIL PROJECT</p>", unsafe_allow_html=True)
