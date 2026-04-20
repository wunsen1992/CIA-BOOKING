import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  Users, 
  XCircle, 
  Trash2, 
  Search,
  BookOpen,
  Users2,
  Monitor,
  HardHat,
  ChevronRight,
  AlertCircle,
  Sparkles,
  Loader2,
  ListChecks,
  CheckCircle2
} from 'lucide-react';

// Configuration
const apiKey = ""; // <--- ใส่ API Key ของคุณที่นี่
const appId = typeof __app_id !== 'undefined' ? __app_id : 'cia-booking-final';

// ข้อมูลห้องและโต๊ะตามโจทย์ CIA Booking
const ROOM_DATA = [
  { id: 'tr1', name: 'Theater Room 1', type: 'theater', capacity: 10, facilities: ['Projector', 'Audio', 'AC'], description: 'ห้องประชุมขนาดใหญ่ เหมาะสำหรับการสัมมนาหรือพรีเซนต์งานโครงงานใหญ่', image: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&q=80&w=400' },
  { id: 'tr2', name: 'Theater Room 2', type: 'theater', capacity: 10, facilities: ['Projector', 'Audio', 'AC'], description: 'ห้องเอนกประสงค์พร้อมเครื่องเสียงครบครัน สำหรับการซ้อมนำเสนอผลงาน', image: 'https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&q=80&w=400' },
  ...[1, 2, 3, 4, 5].map(i => ({
    id: `mr${i}`,
    name: `Meeting Room ${i}`,
    type: 'meeting',
    capacity: 8,
    facilities: ['Whiteboard', 'Smart TV', 'AC'],
    description: 'ห้องทำงานกลุ่มขนาดกลาง เหมาะสำหรับการระดมสมองและเขียนแบบโครงสร้าง',
    image: 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&q=80&w=400'
  })),
  ...[1, 2, 3, 4, 5, 6].map(i => ({
    id: `et${i}`,
    name: `Table ${i}`,
    type: 'table',
    capacity: 6,
    facilities: ['Outdoor', 'WiFi'],
    description: 'พื้นที่เปิดโล่งสำหรับนั่งทำงานหรือติวหนังสือกลุ่ม จุได้ 6 ท่าน',
    image: 'https://images.unsplash.com/photo-1529148482759-b35b25c5f217?auto=format&fit=crop&q=80&w=400'
  }))
];

const HOURS = Array.from({ length: 8 }, (_, i) => i + 9); // [9, 10, ..., 16]
const CLOSING_HOUR = 17;

export default function App() {
  // Load data from LocalStorage on mount
  const [bookings, setBookings] = useState(() => {
    const saved = localStorage.getItem('cia_bookings_v1');
    return saved ? JSON.parse(saved) : [];
  });

  const [selectedRoom, setSelectedRoom] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [view, setView] = useState('browse');
  
  // AI States
  const [aiInput, setAiInput] = useState('');
  const [aiResponse, setAiResponse] = useState(null);
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [showAiPanel, setShowAiPanel] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    studentId: '',
    startHour: 9,
    duration: 1
  });

  // Save to LocalStorage whenever bookings change
  useEffect(() => {
    localStorage.setItem('cia_bookings_v1', JSON.stringify(bookings));
  }, [bookings]);

  const filteredRooms = ROOM_DATA.filter(room => {
    const matchesType = filterType === 'all' || room.type === filterType;
    const matchesSearch = room.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  // --- AI Integration (Fixed Model Name) ---
  const callGemini = async (prompt, retries = 3) => {
    const systemPrompt = `You are an AI Assistant for Civil Engineering students at CIA. 
    Opening Hours: 09:00 - 17:00. 
    If a student describes a project, suggest a room (Theater/Meeting/Table) and provide a 3-step technical milestone.
    Always respond in Thai language. Be professional.`;

    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
          systemInstruction: { parts: [{ text: systemPrompt }] }
        })
      });

      if (!response.ok) throw new Error('API Error');
      const data = await response.json();
      return data.candidates?.[0]?.content?.parts?.[0]?.text;
    } catch (error) {
      if (retries > 0) return callGemini(prompt, retries - 1);
      throw error;
    }
  };

  const handleAiConsult = async () => {
    if (!aiInput.trim()) return;
    setIsAiLoading(true);
    setAiResponse(null);
    try {
      const result = await callGemini(`โปรเจกต์ของฉันคือ: ${aiInput}. ช่วยแนะนำห้องที่เหมาะและขั้นตอนทำงานโยธา 3 ขั้นตอน`);
      setAiResponse(result);
    } catch (error) {
      setAiResponse("ขออภัย ระบบ AI ขัดข้อง กรุณาตรวจสอบ API Key หรือลองใหม่อีกครั้ง");
    } finally {
      setIsAiLoading(false);
    }
  };

  // --- Booking Logic ---
  const isRoomConflict = (roomId, start, duration) => {
    const requestedSlots = Array.from({ length: duration }, (_, i) => start + i);
    return bookings.some(b => {
      if (b.roomId !== roomId) return false;
      const bookedSlots = Array.from({ length: b.duration }, (_, i) => b.startHour + i);
      return requestedSlots.some(slot => bookedSlots.includes(slot));
    });
  };

  const handleBooking = (e) => {
    e.preventDefault();
    if (isRoomConflict(selectedRoom.id, formData.startHour, formData.duration)) {
      alert('❌ ช่วงเวลานี้มีการจองแล้ว กรุณาเลือกเวลาอื่น');
      return;
    }

    if (bookings.some(b => b.studentId === formData.studentId)) {
      alert('❌ รหัสนักศึกษานี้มีการจองค้างอยู่ในระบบแล้ว (จำกัด 1 สิทธิ์ต่อคน)');
      return;
    }

    const newBooking = {
      id: Date.now(),
      roomId: selectedRoom.id,
      roomName: selectedRoom.name,
      ...formData,
      timestamp: new Date().toLocaleString('th-TH')
    };

    setBookings([...bookings, newBooking]);
    setSelectedRoom(null);
    setFormData({ name: '', studentId: '', duration: 1, startHour: 9 });
    setView('my-bookings');
  };

  const formatTimeRange = (start, duration) => {
    return `${String(start).padStart(2, '0')}:00 - ${String(start + duration).padStart(2, '0')}:00`;
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] font-sans text-slate-900 pb-20">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('browse')}>
            <div className="bg-orange-600 p-2 rounded-lg text-white shadow-lg shadow-orange-200">
              <HardHat size={20} />
            </div>
            <h1 className="text-xl font-black text-slate-800 tracking-tight">CIA BOOKING</h1>
          </div>
          <nav className="flex gap-1 bg-slate-100 p-1 rounded-xl">
            <button onClick={() => setView('browse')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${view === 'browse' ? 'bg-white shadow-sm text-orange-600' : 'text-slate-500'}`}>ค้นหาพื้นที่</button>
            <button onClick={() => setView('my-bookings')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${view === 'my-bookings' ? 'bg-white shadow-sm text-orange-600' : 'text-slate-500'}`}>
              รายการของฉัน {bookings.length > 0 && <span className="bg-orange-600 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full">{bookings.length}</span>}
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {view === 'browse' ? (
          <>
            {/* AI Panel */}
            <div className={`mb-8 overflow-hidden bg-slate-900 rounded-[2rem] shadow-2xl transition-all duration-500 ${showAiPanel ? 'max-h-[1000px]' : 'max-h-24'}`}>
              <div className="p-6 md:p-8">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <Sparkles className="text-orange-400" />
                    <h2 className="text-xl font-bold text-white">AI Civil Assistant</h2>
                  </div>
                  <button onClick={() => setShowAiPanel(!showAiPanel)} className="text-sm font-bold text-slate-400 hover:text-white uppercase tracking-widest">
                    {showAiPanel ? 'Close' : 'Consult AI'}
                  </button>
                </div>
                {showAiPanel && (
                  <div className="grid md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-top-4">
                    <div className="space-y-4">
                      <textarea 
                        className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white placeholder-slate-500 focus:ring-2 focus:ring-orange-500 outline-none h-32"
                        placeholder="บอกหัวข้อโปรเจกต์โยธาของคุณ..."
                        value={aiInput}
                        onChange={(e) => setAiInput(e.target.value)}
                      />
                      <button onClick={handleAiConsult} disabled={isAiLoading || !aiInput.trim()} className="w-full py-3 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-700 text-white font-bold rounded-xl transition-all flex items-center justify-center gap-2">
                        {isAiLoading ? <Loader2 className="animate-spin" /> : <Sparkles size={18} />}
                        ถาม AI
                      </button>
                    </div>
                    <div className="bg-white/5 rounded-xl p-6 text-slate-300 text-sm leading-relaxed overflow-y-auto max-h-48 border border-white/5">
                      {isAiLoading ? "กำลังประมวลผล..." : aiResponse || "แผนการทำงานจะปรากฏที่นี่..."}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Filters & Search */}
            <div className="flex flex-col md:flex-row gap-4 mb-8">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                <input 
                  type="text" placeholder="ค้นหาชื่อห้อง..." 
                  className="w-full pl-12 pr-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-orange-500 outline-none"
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                {['all', 'theater', 'meeting', 'table'].map(type => (
                  <button key={type} onClick={() => setFilterType(type)} className={`px-4 py-2 rounded-xl text-xs font-black uppercase transition-all ${filterType === type ? 'bg-slate-900 text-white' : 'bg-white text-slate-500 border border-slate-200'}`}>
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {filteredRooms.map(room => (
                <div key={room.id} className="bg-white rounded-3xl overflow-hidden shadow-sm border border-slate-100 hover:shadow-xl transition-all group">
                  <div className="h-40 overflow-hidden relative">
                    <img src={room.image} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                    <div className="absolute top-3 left-3 bg-white/90 backdrop-blur px-3 py-1 rounded-full text-[10px] font-black uppercase">{room.type}</div>
                  </div>
                  <div className="p-5">
                    <h3 className="font-bold text-slate-800 mb-1">{room.name}</h3>
                    <div className="flex items-center gap-2 text-slate-400 text-xs mb-4">
                      <Users size={12} /> {room.capacity} Seats
                    </div>
                    <button onClick={() => setSelectedRoom(room)} className="w-full py-3 bg-slate-100 hover:bg-orange-600 hover:text-white text-slate-600 font-bold rounded-xl transition-all text-sm">
                      จองพื้นที่
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          /* My Bookings View */
          <div className="max-w-2xl mx-auto py-10">
            <h2 className="text-3xl font-black mb-8 flex items-center gap-3">
              <CheckCircle2 className="text-orange-600" size={32} /> การจองของคุณ
            </h2>
            {bookings.length === 0 ? (
              <div className="text-center py-20 bg-white rounded-[3rem] border-2 border-dashed border-slate-200">
                <Calendar className="mx-auto text-slate-200 mb-4" size={48} />
                <p className="text-slate-400 font-bold">ยังไม่มีข้อมูลการจองในขณะนี้</p>
              </div>
            ) : (
              <div className="space-y-4">
                {bookings.map(b => (
                  <div key={b.id} className="bg-white p-6 rounded-3xl border border-slate-200 flex items-center gap-6 hover:border-orange-500 transition-all">
                    <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center text-orange-600 shrink-0">
                      <Clock size={32} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-bold text-lg">{b.roomName}</h4>
                      <p className="text-orange-600 font-bold">{formatTimeRange(b.startHour, b.duration)} น.</p>
                      <p className="text-xs text-slate-400 mt-1 uppercase font-bold">{b.name} • {b.studentId}</p>
                    </div>
                    <button 
                      onClick={() => confirm('ต้องการยกเลิกการจอง?') && setBookings(bookings.filter(item => item.id !== b.id))}
                      className="p-3 text-slate-300 hover:text-red-500 transition-colors"
                    >
                      <Trash2 size={24} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Booking Modal */}
      {selectedRoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white w-full max-w-md rounded-[2.5rem] overflow-hidden shadow-2xl animate-in zoom-in duration-200">
            <div className="bg-slate-900 p-8 text-white flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-black">{selectedRoom.name}</h2>
                <p className="text-orange-400 text-xs font-bold uppercase tracking-widest mt-1">Confirm Booking</p>
              </div>
              <button onClick={() => setSelectedRoom(null)} className="text-slate-400 hover:text-white"><XCircle size={28} /></button>
            </div>
            <form onSubmit={handleBooking} className="p-8 space-y-5">
              <div className="space-y-4">
                <input required placeholder="ชื่อ-นามสกุล" className="w-full px-5 py-3 rounded-xl border border-slate-200 outline-none focus:border-orange-500 font-bold" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                <input required placeholder="รหัสนักศึกษา" className="w-full px-5 py-3 rounded-xl border border-slate-200 outline-none focus:border-orange-500 font-bold" value={formData.studentId} onChange={e => setFormData({...formData, studentId: e.target.value})} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase ml-2">เริ่มเวลา</label>
                  <select className="w-full px-4 py-3 rounded-xl border border-slate-200 font-bold mt-1" value={formData.startHour} onChange={e => setFormData({...formData, startHour: parseInt(e.target.value), duration: 1})}>
                    {HOURS.map(h => <option key={h} value={h}>{String(h).padStart(2, '0')}:00 น.</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase ml-2">ระยะเวลา</label>
                  <select className="w-full px-4 py-3 rounded-xl border border-slate-200 font-bold mt-1" value={formData.duration} onChange={e => setFormData({...formData, duration: parseInt(e.target.value)})}>
                    {[1, 2, 3, 4].filter(d => formData.startHour + d <= CLOSING_HOUR).map(d => <option key={d} value={d}>{d} ชม.</option>)}
                  </select>
                </div>
              </div>
              <div className="bg-orange-50 p-4 rounded-2xl flex items-center gap-3 border border-orange-100">
                <AlertCircle className="text-orange-600" size={20} />
                <span className="text-sm font-bold text-orange-900">{formatTimeRange(formData.startHour, formData.duration)} น.</span>
              </div>
              <button type="submit" className="w-full py-4 bg-orange-600 text-white font-black rounded-2xl hover:bg-orange-700 transition-all flex items-center justify-center gap-2">
                ยืนยันการจอง <ChevronRight size={18} />
              </button>
            </form>
          </div>
        </div>
      )}

      <footer className="text-center py-10 text-slate-300 text-[10px] font-black uppercase tracking-[0.3em]">
        CIA Booking System • Year 2 Civil Project
      </footer>
    </div>
  );
}
