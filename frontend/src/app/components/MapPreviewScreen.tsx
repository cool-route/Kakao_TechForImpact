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

          const content = `<div style="background:#FFD700;border:2px solid white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.2)">🏠</div>`;
          const overlay = new window.kakao.maps.CustomOverlay({ position, content, map, yAnchor: 1 });
          overlaysRef.current.push(overlay);
        });

        // 출발/도착 아이콘(주석 처리)
        /*
        const startPos = new window.kakao.maps.LatLng(route.start[0], route.start[1]);
        const endPos = new window.kakao.maps.LatLng(route.end[0], route.end[1]);
        bounds.extend(startPos);
        bounds.extend(endPos);
        
        const startContent = `<div style="background:#3A9E66;border:2px solid white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3)">출</div>`;
        const endContent = `<div style="background:#E74C3C;border:2px solid white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3)">도</div>`;
        overlaysRef.current.push(new window.kakao.maps.CustomOverlay({ position: startPos, content: startContent, map, yAnchor: 1, zIndex: 3 }));
        overlaysRef.current.push(new window.kakao.maps.CustomOverlay({ position: endPos, content: endContent, map, yAnchor: 1, zIndex: 3 }));
        */

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

  // 드래그(스와이프) 이벤트 핸들러
  const handleTouchStart = (e: React.TouchEvent) => {
    setStartY(e.touches[0].clientY);
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const endY = e.changedTouches[0].clientY;
    const deltaY = endY - startY;

    if (deltaY < -40) {
      setSheetExpanded(true); // 위로 슬라이드
    } else if (deltaY > 40) {
      setSheetExpanded(false); // 아래로 슬라이드
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
    { icon: <Thermometer size={16} color="#E74C3C" />, label: '체감 온도', value: avgTemp ? `${avgTemp.toFixed(1)}°C` : '--', sub: '경로 평균 체감온도', color: '#FFE8E8' },
    { icon: <Sun size={16} color="#F5A623" />, label: '열 지수', value: `${heatScore}점`, sub: '높을수록 쾌적한 경로', color: '#FFF5E8' },
    { icon: <TreePine size={16} color="#5DB87C" />, label: '그림자 비율', value: `${shadeRatio}%`, sub: '경로의 그늘 구간 비율', color: '#E8F8EF' },
    { icon: <Wind size={16} color="#4A90D9" />, label: '쉼터', value: `${route.shelters?.length ?? 0}개`, sub: '경로 내 무더위쉼터', color: '#E8F4FF' },
  ];

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#E8F4F8]">
      
      <div className="absolute inset-0 z-0">
        {kakaoApiKey ? (
           <KakaoMapComponent apiKey={kakaoApiKey} route={route} />
        ) : (
           <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 font-bold bg-[#E8F4F8]">
             <p className="text-lg">지도가 뜨지 않습니다 :(</p>
           </div>
        )}
      </div>

      <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
        <button onClick={onBack} className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform">
          <ArrowLeft size={20} color="#333" />
        </button>
        <span className="text-lg font-bold text-gray-800 bg-white/90 px-3 py-1 rounded-full backdrop-blur-sm shadow-sm">
          경로 미리보기
        </span>
      </div>

      <div 
        className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.15)] flex flex-col transition-all duration-300 ease-out"
        style={{ height: sheetExpanded ? '80%' : '45%', zIndex: 10 }}
      >
        {/* 드래그 영역 (헤더 전체) */}
        <div 
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
          className="w-full px-5 pt-3 pb-4 border-b border-gray-100 cursor-grab active:cursor-grabbing"
        >
          <div className="flex flex-col items-center mb-3">
            <div className="w-10 h-1.5 rounded-full bg-gray-300" />
            <button onClick={() => setSheetExpanded(v => !v)} className="flex items-center gap-1 mt-2 active:opacity-70">
              <span style={{ fontSize: '12px', color: '#9BB5D0', fontWeight: 'bold' }}>
                {sheetExpanded ? '접기' : '자세히 보기'}
              </span>
              {sheetExpanded ? <ChevronDown size={14} color="#9BB5D0" /> : <ChevronUp size={14} color="#9BB5D0" />}
            </button>
          </div>
          
          <div className="flex justify-between items-end">
            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-1">{route.name}</h3>
              <div className="flex gap-3 text-sm text-gray-500">
                <span>📏 {route.distance}</span>
                <span>⏱ {route.duration}</span>
                {route.tags.includes("반려동물") && (
                  <span className="text-[#D78B42] font-bold">🐕 반려동물 가능</span>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* 콘텐츠 영역 (스크롤 확장으로 위치 유지) */}
        <div className="flex-1 overflow-y-auto p-5" style={{ scrollbarWidth: 'none' }}>
          
          <div className="mb-8">
            <p className="font-bold text-gray-800 mb-3 text-sm">경로 기상 정보</p>
            <div className="flex flex-col gap-2.5">
              {weatherStats.map((stat, i) => (
                <div key={i} className="flex items-center gap-3 rounded-xl px-4 py-3" style={{ background: stat.color }}>
                  <div className="w-8 h-8 rounded-full flex items-center justify-center bg-white shadow-sm">
                    {stat.icon}
                  </div>
                  <div className="flex-1">
                    <div className="text-xs font-bold text-gray-600 mb-0.5">{stat.label}</div>
                    <div className="text-sm font-black text-gray-800">{stat.value}</div>
                  </div>
                  <span className="text-[11px] text-gray-500 font-medium">{stat.sub}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <p className="font-bold text-gray-800 mb-4 text-sm">경로 상세 (무더위 쉼터)</p>
            <div className="relative pl-6 border-l-2 border-gray-200 ml-3 flex flex-col gap-6 pb-4">
              
              {/* 출발/도착 제거. 쉼터 경유지만 매핑 */}
              {(route.shelters ?? []).length > 0 ? (
                (route.shelters ?? []).map((shelter, idx) => (
                  <div key={idx} className="relative">
                    <div className="absolute -left-[31px] bg-white w-4 h-4 rounded-full flex items-center justify-center">
                       <MapPin size={16} color="#E74C3C" fill="#FCECEC" />
                    </div>
                    <p className="font-bold text-gray-700 text-sm">{shelter.name || '무더위 쉼터 경유'}</p>
                    <p className="text-xs text-gray-400">경유지</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">경유하는 쉼터가 없습니다.</p>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}