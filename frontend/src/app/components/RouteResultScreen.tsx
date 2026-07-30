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
    
    const rankColors = ["#3A9E66", "#4A90D9", "#F5A623"];

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
          // 총 3개만 추천하도록 slice 설정
          setRoutes(data.slice(0, 3).map((item: any, i: number) => apiItemToRouteInfo(item, i)));
        } else {
          setRoutes([
            { id: 1, rank: 1, name: "시민한길 A코스", distance: "2.1km", duration: "30분", tags: ["시원한길", "반려동물"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#3A9E66" },
            { id: 2, rank: 2, name: "강가 그늘길 코스", distance: "2.3km", duration: "32분", tags: ["그늘", "뷰 좋음"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#4A90D9" },
            { id: 3, rank: 3, name: "숲속 산책길 코스", distance: "1.9km", duration: "28분", tags: ["잔디", "그늘"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#F5A623" },
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

  const getRankText = (index: number) => {
    if (index === 0) return "가장 추천하는 경로";
    if (index === 1) return "2번째 경로";
    if (index === 2) return "3번째 경로";
    return `${index + 1}번째 경로`;
  };

  return (
    <div className={`w-full h-full bg-[#F5F7F5] pt-4 px-4 pb-6 flex flex-col relative ${disableAnimation ? '' : 'animate-[fadeIn_0.2s_ease-out]'}`}>
      
      {/* [수정] 경로 카드 슬라이드 애니메이션 Keyframes 추가 */}
      <style>{`
        @keyframes fadeIn {
          0% { opacity: 0; }
          100% { opacity: 1; }
        }
        @keyframes slideInFromCenter {
          0% { transform: translateX(50vw); opacity: 0; }
          100% { transform: translateX(0); opacity: 1; }
        }
      `}</style>
      
      <div className="absolute top-4 left-4 z-10 flex items-center gap-3">
        <button onClick={onBack} className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform">
          <ArrowLeft size={24} color="#333" />
        </button>
        <span className="text-xl font-bold text-gray-800 bg-white/90 px-4 py-2 rounded-full backdrop-blur-sm shadow-sm">
          경로 추천 완료
        </span>
      </div>

      <div className="mt-16"></div>

      <div className="bg-[#E8F5E9] p-5 rounded-2xl w-full text-center mb-8 shadow-sm">
        <p className="text-lg font-black text-gray-800">🎉 경로 추천이 완료되었어요!</p>
        <p className="text-sm text-gray-600 mt-2 font-medium">마음에 드는 경로를 선택해 미리보기를 확인해보세요</p>
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-5 pb-6 overflow-x-hidden" style={{ scrollbarWidth: 'none' }}>
        {isLoading ? (
          <div className="flex justify-center items-center h-full text-gray-500 text-xl font-bold">경로 불러오는 중...</div>
        ) : (
         routes.map((route, i) => (
            <button
              key={route.id}
              onClick={() => onSelectRoute(route)}
              style={disableAnimation ? {} : {
                animation: `slideInFromCenter 0.13s ease-out forwards`,
                animationDelay: `${i * 0.05}s`,
                opacity: 0,
              }}
              className={`bg-white border-2 border-[#E8F5E9] rounded-3xl p-6 text-left active:scale-[0.98] transition-transform shadow-md flex items-center justify-between ${disableAnimation ? 'opacity-100' : ''}`}
            >
              <div>
                <p className="text-lg font-black mb-2" style={{ color: route.rankColor }}>{getRankText(i)}</p>
                <p className="text-3xl font-black text-gray-800 mb-4">{route.name}</p>
                <div className="flex gap-4 text-xl text-gray-600 font-bold">
                  <span>⏱ {route.duration}</span>
                  <span>📏 {route.distance}</span>
                </div>
              </div>
              <ArrowLeft size={28} color="#9BB5D0" className="transform rotate-180" />
            </button>
          ))
        )}
      </div>
    </div>
  );
}