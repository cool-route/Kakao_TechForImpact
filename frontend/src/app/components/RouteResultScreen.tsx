import { useState, useEffect } from 'react';
import { ArrowLeft } from 'lucide-react';
import type { RouteInfo } from '../App';

interface RouteResultScreenProps {
  selectedTags: string[]; // SearchFlow에서 전달받은 최종 확정 프리셋
  onBack: () => void;
  onSelectRoute: (route: RouteInfo) => void;
}

export default function RouteResultScreen({ selectedTags, onBack, onSelectRoute }: RouteResultScreenProps) {
  const [routes, setRoutes] = useState<RouteInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const apiItemToRouteInfo = (item: any, index: number): RouteInfo => {
    const features = item.geojson?.features ?? [];
    const firstCoord = features[0]?.geometry?.coordinates?.[0] ?? [127.1, 37.33];
    const lastFeature = features[features.length - 1];
    const lastCoords = lastFeature?.geometry?.coordinates ?? [[127.1, 37.33]];
    const lastCoord = lastCoords[lastCoords.length - 1];
    
    const rankColors = ["#3A9E66", "#4A90D9", "#F5A623", "#9B59B6"];

    return {
      id: item.id || index,
      rank: index + 1,
      rankColor: rankColors[index] || "#9BB5D0",
      name: item.name || `추천 코스 ${index + 1}`,
      distance: `${(item.distance_m / 1000).toFixed(1)}km`,
      duration: `${Math.round(item.distance_m / 1000 * 15)}분`,
      tags: item.tags || ['평탄'], // 백엔드 추천 근거 태그 매핑
      start: [firstCoord[1], firstCoord[0]] as [number, number],
      end: [lastCoord[1], lastCoord[0]] as [number, number],
      geojson: item.geojson,
      shelters: item.shelters ?? [],
    };
  };

  // =====================================================================
  // [기능 추가 예정] 3. 알고리즘 기반 경로 추천 (POST /recommend)
  // 확정된 프리셋 배열을 백엔드로 전송하여 Top 3(또는 4) 경로를 반환받습니다.
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
      setRoutes(data.slice(0, 4).map((item: any, i: number) => apiItemToRouteInfo(item, i)));
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
          setRoutes(data.slice(0, 4).map((item: any, i: number) => apiItemToRouteInfo(item, i)));
        } else {
          setRoutes([
            { id: 1, rank: 1, name: "시민한길 A코스", distance: "2.1km", duration: "30분", tags: ["시원한길", "반려동물"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#3A9E66" },
            { id: 2, rank: 2, name: "강가 그늘길 코스", distance: "2.3km", duration: "32분", tags: ["그늘", "뷰 좋음"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#4A90D9" },
            { id: 3, rank: 3, name: "숲속 산책길 코스", distance: "1.9km", duration: "28분", tags: ["잔디", "그늘"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#F5A623" },
            { id: 4, rank: 4, name: "탄천 수변길", distance: "3.5km", duration: "45분", tags: ["수변", "바람"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#9B59B6" },
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
    <div className="w-full h-full bg-[#F5F7F5] pt-4 px-4 pb-6 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-black text-gray-800">경로 추천 완료!</h2>
      </div>

      <div className="bg-[#E8F5E9] p-4 rounded-xl w-full text-center mb-6 shadow-sm">
        <p className="text-[15px] font-bold text-gray-800">🎉 경로 추천이 완료되었어요!</p>
        <p className="text-xs text-gray-500 mt-1">마음에 드는 경로를 선택해 미리보기를 확인해보세요</p>
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pb-6" style={{ scrollbarWidth: 'none' }}>
        <p className="text-sm font-bold text-gray-600 mb-1">당신을 위한 추천 경로 TOP 4</p>
        {isLoading ? (
          <div className="flex justify-center items-center h-full text-gray-500 text-sm font-bold">경로 불러오는 중...</div>
        ) : (
          routes.map((route, i) => (
            <button
              key={route.id}
              onClick={() => onSelectRoute(route)}
              className="bg-white border-[1.5px] border-[#E8F5E9] rounded-2xl p-4 text-left active:scale-[0.98] transition-transform shadow-sm flex items-center justify-between"
            >
              <div>
                <p className="text-xs text-gray-500 font-bold mb-1">경로 {i + 1}</p>
                <p className="text-lg font-bold text-gray-800 mb-2">{route.name}</p>
                <div className="flex gap-2 text-sm text-gray-600 font-medium">
                  <span>⏱ {route.duration}</span>
                  <span>📏 {route.distance}</span>
                </div>
              </div>
              <ArrowLeft size={16} color="#9BB5D0" className="transform rotate-180" />
            </button>
          ))
        )}
      </div>
    </div>
  );
}