import { useState } from 'react';
import SearchFlow from './components/SearchFlow';
import RouteResultScreen from './components/RouteResultScreen';
import MapPreviewScreen from './components/MapPreviewScreen';

export type Step = 'start' | 'voice_input' | 'voice_confirm' | 'analyzing' | 'preset' | 'searching' | 'route_list' | 'map_preview';

export interface RouteInfo {
  id: number;
  rank: number;
  rankColor: string;
  name: string;
  distance: string;
  duration: string;
  tags: string[];
  start: [number, number];
  end: [number, number];
  geojson: any;
  shelters: any[];
}

export default function App() {
  const [currentStep, setCurrentStep] = useState<Step>('start');
  const [selectedRoute, setSelectedRoute] = useState<RouteInfo | null>(null);
  
  const [recognizedText, setRecognizedText] = useState("");
  // SearchFlow에서 확정한 최종 프리셋(태그) 상태
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  
  const kakaoApiKey = (import.meta as any).env?.VITE_KAKAO_MAPS_API_KEY ?? '';

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-4 p-4"
      style={{ background: 'linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%)' }}
    >
      <div className="text-center">
        <h1 className="text-gray-800" style={{ fontSize: '22px', fontWeight: '800' }}>
          🍃 시원한길 🍃
        </h1>
        <p className="text-gray-600" style={{ fontSize: '13px', marginTop: '2px' }}>기후 기반 도보 내비게이션</p>
      </div>

      <div
        style={{
          width: '390px',
          height: '844px',
          borderRadius: '44px',
          overflow: 'hidden',
          boxShadow: '0 30px 80px rgba(0,0,0,0.2)',
          border: '8px solid #1A1A2E',
          position: 'relative',
          background: '#F5F7F5',
          flexShrink: 0,
        }}
      >
        <div style={{ position: 'absolute', top: '12px', left: '50%', transform: 'translateX(-50%)', width: '126px', height: '37px', background: '#000', borderRadius: '20px', zIndex: 100 }} />
        <div className="absolute top-0 left-0 right-0 px-6 pt-4 flex justify-between items-center z-50 pointer-events-none">
          <span className="text-xs font-bold text-gray-800">9:41</span>
          <div className="flex gap-1">
            <div className="w-4 h-3 bg-gray-800 rounded-sm"></div>
            <div className="w-6 h-3 border border-gray-800 rounded-sm p-0.5"><div className="w-4 h-full bg-green-500 rounded-sm"></div></div>
          </div>
        </div>

        <div className="w-full h-full relative pt-12">
          {['start', 'voice_input', 'voice_confirm', 'analyzing', 'preset', 'searching'].includes(currentStep) && (
            <SearchFlow 
              step={currentStep as any} 
              setStep={setCurrentStep}
              recognizedText={recognizedText}
              setRecognizedText={setRecognizedText}
              setSelectedTags={setSelectedTags}
            />
          )}

          {currentStep === 'route_list' && (
            <RouteResultScreen 
              selectedTags={selectedTags} // API 연동을 위해 선택된 태그 전달
              onBack={() => setCurrentStep('start')}
              onSelectRoute={(route) => {
                setSelectedRoute(route);
                setCurrentStep('map_preview');
              }}
            />
          )}

          {currentStep === 'map_preview' && selectedRoute && (
            <MapPreviewScreen 
              route={selectedRoute}
              kakaoApiKey={kakaoApiKey}
              onBack={() => setCurrentStep('route_list')}
            />
          )}
        </div>
      </div>
    </div>
  );
}