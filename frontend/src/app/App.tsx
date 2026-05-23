import { useState } from 'react';
import { MainScreen } from './components/MainScreen';
import { RouteListScreen } from './components/RouteListScreen';
import type { RouteInfo } from './components/RouteListScreen';
import { MapDetailScreen } from './components/MapDetailScreen';

type AppScreen = 'main' | 'routeList' | 'mapDetail';
// healthcheck api
type HealthStatus = {
  status: 'idle' | 'loading' | 'success' | 'error';
  message: string;
};

export default function App() {
  const [screen, setScreen] = useState<AppScreen>('main');
  const [selectedRoute, setSelectedRoute] = useState<RouteInfo | null>(null);
  const [mode, setMode] = useState<'general' | 'elderly' | 'dog'>('general');
  const kakaoApiKey = (import.meta as any).env?.VITE_KAKAO_MAPS_API_KEY ?? '';

  // heathcheck api
  const [healthStatus, setHealthStatus] = useState<HealthStatus>({ status: 'idle', message: '대기 중...' });
  const checkServerHealth = async () => {
    setHealthStatus({ status: 'loading', message: '요청 중...' });
    try {
      const res = await fetch('http://127.0.0.1:8000/healthcheck');
      if (res.ok) {
        const data = await res.json();
        setHealthStatus({ status: 'success', message: `✅ 성공! 백엔드 상태: ${data.status}` });
      } else {
        setHealthStatus({ status: 'error', message: `❌ HTTP 에러: ${res.status}` });
      }
    } catch (err) {
      setHealthStatus({ status: 'error', message: '⚠️ 연결 실패 (서버가 켜져 있는지 확인하세요)' });
      console.error('Healthcheck Error:', err);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-4 p-4"
      style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
    >
      {/* App title */}
      <div className="text-center">
        <h1 className="text-white" style={{ fontSize: '22px', fontWeight: '800', letterSpacing: '-0.5px' }}>
          🌿 쿨워크 CoolWalk
        </h1>
        <p className="text-white/70" style={{ fontSize: '13px', marginTop: '2px' }}>기후 기반 도보 내비게이션</p>
      </div>

      {/* healthcheck api ui */}
      <div className="flex flex-col items-center gap-2 mb-2 w-full max-w-[390px]">
        <button
          onClick={checkServerHealth}
          className="flex items-center gap-2 rounded-xl px-4 py-2 transition-all active:scale-95"
          style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.3)' }}
        >
          <span style={{ fontSize: '13px', color: 'white', fontWeight: '600' }}>
            ⚙️ 백엔드 연동 테스트
          </span>
        </button>
        {healthStatus.status !== 'idle' && (
          <div 
            style={{ 
              fontSize: '12px', 
              fontWeight: '600',
              color: healthStatus.status === 'success' ? '#A7F3D0' : healthStatus.status === 'error' ? '#FECACA' : '#FDE68A',
              textShadow: '0 1px 2px rgba(0,0,0,0.2)'
            }}
          >
            {healthStatus.message}
          </div>
        )}
      </div>

      {/* Phone frame */}
      <div
        style={{
          width: '390px',
          height: '844px',
          borderRadius: '44px',
          overflow: 'hidden',
          boxShadow: '0 30px 80px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.1), inset 0 0 0 2px rgba(255,255,255,0.05)',
          border: '8px solid #1A1A2E',
          position: 'relative',
          background: '#fff',
          flexShrink: 0,
        }}
      >
        {/* Side buttons (decorative) */}
        <div style={{ position: 'absolute', left: '-10px', top: '120px', width: '4px', height: '32px', background: '#1A1A2E', borderRadius: '2px 0 0 2px' }} />
        <div style={{ position: 'absolute', left: '-10px', top: '165px', width: '4px', height: '56px', background: '#1A1A2E', borderRadius: '2px 0 0 2px' }} />
        <div style={{ position: 'absolute', left: '-10px', top: '235px', width: '4px', height: '56px', background: '#1A1A2E', borderRadius: '2px 0 0 2px' }} />
        <div style={{ position: 'absolute', right: '-10px', top: '185px', width: '4px', height: '80px', background: '#1A1A2E', borderRadius: '0 2px 2px 0' }} />

        {/* Dynamic Island */}
        <div style={{ position: 'absolute', top: '12px', left: '50%', transform: 'translateX(-50%)', width: '126px', height: '37px', background: '#000', borderRadius: '20px', zIndex: 100 }} />

        {/* Screen content */}
        <div className="w-full h-full">
          {screen === 'main' && (
            <MainScreen
              selectedMode={mode}
              onModeChange={setMode}
              onNavigateToRoutes={() => setScreen('routeList')}
            />
          )}
          {screen === 'routeList' && (
            <RouteListScreen
              mode={mode}
              onBack={() => setScreen('main')}
              onSelectRoute={route => {
                setSelectedRoute(route);
                setScreen('mapDetail');
              }}
            />
          )}
          {screen === 'mapDetail' && selectedRoute && (
            <MapDetailScreen
              route={selectedRoute}
              onBack={() => setScreen('routeList')}
              kakaoApiKey={kakaoApiKey}
            />
          )}
        </div>
      </div>

      {/* Screen indicators */}
      <div className="flex gap-2 items-center">
        {(['main', 'routeList', 'mapDetail'] as AppScreen[]).map((s, i) => (
          <div
            key={s}
            className="rounded-full transition-all"
            style={{
              width: screen === s ? '24px' : '8px',
              height: '8px',
              background: screen === s ? 'white' : 'rgba(255,255,255,0.4)',
            }}
          />
        ))}
      </div>
      <div className="flex gap-3">
        {[
          { screen: 'main' as AppScreen, label: '메인', emoji: '🏠' },
          { screen: 'routeList' as AppScreen, label: '경로 목록', emoji: '📋' },
        ].map(({ screen: s, label, emoji }) => (
          <button
            key={s}
            onClick={() => setScreen(s)}
            className="rounded-xl px-3 py-1.5 transition-all active:scale-95"
            style={{
              background: screen === s ? 'white' : 'rgba(255,255,255,0.2)',
              color: screen === s ? '#4A90D9' : 'white',
              fontSize: '12px',
              fontWeight: screen === s ? '700' : '500',
            }}
          >
            {emoji} {label}
          </button>
        ))}
      </div>
    </div>
  );
}
