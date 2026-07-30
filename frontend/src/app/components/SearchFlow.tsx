import { useState, useRef } from 'react';
import { Mic, Check, X, Plus, ArrowLeft } from 'lucide-react';
import type { Step, TagItem } from '../App';

interface SearchFlowProps {
  step: 'start' | 'voice_input' | 'voice_confirm' | 'analyzing' | 'preset' | 'searching';
  setStep: (step: Step) => void;
  recognizedText: string;
  setRecognizedText: (text: string) => void;
  setSelectedTags: (tags: string[]) => void;
  activeTags: TagItem[];
  setActiveTags: React.Dispatch<React.SetStateAction<TagItem[]>>;
  inactiveTags: TagItem[];
  setInactiveTags: React.Dispatch<React.SetStateAction<TagItem[]>>;
}

export default function SearchFlow({ step, setStep, recognizedText, setRecognizedText, setSelectedTags, activeTags, setActiveTags, inactiveTags, setInactiveTags }: SearchFlowProps) {
  const [tagError, setTagError] = useState(false);
  const voiceTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tagErrorTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

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
      if (activeTags.length === 0 && inactiveTags.length === 0) {
        setActiveTags([
          { id: '1', label: '시원한길', originalType: 'selected' },
          { id: '2', label: '30분', originalType: 'selected' },
          { id: '3', label: '반려동물', originalType: 'selected' },
        ]);
        setInactiveTags([
          { id: '4', label: '쉼터많음', originalType: 'recommended' },
          { id: '5', label: '평지', originalType: 'recommended' },
        ]);
      }
      setStep('preset');
      setTagError(false);
    }, 2000);
  };

  const handleSearchRoutes = () => {
   if (activeTags.length > 3) {
      setTagError(true);
      if (tagErrorTimeout.current) clearTimeout(tagErrorTimeout.current);
      tagErrorTimeout.current = setTimeout(() => {
        setTagError(false);
      }, 3000);
      return;
    }
    setTagError(false);
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
       className={`flex items-center gap-2 px-5 py-3 rounded-full text-xl font-bold shadow-md transition-transform active:scale-95 ${bgClass}`}
    >
      #{tag.label} {currentZone === 'active' ? <X size={22} /> : <Plus size={22} />}
      </button>
    );
  };

  return (
    <div className="w-full h-full flex flex-col items-center">
      <style>{`
        @keyframes popIn {
          0% { opacity: 0; transform: scale(0.95) translateY(10px); }
          100% { opacity: 1; transform: scale(1) translateY(0); }
        }
        .animate-pop-in { animation: popIn 0.3s ease-out forwards; }
        
        @keyframes fadeOutMsg {
          0% { opacity: 0; transform: translateY(10px); }
          10% { opacity: 1; transform: translateY(0); }
          70% { opacity: 1; transform: translateY(0); }
          100% { opacity: 0; transform: translateY(-10px); display: none; }
        }
        .animate-fade-out-msg { animation: fadeOutMsg 2.5s forwards; }
      `}</style>
      <div className="w-full h-40 bg-[#DDF4E4] relative mb-6 shrink-0 mt-2 rounded-t-[32px]">
        <div className="absolute top-10 left-8 w-14 h-14 bg-[#FFD54F] rounded-full"></div>
        <div className="absolute top-10 left-24 w-24 h-10 bg-white rounded-full opacity-80"></div>
        <div className="absolute bottom-0 w-full h-12 bg-[#A5D6A7]">
          <div className="w-24 h-full bg-[#D7B882] mx-auto"></div>
        </div>
      </div>

      {(step === 'start' || step === 'voice_input' || step === 'voice_confirm') && (
        <div className="flex-1 w-full px-6 flex flex-col items-center h-full pb-8">
          
          <div className="w-full flex flex-col items-center">
            <p className="text-[#3A9E66] font-extrabold text-xl mb-3">🌿 산책 도우미</p>
            <h2 className="text-4xl font-black text-gray-800 text-center leading-snug">
              오늘은 어떤 길을<br/>산책할까요?
            </h2>
          </div>

          <div className="flex-1 w-full relative flex flex-col items-center justify-center mt-6">
            <div className={`absolute top-4 w-full transition-all duration-700 ease-out z-10 ${step === 'voice_confirm' ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-10 scale-90 pointer-events-none'}`}>
              <div className="bg-[#E8F5E9] p-8 rounded-3xl w-full shadow-md">
                <p className="text-2xl text-gray-800 font-bold leading-relaxed text-center break-keep">{recognizedText || "인식 중..."}</p>
              </div>
            </div>
            <div className={`absolute transition-all duration-[350ms] ease-in-out z-20 flex items-center justify-center
                ${step === 'start' ? 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[calc(100%-3rem)] h-24' :
                  step === 'voice_input' ? 'top-4 left-1/2 -translate-x-1/2 -translate-y-0 w-40 h-40' :
                  'top-8 left-1/2 -translate-x-1/2 -translate-y-0 w-0 h-0 opacity-0 scale-0'}`}
            >
              <button 
                onClick={step === 'start' ? handleStartVoice : undefined} 
                className={`w-full h-full bg-[#3A9E66] flex items-center justify-center text-white shadow-lg overflow-hidden transition-all duration-[350ms] 
                ${step === 'start' ? 'rounded-2xl' : 'rounded-full pointer-events-none'} 
                ${step === 'voice_input' ? 'shadow-[0_0_40px_rgba(111,207,151,0.6)] animate-[pulse_1.5s_ease-in-out_infinite]' : ''}`}
              >
                 <Mic size={step === 'start' ? 36 : 56} className="shrink-0 flex-none" />
                 <span className={`font-bold text-2xl ml-3 whitespace-nowrap transition-all duration-300 ${step === 'start' ? 'opacity-100 w-auto' : 'opacity-0 w-0 hidden'}`}>
                    시작하기
                 </span>
              </button>
            </div>
            <div className={`absolute top-[90%] flex flex-col items-center transition-all duration-250 z-10 ${step === 'voice_input' ? 'opacity-100 translate-y-0 delay-150' : 'opacity-0 translate-y-10 pointer-events-none'}`}>
                <div className="flex gap-1.5 items-center justify-center h-10 mb-3">
                   <div className="w-1.5 bg-[#3A9E66] rounded-full animate-bounce h-4" style={{ animationDelay: '0.0s' }}></div>
                   <div className="w-1.5 bg-[#3A9E66] rounded-full animate-bounce h-7" style={{ animationDelay: '0.2s' }}></div>
                   <div className="w-1.5 bg-[#3A9E66] rounded-full animate-bounce h-5" style={{ animationDelay: '0.4s' }}></div>
                   <div className="w-1.5 bg-[#3A9E66] rounded-full animate-bounce h-8" style={{ animationDelay: '0.1s' }}></div>
                   <div className="w-1.5 bg-[#3A9E66] rounded-full animate-bounce h-6" style={{ animationDelay: '0.3s' }}></div>
                </div>
                <p className="text-xl font-bold text-[#3A9E66] animate-pulse">🎙 열심히 듣고 있어요...</p>
            </div>
          </div>
          <div className="w-full relative h-40 mt-4">
              <button
                  onClick={handleStopVoice}
                  className={`absolute bottom-0 w-full px-10 py-6 bg-[#FFEAEA] text-[#FF4B4B] rounded-2xl font-bold text-2xl shadow-sm active:scale-95 transition-all duration-500 ${step === 'voice_input' ? 'opacity-100 translate-y-0 pointer-events-auto delay-300' : 'opacity-0 translate-y-10 pointer-events-none'}`}
              >
                  ⏹ 입력 종료
              </button>
              <div className={`absolute bottom-0 w-full flex flex-col gap-4 transition-all duration-700 ease-out ${step === 'voice_confirm' ? 'opacity-100 translate-y-0 pointer-events-auto delay-300' : 'opacity-0 translate-y-10 pointer-events-none'}`}>
                  <button onClick={handleConfirmVoice} className="w-full bg-[#0047AB] text-white py-6 rounded-2xl font-bold text-2xl flex justify-center items-center gap-2 shadow-sm active:bg-[#003380] transition-colors">
                      ✓ 확인
                  </button>
                  <button onClick={handleStartVoice} className="w-full bg-[#3A9E66] text-white py-6 rounded-2xl font-bold text-2xl flex justify-center items-center gap-2 shadow-sm active:bg-[#2F8152] transition-colors">
                      🔄 다시 말하기
                  </button>
              </div>
          </div>
        </div>
      )}

      {(step === 'analyzing' || step === 'searching') && (
        <div className="flex-1 w-full px-6 flex flex-col items-center mt-16 animate-pop-in">
          <div className="w-36 h-36 bg-white rounded-full border-8 border-[#3A9E66] border-t-transparent animate-spin mb-10 flex items-center justify-center shadow-md">
            <div className="w-20 h-20 bg-gray-200 rounded-full animate-none" />
          </div>
          <h2 className="text-3xl font-black text-gray-800 text-center mb-6 leading-snug break-keep">
            {step === 'analyzing' ? '당신의 말을 분석해서\n프리셋을 만들고 있어요!' : '당신에게 딱 맞는\n경로를 찾고 있어요!'}
          </h2>
          <p className="text-xl text-gray-500 mb-10 font-bold">잠시만 기다려 주세요</p>
        </div>
      )}

      {step === 'preset' && (
        <div className="absolute inset-0 bg-white z-20 flex flex-col pt-20 pb-6 px-6 animate-pop-in">
          <div className="absolute top-6 left-6 z-30">
            <button onClick={() => { setRecognizedText(""); setStep('start'); }} className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform border border-gray-100">
              <ArrowLeft size={24} color="#333" />
            </button>
          </div>

          <div className="mb-8 mt-2">
            <p className="text-[#F5A623] font-black text-2xl flex items-center gap-2 mt-1">✨ 추천 프리셋 ✨</p>
          </div>
          <div className="mb-6">
            <p className="text-lg font-bold text-gray-700 mb-4">선택한 조건</p>
            <div className="flex flex-wrap gap-2.5">{activeTags.map(tag => renderTag(tag, 'active'))}</div>
          </div>
          <div className="mb-6 flex-1">
            <p className="text-xl font-bold text-gray-700 mb-5">이런 조건도 있어요!</p>
            <div className="flex flex-wrap gap-3">{inactiveTags.map(tag => renderTag(tag, 'inactive'))}</div>
          </div>

          <div className={`mb-4 text-center text-[#E74C3C] font-bold text-lg bg-[#FCECEC] py-4 px-4 rounded-2xl border border-[#F5B7B1] transition-opacity duration-300 pointer-events-none ${tagError ? 'opacity-100' : 'opacity-0'}`}>
            ⚠️ 태그는 3개까지 선택해주세요!
          </div>

          <button onClick={handleSearchRoutes} className="w-full bg-[#0047AB] text-white py-6 rounded-2xl font-bold text-2xl flex justify-center items-center gap-2 shadow-lg active:bg-[#003380] active:scale-[0.98] transition-transform">
            경로 추천받기
          </button>
        </div>
      )}
    </div>
  );
}