import { useEffect, useState } from 'react';
import { recommendRoutes } from '../../api/searchApi';

interface Props {
  tags: string[];
  onSelectRoute: (routeId?: string) => void;
}

export type RouteItem = { id: string; title: string; distance: string; time: string; tags: string[] };

export default function ResultsFlow({ tags, onSelectRoute }: Props) {
  const [routes, setRoutes] = useState<RouteItem[]>([]);

  useEffect(() => {
    let mounted = true;
    recommendRoutes(tags).then(res => {
      if (!mounted) return;
      const mapped = res.routes.map(r => ({ id: r.id, title: r.name, distance: `${r.distance}km`, time: `${r.duration_minutes}분`, tags: [] }));
      setRoutes(mapped);
    }).catch(() => {
      // fallback to empty
      if (!mounted) return;
      setRoutes([]);
    });
    return () => { mounted = false; };
  }, [tags]);

  return (
    <div className="flex-1 flex flex-col p-4">
      <h3 className="text-lg font-semibold">경로 추천 완료!</h3>
      <div className="mt-4 space-y-3">
        {routes.map((r, idx) => (
          <div key={r.id} className="p-3 rounded-xl bg-white shadow-sm" onClick={() => onSelectRoute(r.id)}>
            <div className="flex justify-between items-center">
              <div className="font-semibold">{idx + 1}위 {r.title}</div>
              <div className="text-sm text-gray-500">{r.distance} · {r.time}</div>
            </div>
            <div className="mt-2 text-sm text-gray-500 flex gap-2">
              {r.tags.map(t => <span key={t} className="px-2 py-1 rounded-full bg-gray-100">{t}</span>)}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-auto pb-6 text-center text-sm text-gray-400">원하는 경로를 선택해 지도를 미리보기하세요</div>
    </div>
  );
}
