import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import proj4 from 'proj4';
import type { RouteInfo } from '../App';

proj4.defs(
  'EPSG:5186',
  '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m +no_defs'
);

function heatScoreToColor(heatScore: number): string {
  if (heatScore < 20) return '#4A90D9';
  if (heatScore < 22) return '#5DB87C';
  if (heatScore < 24) return '#F5A623';
  return '#E74C3C';
}

interface RouteResultScreenProps {
  selectedTags: string[];
  onBack: () => void;
  onSelectRoute: (route: RouteInfo) => void;
  disableAnimation?: boolean;
}

function MiniMap({ route, apiKey }: { route: RouteInfo; apiKey: string }) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [isMapLoading, setIsMapLoading] = useState(true);

  useEffect(() => {
    if (!apiKey) return;

    const initThumbnailMap = () => {
      if (!mapRef.current || !window.kakao?.maps?.load) return;

      window.kakao.maps.load(() => {
        const mapOption = {
          center: new window.kakao.maps.LatLng(37.32, 127.12),
          level: 5,
          draggable: false,        // 드래그 금지
          scrollwheel: false,      // 휠 줌 금지
          disableDoubleClick: true,
          disableDoubleClickZoom: true,
          keyboardShortcuts: false,
        };
        
        const map = new window.kakao.maps.Map(mapRef.current!, mapOption);
        const bounds = new window.kakao.maps.LatLngBounds();

        const geojson = typeof route.geojson === 'string' ? JSON.parse(route.geojson) : (route.geojson || {});
        const features = geojson.features || [];

        // ⚠️ API 에러로 Mock 데이터(geojson: null)가 들어오면 선을 그리지 않고 종료
        if (features.length === 0) return;

        features.forEach((feature: any) => {
          const heatScore = feature.properties?.heat_score ?? 22;
          const strokeColor = heatScoreToColor(heatScore);
          
          const path = feature.geometry.coordinates.map(([x, y]: [number, number]) => {
            let lng = x, lat = y;
            if (x > 1000) { 
              [lng, lat] = proj4('EPSG:5186', 'EPSG:4326', [x, y]);
            }
            const latlng = new window.kakao.maps.LatLng(lat, lng);
            bounds.extend(latlng);
            return latlng;
          });

          const polyline = new window.kakao.maps.Polyline({
            path, 
            strokeWeight: 4,
            strokeColor: strokeColor,
            strokeOpacity: 0.9, 
            strokeStyle: 'solid',
          });
          polyline.setMap(map);
        });

        // 경로가 있을 때만 지도의 중심과 확대 축소를 경로에 맞춤
        if (!bounds.isEmpty()) {
          map.setBounds(bounds, 16, 16, 16, 16); 
        }
        setIsMapLoading(false);
      });
    };

    // ========================================================
    // 💡 카카오맵 SDK 스크립트 안전 주입 로직 (핵심 수정 사항)
    // ========================================================
    const scriptId = 'kakao-map-script';
    let script = document.getElementById(scriptId) as HTMLScriptElement;

    // 문서에 스크립트가 없다면 동적으로 생성해서 헤더에 추가
    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${encodeURIComponent(apiKey)}&autoload=false&libraries=services`;
      document.head.appendChild(script);
    }

    // 이미 로드가 완료된 상태인지 확인 후 실행, 아니면 load 이벤트 대기
    if (window.kakao && window.kakao.maps) {
      initThumbnailMap();
    } else {
      script.addEventListener('load', initThumbnailMap);
    }

    // 컴포넌트 언마운트 시 이벤트 리스너 정리
    return () => {
      if (script) {
        script.removeEventListener('load', initThumbnailMap);
      }
    };
  }, [route, apiKey]);

  return (
    <div className="relative w-full h-full pointer-events-none">
      {isMapLoading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-[#F5F7F5]">
          <Loader2 size={24} className="animate-spin text-[#3B82F6]" />
        </div>
      )}
      <div ref={mapRef} className="w-full h-full" />
    </div>
  );
}

export default function RouteResultScreen({ selectedTags, onBack, onSelectRoute, disableAnimation }: RouteResultScreenProps) {
  const [routes, setRoutes] = useState<RouteInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const kakaoApiKey = (import.meta as any).env?.VITE_KAKAO_MAPS_API_KEY ?? '';
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showTopArrow, setShowTopArrow] = useState(false);
  const [showBottomArrow, setShowBottomArrow] = useState(false);

  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      setShowTopArrow(scrollTop > 10); // 위로 스크롤 가능하면 위 화살표
      setShowBottomArrow(Math.ceil(scrollTop + clientHeight) < scrollHeight - 10); // 밑에 내용이 남았으면 아래 화살표
    }
  };

  useEffect(() => {
    setTimeout(handleScroll, 100); 
  }, [routes, isLoading]);

  const apiItemToRouteInfo = (item: any, index: number): RouteInfo => {
    const features = item.geojson?.features ?? [];
    const firstCoord = features[0]?.geometry?.coordinates?.[0] ?? [127.1, 37.33];
    const lastFeature = features[features.length - 1];
    const lastCoords = lastFeature?.geometry?.coordinates ?? [[127.1, 37.33]];
    const lastCoord = lastCoords[lastCoords.length - 1];
    
    const rankColors = ["#3B82F6", "#60A5FA", "#93C5FD"];

    return {
      id: item.id || index,
      rank: index + 1,
      rankColor: rankColors[index] || "#9BB5D0",
      name: item.name || `추천 코스 ${index + 1}`,
      distance: `${(item.distance_m / 1000).toFixed(1)}km`,
      duration: `${Math.round(item.distance_m / 1000 * 15)}분`,
      tags: item.tags || ['평탄'],
      start: [firstCoord[1], firstCoord[0]] as [number, number],
      end: [lastCoord[1], lastCoord[0]] as [number, number],
      geojson: item.geojson,
      shelters: item.shelters ?? [],
    };
  };

  useEffect(() => {
    const fetchRoutes = async () => {
      // 임시 Mock 로직 (기존 기능 유지)
      setIsLoading(true);
      try {
        const res = await fetch('/routes');
        if (res.ok) {
          const data = await res.json();
          setRoutes(data.slice(0, 3).map((item: any, i: number) => apiItemToRouteInfo(item, i)));
        } else {
          setRoutes([
            { id: 1, rank: 1, name: "시민한길 A코스", distance: "2.1km", duration: "30분", tags: ["시민한길", "30분", "반려동물"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#3B82F6" },
            { id: 2, rank: 2, name: "시민한길 B코스", distance: "3.1km", duration: "38분", tags: ["시민한길", "38분"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#3B82F6" },
            { id: 3, rank: 3, name: "올림픽공원 산책로", distance: "2.8km", duration: "35분", tags: ["올림픽공원"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#3B82F6" },
          ]);
        }
      } catch (err) {
        console.error("Failed to fetch routes, using mock data.", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchRoutes();
  }, [selectedTags]);

  return (
    <div className={`w-full h-full bg-[#FFFFFF] pt-8 px-6 pb-6 flex flex-col relative ${disableAnimation ? '' : 'animate-[fadeIn_0.2s_ease-out]'}`}>
      
      <style>{`
        @keyframes fadeIn {
          0% { opacity: 0; }
          100% { opacity: 1; }
        }
        @keyframes slideInFromBottom {
          0% { transform: translateY(20px); opacity: 0; }
          100% { transform: translateY(0); opacity: 1; }
        }
      `}</style>
      
      <div className="z-10 flex items-start gap-4 mb-8 mt-2">
        <button onClick={onBack} className="p-1 active:scale-90 transition-transform mt-0.5">
          <ArrowLeft size={30} color="#333" />
        </button>
        <div>
          <h2 className="text-[26px] font-black text-gray-800">경로 추천 완료!</h2>
          <p className="text-[15px] font-bold text-gray-400 mt-1">당신을 위한 {routes.length}가지 경로</p>
        </div>
      </div>

      <div className="bg-[#EBF5FF] p-7 rounded-3xl w-full text-center mb-8 shadow-sm">
        <p className="text-[22px] font-black text-[#3B82F6] mb-4">경로 추천이 완료되었어요!</p>
        {selectedTags.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2.5 font-bold text-gray-700 text-[16px]">
            {selectedTags.map((tag, idx) => (
              <span key={idx}>#{tag}</span>
            ))}
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-5 pb-6 overflow-x-hidden" style={{ scrollbarWidth: 'none' }}>
        {showTopArrow && (
          <div className="absolute top-[260px] left-0 right-0 flex justify-center z-20 pointer-events-none pt-2">
            <div className="bg-white/95 rounded-full p-1 shadow-md animate-bounce border border-gray-100">
              <ChevronUp size={32} color="#3B82F6" />
            </div>
          </div>
        )}
      <div 
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto flex flex-col gap-6 pb-6 overflow-x-hidden relative" 
        style={{ scrollbarWidth: 'none' }}
      >
        {isLoading ? (
          <div className="flex justify-center items-center h-full text-[#3B82F6] text-[20px] font-bold">경로 불러오는 중...</div>
        ) : (
         routes.map((route, i) => (
             <button
               key={route.id}
               onClick={() => onSelectRoute(route)}
               style={disableAnimation ? {} : {
                 animation: `slideInFromBottom 0.2s ease-out forwards`,
                 animationDelay: `${i * 0.08}s`,
                 opacity: 0,
               }}
               // 💡 1. flex-col로 변경하여 위아래 레이아웃으로 나눔
               className={`bg-white border-[1.5px] border-gray-100 rounded-[28px] p-6 text-left active:scale-[0.98] transition-transform shadow-[0_4px_20px_rgba(0,0,0,0.04)] flex flex-col gap-4 ${disableAnimation ? 'opacity-100' : ''}`}
             >
               {/* 💡 2. 상단 (Row 1): 순위 동그라미 + 경로 이름 (가로 공간을 넓게 씀) */}
               <div className="flex items-center gap-3 w-full">
                 <div className="w-12 h-12 rounded-full bg-[#3B82F6] text-white flex items-center justify-center font-black text-[22px] shrink-0 shadow-sm">
                   {route.rank}
                 </div>
                 <p className="text-[24px] font-black text-gray-800 break-keep leading-tight flex-1">
                   {route.name}
                 </p>
               </div>

               {/* 💡 3. 하단 (Row 2): [거리, 시간] 정보 + 미니맵 */}
               <div className="flex justify-between items-end w-full pl-1 mt-1">
                 {/* 좌측: 세로로 나열된 거리와 시간 */}
                 <div className="flex flex-col gap-2.5">
                   <span className="flex items-center gap-2 text-[22px] text-gray-500 font-bold">
                     📏 {route.distance}
                   </span>
                   <span className="flex items-center gap-2 text-[22px] text-gray-500 font-bold">
                     ⏱ {route.duration}
                   </span>
                 </div>
                 
                 {/* 우측: 미니맵 */}
                 <div className="w-[84px] h-[84px] bg-[#F5F7F5] rounded-2xl overflow-hidden shrink-0 shadow-inner border border-gray-100">
                   <MiniMap route={route} apiKey={kakaoApiKey} />
                 </div>
               </div>
             </button>
           ))
        )}
      </div>
      {showBottomArrow && (
        <div className="absolute bottom-6 left-0 right-0 flex justify-center z-20 pointer-events-none">
          <div className="bg-[#3B82F6]/90 rounded-full p-2 shadow-md animate-bounce">
            <ChevronDown size={32} color="white" />
          </div>
        </div>
      )}
      </div>
    </div>
  );
}