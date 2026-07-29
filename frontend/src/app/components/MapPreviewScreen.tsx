import { useEffect, useRef } from 'react';
import { ArrowLeft, MapPin, Flag } from 'lucide-react';
import type { RouteInfo } from '../App';

// TypeScript 오류 방지를 위한 Kakao Maps 전역 타입 선언
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

// 온도/열 지수에 따른 폴리라인 색상 반환 함수 (원본 코드 기반)
function heatScoreToColor(heatScore: number): string {
  if (heatScore < 20) return '#4A90D9'; // 쾌적
  if (heatScore < 22) return '#5DB87C'; // 보통
  if (heatScore < 24) return '#F5A623'; // 더움
  return '#E74C3C'; // 매우 더움
}

// 1. 카카오 지도를 그리는 컴포넌트를 완전히 분리 (재렌더링 충돌 방지)
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

        // 기존 오버레이 초기화
        overlaysRef.current.forEach((o: any) => o.setMap(null));
        overlaysRef.current = [];
        const bounds = new (window.kakao.maps as any).LatLngBounds();

        // 백엔드에서 받은 geojson 처리 (문자열일 경우 파싱)
        const geojson = typeof route.geojson === 'string' ? JSON.parse(route.geojson) : route.geojson;
        const features = geojson?.features || [];

        // 경로(Polyline) 그리기
        features.forEach((feature: any) => {
          const heatScore = feature.properties?.heat_score ?? 22;
          const path = feature.geometry.coordinates.map(([lng, lat]: [number, number]) => {
            const latlng = new window.kakao.maps.LatLng(lat, lng);
            bounds.extend(latlng);
            return latlng;
          });

          const polyline = new window.kakao.maps.Polyline({
            path,
            strokeWeight: 7,
            strokeColor: heatScoreToColor(heatScore),
            strokeOpacity: 0.9,
            strokeStyle: 'solid',
          });
          polyline.setMap(map);
          overlaysRef.current.push(polyline);
        });

        // 쉼터 마커(CustomOverlay) 그리기
        (route.shelters ?? []).forEach((shelter: any) => {
          const position = new window.kakao.maps.LatLng(shelter.lat, shelter.lng);
          bounds.extend(position);

          const content = `<div style="background:#FFD700;border:2px solid white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.2)">🏠</div>`;
          const overlay = new window.kakao.maps.CustomOverlay({ position, content, map, yAnchor: 1 });
          overlaysRef.current.push(overlay);
        });

        // 출발 / 도착 마커
        const startPos = new window.kakao.maps.LatLng(route.start[0], route.start[1]);
        const endPos = new window.kakao.maps.LatLng(route.end[0], route.end[1]);
        bounds.extend(startPos);
        bounds.extend(endPos);
        
        const startContent = `<div style="background:#3A9E66;border:2px solid white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3)">출</div>`;
        const endContent = `<div style="background:#E74C3C;border:2px solid white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3)">도</div>`;
        overlaysRef.current.push(new window.kakao.maps.CustomOverlay({ position: startPos, content: startContent, map, yAnchor: 1, zIndex: 3 }));
        overlaysRef.current.push(new window.kakao.maps.CustomOverlay({ position: endPos, content: endContent, map, yAnchor: 1, zIndex: 3 }));

        // 지도 영역 자동 맞춤
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

// 2. UI를 담당하는 메인 스크린 컴포넌트
interface MapPreviewScreenProps {
  route: RouteInfo;
  kakaoApiKey: string;
  onBack: () => void;
}

export default function MapPreviewScreen({ route, kakaoApiKey, onBack }: MapPreviewScreenProps) {
  return (
    <div className="w-full h-full relative overflow-hidden bg-[#E8F4F8]">
      
      {/* 백그라운드 카카오 맵 영역 (분리된 컴포넌트 사용) */}
      <div className="absolute inset-0 z-0">
        {kakaoApiKey ? (
           <KakaoMapComponent apiKey={kakaoApiKey} route={route} />
        ) : (
           <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 font-bold bg-[#E8F4F8]">
             <p>API 키를 불러올 수 없습니다.</p>
           </div>
        )}
      </div>

      {/* 상단 네비게이션 */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
        <button onClick={onBack} className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform">
          <ArrowLeft size={20} color="#333" />
        </button>
        <span className="text-lg font-bold text-gray-800 bg-white/90 px-3 py-1 rounded-full backdrop-blur-sm shadow-sm">
          경로 미리보기
        </span>
      </div>

      {/* 하단 경로 상세 정보 바텀 시트 */}
      <div 
        className="absolute bottom-0 left-0 right-0 bg-white rounded-t-3xl shadow-[0_-4px_20px_rgba(0,0,0,0.1)] flex flex-col"
        style={{ height: '45%', zIndex: 10 }}
      >
        <div className="p-5 border-b border-gray-100">
          <h3 className="text-lg font-bold text-gray-800 mb-1">{route.name}</h3>
          <div className="flex gap-3 text-sm text-gray-500">
            <span>📏 {route.distance}</span>
            <span>⏱ {route.duration}</span>
            {route.tags.includes("반려동물") && (
              <span className="text-[#D78B42] font-bold">🐕 반려동물 가능</span>
            )}
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5" style={{ scrollbarWidth: 'none' }}>
          <p className="font-bold text-gray-800 mb-4">경로 상세</p>
          
          <div className="relative pl-6 border-l-2 border-gray-200 ml-3 flex flex-col gap-6 pb-4">
            
            {/* 출발지 노드 */}
            <div className="relative">
              <div className="absolute -left-[31px] bg-white w-4 h-4 rounded-full flex items-center justify-center border-2 border-white shadow-sm">
                <div className="w-3 h-3 bg-[#3A9E66] rounded-full"></div>
              </div>
              <p className="font-bold text-gray-800 text-sm">출발</p>
              <p className="text-xs text-gray-400">0km · 00:00</p>
            </div>
            
            {/* 쉼터 등 중간 경유지 매핑 */}
            {(route.shelters ?? []).map((shelter, idx) => (
              <div key={idx} className="relative">
                <div className="absolute -left-[31px] bg-white w-4 h-4 rounded-full flex items-center justify-center">
                   <MapPin size={16} color="#E74C3C" fill="#FCECEC" />
                </div>
                <p className="font-bold text-gray-700 text-sm">{shelter.name || '무더위 쉼터 경유'}</p>
                <p className="text-xs text-gray-400">경유지</p>
              </div>
            ))}
            
            {/* 도착지 노드 */}
            <div className="relative">
              <div className="absolute -left-[31px] bg-white w-4 h-4 rounded-full flex items-center justify-center">
                <Flag size={16} color="#333" />
              </div>
              <p className="font-bold text-gray-800 text-sm">도착</p>
              <p className="text-xs text-gray-400">{route.distance} · {route.duration}</p>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}