import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, Navigation, Thermometer, Wind, Sun, TreePine, ChevronUp, ChevronDown, MapPin } from 'lucide-react';
import type { RouteInfo } from './RouteListScreen';

declare global {
  interface Window {
    kakao: {
      maps: {
        load: (callback: () => void) => void;
        Map: new (container: HTMLElement, options: KakaoMapOptions) => KakaoMap;
        LatLng: new (lat: number, lng: number) => KakaoLatLng;
        Polyline: new (options: KakaoPolylineOptions) => KakaoPolyline;
        Marker: new (options: KakaoMarkerOptions) => KakaoMarker;
        MarkerImage: new (src: string, size: KakaoSize) => KakaoMarkerImage;
        Size: new (w: number, h: number) => KakaoSize;
        CustomOverlay: new (options: KakaoOverlayOptions) => KakaoCustomOverlay;
      };
    };
  }
}

interface KakaoMapOptions { center: KakaoLatLng; level: number; }
interface KakaoMap { setCenter: (latlng: KakaoLatLng) => void; }
interface KakaoLatLng { getLat: () => number; getLng: () => number; }
interface KakaoPolylineOptions { path: KakaoLatLng[]; strokeWeight: number; strokeColor: string; strokeOpacity: number; strokeStyle: string; }
interface KakaoPolyline { setMap: (map: KakaoMap | null) => void; }
interface KakaoMarkerOptions { position: KakaoLatLng; map: KakaoMap; image?: KakaoMarkerImage; }
interface KakaoMarker { setMap: (map: KakaoMap | null) => void; }
interface KakaoMarkerImage {}
interface KakaoSize {}
interface KakaoOverlayOptions { position: KakaoLatLng; content: string; map: KakaoMap; yAnchor?: number; }
interface KakaoCustomOverlay { setMap: (map: KakaoMap | null) => void; }

// Route coordinates for 수지구 area (광교산 그늘길 approximation)
const ROUTE_SEGMENTS = [
  // Segment 1: Cool (blue)
  { color: '#4A90D9', coords: [[37.3220, 127.0960], [37.3210, 127.0930], [37.3195, 127.0900]] },
  // Segment 2: Comfortable (green)
  { color: '#5DB87C', coords: [[37.3195, 127.0900], [37.3180, 127.0875], [37.3165, 127.0850]] },
  // Segment 3: Warm (orange)
  { color: '#F5A623', coords: [[37.3165, 127.0850], [37.3150, 127.0820], [37.3140, 127.0800]] },
  // Segment 4: Cool again (blue)
  { color: '#4A90D9', coords: [[37.3140, 127.0800], [37.3125, 127.0780], [37.3110, 127.0760]] },
];

const SHELTER_MARKERS = [
  { lat: 37.3175, lng: 127.0870, name: '수지구청 무더위쉼터' },
  { lat: 37.3145, lng: 127.0815, name: '광교산 입구 쉼터' },
  { lat: 37.3120, lng: 127.0770, name: '근린공원 쉼터' },
];

function MockMap({ route }: { route: RouteInfo }) {
  return (
    <div className="w-full h-full relative overflow-hidden" style={{ background: '#E8F4F8' }}>
      {/* Mock map grid */}
      <svg width="100%" height="100%" style={{ position: 'absolute', top: 0, left: 0 }}>
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#D0E8F0" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
        {/* Roads */}
        <line x1="20%" y1="0" x2="20%" y2="100%" stroke="#C8DDE8" strokeWidth="6" />
        <line x1="60%" y1="0" x2="60%" y2="100%" stroke="#C8DDE8" strokeWidth="10" />
        <line x1="0" y1="30%" x2="100%" y2="30%" stroke="#C8DDE8" strokeWidth="8" />
        <line x1="0" y1="65%" x2="100%" y2="65%" stroke="#C8DDE8" strokeWidth="6" />
        <line x1="80%" y1="0" x2="80%" y2="100%" stroke="#C8DDE8" strokeWidth="4" />
        {/* Building blocks */}
        <rect x="25%" y="5%" width="30%" height="20%" rx="4" fill="#D4EAF2" />
        <rect x="65%" y="5%" width="12%" height="22%" rx="4" fill="#D4EAF2" />
        <rect x="25%" y="36%" width="30%" height="25%" rx="4" fill="#D4EAF2" />
        <rect x="65%" y="36%" width="12%" height="25%" rx="4" fill="#D4EAF2" />
        <rect x="2%" y="5%" width="15%" height="22%" rx="4" fill="#D4EAF2" />
        <rect x="2%" y="36%" width="15%" height="25%" rx="4" fill="#D4EAF2" />
        {/* Green park area */}
        <ellipse cx="40%" cy="75%" rx="20%" ry="12%" fill="#B8DFB0" opacity="0.6" />
        <text x="40%" y="75%" textAnchor="middle" dominantBaseline="middle" fontSize="11" fill="#4A8A42">광교산 근린공원</text>
        {/* Route polyline - simulated */}
        <polyline
          points="85%,15% 75%,25% 65%,38% 55%,50% 45%,58% 35%,68% 25%,75%"
          fill="none"
          stroke="#4A90D9"
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray="0"
          opacity="0.9"
        />
        <polyline
          points="65%,38% 55%,50% 45%,58%"
          fill="none"
          stroke="#5DB87C"
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.9"
        />
        <polyline
          points="45%,58% 35%,68%"
          fill="none"
          stroke="#F5A623"
          strokeWidth="5"
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity="0.9"
        />
        {/* Start marker */}
        <circle cx="85%" cy="15%" r="9" fill="#4A90D9" />
        <circle cx="85%" cy="15%" r="5" fill="white" />
        {/* End marker */}
        <circle cx="25%" cy="75%" r="9" fill="#E74C3C" />
        <circle cx="25%" cy="75%" r="5" fill="white" />
        {/* Shelter markers */}
        <circle cx="65%" cy="38%" r="8" fill="#FFD700" stroke="white" strokeWidth="2" />
        <text x="65%" y="38%" textAnchor="middle" dominantBaseline="middle" fontSize="8">🏠</text>
        <circle cx="45%" cy="58%" r="8" fill="#FFD700" stroke="white" strokeWidth="2" />
        <text x="45%" y="58%" textAnchor="middle" dominantBaseline="middle" fontSize="8">🏠</text>
      </svg>
      {/* Shelter label */}
      <div className="absolute rounded-xl px-2 py-1" style={{ top: '34%', left: '62%', background: 'rgba(255,215,0,0.9)', fontSize: '10px', fontWeight: '600', color: '#7B5800', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}>
        무더위쉼터
      </div>
      {/* Legend */}
      <div className="absolute bottom-4 right-3 rounded-xl p-2 flex flex-col gap-1" style={{ background: 'rgba(255,255,255,0.9)', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        {[['#4A90D9', '쾌적'], ['#5DB87C', '보통'], ['#F5A623', '더움']].map(([color, label]) => (
          <div key={label} className="flex items-center gap-1.5">
            <div style={{ width: '16px', height: '4px', background: color, borderRadius: '2px' }} />
            <span style={{ fontSize: '10px', color: '#555' }}>{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function KakaoMapComponent({ apiKey, route }: { apiKey: string; route: RouteInfo }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<KakaoMap | null>(null);
  const overlaysRef = useRef<(KakaoPolyline | KakaoMarker | KakaoCustomOverlay)[]>([]);

  useEffect(() => {
    if (!apiKey || !mapRef.current) return;

    const existingScript = document.querySelector(`script[src*="dapi.kakao.com"]`);

    function initMap() {
      if (!mapRef.current) return;
      window.kakao.maps.load(() => {
        const center = new window.kakao.maps.LatLng(37.3165, 127.0850);
        const map = new window.kakao.maps.Map(mapRef.current!, { center, level: 5 });
        mapInstanceRef.current = map;

        overlaysRef.current.forEach(o => o.setMap(null));
        overlaysRef.current = [];

        // Draw route segments
        ROUTE_SEGMENTS.forEach(seg => {
          const path = seg.coords.map(([lat, lng]) => new window.kakao.maps.LatLng(lat, lng));
          const polyline = new window.kakao.maps.Polyline({
            path,
            strokeWeight: 7,
            strokeColor: seg.color,
            strokeOpacity: 0.9,
            strokeStyle: 'solid',
          });
          polyline.setMap(map);
          overlaysRef.current.push(polyline);
        });

        // Shelter markers
        SHELTER_MARKERS.forEach(shelter => {
          const position = new window.kakao.maps.LatLng(shelter.lat, shelter.lng);
          const content = `<div style="background:#FFD700;border:2px solid white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.2)">🏠</div>`;
          const overlay = new window.kakao.maps.CustomOverlay({ position, content, map, yAnchor: 1 });
          overlaysRef.current.push(overlay);
        });

        // Start/End markers
        const startPos = new window.kakao.maps.LatLng(37.3220, 127.0960);
        const endPos = new window.kakao.maps.LatLng(37.3110, 127.0760);
        const startContent = `<div style="background:#4A90D9;border:2px solid white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3)">출</div>`;
        const endContent = `<div style="background:#E74C3C;border:2px solid white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:white;font-size:11px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3)">도</div>`;
        overlaysRef.current.push(new window.kakao.maps.CustomOverlay({ position: startPos, content: startContent, map, yAnchor: 1 }));
        overlaysRef.current.push(new window.kakao.maps.CustomOverlay({ position: endPos, content: endContent, map, yAnchor: 1 }));
      });
    }

    if (existingScript) {
      if (window.kakao?.maps) {
        initMap();
      } else {
        existingScript.addEventListener('load', initMap);
      }
      return;
    }

    const script = document.createElement('script');
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${apiKey}&autoload=false`;
    script.onload = initMap;
    script.onerror = () => console.error('Kakao Maps 로드 실패. API 키를 확인해주세요.');
    document.head.appendChild(script);
  }, [apiKey]);

  return <div ref={mapRef} className="w-full h-full" />;
}

interface MapDetailScreenProps {
  route: RouteInfo;
  onBack: () => void;
  kakaoApiKey: string;
}

export function MapDetailScreen({ route, onBack, kakaoApiKey }: MapDetailScreenProps) {
  const [sheetExpanded, setSheetExpanded] = useState(false);

  const weatherStats = [
    { icon: <Thermometer size={16} color="#E74C3C" />, label: '체감 온도', value: '33.2°C', sub: '실제보다 4.6°C 높음', color: '#FFE8E8' },
    { icon: <Sun size={16} color="#F5A623" />, label: '지면 온도', value: '41.5°C', sub: '아스팔트 노출 최소화', color: '#FFF5E8' },
    { icon: <TreePine size={16} color="#5DB87C" />, label: '그림자 비율', value: `${route.shadeRatio}%`, sub: '경로의 대부분이 그늘', color: '#E8F8EF' },
    { icon: <Wind size={16} color="#4A90D9" />, label: '풍속', value: '2.3 m/s', sub: '약한 바람, 체감 쾌적', color: '#E8F4FF' },
  ];

  return (
    <div className="w-full h-full flex flex-col relative overflow-hidden">
      {/* Map */}
      <div className="absolute inset-0">
        {kakaoApiKey ? (
          <KakaoMapComponent apiKey={kakaoApiKey} route={route} />
        ) : (
          <MockMap route={route} />
        )}
      </div>

      {/* Top bar */}
      <div className="relative z-10 flex items-center gap-3 px-4 pt-12 pb-3">
        <button
          onClick={onBack}
          className="w-10 h-10 rounded-full flex items-center justify-center active:scale-90 transition-transform"
          style={{ background: 'rgba(255,255,255,0.92)', boxShadow: '0 2px 12px rgba(0,0,0,0.15)' }}
        >
          <ArrowLeft size={18} color="#1A3A5C" strokeWidth={2.5} />
        </button>
        <div className="flex-1 rounded-2xl px-4 py-2.5 flex items-center gap-2" style={{ background: 'rgba(255,255,255,0.92)', boxShadow: '0 2px 12px rgba(0,0,0,0.12)' }}>
          <div className="w-2.5 h-2.5 rounded-full" style={{ background: route.color }} />
          <span style={{ fontSize: '15px', fontWeight: '700', color: '#1A3A5C' }}>{route.name}</span>
          <span className="ml-auto rounded-full px-2 py-0.5" style={{ fontSize: '11px', fontWeight: '600', background: `${route.color}18`, color: route.color }}>
            쾌적도 {route.heatScore}점
          </span>
        </div>
      </div>

      {/* Shelter legend */}
      <div className="relative z-10 mx-4">
        <div className="rounded-xl px-3 py-2 flex items-center gap-2 w-fit" style={{ background: 'rgba(255,255,255,0.92)', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <span style={{ fontSize: '14px' }}>🏠</span>
          <span style={{ fontSize: '12px', fontWeight: '600', color: '#7B5800' }}>무더위 쉼터 {SHELTER_MARKERS.length}개</span>
        </div>
      </div>

      {/* Bottom Sheet */}
      <div
        className="absolute bottom-0 left-0 right-0 z-20 rounded-t-3xl flex flex-col transition-all duration-300"
        style={{
          background: 'white',
          boxShadow: '0 -4px 30px rgba(0,0,0,0.15)',
          maxHeight: sheetExpanded ? '75%' : '42%',
        }}
      >
        {/* Sheet handle */}
        <button
          onClick={() => setSheetExpanded(v => !v)}
          className="w-full flex flex-col items-center pt-3 pb-2 active:opacity-70 transition-opacity"
        >
          <div className="w-10 h-1 rounded-full" style={{ background: '#D0D8E4' }} />
          <div className="flex items-center gap-1 mt-1.5">
            <span style={{ fontSize: '12px', color: '#9BB5D0' }}>{sheetExpanded ? '접기' : '자세히 보기'}</span>
            {sheetExpanded ? <ChevronDown size={12} color="#9BB5D0" /> : <ChevronUp size={12} color="#9BB5D0" />}
          </div>
        </button>

        {/* Route summary */}
        <div className="px-5 pb-3 flex items-center justify-between border-b" style={{ borderColor: '#F0F5FA' }}>
          <div>
            <div style={{ fontSize: '18px', fontWeight: '700', color: '#1A3A5C' }}>{route.name}</div>
            <div className="flex items-center gap-1 mt-0.5">
              <MapPin size={12} color="#9BB5D0" />
              <span style={{ fontSize: '12px', color: '#9BB5D0' }}>{route.subtitle}</span>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="text-center">
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#4A90D9' }}>{route.distance}</div>
              <div style={{ fontSize: '10px', color: '#9BB5D0' }}>거리</div>
            </div>
            <div style={{ width: '1px', background: '#E8EFF5' }} />
            <div className="text-center">
              <div style={{ fontSize: '16px', fontWeight: '700', color: '#5DB87C' }}>{route.duration}</div>
              <div style={{ fontSize: '10px', color: '#9BB5D0' }}>시간</div>
            </div>
          </div>
        </div>

        {/* Weather stats */}
        <div className="flex-1 overflow-y-auto px-5 py-3 flex flex-col gap-2.5" style={{ scrollbarWidth: 'none' }}>
          <div style={{ fontSize: '13px', fontWeight: '600', color: '#9BB5D0', marginBottom: '2px' }}>경로 기상 정보</div>
          {weatherStats.map((stat, i) => (
            <div
              key={i}
              className="flex items-center gap-3 rounded-xl px-4 py-3"
              style={{ background: stat.color }}
            >
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'white' }}>
                {stat.icon}
              </div>
              <div className="flex-1">
                <div style={{ fontSize: '12px', color: '#8AA0B8' }}>{stat.label}</div>
                <div style={{ fontSize: '15px', fontWeight: '700', color: '#1A3A5C' }}>{stat.value}</div>
              </div>
              <span style={{ fontSize: '11px', color: '#8AA0B8' }}>{stat.sub}</span>
            </div>
          ))}
        </div>

        {/* CTA Button */}
        <div className="px-5 pb-6 pt-2">
          <button
            className="w-full rounded-2xl py-4 flex items-center justify-center gap-2.5 active:scale-[0.98] transition-transform"
            style={{ background: `linear-gradient(135deg, ${route.color}, ${route.color}CC)`, boxShadow: `0 6px 24px ${route.color}55` }}
          >
            <Navigation size={18} color="white" strokeWidth={2.5} />
            <span style={{ fontSize: '17px', fontWeight: '700', color: 'white' }}>경로 생성하기</span>
          </button>
        </div>
      </div>
    </div>
  );
}
