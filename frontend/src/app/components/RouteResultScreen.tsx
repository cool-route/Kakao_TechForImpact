import { useState, useEffect } from 'react';
import { MapPin, Clock, ArrowLeft } from 'lucide-react';
import type { RouteInfo } from '../App';

interface RouteResultScreenProps {
  onBack: () => void;
  onSelectRoute: (route: RouteInfo) => void;
}

export default function RouteResultScreen({ onBack, onSelectRoute }: RouteResultScreenProps) {
  const [routes, setRoutes] = useState<RouteInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 백엔드 API 데이터를 UI Model로 변환
  const apiItemToRouteInfo = (item: any, index: number): RouteInfo => {
    const features = item.geojson?.features ?? [];
    const firstCoord = features[0]?.geometry?.coordinates?.[0] ?? [127.1, 37.33];
    const lastFeature = features[features.length - 1];
    const lastCoords = lastFeature?.geometry?.coordinates ?? [[127.1, 37.33]];
    const lastCoord = lastCoords[lastCoords.length - 1];
    
    // 순위에 따른 테마 색상 지정
    const rankColors = ["#3A9E66", "#4A90D9", "#F5A623"];

    return {
      id: item.id || index,
      rank: index + 1,
      rankColor: rankColors[index] || "#9BB5D0",
      name: item.name || `추천 코스 ${index + 1}`,
      distance: `${(item.distance_m / 1000).toFixed(1)}km`,
      duration: `${Math.round(item.distance_m / 1000 * 15)}분`,
      tags: item.shelters?.length > 0 ? ['평탄', '쉼터 경유'] : ['기본 경로'],
      start: [firstCoord[1], firstCoord[0]] as [number, number],
      end: [lastCoord[1], lastCoord[0]] as [number, number],
      geojson: item.geojson,
      shelters: item.shelters ?? [],
    };
  };

  useEffect(() => {
    const fetchRoutes = async () => {
      setIsLoading(true);
      try {
        const res = await fetch('/routes');
        if (res.ok) {
          const data = await res.json();
          // 백엔드에서 받은 경로 상위 3개를 변환하여 세팅
          setRoutes(data.slice(0, 3).map((item: any, i: number) => apiItemToRouteInfo(item, i)));
        } else {
          // 백엔드 연결 안 될 시 사용할 Mock Data (스크린샷 기반)
          setRoutes([
            { id: 1, rank: 1, name: "시민한길 A코스", distance: "2.1km", duration: "30분", tags: ["평탄", "반려동물"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#3A9E66" },
            { id: 2, rank: 2, name: "시민한길 B코스", distance: "3.1km", duration: "38분", tags: ["약간 언덕", "뷰 좋음"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#4A90D9" },
            { id: 3, rank: 3, name: "올림픽공원 산책로", distance: "2.8km", duration: "35분", tags: ["잔디", "그늘"], start: [37.5, 127.0], end: [37.51, 127.01], geojson: null, shelters: [], rankColor: "#F5A623" },
          ]);
        }
      } catch (err) {
        console.error("Failed to fetch routes, using mock data.", err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchRoutes();
  }, []);

  return (
    <div className="w-full h-full bg-[#F5F7F5] pt-4 px-4 pb-6 flex flex-col">
      <div className="flex items-center gap-3 mb-4">
        {/* 4. 뒤로가기 버튼 추가 -> 클릭 시 1번째 화면으로 */}
        <button onClick={onBack} className="w-8 h-8 rounded-full flex items-center justify-center active:scale-90 bg-white shadow-sm">
          <ArrowLeft size={18} color="#333" />
        </button>
        <div>
          <h2 className="text-xl font-black text-gray-800">경로 추천 완료!</h2>
          <p className="text-sm text-gray-500">당신을 위한 경로 TOP 3</p>
        </div>
      </div>

      <div className="bg-[#E8F5E9] p-4 rounded-xl w-full text-center mb-6 shadow-sm">
        <p className="text-sm font-bold text-gray-700">🎉 경로 추천이 완료되었어요!</p>
        <p className="text-xs text-gray-500 mt-1">마음에 드는 경로를 선택해 미리보기를 확인해보세요</p>
      </div>

      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pb-6" style={{ scrollbarWidth: 'none' }}>
        {isLoading ? (
          <div className="flex justify-center items-center h-full text-gray-500 text-sm font-bold">경로 불러오는 중...</div>
        ) : (
          routes.map(route => (
            <button
              key={route.id}
              onClick={() => onSelectRoute(route)}
              className="bg-white border-[1.5px] border-[#A5D6A7] rounded-2xl p-4 text-left active:scale-[0.98] transition-transform shadow-sm"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="text-white text-xs font-bold px-2.5 py-1 rounded-full" style={{ backgroundColor: route.rankColor }}>
                  {route.rank}위
                </span>
                <span className="text-lg font-bold text-gray-800">{route.name}</span>
              </div>
              
              <div className="flex items-center gap-3 text-sm text-gray-600 mb-3 font-medium">
                <div className="flex items-center gap-1"><MapPin size={14} color="#9BB5D0" /> {route.distance}</div>
                <div className="flex items-center gap-1"><Clock size={14} color="#9BB5D0" /> {route.duration}</div>
              </div>

              <div className="flex gap-1.5">
                {route.tags.map(tag => (
                  <span key={tag} className="bg-[#F0F8FF] text-[#4A90D9] text-xs font-bold px-2 py-1 rounded-full">
                    #{tag}
                  </span>
                ))}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}