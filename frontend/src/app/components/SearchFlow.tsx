import { useState, useRef } from 'react';
import { Mic, Check, X, Plus } from 'lucide-react';
// 폴더 구조 변경으로 상위 경로(../App)에서 타입 임포트
import type { Step } from '../App';

interface SearchFlowProps {
  step: 'start' | 'voice_input' | 'voice_confirm' | 'analyzing' | 'preset' | 'searching';
  setStep: (step: Step) => void;
  recognizedText: string;
  setRecognizedText: (text: string) => void;
  setSelectedTags: (tags: string[]) => void;
}

type TagItem = { id: string; label: string; originalType: 'selected' | 'recommended' };

export default function SearchFlow({ step, setStep, recognizedText, setRecognizedText, setSelectedTags }: SearchFlowProps) {
  const [activeTags, setActiveTags] = useState<TagItem[]>([]);
  const [inactiveTags, setInactiveTags] = useState<TagItem[]>([]);
  
  // 3. NodeJS.Timeout 에러 해결: 브라우저 환경의 ReturnType<typeof setTimeout> 활용
  const voiceTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const startSTTService = async () => {
    // API 연결 전 Mock 로직
    voiceTimeout.current = setTimeout(() => {
      setRecognizedText("강아지와 함께 30분 정도 시민한길을 걷고 싶어요!");
      setStep('voice_confirm');
    }, 2000);
  };

  const stopSTTService = () => {
    // STT 정지 처리용 추상화 함수
  };

  const handleStartVoice = () => {
    setStep('voice_input');
    startSTTService();
  };

  const handleStopVoice = () => {
    if (voiceTimeout.current) clearTimeout(voiceTimeout.current);
    stopSTTService();
    setRecognizedText(""); 
    setStep('start');
  };

  const handleConfirmVoice = () => {
    setStep('analyzing');
    setTimeout(() => {
      setActiveTags([
        { id: '1', label: '시민한길', originalType: 'selected' },
        { id: '2', label: '30분', originalType: 'selected' },
        { id: '3', label: '반려동물', originalType: 'selected' },
      ]);
      setInactiveTags([
        { id: '4', label: '살리라산', originalType: 'recommended' },
        { id: '5', label: '청지', originalType: 'recommended' },
      ]);
      setStep('preset');
    }, 2000);
  };

  const handleSearchRoutes = () => {
    setStep('searching');
    setSelectedTags(activeTags.map(t => t.label));
    setTimeout(() => setStep('route_list'), 2000);
  };

  const toggleTag = (tag: TagItem, from: 'active' | 'inactive') => {
    if (from === 'active') {
      setActiveTags(prev => prev.filter(t => t.id !== tag.id));
      setInactiveTags(prev => [...prev, tag]);
    } else {
      setInactiveTags(prev => prev.filter(t => t.id !== tag.id));
      setActiveTags(prev => [...prev, tag]);
    }
  };

  const renderTag = (tag: TagItem, currentZone: 'active' | 'inactive') => {
    const isOriginalSelected = tag.originalType === 'selected';
    const bgClass = isOriginalSelected ? 'bg-[#3A9E66] text-white' : 'bg-white text-[#3A9E66] border border-[#3A9E66]';
    return (
      <button
        key={tag.id}
        onClick={() => toggleTag(tag, currentZone)}
        className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-bold shadow-sm transition-transform active:scale-95 ${bgClass}`}
      >
        #{tag.label} {currentZone === 'active' ? <X size={14} /> : <Plus size={14} />}
      </button>
    );
  };

  // (이하 JSX 렌더링 로직은 기존 코드와 100% 동일하므로 생략 없이 유지됩니다)
  return (
    <div className="w-full h-full flex flex-col items-center">
      <div className="w-full h-40 bg-[#DDF4E4] relative mb-6 shrink-0">
        <div className="absolute top-10 left-8 w-10 h-10 bg-[#FFD54F] rounded-full"></div>
        <div className="absolute top-10 left-24 w-16 h-6 bg-white rounded-full opacity-80"></div>
        <div className="absolute bottom-0 w-full h-8 bg-[#A5D6A7]">
          <div className="w-16 h-full bg-[#D7B882] mx-auto"></div>
        </div>
      </div>

      {step === 'start' && (
        <div className="flex-1 w-full px-6 flex flex-col items-center">
          <p className="text-[#3A9E66] font-bold text-sm mb-2">🌿 산책 도우미</p>
          <h2 className="text-2xl font-black text-gray-800 text-center leading-tight mb-8">오늘은 어떤 길을<br/>산책할까요?</h2>
          <div className="bg-[#E8F5E9] p-6 rounded-2xl w-full text-center mb-6">
            <p className="text-sm text-gray-600 font-medium">음성으로 원하는 산책 조건을<br/>말씀해 주시면 딱 맞는 경로를<br/>추천해 드릴게요!</p>
          </div>
          <button onClick={handleStartVoice} className="w-full bg-[#3A9E66] text-white py-4 rounded-xl font-bold flex justify-center gap-2 active:bg-[#2F8152]">
            <Mic size={20} /> 시작하기
          </button>
        </div>
      )}

      {step === 'voice_input' && (
        <div className="flex-1 w-full px-6 flex flex-col items-center">
          <h2 className="text-2xl font-black text-gray-800 text-center leading-tight mb-12">오늘은 어떤 길을<br/>산책할까요?</h2>
          <div className="w-24 h-24 bg-[#6FCF97] rounded-full flex items-center justify-center mb-6 animate-pulse opacity-80">
            <div className="w-16 h-16 bg-[#3A9E66] rounded-full flex items-center justify-center">
              <Mic size={32} color="white" />
            </div>
          </div>
          <div className="bg-[#E8F5E9] p-4 rounded-xl w-full text-center mb-6">
            <p className="text-sm font-bold text-[#3A9E66] mb-1">🎙 듣고 있어요...</p>
            <p className="text-sm text-gray-600">"한강 근처 30분 코스 추천해줘"</p>
          </div>
          <button onClick={handleStopVoice} className="px-6 py-2 bg-[#FFEAEA] text-[#FF4B4B] rounded-xl font-bold text-sm">
            ⏹ 입력 중지
          </button>
        </div>
      )}

      {step === 'voice_confirm' && (
        <div className="flex-1 w-full px-6 flex flex-col items-center">
          <h2 className="text-2xl font-black text-gray-800 text-center leading-tight mb-10">오늘은 어떤 길을<br/>산책할까요?</h2>
          <div className="w-16 h-16 bg-[#3A9E66] rounded-full flex items-center justify-center mb-10 shadow-lg">
            <Check size={32} color="white" strokeWidth={3} />
          </div>
          <div className="bg-[#E8F5E9] p-5 rounded-xl w-full mb-6">
            <p className="text-xs font-bold text-gray-500 mb-2">📝 인식된 내용</p>
            <p className="text-base text-gray-800 font-bold leading-relaxed">{recognizedText}</p>
          </div>
          <div className="flex gap-3 w-full">
            <button onClick={handleStartVoice} className="flex-1 bg-gray-100 text-gray-600 py-3 rounded-xl font-bold flex justify-center items-center gap-1">
              🔄 다시 말하기
            </button>
            <button onClick={handleConfirmVoice} className="flex-1 bg-[#3A9E66] text-white py-3 rounded-xl font-bold flex justify-center items-center gap-1">
              ✓ 확인
            </button>
          </div>
        </div>
      )}

      {(step === 'analyzing' || step === 'searching') && (
        <div className="flex-1 w-full px-6 flex flex-col items-center mt-12">
          <div className="text-4xl mb-6">{step === 'analyzing' ? '🏃‍♂️' : '🔍'}</div>
          <h2 className="text-xl font-black text-gray-800 text-center mb-3">
            {step === 'analyzing' ? '프리셋을 분석하고 있어요!' : '당신에게 딱 맞는\n경로를 찾고 있어요!'}
          </h2>
          <div className="flex gap-2 mt-6">
            <div className="w-3 h-3 bg-[#3A9E66] rounded-full animate-bounce"></div>
            <div className="w-3 h-3 bg-[#6FCF97] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-3 h-3 bg-[#A5D6A7] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      )}

      {step === 'preset' && (
        <div className="absolute inset-0 bg-white z-20 flex flex-col pt-12 pb-6 px-6">
          <div className="mb-6">
            <p className="text-[#F5A623] font-bold text-sm flex items-center gap-1">⭐ 추천 프리셋</p>
            <h2 className="text-2xl font-black text-gray-800">프리셋 확인 및 수정</h2>
          </div>
          <div className="bg-[#E8F5E9] rounded-2xl p-5 mb-4 shadow-sm">
            <p className="text-sm font-bold text-gray-600 mb-3">선택된 조건</p>
            <div className="flex flex-wrap gap-2">{activeTags.map(tag => renderTag(tag, 'active'))}</div>
          </div>
          <div className="bg-white border border-[#A5D6A7] rounded-2xl p-5 mb-6 shadow-sm">
            <p className="text-sm font-bold text-gray-600 mb-3">이런 조건도 있어요!</p>
            <div className="flex flex-wrap gap-2">{inactiveTags.map(tag => renderTag(tag, 'inactive'))}</div>
          </div>
          <button onClick={handleSearchRoutes} className="w-full mt-auto bg-[#3A9E66] text-white py-4 rounded-xl font-bold text-lg flex justify-center items-center gap-2">
            🗺️ 경로 추천받기
          </button>
        </div>
      )}
    </div>
  );
}