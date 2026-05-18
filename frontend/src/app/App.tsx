import { useState } from 'react';
import { MainScreen } from './components/MainScreen';
import { RouteListScreen } from './components/RouteListScreen';
import type { RouteInfo } from './components/RouteListScreen';
import { MapDetailScreen } from './components/MapDetailScreen';
import { Key, Eye, EyeOff } from 'lucide-react';

type AppScreen = 'main' | 'routeList' | 'mapDetail';

export default function App() {
  const [screen, setScreen] = useState<AppScreen>('main');
  const [selectedRoute, setSelectedRoute] = useState<RouteInfo | null>(null);
  const [mode, setMode] = useState<'general' | 'elderly' | 'dog'>('general');
  const [kakaoApiKey, setKakaoApiKey] = useState('');
  const [showApiInput, setShowApiInput] = useState(false);
  const [apiKeyVisible, setApiKeyVisible] = useState(false);

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

      {/* API Key section */}
      <div className="flex flex-col items-center gap-2 w-full max-w-[390px]">
        <button
          onClick={() => setShowApiInput(v => !v)}
          className="flex items-center gap-2 rounded-xl px-4 py-2 transition-all active:scale-95"
          style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(8px)' }}
        >
          <Key size={14} color="white" />
          <span style={{ fontSize: '13px', color: 'white', fontWeight: '500' }}>
            카카오맵 API 키 {kakaoApiKey ? '✅ 설정됨' : '설정하기'}
          </span>
        </button>

        {showApiInput && (
          <div
            className="w-full rounded-2xl p-4 flex flex-col gap-3"
            style={{ background: 'rgba(255,255,255,0.15)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.3)' }}
          >
            <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.9)', lineHeight: '1.6' }}>
              카카오 개발자 센터(developers.kakao.com)에서 발급받은<br />
              JavaScript 앱 키를 입력하세요.
            </p>
            <div className="flex gap-2">
              <div className="flex-1 flex items-center gap-2 rounded-xl px-3 py-2.5" style={{ background: 'rgba(255,255,255,0.9)' }}>
                <input
                  type={apiKeyVisible ? 'text' : 'password'}
                  placeholder="카카오맵 JavaScript API 키"
                  value={kakaoApiKey}
                  onChange={e => setKakaoApiKey(e.target.value)}
                  className="flex-1 outline-none bg-transparent"
                  style={{ fontSize: '13px', color: '#1A3A5C' }}
                />
                <button onClick={() => setApiKeyVisible(v => !v)} className="opacity-50 hover:opacity-100 transition-opacity">
                  {apiKeyVisible ? <EyeOff size={14} color="#1A3A5C" /> : <Eye size={14} color="#1A3A5C" />}
                </button>
              </div>
              <button
                onClick={() => setShowApiInput(false)}
                className="rounded-xl px-4 py-2.5 transition-all active:scale-95"
                style={{ background: 'rgba(255,255,255,0.9)', fontSize: '13px', fontWeight: '700', color: '#4A90D9' }}
              >
                확인
              </button>
            </div>
            {!kakaoApiKey && (
              <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.7)' }}>
                ℹ️ API 키 없이도 모의 지도로 앱을 체험할 수 있습니다.
              </p>
            )}
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
