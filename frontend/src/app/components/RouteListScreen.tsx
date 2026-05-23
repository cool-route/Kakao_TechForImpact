import { useState, useEffect } from 'react';
import { ArrowLeft, Flame, Clock, MapPin, Star, ChevronRight, TreePine, Umbrella, Thermometer, Wind, Navigation } from 'lucide-react';

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
  mode: 'general' | 'elderly' | 'dog';
  start: [number, number];
  end: [number, number];
  geojson: any;
  shelters: Array<{ name: string; lat: number; lng: number; operating_hours: string }>;
}


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
const routeColor: Record<string, string> = { general: '#4A90D9', elderly: '#5DB87C', dog: '#9B59B6' };

export function RouteListScreen({ onBack, onSelectRoute, mode }: RouteListScreenProps) {
  const [filter, setFilter] = useState<FilterType>('전체');
  const [routes, setRoutes] = useState<RouteInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // 위치 기반 경로 추천
  const [addressInput, setAddressInput] = useState('');
  const [resolvedAddress, setResolvedAddress] = useState('');
  const [nearestRoute, setNearestRoute] = useState<RouteInfo | null>(null);
  const [nearestDist, setNearestDist] = useState<number | null>(null);
  const [nearestLoading, setNearestLoading] = useState(false);
  const [nearestError, setNearestError] = useState('');

  const apiItemToRouteInfo = (item: any): RouteInfo => {
    const features = item.geojson?.features ?? [];
    const avgShadeRatio = features.length > 0
      ? features.reduce((s: number, f: any) => s + (f.properties?.shade_ratio ?? 0), 0) / features.length
      : 0;
    const firstCoord = features[0]?.geometry?.coordinates?.[0] ?? [127.1, 37.33];
    const lastFeature = features[features.length - 1];
    const lastCoords = lastFeature?.geometry?.coordinates ?? [[127.1, 37.33]];
    const lastCoord = lastCoords[lastCoords.length - 1];
    return {
      id: item.id,
      name: item.name,
      subtitle: `${item.mode} 맞춤 경로`,
      heatScore: Math.round(Math.max(0, Math.min(100, 90 - (item.heat_score_avg - 19) * 5))),
      distance: `${(item.distance_m / 1000).toFixed(1)}km`,
      duration: `${Math.round(item.distance_m / 1000 * 15)}분`,
      shadeRatio: Math.round(avgShadeRatio * 100),
      tags: item.shelters?.length > 0 ? ['쉼터 경유'] : ['기본 경로'],
      color: routeColor[mode] ?? '#4A90D9',
      difficulty: '보통',
      mode,
      start: [firstCoord[1], firstCoord[0]] as [number, number],
      end: [lastCoord[1], lastCoord[0]] as [number, number],
      geojson: item.geojson,
      shelters: item.shelters ?? [],
    };
  };

  const callNearestRoute = async (lat: number, lng: number, label: string) => {
    try {
      const res = await fetch(`/nearest-route?lat=${lat}&lng=${lng}`);
      if (res.ok) {
        const data = await res.json();
        setNearestRoute(apiItemToRouteInfo(data));
        setNearestDist(data.distance_to_user_m);
        setResolvedAddress(label);
      } else {
        setNearestError('경로를 찾을 수 없습니다.');
      }
    } catch {
      setNearestError('서버에 연결할 수 없습니다.');
    } finally {
      setNearestLoading(false);
    }
  };

  const handleFindNearest = async () => {
    const query = addressInput.trim();
    if (!query) { setNearestError('주소 또는 장소명을 입력해 주세요.'); return; }

    setNearestError('');
    setNearestRoute(null);
    setNearestLoading(true);

    try {
      const params = new URLSearchParams({ q: query, format: 'json', limit: '1', countrycodes: 'kr', 'accept-language': 'ko' });
      const res = await fetch(`https://nominatim.openstreetmap.org/search?${params}`, {
        headers: { 'User-Agent': 'CoolWalk/1.0' },
      });
      const data = await res.json();
      if (!data.length) {
        setNearestError('주소나 장소를 찾을 수 없습니다.');
        setNearestLoading(false);
        return;
      }
      const { lat, lon, display_name } = data[0];
      await callNearestRoute(parseFloat(lat), parseFloat(lon), display_name);
    } catch {
      setNearestError('주소 검색 서비스에 연결할 수 없습니다.');
      setNearestLoading(false);
    }
  };

  useEffect(() => {
    const fetchRoutes = async () => {
      setIsLoading(true);
      try {
        const res = await fetch('/routes');
        if (res.ok) {
          const data = await res.json();
          setRoutes(data.map(apiItemToRouteInfo));
        } else {
          console.error('경로 목록 조회 실패:', res.status);
        }
      } catch (err) {
        console.error('네트워크 오류:', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchRoutes();
  }, [mode]);

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

      {/* 위치 기반 경로 추천 */}
      <div className="px-4 pt-3 pb-1">
        <div className="rounded-2xl p-3 flex flex-col gap-2" style={{ background: 'white', boxShadow: '0 2px 12px rgba(74,144,217,0.12)', border: '1.5px solid #D0E8FF' }}>
          <div className="flex items-center gap-1.5">
            <Navigation size={14} color="#4A90D9" />
            <span style={{ fontSize: '13px', fontWeight: '700', color: '#1A3A5C' }}>내 위치로 가장 가까운 경로 찾기</span>
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="주소, 장소명, 우편번호 입력"
              value={addressInput}
              onChange={e => setAddressInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleFindNearest()}
              className="flex-1 rounded-xl px-3 py-2 outline-none"
              style={{ fontSize: '12px', border: '1.5px solid #D0E8FF', background: '#F7FBFF', color: '#1A3A5C' }}
            />
            <button
              onClick={handleFindNearest}
              disabled={nearestLoading}
              className="rounded-xl px-4 py-2 transition-all active:scale-95 flex-shrink-0"
              style={{ background: '#4A90D9', color: 'white', fontSize: '12px', fontWeight: '700', opacity: nearestLoading ? 0.6 : 1 }}
            >
              {nearestLoading ? '...' : '찾기'}
            </button>
          </div>
          {nearestError && (
            <span style={{ fontSize: '12px', color: '#E55' }}>{nearestError}</span>
          )}
          {resolvedAddress && nearestRoute && (
            <span style={{ fontSize: '11px', color: '#9BB5D0' }}>📍 {resolvedAddress.split(',').slice(0, 3).join(',')}</span>
          )}
          {nearestRoute && nearestDist !== null && (
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ background: '#5DB87C' }} />
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#5DB87C' }}>
                  가장 가까운 경로 — {nearestDist < 1000 ? `${Math.round(nearestDist)}m` : `${(nearestDist / 1000).toFixed(1)}km`} 거리
                </span>
              </div>
              <RouteCard route={nearestRoute} onSelect={() => onSelectRoute(nearestRoute)} />
            </div>
          )}
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
