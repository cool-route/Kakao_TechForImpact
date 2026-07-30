import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, MapPin, Thermometer, Sun, TreePine, Wind, ChevronUp, ChevronDown } from 'lucide-react';
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

function KakaoMapComponent({ apiKey, route }: { apiKey: string; route: RouteInfo }) {
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

          const content = `<div style="background:#FFD700;border:2px solid white;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-size:16px;box-shadow:0 2px 8px rgba(0,0,0,0.2)">🏠</div>`;
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

  return <div ref={mapRef} className="w-full h-full bg-[#E8F4F8]" />;
}

interface MapPreviewScreenProps {
  route: RouteInfo;
  kakaoApiKey: string;
  onBack: () => void;
}

export default function MapPreviewScreen({ route, kakaoApiKey, onBack }: MapPreviewScreenProps) {
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
    { icon: <Thermometer size={20} color="#E74C3C" />, label: '체감 온도', value: avgTemp ? `${avgTemp.toFixed(1)}°C` : '--', sub: '경로 평균 체감온도', color: '#FFE8E8' },
    { icon: <Sun size={20} color="#F5A623" />, label: '열 지수', value: `${heatScore}점`, sub: '높을수록 쾌적한 경로', color: '#FFF5E8' },
    { icon: <TreePine size={20} color="#5DB87C" />, label: '그림자 비율', value: `${shadeRatio}%`, sub: '경로의 그늘 구간 비율', color: '#E8F8EF' },
    { icon: <Wind size={20} color="#4A90D9" />, label: '쉼터', value: `${route.shelters?.length ?? 0}개`, sub: '경로 내 무더위쉼터', color: '#E8F4FF' },
  ];

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#E8F4F8]">
      
      <div className="absolute inset-0 z-0">
        {kakaoApiKey ? (
           <KakaoMapComponent apiKey={kakaoApiKey} route={route} />
        ) : (
           <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 font-bold bg-[#E8F4F8]">
             <p className="text-xl">지도가 뜨지 않습니다 :(</p>
           </div>
        )}
      </div>

      <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
        <button onClick={onBack} className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform">
          <ArrowLeft size={24} color="#333" />
        </button>
        <span className="text-xl font-bold text-gray-800 bg-white/90 px-4 py-2 rounded-full backdrop-blur-sm shadow-sm">
          경로 미리보기
        </span>
      </div>

      <div 
        className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.15)] flex flex-col transition-all duration-300 ease-out"
        style={{ height: sheetExpanded ? '80%' : '45%', zIndex: 10 }}
      >
        <div 
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
          className="w-full px-6 pt-4 pb-5 border-b border-gray-100 cursor-grab active:cursor-grabbing"
        >
          <div className="flex flex-col items-center mb-4">
            <div className="w-12 h-2 rounded-full bg-gray-300" />
            <button onClick={() => setSheetExpanded(v => !v)} className="flex items-center gap-1 mt-3 active:opacity-70">
              <span style={{ fontSize: '14px', color: '#9BB5D0', fontWeight: 'bold' }}>
                {sheetExpanded ? '접기' : '자세히 보기'}
              </span>
              {sheetExpanded ? <ChevronDown size={20} color="#9BB5D0" /> : <ChevronUp size={20} color="#9BB5D0" />}
            </button>
          </div>
          
          <div className="flex justify-between items-end">
            <div>
              <h3 className="text-2xl font-black text-gray-800 mb-2">{route.name}</h3>
              <div className="flex gap-4 text-base font-bold text-gray-500">
                <span>📏 {route.distance}</span>
                <span>⏱ {route.duration}</span>
                {route.tags.includes("반려동물") && (
                  <span className="text-[#D78B42] font-black">🐕 반려동물 가능</span>
                )}
              </div>
            </div>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-6" style={{ scrollbarWidth: 'none' }}>
          
          <div className="mb-10">
            <p className="font-bold text-gray-800 mb-4 text-base">경로 기상 정보</p>
            <div className="flex flex-col gap-3">
              {weatherStats.map((stat, i) => (
                <div key={i} className="flex items-center gap-4 rounded-2xl px-5 py-4" style={{ background: stat.color }}>
                  <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white shadow-sm">
                    {stat.icon}
                  </div>
                  <div className="flex-1">
                    <div className="text-base font-bold text-gray-600 mb-1">{stat.label}</div>
                  <div className="text-2xl font-black text-gray-800">{stat.value}</div>
                  </div>
                  <span className="text-sm text-gray-500 font-medium">{stat.sub}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="font-bold text-gray-800 mb-5 text-base">경로 상세 (무더위 쉼터)</p>
            <div className="relative pl-7 border-l-[3px] border-gray-200 ml-4 flex flex-col gap-8 pb-4">
              
              {(route.shelters ?? []).length > 0 ? (
                (route.shelters ?? []).map((shelter, idx) => (
                  <div key={idx} className="relative">
                    <div className="absolute -left-[46px] bg-white w-8 h-8 rounded-full flex items-center justify-center">
                      <MapPin size={26} color="#E74C3C" fill="#FCECEC" />
                    </div>
                    <p className="font-black text-gray-700 text-xl mb-1">{shelter.name || '무더위 쉼터 경유'}</p>
                    <p className="text-sm font-medium text-gray-400">경유지</p>
                  </div>
                ))
              ) : (
                <p className="text-base font-medium text-gray-500">경유하는 쉼터가 없습니다.</p>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}