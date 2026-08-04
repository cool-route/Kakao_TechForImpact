import { useState, useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import type { RouteInfo } from '../App';

interface RouteResultScreenProps {
  selectedTags: string[];
  onBack: () => void;
  onSelectRoute: (route: RouteInfo) => void;
  disableAnimation?: boolean;
}

export default function RouteResultScreen({ selectedTags, onBack, onSelectRoute, disableAnimation }: RouteResultScreenProps) {
  const [routes, setRoutes] = useState<RouteInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

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

  // =====================================================================
  // [기능 추가 예정] 3. 알고리즘 기반 경로 추천 (POST /recommend)
  // 확정된 프리셋 배열을 백엔드로 전송하여 Top 3 경로를 반환받습니다.
  // =====================================================================
  /*
  const fetchRecommendedRoutes = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tags: selectedTags })
      });
      const data = await res.json();
      
      // Top 3 경로만 가져옵니다.
      setRoutes(data.slice(0, 3).map((item: any, i: number) => apiItemToRouteInfo(item, i)));
    } catch (err) {
      console.error("추천 경로 로드 실패", err);
    } finally {
      setIsLoading(false);
    }
  };
  */

  useEffect(() => {
    const fetchRoutes = async () => {
      // fetchRecommendedRoutes(); // API 연동 시 주석 해제 후 아래 기존 로직 삭제

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
              className={`bg-white border-[1.5px] border-gray-100 rounded-[28px] p-6 text-left active:scale-[0.98] transition-transform shadow-[0_4px_20px_rgba(0,0,0,0.04)] flex items-center gap-5 ${disableAnimation ? 'opacity-100' : ''}`}
            >
              <div className="w-10 h-10 rounded-full bg-[#3B82F6] text-white flex items-center justify-center font-bold text-[18px] shrink-0 shadow-sm">
                {route.rank}
              </div>
              <div className="flex-1">
                <p className="text-[24px] font-black text-gray-800 mb-2.5">{route.name}</p>
                <div className="flex gap-4 text-[16px] text-gray-500 font-bold">
                  <span className="flex items-center gap-1.5">📏 {route.distance}</span>
                  <span className="flex items-center gap-1.5">⏱ {route.duration}</span>
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}