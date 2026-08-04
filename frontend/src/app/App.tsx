import { useState, useRef, useEffect } from 'react';
import SearchFlow from './components/SearchFlow';
import RouteResultScreen from './components/RouteResultScreen';
import MapPreviewScreen from './components/MapPreviewScreen';
import NavigatingScreen from './components/NavigatingScreen';

export type Step = 'start' | 'voice_input' | 'voice_confirm' | 'analyzing' | 'preset' | 'searching' | 'route_list' | 'map_preview' | 'navigating';
export type TagItem = { id: string; label: string; originalType: 'selected' | 'recommended' };

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

  const prevStepRef = useRef<Step>('start');
  useEffect(() => {
    prevStepRef.current = currentStep;
  }, [currentStep]);
  
  const [recognizedText, setRecognizedText] = useState("");
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  const [activeTags, setActiveTags] = useState<TagItem[]>([]);
  const [inactiveTags, setInactiveTags] = useState<TagItem[]>([]);
  
  const kakaoApiKey = (import.meta as any).env?.VITE_KAKAO_MAPS_API_KEY ?? '';

  const handleRestart = () => {
    setCurrentStep('start');
    setRecognizedText("");
    setSelectedTags([]);
    setActiveTags([]);
    setInactiveTags([]);
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-4 bg-[#F5F7F5]"
      style={{ fontFamily: 'sans-serif' }}
    >
      <div
        style={{
          width: '390px',
          height: '844px',
          borderRadius: '44px',
          overflow: 'hidden',
          boxShadow: '0 30px 80px rgba(0,0,0,0.1)',
          border: '8px solid #1A1A2E',
          position: 'relative',
          background: '#FFFFFF',
          flexShrink: 0,
        }}
      >
        <div style={{ position: 'absolute', top: '12px', left: '50%', transform: 'translateX(-50%)', width: '126px', height: '37px', background: '#000', borderRadius: '20px', zIndex: 100 }} />
        <div className="absolute top-0 left-0 right-0 px-6 pt-4 flex justify-between items-center z-50 pointer-events-none">
          <span className="text-sm font-bold text-gray-800">9:41</span>
          <div className="flex gap-1">
            <div className="w-5 h-3.5 bg-gray-800 rounded-sm"></div>
            <div className="w-7 h-3.5 border border-gray-800 rounded-sm p-0.5"><div className="w-5 h-full bg-[#3B82F6] rounded-sm"></div></div>
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
              activeTags={activeTags}
              setActiveTags={setActiveTags}
              inactiveTags={inactiveTags}
              setInactiveTags={setInactiveTags}
            />
          )}

          {currentStep === 'route_list' && (
            <RouteResultScreen 
              selectedTags={selectedTags}
              onBack={() => setCurrentStep('preset')}
              onSelectRoute={(route) => {
                setSelectedRoute(route);
                setCurrentStep('map_preview');
              }}
              disableAnimation={prevStepRef.current === 'map_preview'}
            />
          )}

          {currentStep === 'map_preview' && selectedRoute && (
            <MapPreviewScreen 
              route={selectedRoute}
              kakaoApiKey={kakaoApiKey}
              onBack={() => setCurrentStep('route_list')}
              onStartNavigating={() => setCurrentStep('navigating')}
            />
          )}

          {currentStep === 'navigating' && selectedRoute && (
            <NavigatingScreen 
              route={selectedRoute}
              kakaoApiKey={kakaoApiKey}
              onRestart={handleRestart}
            />
          )}
        </div>
      </div>
    </div>
  );
}