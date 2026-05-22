import { useState } from 'react';
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
}

const ROUTES: RouteInfo[] = [
  {
    id: 1,
    name: '광교산 그늘길',
    subtitle: '숲 터널 코스 · 수지구청 출발',
    heatScore: 92,
    distance: '2.3km',
    duration: '35분',
    shadeRatio: 84,
    tags: ['그늘 우선', '자연'],
    color: '#4A90D9',
    difficulty: '쉬움',
  },
  {
    id: 2,
    name: '탄천 수변로',
    subtitle: '하천변 바람길 · 정자역 출발',
    heatScore: 78,
    distance: '1.8km',
    duration: '27분',
    shadeRatio: 52,
    tags: ['쉼터 우선', '바람'],
    color: '#5DB87C',
    difficulty: '쉬움',
  },
  {
    id: 3,
    name: '죽전 근린공원길',
    subtitle: '지면 온도 낮은 공원 산책로',
    heatScore: 71,
    distance: '1.2km',
    duration: '18분',
    shadeRatio: 61,
    tags: ['지면온도 우선'],
    color: '#9B59B6',
    difficulty: '쉬움',
  },
  {
    id: 4,
    name: '수지 미금 하천길',
    subtitle: '미금역 ~ 수지구청 수변 코스',
    heatScore: 65,
    distance: '3.1km',
    duration: '46분',
    shadeRatio: 38,
    tags: ['바람 우선'],
    color: '#E67E22',
    difficulty: '보통',
  },
  {
    id: 5,
    name: '광교호수공원 둘레길',
    subtitle: '호숫가 바람, 벤치 쉼터 다수',
    heatScore: 88,
    distance: '4.2km',
    duration: '62분',
    shadeRatio: 70,
    tags: ['쉼터 우선', '그늘 우선'],
    color: '#2ECC71',
    difficulty: '보통',
  },
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
const modeEmoji: Record<string, string> = { general: '🚶', elderly: '🧓', dog: '🐕' };

export function RouteListScreen({ onBack, onSelectRoute, mode }: RouteListScreenProps) {
  const [filter, setFilter] = useState<FilterType>('전체');

  const filtered = filter === '전체' ? ROUTES : ROUTES.filter(r => r.tags.includes(filter));

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

      {/* Route cards */}
      <div className="flex-1 overflow-y-auto px-4 pb-6 flex flex-col gap-3" style={{ scrollbarWidth: 'none' }}>
        {filtered.map(route => (
          <RouteCard key={route.id} route={route} onSelect={() => onSelectRoute(route)} />
        ))}
      </div>
    </div>
  );
}
