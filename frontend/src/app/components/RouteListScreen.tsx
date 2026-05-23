import { useState, useEffect } from 'react';
import { ArrowLeft, Flame, Clock, MapPin, Star, ChevronRight, TreePine, Umbrella, Thermometer, Wind } from 'lucide-react';

export interface RouteInfo {
  id: number;
  name: string;
  subtitle: string;
  heatScore: number;
  distance: string;
  duration: string;
  shadeRatio: number;
  tags: string[];
  color: string;
  difficulty: string;
  // API 연동을 위해 추가된 속성 (실제 경로 그릴 때 사용)
  mode: 'general' | 'elderly' | 'dog';
  start: [number, number];
  end: [number, number];
}

// 테스트용 하드코딩 샘플 데이터
export const SAMPLE_ROUTES: RouteInfo[] = [
  {
    id: 991,
    name: '수지구청 ↔ 죽전역 테스트 경로',
    subtitle: '일반 맞춤 경로 (테스트)',
    heatScore: 85,
    distance: '2.5km',
    duration: '38분',
    shadeRatio: 72,
    tags: ['테스트', '그늘 우선'],
    color: '#4A90D9',
    difficulty: '보통',
    mode: 'general',
    start: [37.3219, 127.0972], // 수지구청
    end: [37.3247, 127.1245]    // 죽전역
  },
  {
    id: 992,
    name: '광교산 입구 쉼터 경로',
    subtitle: '노약자 맞춤 경로 (테스트)',
    heatScore: 92,
    distance: '1.2km',
    duration: '18분',
    shadeRatio: 88,
    tags: ['쉼터 경유', '매우 쾌적'],
    color: '#5DB87C',
    difficulty: '쉬움',
    mode: 'elderly',
    start: [37.3165, 127.0850], // 광교산 부근 임시 출발지
    end: [37.3110, 127.0760]    // 근린공원 부근 도착지
  }
];


type FilterType = '전체' | '그늘 우선' | '쉼터 우선' | '지면온도 우선' | '바람 우선';
const FILTERS: FilterType[] = ['전체', '그늘 우선', '쉼터 우선', '지면온도 우선', '바람 우선'];

const filterIcons: Record<FilterType, React.ReactNode> = {
  '전체': <Star size={12} />,
  '그늘 우선': <TreePine size={12} />,
  '쉼터 우선': <Umbrella size={12} />,
  '지면온도 우선': <Thermometer size={12} />,
  '바람 우선': <Wind size={12} />,
};

function HeatScoreBadge({ score }: { score: number }) {
  const color = score >= 85 ? '#4A90D9' : score >= 70 ? '#5DB87C' : '#F5A623';
  const label = score >= 85 ? '매우 쾌적' : score >= 70 ? '쾌적' : '보통';
  return (
    <div className="flex items-center gap-1.5 rounded-full px-2.5 py-1" style={{ background: `${color}18` }}>
      <div className="rounded-full" style={{ width: '8px', height: '8px', background: color }} />
      <span style={{ fontSize: '12px', fontWeight: '700', color }}>{score}점</span>
      <span style={{ fontSize: '11px', color, opacity: 0.8 }}>{label}</span>
    </div>
  );
}

function RouteCard({ route, onSelect }: { route: RouteInfo; onSelect: () => void }) {
  return (
    <button
      onClick={onSelect}
      className="w-full rounded-2xl p-4 flex flex-col gap-3 active:scale-[0.98] transition-transform text-left"
      style={{ background: 'white', boxShadow: '0 2px 16px rgba(0,0,0,0.08)', border: `1.5px solid ${route.color}22` }}
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: route.color }} />
            <span style={{ fontSize: '16px', fontWeight: '700', color: '#1A3A5C' }}>{route.name}</span>
          </div>
          <div className="flex items-center gap-1 mt-0.5">
            <MapPin size={11} color="#9BB5D0" />
            <span style={{ fontSize: '12px', color: '#9BB5D0' }}>{route.subtitle}</span>
          </div>
        </div>
        <HeatScoreBadge score={route.heatScore} />
      </div>

      <div className="flex gap-2">
        <div className="flex items-center gap-1.5 rounded-xl px-3 py-2 flex-1" style={{ background: '#F0F8FF' }}>
          <MapPin size={13} color="#4A90D9" />
          <div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1A3A5C' }}>{route.distance}</div>
            <div style={{ fontSize: '10px', color: '#9BB5D0' }}>거리</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-xl px-3 py-2 flex-1" style={{ background: '#F0FFF6' }}>
          <Clock size={13} color="#5DB87C" />
          <div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1A3A5C' }}>{route.duration}</div>
            <div style={{ fontSize: '10px', color: '#9BB5D0' }}>소요시간</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 rounded-xl px-3 py-2 flex-1" style={{ background: '#FFFAF0' }}>
          <Flame size={13} color="#F5A623" />
          <div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#1A3A5C' }}>{route.shadeRatio}%</div>
            <div style={{ fontSize: '10px', color: '#9BB5D0' }}>그늘 비율</div>
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center">
        <div className="flex gap-1.5 flex-wrap">
          {route.tags.map(tag => (
            <span
              key={tag}
              className="rounded-full px-2.5 py-1"
              style={{ fontSize: '11px', fontWeight: '600', background: `${route.color}18`, color: route.color }}
            >
              {tag}
            </span>
          ))}
          <span className="rounded-full px-2.5 py-1" style={{ fontSize: '11px', fontWeight: '600', background: '#F5F5F5', color: '#888' }}>
            {route.difficulty}
          </span>
        </div>
        <ChevronRight size={16} color={route.color} />
      </div>
    </button>
  );
}

interface RouteListScreenProps {
  onBack: () => void;
  onSelectRoute: (route: RouteInfo) => void;
  mode: 'general' | 'elderly' | 'dog';
}

const modeLabel: Record<string, string> = { general: '일반 모드', elderly: '노약자 모드', dog: '강아지 산책 모드' };
// 백엔드의 한글 모드명 맵핑을 위한 객체
const apiModeQuery: Record<string, string> = { general: '일반', elderly: '노약자', dog: '반려동물' };
const modeEmoji: Record<string, string> = { general: '🚶', elderly: '🧓', dog: '🐕' };

export function RouteListScreen({ onBack, onSelectRoute, mode }: RouteListScreenProps) {
  const [filter, setFilter] = useState<FilterType>('전체');
  // ✅ 추가: API에서 받아올 경로 상태와 로딩 상태 관리
  // const [routes, setRoutes] = useState<RouteInfo[]>([]);
  // const [isLoading, setIsLoading] = useState(true);
  // 테스트용 (위 아래 둘 중 하나만 사용할 것. 테스트일 경우 useEffect 주석 처리)
  const [routes, setRoutes] = useState<RouteInfo[]>(SAMPLE_ROUTES); 
  const [isLoading, setIsLoading] = useState(false);

  // ✅ 추가: 화면 로드 시 백엔드 API(GET /routes) 호출
  // useEffect(() => {
  //   const fetchRoutes = async () => {
  //     setIsLoading(true);
  //     try {
  //       // 백엔드가 인식할 수 있는 한글 모드명(일반, 노약자, 반려동물)으로 쿼리 스트링 구성
  //       const targetMode = apiModeQuery[mode];
  //       const res = await fetch(`http://127.0.0.1:8000/routes?mode=${targetMode}`);
        
  //       if (res.ok) {
  //         const data = await res.json();
          
  //         // API 응답 데이터를 프론트엔드 UI(RouteInfo) 구조에 맞게 변환 (매핑)
  //         const formattedRoutes = data.map((item: any, index: number) => ({
  //           id: item.id,
  //           name: item.name,
  //           subtitle: `${item.mode} 맞춤 경로`,
  //           heatScore: Math.round(item.heat_score_avg * 100), // 점수 스케일링 임시 처리
  //           distance: `${(item.distance_m / 1000).toFixed(1)}km`,
  //           duration: `${Math.round(item.distance_m / 1000 * 15)}분`, // 임시 소요시간 추정
  //           shadeRatio: 65, // 백엔드에서 shade_ratio가 오면 갱신
  //           tags: item.shelters && item.shelters.length > 0 ? ['쉼터 경유'] : ['기본 경로'],
  //           color: mode === 'elderly' ? '#5DB87C' : mode === 'dog' ? '#9B59B6' : '#4A90D9',
  //           difficulty: '보통',
  //           // 지도 렌더링(MapDetailScreen)으로 넘겨주기 위한 필수 데이터
  //           mode: mode,
  //           start: item.geojson.coordinates[0].reverse(), // GeoJSON(Lng,Lat) -> 지도(Lat,Lng)
  //           end: item.geojson.coordinates[item.geojson.coordinates.length - 1].reverse()
  //         }));
          
  //         setRoutes(formattedRoutes);
  //       } else {
  //         console.error('Failed to fetch route list:', res.status);
  //       }
  //     } catch (err) {
  //       console.error('Network Error:', err);
  //     } finally {
  //       setIsLoading(false);
  //     }
  //   };

  //   fetchRoutes();
  // }, [mode]); // 모드가 변경될 때마다 새로 호출

  // 필터 적용 로직
  const filtered = filter === '전체' ? routes : routes.filter(r => r.tags.includes(filter));

  return (
    <div className="w-full h-full flex flex-col" style={{ background: '#F0F7FF' }}>
      {/* Header with gradient */}
      <div className="px-4 pt-12 pb-3" style={{ background: 'linear-gradient(180deg, #4A90D9 0%, #3A7BC8 100%)' }}>
        <div className="flex items-center gap-3 mb-4">
          <button
            onClick={onBack}
            className="w-9 h-9 rounded-full flex items-center justify-center active:scale-90 transition-transform"
            style={{ background: 'rgba(255,255,255,0.2)' }}
          >
            <ArrowLeft size={18} color="white" strokeWidth={2.5} />
          </button>
          <div>
            <div style={{ fontSize: '18px', fontWeight: '700', color: 'white' }}>추천 경로 목록</div>
            <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.8)' }}>
              {modeEmoji[mode]} {modeLabel[mode]} · 수지구 기준
            </div>
          </div>
        </div>

        {/* Filter chips */}
        <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className="flex items-center gap-1.5 rounded-full px-3 py-1.5 whitespace-nowrap transition-all active:scale-95 flex-shrink-0"
              style={{
                background: filter === f ? 'white' : 'rgba(255,255,255,0.2)',
                color: filter === f ? '#4A90D9' : 'white',
                fontWeight: filter === f ? '700' : '500',
                fontSize: '13px',
                boxShadow: filter === f ? '0 2px 8px rgba(0,0,0,0.15)' : 'none',
              }}
            >
              <span style={{ color: filter === f ? '#4A90D9' : 'rgba(255,255,255,0.9)' }}>
                {filterIcons[f]}
              </span>
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Count bar */}
      <div className="px-4 py-3 flex items-center justify-between">
        <span style={{ fontSize: '14px', fontWeight: '600', color: '#5B8CC4' }}>
          총 {filtered.length}개 경로
        </span>
        <div className="flex items-center gap-1.5 rounded-full px-3 py-1.5" style={{ background: 'rgba(74,144,217,0.1)' }}>
          <div className="w-2 h-2 rounded-full" style={{ background: '#4A90D9', animation: 'pulse 2s infinite' }} />
          <span style={{ fontSize: '12px', color: '#4A90D9', fontWeight: '600' }}>실시간 업데이트</span>
        </div>
      </div>

      {/* Route cards / Loading spinner */}
      <div className="flex-1 overflow-y-auto px-4 pb-6 flex flex-col gap-3" style={{ scrollbarWidth: 'none' }}>
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <div className="w-8 h-8 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-sm font-bold">경로 데이터를 불러오는 중...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-400">
            <p className="font-bold">조건에 맞는 경로가 없습니다.</p>
          </div>
        ) : (
          filtered.map(route => (
            <RouteCard key={route.id} route={route} onSelect={() => onSelectRoute(route)} />
          ))
        )}
      </div>
    </div>
  );
}
