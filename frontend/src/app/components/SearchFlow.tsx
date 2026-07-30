import { useState, useRef } from 'react';
import { Mic, Check, X, Plus } from 'lucide-react';
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
  
  const voiceTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  // =====================================================================
  // [기능 추가 예정] 1. STT 연동 (POST /speech)
  // MediaRecorder API를 사용해 녹음된 음성을 백엔드로 보내 텍스트를 받아옵니다.
  // =====================================================================
  /*
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  const startRealSTT = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      mediaRecorder.current.ondataavailable = (e) => { audioChunks.current.push(e.data); };
      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("audio", audioBlob);

        // POST /speech API 호출
        const res = await fetch('/speech', { method: 'POST', body: formData });
        const data = await res.json();
        setRecognizedText(data.text);
        setStep('voice_confirm');
      };
      mediaRecorder.current.start();
    } catch (err) { console.error("마이크 권한이 필요합니다.", err); }
  };

  const stopRealSTT = () => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop();
    }
  };
  */

  const startSTTService = async () => {
    // startRealSTT(); // API 연동 시 주석 해제
    
    // 임시 Mock 로직 (기존 기능 유지)
    voiceTimeout.current = setTimeout(() => {
      setRecognizedText("강아지랑 30분 정도 시원한 그늘 길을 걷고 싶어요.");
      setStep('voice_confirm');
    }, 2000);
  };

  const stopSTTService = () => {
    // stopRealSTT(); // API 연동 시 주석 해제
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

  // =====================================================================
  // [기능 추가 예정] 2. GPT를 활용한 프리셋 추출 (POST /preset)
  // 사용자 텍스트를 분석하여 기본 프리셋과 서브 프리셋(JSON)을 생성합니다.
  // =====================================================================
  /*
  const fetchPresetsFromAI = async () => {
    try {
      const res = await fetch('/preset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: recognizedText })
      });
      const data = await res.json();
      
      // JSON Schema 매핑 (예상 반환 포맷에 맞춰 매핑)
      const basePresets = data.base_presets.map((t: string, i: number) => ({ id: `base_${i}`, label: t, originalType: 'selected' }));
      const subPresets = data.sub_presets.map((t: string, i: number) => ({ id: `sub_${i}`, label: t, originalType: 'recommended' }));
      
      setActiveTags(basePresets);
      setInactiveTags(subPresets);
      setStep('preset');
    } catch (err) {
      console.error("프리셋 추출 실패", err);
    }
  };
  */

  const handleConfirmVoice = () => {
    setStep('analyzing');
    // fetchPresetsFromAI(); // API 연동 시 주석 해제

    // 임시 Mock 로직 (기존 기능 유지)
    setTimeout(() => {
      setActiveTags([
        { id: '1', label: '시원한길', originalType: 'selected' },
        { id: '2', label: '30분', originalType: 'selected' },
        { id: '3', label: '반려동물', originalType: 'selected' },
      ]);
      setInactiveTags([
        { id: '4', label: '쉼터많음', originalType: 'recommended' },
        { id: '5', label: '평지', originalType: 'recommended' },
      ]);
      setStep('preset');
    }, 2000);
  };

  const handleSearchRoutes = () => {
    setStep('searching');
    // 사용자가 최종 확정한 프리셋(태그)들을 부모 상태로 업데이트
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
          <button onClick={handleStartVoice} className="w-full bg-[#3A9E66] text-white py-4 rounded-xl font-bold flex justify-center gap-2 active:bg-[#2F8152] mt-4">
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
          <button onClick={handleStopVoice} className="px-6 py-2 bg-[#FFEAEA] text-[#FF4B4B] rounded-xl font-bold text-sm mt-8">
            ⏹ 입력 종료
          </button>
        </div>
      )}

      {step === 'voice_confirm' && (
        <div className="flex-1 w-full px-6 flex flex-col items-center">
          <h2 className="text-2xl font-black text-gray-800 text-center leading-tight mb-10">오늘은 어떤 길을<br/>산책할까요?</h2>
          <div className="w-16 h-16 bg-[#3A9E66] rounded-full flex items-center justify-center mb-10 shadow-lg">
            <Mic size={32} color="white" />
          </div>
          <div className="bg-[#E8F5E9] p-5 rounded-xl w-full mb-6">
            <p className="text-base text-gray-800 font-bold leading-relaxed">{recognizedText}</p>
          </div>
          <div className="flex gap-3 w-full">
            <button onClick={handleStartVoice} className="flex-1 bg-gray-100 text-gray-600 py-3 rounded-xl font-bold flex justify-center items-center gap-1">
              🔄 다시 입력하기
            </button>
            <button onClick={handleConfirmVoice} className="flex-1 bg-[#0047AB] text-white py-3 rounded-xl font-bold flex justify-center items-center gap-1">
              ✓ 확인
            </button>
          </div>
        </div>
      )}

      {(step === 'analyzing' || step === 'searching') && (
        <div className="flex-1 w-full px-6 flex flex-col items-center mt-12">
          <div className="w-24 h-24 bg-white rounded-full border-4 border-[#3A9E66] border-t-transparent animate-spin mb-6 flex items-center justify-center">
            {/* 임시 캐릭터 아이콘 영역 */}
            <div className="w-16 h-16 bg-gray-200 rounded-full animate-none" />
          </div>
          <h2 className="text-xl font-black text-gray-800 text-center mb-3">
            {step === 'analyzing' ? '당신의 말을 분석해서\n프리셋을 만들고 있어요!' : '당신에게 딱 맞는\n경로를 찾고 있어요!'}
          </h2>
          <p className="text-sm text-gray-500 mb-6">잠시만 기다려 주세요</p>
          <div className="flex gap-2">
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      )}

      {step === 'preset' && (
        <div className="absolute inset-0 bg-white z-20 flex flex-col pt-12 pb-6 px-6">
          <div className="mb-6">
            <p className="text-[#F5A623] font-bold text-sm flex items-center gap-1">✨ 추천 프리셋 ✨</p>
          </div>
          <div className="mb-4">
            <p className="text-sm font-bold text-gray-600 mb-3">선택한 조건</p>
            <div className="flex flex-wrap gap-2">{activeTags.map(tag => renderTag(tag, 'active'))}</div>
          </div>
          <div className="mt-6 mb-6">
            <p className="text-sm font-bold text-gray-600 mb-3">이런 조건도 있어요!</p>
            <div className="flex flex-wrap gap-2">{inactiveTags.map(tag => renderTag(tag, 'inactive'))}</div>
          </div>
          <button onClick={handleSearchRoutes} className="w-full mt-auto bg-[#0047AB] text-white py-4 rounded-xl font-bold text-lg flex justify-center items-center gap-2">
            경로 추천받기
          </button>
        </div>
      )}
    </div>
  );
}