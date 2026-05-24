import { MapPin, Droplets, Sun, Wind, ChevronRight, Navigation } from 'lucide-react';

interface MainScreenProps {
  selectedMode: 'general' | 'elderly' | 'dog';
  onModeChange: (mode: 'general' | 'elderly' | 'dog') => void;
  onNavigateToRoutes: () => void;
}

function DogCharacter() {
  return (
    <svg viewBox="0 0 120 110" width="110" height="100" xmlns="http://www.w3.org/2000/svg">
      {/* Body */}
      <ellipse cx="60" cy="75" rx="28" ry="22" fill="#F4C885" />
      {/* Head */}
      <circle cx="60" cy="45" r="22" fill="#F4C885" />
      {/* Left ear */}
      <ellipse cx="43" cy="30" rx="9" ry="14" fill="#E8A85A" transform="rotate(-20 43 30)" />
      {/* Right ear */}
      <ellipse cx="77" cy="30" rx="9" ry="14" fill="#E8A85A" transform="rotate(20 77 30)" />
      {/* Inner ears */}
      <ellipse cx="43" cy="32" rx="5" ry="9" fill="#F4B8A0" transform="rotate(-20 43 32)" />
      <ellipse cx="77" cy="32" rx="5" ry="9" fill="#F4B8A0" transform="rotate(20 77 32)" />
      {/* Eyes */}
      <circle cx="53" cy="43" r="4" fill="#2C1810" />
      <circle cx="67" cy="43" r="4" fill="#2C1810" />
      <circle cx="54.5" cy="41.5" r="1.5" fill="white" />
      <circle cx="68.5" cy="41.5" r="1.5" fill="white" />
      {/* Nose */}
      <ellipse cx="60" cy="51" rx="5" ry="3.5" fill="#2C1810" />
      {/* Mouth */}
      <path d="M 55 54 Q 60 58 65 54" stroke="#2C1810" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Tongue */}
      <ellipse cx="60" cy="57" rx="4" ry="3" fill="#F47F7F" />
      {/* Tail */}
      <path d="M 87 65 Q 100 50 95 40" stroke="#F4C885" strokeWidth="7" fill="none" strokeLinecap="round" />
      {/* Front legs */}
      <rect x="40" y="90" width="10" height="16" rx="5" fill="#F4C885" />
      <rect x="70" y="90" width="10" height="16" rx="5" fill="#F4C885" />
      {/* Back legs */}
      <rect x="33" y="88" width="10" height="14" rx="5" fill="#E8A85A" />
      <rect x="77" y="88" width="10" height="14" rx="5" fill="#E8A85A" />
      {/* Collar */}
      <rect x="47" y="62" width="26" height="5" rx="2.5" fill="#4A90D9" />
      <circle cx="60" cy="64.5" r="2.5" fill="#FFD700" />
      {/* Cheeks */}
      <circle cx="46" cy="50" r="5" fill="#FFAAA0" opacity="0.5" />
      <circle cx="74" cy="50" r="5" fill="#FFAAA0" opacity="0.5" />
    </svg>
  );
}

function PersonCharacter() {
  return (
    <svg viewBox="0 0 80 120" width="60" height="90" xmlns="http://www.w3.org/2000/svg">
      {/* Head */}
      <circle cx="40" cy="20" r="14" fill="#FFD4A8" />
      {/* Hair */}
      <path d="M 26 16 Q 28 6 40 6 Q 52 6 54 16 Q 50 10 40 10 Q 30 10 26 16Z" fill="#5D4037" />
      {/* Eyes */}
      <circle cx="35" cy="19" r="2" fill="#2C1810" />
      <circle cx="45" cy="19" r="2" fill="#2C1810" />
      {/* Smile */}
      <path d="M 36 25 Q 40 28 44 25" stroke="#2C1810" strokeWidth="1.5" fill="none" strokeLinecap="round" />
      {/* Body */}
      <rect x="28" y="34" width="24" height="32" rx="4" fill="#5BC4D4" />
      {/* Neck */}
      <rect x="36" y="32" width="8" height="6" rx="2" fill="#FFD4A8" />
      {/* Left arm (raised) */}
      <path d="M 28 38 Q 18 30 14 22" stroke="#FFD4A8" strokeWidth="7" fill="none" strokeLinecap="round" />
      {/* Right arm (down) */}
      <path d="M 52 38 Q 62 46 64 54" stroke="#FFD4A8" strokeWidth="7" fill="none" strokeLinecap="round" />
      {/* Left leg */}
      <path d="M 34 66 Q 30 82 26 95" stroke="#2C3E72" strokeWidth="9" fill="none" strokeLinecap="round" />
      {/* Right leg */}
      <path d="M 46 66 Q 52 82 54 95" stroke="#2C3E72" strokeWidth="9" fill="none" strokeLinecap="round" />
      {/* Shoes */}
      <ellipse cx="24" cy="96" rx="7" ry="4" fill="#2C1810" />
      <ellipse cx="55" cy="96" rx="7" ry="4" fill="#2C1810" />
    </svg>
  );
}

const modes = [
  { id: 'elderly' as const, icon: '🧓', label: '노약자' },
  { id: 'dog' as const, icon: '🐕', label: '강아지 산책' },
  { id: 'general' as const, icon: '🚶', label: '일반' },
];

export function MainScreen({ selectedMode, onModeChange, onNavigateToRoutes }: MainScreenProps) {
  return (
    <div className="w-full h-full flex flex-col overflow-hidden" style={{ background: 'linear-gradient(180deg, #B8E4F9 0%, #D4F0E8 40%, #E8F8F2 70%, #F0FBF7 100%)' }}>
      {/* Status Bar */}
      <div className="flex justify-between items-center px-5 pt-3 pb-1">
        <span style={{ fontSize: '13px', fontWeight: '600', color: '#2D5A8E' }}>0:00</span>
        <div className="flex gap-1 items-center">
          <div className="flex gap-0.5">
            {[1,2,3,4].map(i => (
              <div key={i} style={{ width: '3px', height: `${4 + i * 2}px`, backgroundColor: '#2D5A8E', borderRadius: '1px' }} />
            ))}
          </div>
          <svg width="16" height="12" viewBox="0 0 16 12" fill="none">
            <path d="M8 3C9.9 3 11.6 3.8 12.8 5.1L14.2 3.7C12.6 2 10.4 1 8 1C5.6 1 3.4 2 1.8 3.7L3.2 5.1C4.4 3.8 6.1 3 8 3Z" fill="#2D5A8E" />
            <path d="M8 5.5C9.2 5.5 10.3 6 11.1 6.8L12.5 5.4C11.3 4.2 9.7 3.5 8 3.5C6.3 3.5 4.7 4.2 3.5 5.4L4.9 6.8C5.7 6 6.8 5.5 8 5.5Z" fill="#2D5A8E" />
            <circle cx="8" cy="10" r="1.5" fill="#2D5A8E" />
          </svg>
          <svg width="22" height="12" viewBox="0 0 22 12" fill="none">
            <rect x="0.5" y="0.5" width="18" height="11" rx="2.5" stroke="#2D5A8E" />
            <rect x="2" y="2" width="14" height="8" rx="1.5" fill="#2D5A8E" />
            <path d="M20 4.5V7.5C20.8 7.2 21.3 6.4 21.3 5.7C21.3 4.9 20.8 4.3 20 4.5Z" fill="#2D5A8E" />
          </svg>
        </div>
      </div>

      {/* Weather Widget */}
      <div className="mx-4 mt-2 rounded-2xl p-4" style={{ background: 'rgba(255,255,255,0.75)', backdropFilter: 'blur(12px)', boxShadow: '0 4px 20px rgba(74,144,217,0.15)' }}>
        <div className="flex justify-between items-start">
          <div>
            <div className="flex items-center gap-1.5">
              <MapPin size={14} color="#4A90D9" strokeWidth={2.5} />
              <span style={{ fontSize: '14px', color: '#4A90D9', fontWeight: '600' }}>수지구, 용인시</span>
            </div>
            <div className="flex items-end gap-1 mt-1">
              <span style={{ fontSize: '38px', fontWeight: '700', color: '#1A4B8C', lineHeight: 1.1 }}>28.6°</span>
              <span style={{ fontSize: '16px', color: '#5B8CC4', marginBottom: '6px' }}>C</span>
            </div>
            <div style={{ fontSize: '12px', color: '#6B9ED4', marginTop: '2px' }}>맑음 · 느껴지는 온도 31.2°C</div>
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-1.5 rounded-xl px-2.5 py-1.5" style={{ background: 'rgba(74,144,217,0.12)' }}>
              <Droplets size={14} color="#4A90D9" />
              <span style={{ fontSize: '12px', color: '#2D5A8E', fontWeight: '600' }}>습도 72%</span>
            </div>
            <div className="flex items-center gap-1.5 rounded-xl px-2.5 py-1.5" style={{ background: 'rgba(255,165,0,0.12)' }}>
              <Sun size={14} color="#F5A623" />
              <span style={{ fontSize: '12px', color: '#8B5E00', fontWeight: '600' }}>자외선 7 (높음)</span>
            </div>
            <div className="flex items-center gap-1.5 rounded-xl px-2.5 py-1.5" style={{ background: 'rgba(93,184,124,0.12)' }}>
              <Wind size={14} color="#5DB87C" />
              <span style={{ fontSize: '12px', color: '#2D6E47', fontWeight: '600' }}>풍속 2.3m/s</span>
            </div>
          </div>
        </div>
        {/* Heat advisory */}
        <div className="mt-3 rounded-xl px-3 py-2 flex items-center gap-2" style={{ background: 'linear-gradient(135deg, #FFE8B2, #FFDDA0)' }}>
          <span style={{ fontSize: '16px' }}>☀️</span>
          <span style={{ fontSize: '12px', color: '#7B4F00', fontWeight: '500' }}>폭염 특보 발효 중 · 그늘길 이용을 권장드려요</span>
        </div>
      </div>

      {/* Character Illustration */}
      <div className="flex-1 flex flex-col items-center justify-center relative px-4">
        {/* Decorative clouds */}
        <div className="absolute top-0 left-6 rounded-full opacity-60" style={{ width: '50px', height: '24px', background: 'rgba(255,255,255,0.8)' }} />
        <div className="absolute top-2 left-12 rounded-full opacity-40" style={{ width: '35px', height: '18px', background: 'rgba(255,255,255,0.8)' }} />
        <div className="absolute top-4 right-8 rounded-full opacity-60" style={{ width: '45px', height: '22px', background: 'rgba(255,255,255,0.8)' }} />
        <div className="absolute top-6 right-14 rounded-full opacity-40" style={{ width: '30px', height: '16px', background: 'rgba(255,255,255,0.8)' }} />

        {/* Characters */}
        <div className="flex items-end gap-4 mb-4">
          <div className="flex flex-col items-center">
            <div className="rounded-2xl p-3" style={{ background: 'rgba(255,255,255,0.7)' }}>
              <DogCharacter />
            </div>
          </div>
          <div className="flex flex-col items-center mb-2">
            <div className="rounded-2xl p-3" style={{ background: 'rgba(255,255,255,0.7)' }}>
              <PersonCharacter />
            </div>
          </div>
        </div>

        {/* Message bubble */}
        <div className="rounded-2xl px-5 py-3 text-center" style={{ background: 'rgba(255,255,255,0.85)', boxShadow: '0 4px 16px rgba(74,144,217,0.2)' }}>
          <p style={{ fontSize: '15px', color: '#2D5A8E', fontWeight: '600', lineHeight: 1.4 }}>
            🌿 오늘도 시원하게 산책해요!
          </p>
          <p style={{ fontSize: '12px', color: '#6B9ED4', marginTop: '2px' }}>AI가 가장 쾌적한 경로를 찾아드릴게요</p>
        </div>
      </div>

      {/* CTA Button */}
      <div className="px-5 pb-3">
        <button
          onClick={onNavigateToRoutes}
          className="w-full rounded-2xl py-4 flex items-center justify-center gap-3 active:scale-95 transition-transform"
          style={{ background: 'linear-gradient(135deg, #4A90D9, #3A7BC8)', boxShadow: '0 6px 24px rgba(74,144,217,0.45)' }}
        >
          <Navigation size={20} color="white" strokeWidth={2.5} />
          <span style={{ fontSize: '17px', fontWeight: '700', color: 'white' }}>시원한 길 선택하러 가기</span>
          <ChevronRight size={20} color="white" strokeWidth={2.5} />
        </button>
      </div>

      {/* Mode Selector */}
      <div className="mx-4 mb-4 rounded-2xl p-1.5 flex gap-1" style={{ background: 'rgba(255,255,255,0.75)', boxShadow: '0 2px 12px rgba(74,144,217,0.12)' }}>
        {modes.map(mode => (
          <button
            key={mode.id}
            onClick={() => onModeChange(mode.id)}
            className="flex-1 rounded-xl py-2.5 flex flex-col items-center gap-1 transition-all active:scale-95"
            style={{
              background: selectedMode === mode.id
                ? 'linear-gradient(135deg, #4A90D9, #3A7BC8)'
                : 'transparent',
              boxShadow: selectedMode === mode.id ? '0 2px 8px rgba(74,144,217,0.4)' : 'none'
            }}
          >
            <span style={{ fontSize: '20px' }}>{mode.icon}</span>
            <span style={{
              fontSize: '11px',
              fontWeight: '600',
              color: selectedMode === mode.id ? 'white' : '#5B8CC4'
            }}>{mode.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
