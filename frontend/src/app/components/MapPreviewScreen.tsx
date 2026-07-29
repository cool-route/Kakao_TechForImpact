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

// 온도/열 지수에 따른 폴리라인 색상 반환 함수 (참고 코드 반영)
function heatScoreToColor(heatScore: number): string {
  if (heatScore < 20) return '#4A90D9'; // 쾌적 (파랑)
  if (heatScore < 22) return '#5DB87C'; // 보통 (초록)
  if (heatScore < 24) return '#F5A623'; // 약간 더움 (주황)
  return '#E74C3C'; // 더움 (빨강)
}

function KakaoMapComponent({ apiKey, route }: { apiKey: string; route: RouteInfo }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const overlaysRef = useRef<any[]>([]);

  useEffect(() => {
    if (!apiKey || !mapRef.current) {
      console.warn("Kakao API Key가 누락되었거나 지도를 표시할 요소를 찾을 수 없습니다.");
      return;
    }

    mapRef.current.style.width = '100%';
    mapRef.current.style.height = '100%';

    const existingScript = document.querySelector(`script[src*="dapi.kakao.com"]`);

    function initMap() {
      if (!mapRef.current || !window.kakao || !window.kakao.maps) return;
      
      window.kakao.maps.load(() => {
        // 초기 중심 좌표 설정
        const initialCenter = new window.kakao.maps.LatLng(route.start[0], route.start[1]);
        const map = new window.kakao.maps.Map(mapRef.current!, { center: initialCenter, level: 5 });
        mapInstanceRef.current = map;

        // 기존 오버레이 제거
        overlaysRef.current.forEach(o => o.setMap(null));
        overlaysRef.current = [];
        
        const bounds = new window.kakao.maps.LatLngBounds();

        // 1. GeoJSON을 기반으로 선(Polyline) 그리기 및 색상 적용
        (route.geojson?.features ?? []).forEach((feature: any) => {
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

        // 2. 무더위 쉼터 커스텀 오버레이 마커 그리기
        (route.shelters ?? []).forEach((shelter: any) => {
          const position = new window.kakao.maps.LatLng(shelter.lat, shelter.lng);
          bounds.extend(position);
          
          const content = `<div style="background:#FFD700;border:2px solid white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.2)">🏠</div>`;
          const overlay = new window.kakao.maps.CustomOverlay({ position, content, map, yAnchor: 1 });
          overlaysRef.current.push(overlay);
        });

        // 3. 경로가 모두 보이도록 지도 영역 자동 조절
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
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(apiKey)}&autoload=false`;
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
  return (
    <div className="w-full h-full relative overflow-hidden bg-[#E8F4F8]">
      
      {/* 1. 백그라운드 카카오 맵 영역 */}
      <div className="absolute inset-0 z-0">
        {kakaoApiKey ? (
           <KakaoMapComponent apiKey={kakaoApiKey} route={route} />
        ) : (
           <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 font-bold bg-[#E8F4F8]">
             <p>API 키를 불러올 수 없습니다.</p>
             <p className="text-xs font-normal mt-2">frontend/.env 파일을 확인해주세요.</p>
           </div>
        )}
      </div>

      {/* 2. 상단 네비게이션 */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
        <button onClick={onBack} className="w-10 h-10 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform">
          <ArrowLeft size={20} color="#333" />
        </button>
        <span className="text-lg font-bold text-gray-800 bg-white/90 px-3 py-1 rounded-full backdrop-blur-sm shadow-sm">
          경로 미리보기
        </span>
      </div>

      {/* 3. 하단 경로 상세 정보 Бат텀 시트 */}
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
          
          <div className="relative pl-6 border-l-2 border-gray-200 ml-3 flex flex-col gap-6">
            <div className="relative">
              <div className="absolute -left-[31px] bg-white w-4 h-4 rounded-full flex items-center justify-center border-2 border-white shadow-sm">
                <div className="w-3 h-3 bg-[#3A9E66] rounded-full"></div>
              </div>
              <p className="font-bold text-gray-800 text-sm">출발지 (API 연동 예정)</p>
              <p className="text-xs text-gray-400">0km · 00:00</p>
            </div>
            
            {(route.shelters ?? []).length > 0 && (
              <div className="relative">
                <div className="absolute -left-[31px] bg-white w-4 h-4 rounded-full flex items-center justify-center">
                   <MapPin size={16} color="#E74C3C" fill="#FCECEC" />
                </div>
                <p className="font-bold text-gray-700 text-sm">무더위 쉼터 경유</p>
                <p className="text-xs text-gray-400">{route.shelters.length}개 쉼터 경유</p>
              </div>
            )}
            
            <div className="relative">
              <div className="absolute -left-[31px] bg-white w-4 h-4 rounded-full flex items-center justify-center">
                <Flag size={16} color="#333" />
              </div>
              <p className="font-bold text-gray-800 text-sm">도착지 (API 연동 예정)</p>
              <p className="text-xs text-gray-400">{route.distance} · {route.duration}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}