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
  Info,
  ChevronRight,
  AlertCircle,
  Sparkles,
  Loader2,
  ListChecks
} from 'lucide-react';

// Configuration
const apiKey = ""; // API Key will be provided at runtime
const appId = typeof __app_id !== 'undefined' ? __app_id : 'cia-booking-final';

// ข้อมูลห้องและโต๊ะตามโจทย์ CIA Booking ล่าสุด
const ROOM_DATA = [
  // Theater Rooms - ความจุ 10 คน
  { id: 'tr1', name: 'Theater Room 1', type: 'theater', capacity: 10, facilities: ['Projector', 'Audio', 'AC'], description: 'ห้องประชุมขนาดใหญ่ เหมาะสำหรับการสัมมนาหรือพรีเซนต์งานโครงงานใหญ่', image: 'https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&q=80&w=400' },
  { id: 'tr2', name: 'Theater Room 2', type: 'theater', capacity: 10, facilities: ['Projector', 'Audio', 'AC'], description: 'ห้องเอนกประสงค์พร้อมเครื่องเสียงครบครัน สำหรับการซ้อมนำเสนอผลงาน', image: 'https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&q=80&w=400' },
  // Meeting Rooms - ความจุ 8 คน
  ...[1, 2, 3, 4, 5].map(i => ({
    id: `mr${i}`,
    name: `Meeting Room ${i}`,
    type: 'meeting',
    capacity: 8,
    facilities: ['Whiteboard', 'Smart TV', 'AC'],
    description: 'ห้องทำงานกลุ่มขนาดกลาง เหมาะสำหรับการระดมสมองและเขียนแบบโครงสร้าง',
    image: 'https://images.unsplash.com/photo-1431540015161-0bf868a2d407?auto=format&fit=crop&q=80&w=400'
  })),
  // External Tables - ความจุ 6 คน และมี 6 โต๊ะ
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

// "ปรับช่วงเวลาจองใหม่เป็น 09:00 - 17:00"
const HOURS = Array.from({ length: 8 }, (_, i) => i + 9); // [9, 10, 11, 12, 13, 14, 15, 16]
const CLOSING_HOUR = 17;

export default function App() {
  const [bookings, setBookings] = useState([]);
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

  const filteredRooms = ROOM_DATA.filter(room => {
    const matchesType = filterType === 'all' || room.type === filterType;
    const matchesSearch = room.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  // --- AI Integration (Gemini API) ---
  const callGemini = async (prompt, retries = 5, delay = 1000) => {
    const systemPrompt = `You are an AI Assistant for Civil Engineering students at CIA (Civil Infrastructure & Architecture). 
    Help them select the best room and plan their project tasks. 
    Available rooms: Theater Rooms (Capacity: 10), Meeting Rooms (1-5, Capacity: 8), External Tables (1-6, Capacity: 6).
    Opening Hours: 09:00 - 17:00.
    If a student describes a project (e.g., "Bridge Design", "Foundation Analysis"), suggest a room and provide a 3-step project milestone.
    Always respond in Thai language. Use a helpful and professional tone for engineers.`;

    try {
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`, {
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
      if (retries > 0) {
        await new Promise(res => setTimeout(res, delay));
        return callGemini(prompt, retries - 1, delay * 2);
      }
      throw error;
    }
  };

  const handleAiConsult = async () => {
    if (!aiInput.trim()) return;
    setIsAiLoading(true);
    setAiResponse(null);
    try {
      const result = await callGemini(`โปรเจกต์ของฉันคือ: ${aiInput}. ช่วยแนะนำห้องที่เหมาะสมและวางแผนขั้นตอนการทำงานให้หน่อยในช่วงเวลา 09:00-17:00 น.`);
      setAiResponse(result);
    } catch (error) {
      setAiResponse("ขออภัย ระบบขัดข้องชั่วคราว กรุณาลองใหม่อีกครั้งในภายหลัง");
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

  const hasExistingBooking = (studentId) => {
    return bookings.some(b => b.studentId === studentId);
  };

  const handleBooking = (e) => {
    e.preventDefault();
    const duration = parseInt(formData.duration);
    const start = parseInt(formData.startHour);

    if (isRoomConflict(selectedRoom.id, start, duration)) {
      alert('ขออภัย ช่วงเวลานี้มีการจองแล้ว');
      return;
    }

    if (hasExistingBooking(formData.studentId)) {
      alert('ขออภัย 1 รหัสนักศึกษาสามารถจองได้เพียง 1 รายการเท่านั้นในขณะนี้');
      return;
    }

    const newBooking = {
      id: Date.now(),
      roomId: selectedRoom.id,
      roomName: selectedRoom.name,
      ...formData,
      duration: duration,
      startHour: start,
      timestamp: new Date().toLocaleString('th-TH')
    };

    setBookings([...bookings, newBooking]);
    setSelectedRoom(null);
    setFormData({ ...formData, name: '', studentId: '', duration: 1, startHour: 9 });
    setView('my-bookings');
  };

  const formatTimeRange = (start, duration) => {
    const end = start + duration;
    return `${String(start).padStart(2, '0')}:00 - ${String(end).padStart(2, '0')}:00`;
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] font-sans text-slate-900">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setView('browse')}>
            <div className="bg-orange-600 p-2 rounded-lg text-white shadow-lg shadow-orange-200">
              <HardHat size={24} />
            </div>
            <div>
              <h1 className="text-xl font-black text-slate-800 leading-none tracking-tight">CIA BOOKING</h1>
              <span className="text-[10px] font-bold text-orange-600 tracking-tighter uppercase">Civil Eng • 09:00 - 17:00</span>
            </div>
          </div>
          <nav className="flex gap-2 bg-slate-100 p-1 rounded-2xl">
            <button 
              onClick={() => setView('browse')}
              className={`px-4 py-2 rounded-xl transition-all text-sm font-bold ${view === 'browse' ? 'bg-white shadow-sm text-orange-600' : 'text-slate-500 hover:text-slate-800'}`}
            >
              ค้นหาพื้นที่
            </button>
            <button 
              onClick={() => setView('my-bookings')}
              className={`px-4 py-2 rounded-xl transition-all text-sm font-bold flex items-center gap-2 ${view === 'my-bookings' ? 'bg-white shadow-sm text-orange-600' : 'text-slate-500 hover:text-slate-800'}`}
            >
              รายการของฉัน
              {bookings.length > 0 && (
                <span className="bg-orange-600 text-white text-[10px] w-5 h-5 flex items-center justify-center rounded-full font-bold">{bookings.length}</span>
              )}
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {view === 'browse' ? (
          <>
            {/* AI Assistant Section */}
            <div className={`mb-10 transition-all duration-500 ${showAiPanel ? 'max-h-[800px]' : 'max-h-20'} overflow-hidden bg-gradient-to-br from-slate-900 to-indigo-950 rounded-[2.5rem] shadow-2xl relative border-4 border-white`}>
              <div className="p-6 md:p-10">
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-3">
                    <div className="bg-white/10 p-3 rounded-2xl backdrop-blur-md">
                      <Sparkles className="text-orange-400" size={28} />
                    </div>
                    <div>
                      <h2 className="text-2xl font-black text-white">ผู้ช่วย AI วิศวกรโยธา ✨</h2>
                      <p className="text-slate-400 text-sm font-medium">ให้ AI ช่วยวางแผนและเลือกห้องที่เหมาะที่สุด</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setShowAiPanel(!showAiPanel)}
                    className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white font-bold rounded-xl transition-all text-sm backdrop-blur-md"
                  >
                    {showAiPanel ? 'ซ่อน AI' : 'ปรึกษา AI'}
                  </button>
                </div>

                <div className="flex flex-col md:flex-row gap-6">
                  <div className="flex-1 space-y-4">
                    <div className="relative">
                      <textarea 
                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-slate-500 focus:ring-2 focus:ring-orange-500 outline-none min-h-[120px] transition-all font-medium"
                        placeholder="พิมพ์หัวข้อโปรเจกต์ เช่น การออกแบบโครงสร้างสะพาน..."
                        value={aiInput}
                        onChange={(e) => setAiInput(e.target.value)}
                      ></textarea>
                    </div>
                    <button 
                      onClick={handleAiConsult}
                      disabled={isAiLoading || !aiInput.trim()}
                      className="w-full py-4 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-700 text-white font-black rounded-2xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-orange-950"
                    >
                      {isAiLoading ? <Loader2 className="animate-spin" /> : <Sparkles size={20} />}
                      {isAiLoading ? 'กำลังประมวลผล...' : 'ขอคำแนะนำจาก AI ✨'}
                    </button>
                  </div>

                  <div className="flex-1 bg-white/5 border border-white/10 rounded-3xl p-6 min-h-[200px] overflow-y-auto max-h-[300px] scrollbar-hide">
                    {!aiResponse && !isAiLoading && (
                      <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center space-y-2">
                        <ListChecks size={40} className="opacity-20" />
                        <p className="font-medium italic">แผนงานและห้องที่แนะนำจะปรากฏที่นี่</p>
                      </div>
                    )}
                    {isAiLoading && (
                      <div className="h-full flex items-center justify-center space-x-2 text-orange-400 font-bold animate-pulse">
                        <Loader2 className="animate-spin" />
                        <span>กำลังวิเคราะห์แผนงานโยธา...</span>
                      </div>
                    )}
                    {aiResponse && (
                      <div className="text-slate-200 leading-relaxed whitespace-pre-wrap font-medium animate-in fade-in duration-500">
                        {aiResponse}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col md:flex-row gap-4 mb-8">
              <div className="relative flex-1 group">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-orange-500 transition-colors" size={20} />
                <input 
                  type="text" 
                  placeholder="ค้นหาห้องหรือโต๊ะ..." 
                  className="w-full pl-12 pr-4 py-4 rounded-3xl border border-slate-200 focus:ring-4 focus:ring-orange-500/10 focus:border-orange-500 outline-none bg-white transition-all shadow-sm font-semibold"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
                {[
                  { id: 'all', label: 'ทั้งหมด', icon: <BookOpen size={16} /> },
                  { id: 'theater', label: 'Theater', icon: <Monitor size={16} /> },
                  { id: 'meeting', label: 'Meeting', icon: <Users2 size={16} /> },
                  { id: 'table', label: 'Table', icon: <Users size={16} /> }
                ].map(type => (
                  <button
                    key={type.id}
                    onClick={() => setFilterType(type.id)}
                    className={`flex items-center gap-2 px-6 py-2 rounded-2xl whitespace-nowrap transition-all text-sm font-black border-2 ${filterType === type.id ? 'bg-slate-900 border-slate-900 text-white shadow-lg' : 'bg-white border-slate-200 text-slate-500 hover:border-orange-300'}`}
                  >
                    {type.icon}
                    {type.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {filteredRooms.map(room => (
                <div key={room.id} className="bg-white rounded-[2.5rem] overflow-hidden shadow-sm hover:shadow-2xl transition-all border border-slate-100 flex flex-col group relative">
                  <div className="relative h-44 overflow-hidden">
                    <img src={room.image} alt={room.name} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                    <div className="absolute top-4 left-4">
                      <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg ${
                        room.type === 'theater' ? 'bg-orange-600 text-white' : 
                        room.type === 'meeting' ? 'bg-blue-600 text-white' : 'bg-emerald-500 text-white'
                      }`}>
                        {room.type}
                      </span>
                    </div>
                  </div>
                  <div className="p-6 flex flex-col flex-1">
                    <h3 className="text-xl font-black text-slate-800 mb-1 leading-tight group-hover:text-orange-600 transition-colors">{room.name}</h3>
                    <div className="flex items-center gap-2 text-slate-400 text-[10px] font-black mb-4 uppercase tracking-wider">
                      <Users size={14} className="text-orange-500" />
                      <span>จุได้ {room.capacity} ที่นั่ง</span>
                    </div>
                    <p className="text-slate-500 text-xs mb-6 line-clamp-2 font-medium leading-relaxed">
                      {room.description}
                    </p>
                    <button 
                      onClick={() => setSelectedRoom(room)}
                      className="mt-auto w-full py-4 bg-slate-900 text-white font-black rounded-2xl hover:bg-orange-600 transition-all flex items-center justify-center gap-2 group-hover:shadow-xl group-hover:shadow-orange-100"
                    >
                      จองตอนนี้
                      <ChevronRight size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="max-w-2xl mx-auto">
            <h2 className="text-4xl font-black text-slate-900 mb-10 flex items-center gap-4 tracking-tighter">
              <Calendar className="text-orange-600" size={40} />
              การจองของฉัน
            </h2>
            
            {bookings.length === 0 ? (
              <div className="bg-white p-20 rounded-[4rem] text-center border-2 border-dashed border-slate-200 shadow-sm">
                <Calendar className="mx-auto text-slate-200 mb-6" size={60} />
                <h3 className="text-2xl font-black text-slate-800 mb-2">ยังไม่มีการจอง</h3>
                <p className="text-slate-400 mb-10 font-medium text-lg">เริ่มต้นจองพื้นที่สำหรับโปรเจกต์โยธาของคุณได้เลย</p>
                <button 
                  onClick={() => setView('browse')}
                  className="px-10 py-5 bg-orange-600 text-white font-black rounded-[2rem] hover:bg-orange-700 transition-all shadow-2xl shadow-orange-100 text-lg"
                >
                  ค้นหาห้องจอง
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                {bookings.map(booking => (
                  <div key={booking.id} className="bg-white p-8 rounded-[3rem] border-4 border-orange-50 flex items-center gap-8 shadow-xl hover:shadow-2xl transition-all animate-in slide-in-from-bottom duration-500">
                    <div className="w-20 h-20 bg-orange-600 rounded-[2.5rem] flex items-center justify-center text-white shadow-lg shrink-0">
                      <Clock size={40} />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-black text-slate-800 text-2xl mb-1 leading-none">{booking.roomName}</h4>
                      <div className="flex items-center gap-3">
                        <span className="text-orange-600 font-black text-lg">
                          {formatTimeRange(booking.startHour, booking.duration)} น.
                        </span>
                        <span className="text-slate-400 font-bold text-sm">| {booking.duration} ชม.</span>
                      </div>
                      <p className="mt-3 text-[10px] text-slate-400 font-black uppercase tracking-widest">{booking.name} • {booking.studentId}</p>
                    </div>
                    <button 
                      onClick={() => confirm('ต้องการยกเลิกการจองนี้?') && setBookings(bookings.filter(b => b.id !== booking.id))}
                      className="p-5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-3xl transition-all"
                    >
                      <Trash2 size={28} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* Modal */}
      {selectedRoom && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/80 backdrop-blur-md">
          <div className="bg-white w-full max-w-lg rounded-[3.5rem] overflow-hidden shadow-2xl animate-in zoom-in duration-300 border-8 border-white/20">
            <div className="bg-slate-900 p-10 text-white relative">
              <button 
                onClick={() => setSelectedRoom(null)}
                className="absolute top-8 right-8 p-2 hover:bg-white/10 rounded-full transition-all"
              >
                <XCircle size={32} className="text-slate-400" />
              </button>
              <h2 className="text-3xl font-black tracking-tighter">{selectedRoom.name}</h2>
              <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-2 tracking-[0.2em]">Open 09:00 - 17:00</p>
            </div>
            
            <form onSubmit={handleBooking} className="p-10 space-y-8">
              <div className="grid grid-cols-2 gap-6">
                <div className="col-span-2 sm:col-span-1">
                  <label className="block text-[10px] font-black text-slate-400 uppercase mb-3 ml-2 tracking-widest">ชื่อ-นามสกุล</label>
                  <input 
                    required
                    className="w-full px-6 py-5 rounded-2xl border-2 border-slate-100 focus:ring-4 focus:ring-orange-500/10 focus:border-orange-500 outline-none transition-all bg-slate-50 font-bold"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                  />
                </div>
                <div className="col-span-2 sm:col-span-1">
                  <label className="block text-[10px] font-black text-slate-400 uppercase mb-3 ml-2 tracking-widest">รหัสนักศึกษา</label>
                  <input 
                    required
                    className="w-full px-6 py-5 rounded-2xl border-2 border-slate-100 focus:ring-4 focus:ring-orange-500/10 focus:border-orange-500 outline-none transition-all bg-slate-50 font-bold"
                    value={formData.studentId}
                    onChange={(e) => setFormData({...formData, studentId: e.target.value})}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-[10px] font-black text-slate-400 uppercase mb-3 ml-2 tracking-widest">เริ่มเวลา</label>
                  <select 
                    className="w-full px-6 py-5 rounded-2xl border-2 border-slate-100 focus:ring-4 focus:ring-orange-500/10 focus:border-orange-500 outline-none appearance-none bg-slate-50 font-black cursor-pointer"
                    value={formData.startHour}
                    onChange={(e) => setFormData({...formData, startHour: parseInt(e.target.value), duration: 1})}
                  >
                    {HOURS.map(h => (
                      <option key={h} value={h}>{String(h).padStart(2, '0')}:00 น.</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-black text-slate-400 uppercase mb-3 ml-2 tracking-widest">ระยะเวลา (ชม.)</label>
                  <select 
                    className="w-full px-6 py-5 rounded-2xl border-2 border-slate-100 focus:ring-4 focus:ring-orange-500/10 focus:border-orange-500 outline-none appearance-none bg-slate-50 font-black cursor-pointer"
                    value={formData.duration}
                    onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value)})}
                  >
                    {[1, 2, 3, 4]
                      .filter(d => formData.startHour + d <= CLOSING_HOUR)
                      .map(d => (
                        <option key={d} value={d}>{d} ชั่วโมง</option>
                      ))}
                  </select>
                </div>
              </div>

              <div className="bg-slate-900 p-8 rounded-[2.5rem] border-4 border-slate-100 flex items-center gap-6 shadow-xl">
                <AlertCircle className="text-orange-500 shrink-0" size={32} />
                <div>
                  <p className="text-white font-black text-2xl tracking-tighter">
                    {formatTimeRange(formData.startHour, formData.duration)} น.
                  </p>
                  <p className="text-slate-400 text-[10px] font-bold mt-1 uppercase tracking-widest">
                    ตรวจสอบช่วงเวลาก่อนยืนยันการจอง
                  </p>
                </div>
              </div>

              <button 
                type="submit"
                className="w-full py-6 bg-orange-600 text-white font-black rounded-[2rem] hover:bg-orange-500 transition-all shadow-2xl shadow-orange-200 text-xl flex items-center justify-center gap-3"
              >
                ยืนยันการจองพื้นที่
                <ChevronRight size={24} />
              </button>
            </form>
          </div>
        </div>
      )}
      
      <footer className="py-16 text-center text-slate-300 text-[10px] font-black uppercase tracking-[0.5em]">
        CIA Booking System • Year 2 Civil Eng Project • 09:00 - 17:00
      </footer>
    </div>
  );
}
