import { useState } from 'react';
import { Undo2 } from 'lucide-react';
import type { RouteInfo } from '../App';
import { KakaoMapComponent } from './MapPreviewScreen';

interface NavigatingScreenProps {
  route: RouteInfo;
  kakaoApiKey: string;
  onRestart: () => void;
}

export default function NavigatingScreen({ route, kakaoApiKey, onRestart }: NavigatingScreenProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  return (
    <div className="w-full h-full relative overflow-hidden bg-[#EBF5FF]">
      {/* 백그라운드 지도 */}
      <div className="absolute inset-0 z-0">
        {kakaoApiKey ? (
           <KakaoMapComponent apiKey={kakaoApiKey} route={route} />
        ) : (
           <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 font-bold bg-[#EBF5FF]">
             <p className="text-[22px]">지도가 뜨지 않습니다 :(</p>
           </div>
        )}
      </div>

      {/* 상단 경로 확정 카드 (스크린샷 10) */}
      <div className="absolute top-4 left-4 right-4 z-10 bg-white rounded-[24px] shadow-lg p-6 flex items-center justify-between">
        <div>
          <h3 className="text-[24px] font-black text-gray-800">{route.name}</h3>
          <div className="flex items-center gap-3 text-gray-500 font-bold mt-1 text-[16px]">
            <span>📏 {route.distance}</span>
            <span>⏱ {route.duration}</span>
          </div>
        </div>
        {/* 왼쪽 위(상단) '처음으로 돌아가기' 회귀 버튼 */}
        <button
          onClick={() => setShowConfirm(true)}
          title="처음으로 돌아가기"
          className="w-14 h-14 bg-[#F3F4F6] rounded-2xl flex items-center justify-center active:scale-90 transition-transform shadow-sm"
        >
          <Undo2 size={28} color="#4B5563" />
        </button>
      </div>

      {/* 처음으로 돌아갈까요? 모달 */}
      {showConfirm && (
        <div className="absolute inset-0 bg-black/40 z-20 flex flex-col justify-end animate-[fadeIn_0.2s_ease-out]">
          <div className="w-full bg-white rounded-t-[36px] p-8 pb-12 flex flex-col items-center animate-[slideUp_0.3s_ease-out]">
            <div className="w-14 h-1.5 bg-gray-300 rounded-full mb-8"></div>
            <h2 className="text-[28px] font-black text-gray-800 mb-4">처음으로 돌아갈까요?</h2>
            {/* 3. 모달 문구 수정 반영 */}
            <p className="text-gray-500 font-bold text-[17px] text-center mb-10 leading-relaxed break-keep">
              경로 보이기를 멈추고<br/>처음 화면으로 돌아갈까요?
            </p>
            <div className="flex gap-4 w-full">
              <button onClick={() => setShowConfirm(false)} className="flex-1 bg-[#F3F4F6] text-gray-700 py-6 rounded-2xl font-bold text-[22px] active:scale-95 transition-transform">
                아니오
              </button>
              <button onClick={onRestart} className="flex-1 bg-[#3B82F6] text-white py-6 rounded-2xl font-bold text-[22px] shadow-md active:scale-95 transition-transform">
                네
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}