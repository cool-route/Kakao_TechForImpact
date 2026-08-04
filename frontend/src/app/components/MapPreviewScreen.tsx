import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, MapPin, Thermometer, Sun, TreePine, Wind } from 'lucide-react';
import type { RouteInfo } from '../App';

declare global {
  interface Window {
    kakao: {
      maps: {
        load: (callback: () => void) => void;
        Map: new (container: HTMLElement, options: any) => any;
        LatLng: new (lat: number, lng: number) => any;
        LatLngBounds: new () => any;
        Polyline: new (options: any) => any;
        CustomOverlay: new (options: any) => any;
      };
    };
  }
}

function heatScoreToColor(heatScore: number): string {
  if (heatScore < 20) return '#4A90D9'; 
  if (heatScore < 22) return '#5DB87C'; 
  if (heatScore < 24) return '#F5A623'; 
  return '#E74C3C'; 
}

export function KakaoMapComponent({ apiKey, route }: { apiKey: string; route: RouteInfo }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const overlaysRef = useRef<any[]>([]);

  useEffect(() => {
    if (!apiKey || !mapRef.current) return;

    mapRef.current.style.width = '100%';
    mapRef.current.style.height = '100%';

    const existingScript = document.querySelector(`script[src*="dapi.kakao.com"]`);

    function initMap() {
      if (!mapRef.current || !window.kakao || !window.kakao.maps || !window.kakao.maps.load) return;

      window.kakao.maps.load(() => {
        const initialCenter = new window.kakao.maps.LatLng(route.start[0], route.start[1]);
        const map = new window.kakao.maps.Map(mapRef.current!, { center: initialCenter, level: 5 });
        mapInstanceRef.current = map;

        overlaysRef.current.forEach((o: any) => o.setMap(null));
        overlaysRef.current = [];
        const bounds = new (window.kakao.maps as any).LatLngBounds();

        const geojson = typeof route.geojson === 'string' ? JSON.parse(route.geojson) : route.geojson;
        const features = geojson?.features || [];

        features.forEach((feature: any) => {
          const heatScore = feature.properties?.heat_score ?? 22;
          const path = feature.geometry.coordinates.map(([lng, lat]: [number, number]) => {
            const latlng = new window.kakao.maps.LatLng(lat, lng);
            bounds.extend(latlng);
            return latlng;
          });

          const polyline = new window.kakao.maps.Polyline({
            path, strokeWeight: 7, strokeColor: heatScoreToColor(heatScore), strokeOpacity: 0.9, strokeStyle: 'solid',
          });
          polyline.setMap(map);
          overlaysRef.current.push(polyline);
        });

        (route.shelters ?? []).forEach((shelter: any) => {
          const position = new window.kakao.maps.LatLng(shelter.lat, shelter.lng);
          bounds.extend(position);

          const content = `<div style="background:#3B82F6;border:2px solid white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:10px;color:white;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.2)">쉼터</div>`;
          const overlay = new window.kakao.maps.CustomOverlay({ position, content, map, yAnchor: 1 });
          overlaysRef.current.push(overlay);
        });

        if (!bounds.isEmpty()) {
          map.setBounds(bounds, 100, 40, 380, 40);
        }
      });
    }

    if (existingScript) {
      if ((window as any).kakao?.maps) {
        initMap();
      } else {
        existingScript.addEventListener('load', initMap);
      }
      return;
    }

    const script = document.createElement('script');
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(apiKey)}&autoload=false&libraries=services`;
    script.async = true;
    script.defer = true;
    script.addEventListener('load', initMap);
    document.head.appendChild(script);
  }, [apiKey, route]);

  return <div ref={mapRef} className="w-full h-full bg-[#EBF5FF]" />;
}

interface MapPreviewScreenProps {
  route: RouteInfo;
  kakaoApiKey: string;
  onBack: () => void;
  onStartNavigating: () => void;
}

export default function MapPreviewScreen({ route, kakaoApiKey, onBack, onStartNavigating }: MapPreviewScreenProps) {
  // 드래그(회색 바) 패널 기능 상태 추가
  const [sheetExpanded, setSheetExpanded] = useState(false);
  const [startY, setStartY] = useState(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    setStartY(e.touches[0].clientY);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const endY = e.changedTouches[0].clientY;
    const deltaY = endY - startY;

    if (deltaY < -40) {
      setSheetExpanded(true); 
    } else if (deltaY > 40) {
      setSheetExpanded(false); 
    }
  };

  const geojson = typeof route.geojson === 'string' ? JSON.parse(route.geojson) : (route.geojson || {});
  const features = geojson.features ?? [];
  const avgTemp = features.length > 0
    ? features.reduce((s: number, f: any) => s + (f.properties?.temperature ?? 0), 0) / features.length
    : null;
    
  const routeData = route as any; 
  const heatScore = routeData.heatScore ?? 85; 
  const shadeRatio = routeData.shadeRatio ?? (features.length > 0 ? 45 : 0);

  const weatherStats = [
    { icon: <Thermometer size={20} color="#E74C3C" />, label: '체감 온도', value: avgTemp ? `${avgTemp.toFixed(1)}°C` : '--', bg: '#FEE2E2' },
    { icon: <Sun size={20} color="#F5A623" />, label: '열 지수', value: `${heatScore}점`, bg: '#FEF3C7' },
    { icon: <TreePine size={20} color="#5DB87C" />, label: '그림자 비율', value: `${shadeRatio}%`, bg: '#D1FAE5' },
    { icon: <Wind size={20} color="#4A90D9" />, label: '무더위 쉼터', value: `${route.shelters?.length ?? 0}개`, bg: '#DBEAFE' },
  ];

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#EBF5FF]">
      
      <div className="absolute inset-0 z-0">
        {kakaoApiKey ? (
           <KakaoMapComponent apiKey={kakaoApiKey} route={route} />
        ) : (
           <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 font-bold bg-[#EBF5FF]">
             <p className="text-[22px]">지도가 뜨지 않습니다 :(</p>
           </div>
        )}
      </div>

      {/* Header UI */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center gap-3 bg-white px-5 py-4 rounded-2xl shadow-sm">
        <button onClick={onBack} className="active:scale-90 transition-transform">
          <ArrowLeft size={28} color="#333" />
        </button>
        <span className="text-[22px] font-black text-gray-800">
          경로 미리보기
        </span>
      </div>

      {/* Bottom Sheet for Preview */}
      <div 
        className="absolute bottom-0 left-0 right-0 bg-white rounded-t-[32px] shadow-[0_-10px_40px_rgba(0,0,0,0.1)] flex flex-col transition-all duration-300 ease-out z-10"
        style={{ height: sheetExpanded ? '75%' : '45%' }}
      >
        {/* 드래그 핸들러 (회색 바) */}
        <div 
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
          onClick={() => setSheetExpanded(!sheetExpanded)}
          className="w-full pt-4 pb-2 flex justify-center cursor-pointer shrink-0"
        >
          <div className="w-16 h-1.5 bg-gray-300 rounded-full" />
        </div>

        <div className="px-8 pb-5 border-b border-gray-100 shrink-0">
          <h3 className="text-[28px] font-black text-gray-800 mb-2">{route.name}</h3>
          <div className="flex gap-5 text-lg font-bold text-gray-500">
            <span className="flex items-center gap-1.5">📏 {route.distance}</span>
            <span className="flex items-center gap-1.5">⏱ {route.duration}</span>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto px-8 py-6" style={{ scrollbarWidth: 'none' }}>
          <h4 className="font-bold text-gray-800 mb-5 text-xl">경로 상세</h4>
          <div className="relative pl-4 border-l-[3px] border-gray-200 ml-2 flex flex-col gap-8 mb-10">
            <div className="relative">
              <div className="absolute -left-[23px] top-1 w-4 h-4 bg-green-500 rounded-full border-[3px] border-white ring-1 ring-green-200"></div>
              <p className="font-black text-gray-800 text-[18px]">출발 · 임시 출발지</p>
              <p className="text-[14px] font-bold text-gray-400 mt-1">0km · 00:00</p>
            </div>
            <div className="relative">
              <div className="absolute -left-[23px] top-1 w-4 h-4 bg-red-500 rounded-full border-[3px] border-white ring-1 ring-red-200"></div>
              <p className="font-black text-gray-800 text-[18px]">{route.name} 도착</p>
              <p className="text-[14px] font-bold text-gray-400 mt-1">{route.distance} · {route.duration}</p>
            </div>
          </div>

          <h4 className="font-bold text-gray-800 mb-5 text-xl">기상 및 쉼터 정보</h4>
          <div className="grid grid-cols-2 gap-4 mb-4">
            {weatherStats.map((stat, i) => (
              <div key={i} className="flex items-center gap-4 rounded-2xl p-4" style={{ backgroundColor: stat.bg }}>
                <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white/70">
                  {stat.icon}
                </div>
                <div>
                  <div className="text-[13px] font-bold text-gray-600">{stat.label}</div>
                  <div className="text-[17px] font-black text-gray-800">{stat.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 pt-3 bg-white flex gap-3 shrink-0">
          <button onClick={onBack} className="flex-1 bg-white border-2 border-[#3B82F6] text-[#3B82F6] py-5 rounded-2xl font-bold text-[20px] active:bg-blue-50 transition-colors">
            다른 경로 보기
          </button>
          <button onClick={onStartNavigating} className="flex-1 bg-[#3B82F6] text-white py-5 rounded-2xl font-bold text-[20px] shadow-md active:bg-blue-600 transition-colors">
            이 경로로 할게요
          </button>
        </div>
      </div>
    </div>
  );
}