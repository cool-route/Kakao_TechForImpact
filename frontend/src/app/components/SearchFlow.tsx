import { useState, useRef } from 'react';
import { Mic, Check, X, Plus, ArrowLeft, Search, Loader2, AlertTriangle } from 'lucide-react';
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
  const [sttStatus, setSttStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [analyzeError, setAnalyzeError] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const startRealSTT = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunks.current = [];
      setSttStatus('idle');
      setIsEditing(false);

      mediaRecorder.current.ondataavailable = (e) => { 
        if (e.data.size > 0) audioChunks.current.push(e.data); 
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("audio", audioBlob, "audio.webm");

        // 5초가 지나 녹음이 끝나면 확인 화면으로 이동하여 '처리 중' 상태 설정
        setStep('voice_confirm');
        setSttStatus('processing');
        setRecognizedText("텍스트로 변환하고 있어요...");

        try {
          const res = await fetch('http://localhost:8000/speech', { 
            method: 'POST', 
            body: formData 
          });
          const data = await res.json();
          
          if (res.ok && data.text) {
            setRecognizedText(data.text.trim());
            setSttStatus('success'); // 정상 변환 성공
          } else {
            setRecognizedText(data.error ? `오류: ${data.error}` : "음성을 인식하지 못했어요.");
            setSttStatus('error'); // 텍스트 반환 실패 (에러)
          }
        } catch (err) {
          console.error("STT 서버 연동 에러:", err);
          setRecognizedText("서버와 연결할 수 없습니다.");
          setSttStatus('error'); // 서버 연결 실패 (에러)
        } finally {
          stream.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorder.current.start();

      voiceTimeout.current = setTimeout(() => {
        if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
          mediaRecorder.current.stop();
        }
      }, 5000);

    } catch (err) { 
      console.error("마이크 권한이 필요합니다.", err); 
      alert("마이크 사용 권한을 허용해주세요.");
      setStep('start');
    }
  };

  const handleStartVoice = () => {
    setStep('voice_input');
    startRealSTT();
  };

  const handleFinishInput = () => {
    if (voiceTimeout.current) clearTimeout(voiceTimeout.current);
    
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop();
    } else {
      setStep('voice_confirm');
    }
  };

  const handleManualWrite = () => {
    setIsEditing(true);
    setSttStatus('success'); // 붉은 에러 UI를 해제하고 일반 수정 가능 상태로 변경
    setRecognizedText(""); // 기존 에러 메시지 비우기
    setTimeout(() => {
      textareaRef.current?.focus(); // 키보드 창 활성화 (포커스)
    }, 100);
  };

  const fetchPresetsFromAI = async () => {
    try {
      setAnalyzeError(false);

      const res = await fetch('http://localhost:8000/preset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: recognizedText })
      });

      if (!res.ok) throw new Error("서버에서 프리셋 데이터를 가져오지 못했습니다.");

      // 백엔드에서 준 base_presets, sub_presets 파싱
      const data = await res.json();
      
      const basePresets = data.base_presets.map((t: string, i: number) => ({ 
        id: `base_${i}`, 
        label: t, 
        originalType: 'selected' 
      }));
      
      const subPresets = data.sub_presets.map((t: string, i: number) => ({ 
        id: `sub_${i}`, 
        label: t, 
        originalType: 'recommended' 
      }));
      
      setActiveTags(basePresets);
      setInactiveTags(subPresets);
      setStep('preset');
      setTagError(false);

    } catch (err) {
      console.error("프리셋 추출 실패", err);
      setAnalyzeError(true);
    }
  };

  const handleConfirmVoice = () => {
    // 1. 분석 중 화면 띄우기
    setStep('analyzing');
    
    // 2. 백엔드 API 연동 함수 호출 (기존의 setTimeout 더미 로직 완전 삭제)
    fetchPresetsFromAI();
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
    const bgClass = isOriginalSelected ? 'bg-[#1E88E5] text-white' : 'bg-white text-[#1E88E5] border-2 border-[#1E88E5]';
    return (
      <button
        key={tag.id}
        onClick={() => toggleTag(tag, currentZone)}
        className={`flex items-center gap-2.5 px-5 py-3 rounded-full text-[20px] font-bold shadow-md transition-transform active:scale-95 ${bgClass}`}
      >
        #{tag.label} {currentZone === 'active' ? <X size={24} /> : <Plus size={24} />}
      </button>
    );
  };

  return (
    <div className="w-full h-full flex flex-col items-center bg-[#FFFFFF] relative">
      <style>{`
        @keyframes popIn {
          0% { opacity: 0; transform: scale(0.95) translateY(10px); }
          100% { opacity: 1; transform: scale(1) translateY(0); }
        }
        .animate-pop-in { animation: popIn 0.3s ease-out forwards; }
      `}</style>

      {/* ① 첫 화면 */}
      {step === 'start' && (
        <div className="flex-1 w-full px-6 flex flex-col pt-16 pb-12 animate-pop-in">
          <h2 className="text-[34px] font-black text-gray-800 text-center leading-snug mb-8">
            오늘은 어떤 시원한 길을<br/>걸을까요?
          </h2>
          <div className="bg-[#EBF5FF] p-10 rounded-[32px] text-center mb-8 shadow-sm">
            <p className="text-[#1E40AF] font-bold text-[22px] leading-relaxed">
              음성으로<br/>원하는 산책 조건을<br/>말해주세요
            </p>
          </div>
          <button onClick={handleStartVoice} className="w-full bg-[#3B82F6] text-white py-6 rounded-2xl font-bold text-[24px] shadow-md active:bg-blue-600 transition-colors mb-10">
            시작하기
          </button>
          
          <div className="flex flex-col gap-4 mt-auto">
            <div className="bg-[#F0F7FF] text-[#1E3A8A] px-6 py-5 rounded-2xl text-[16px] font-bold shadow-sm break-keep leading-relaxed text-center">
              "반려견이랑 한낮에 산책하려는데 발바닥이 걱정돼"
            </div>
            <div className="bg-[#F0F7FF] text-[#1E3A8A] px-6 py-5 rounded-2xl text-[16px] font-bold shadow-sm break-keep leading-relaxed text-center">
              "할머니랑 짧게 경치 좋은 곳을 걷고 싶어"
            </div>
          </div>
        </div>
      )}

      {/* ② 음성 입력 중 */}
      {step === 'voice_input' && (
        <div className="flex-1 w-full px-6 flex flex-col items-center pt-10 pb-8 animate-pop-in">
          <h2 className="text-[34px] font-black text-gray-800 text-center leading-snug mb-10">
            오늘은 어떤 시원한 길을<br/>걸을까요?
          </h2>
          <div className="relative flex items-center justify-center w-40 h-40 mb-8 mt-4">
            <div className="absolute inset-0 bg-[#3B82F6] rounded-full opacity-10 animate-ping"></div>
            <div className="absolute inset-4 bg-[#3B82F6] rounded-full opacity-30 animate-pulse"></div>
            <div className="absolute inset-8 bg-[#3B82F6] rounded-full flex items-center justify-center shadow-lg">
              <Mic size={52} color="#FFF" />
            </div>
          </div>
          
          <div className="flex gap-2 items-center justify-center h-14 mb-10">
            <div className="w-2 bg-[#8BB4F6] rounded-full animate-bounce h-6" style={{ animationDelay: '0.0s' }}></div>
            <div className="w-2 bg-[#8BB4F6] rounded-full animate-bounce h-10" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 bg-[#3B82F6] rounded-full animate-bounce h-14" style={{ animationDelay: '0.4s' }}></div>
            <div className="w-2 bg-[#3B82F6] rounded-full animate-bounce h-16" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 bg-[#3B82F6] rounded-full animate-bounce h-12" style={{ animationDelay: '0.3s' }}></div>
            <div className="w-2 bg-[#8BB4F6] rounded-full animate-bounce h-8" style={{ animationDelay: '0.5s' }}></div>
            <div className="w-2 bg-[#8BB4F6] rounded-full animate-bounce h-5" style={{ animationDelay: '0.2s' }}></div>
          </div>

          <div className="bg-[#F0F7FF] p-8 rounded-[32px] text-center w-full mb-auto shadow-sm">
            <p className="text-gray-500 font-bold text-[16px] mb-3">듣고 있어요...</p>
            <p className="text-[#1E40AF] font-bold text-[20px]">5초 후 자동으로 처리됩니다</p>
          </div>
          
          <button onClick={handleFinishInput} className="w-full bg-[#3B82F6] text-[#FFFFFF] py-6 rounded-2xl font-bold text-[22px] shadow-sm mt-4 active:scale-95 transition-transform">
            입력 완료
          </button>
        </div>
      )}

      {/* ③ 입력 완료 및 에러 화면 */}
      {step === 'voice_confirm' && (
        <div className="flex-1 w-full px-6 flex flex-col items-center pt-16 pb-10 animate-pop-in">
          <div className="absolute top-4 left-6 z-30">
            <button 
              onClick={() => {
                setRecognizedText("");
                setSttStatus('idle');
                setIsEditing(false);
                setStep('start');
              }} 
              className="w-14 h-14 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform border border-gray-100"
            >
              <ArrowLeft size={30} color="#333" />
            </button>
          </div>
          <h2 className="text-[34px] font-black text-gray-800 text-center leading-snug mb-12">
            오늘은 어떤 시원한 길을<br/>걸을까요?
          </h2>

          {/* 1. 상태에 따른 아이콘 분기 처리 */}
          {sttStatus === 'processing' && (
            <div className="bg-[#3B82F6] rounded-full p-5 mb-10 shadow-md">
              <Loader2 size={48} color="#FFF" strokeWidth={3} className="animate-spin" />
            </div>
          )}
          {sttStatus === 'success' && (
            <div className="bg-[#3B82F6] rounded-full p-5 mb-10 shadow-md">
              <Check size={48} color="#FFF" strokeWidth={3} />
            </div>
          )}
          {sttStatus === 'error' && (
            <div className="bg-[#EF4444] rounded-full p-5 mb-10 shadow-md">
              <AlertTriangle size={48} color="#FFF" strokeWidth={2.5} />
            </div>
          )}
          
          {/* 2. 에러 시 텍스트 박스 붉은색 계열로 변경 */}
          <div className={`p-8 rounded-[32px] w-full mb-8 shadow-sm flex items-center justify-center min-h-[140px] transition-colors duration-300 ${
            sttStatus === 'error' ? 'bg-[#FEF2F2] border-2 border-[#FECACA]' : 'bg-[#F0F7FF]'
          }`}>
             <textarea
                ref={textareaRef}
                value={recognizedText}
                onChange={(e) => setRecognizedText(e.target.value)}
                disabled={sttStatus === 'processing' || sttStatus === 'error'}
                readOnly={!isEditing}
                className={`w-full text-[24px] font-black leading-relaxed text-center break-keep bg-transparent resize-none focus:outline-none ${
                  sttStatus === 'error' ? 'text-[#991B1B]' : 'text-[#1E3A8A]'
                }`}
                rows={3}
              />
          </div>
          
          {/* 상태에 따른 하단 안내 문구 분기 */}
          {sttStatus === 'error' ? (
            <div className="w-full flex flex-col gap-3 mb-auto">
              <div className="bg-[#FEF2F2] text-[#B91C1C] p-5 rounded-2xl w-full text-[16px] font-bold flex items-center justify-center gap-3 shadow-sm">
                <span className="text-[20px]">⚠️</span> 에러가 발생했습니다. 다시 시도해주세요.
              </div>
              <button onClick={handleManualWrite} className="w-full bg-white border-2 border-[#3B82F6] text-[#3B82F6] py-4 rounded-2xl font-bold text-[18px] active:bg-blue-50 transition-colors shadow-sm">
                직접 작성하기
              </button>
            </div>
          ) : (
            <div className="mb-auto" /> /* 💡 박스 완전히 삭제 후 버튼 여백 유지를 위해 빈 div만 남김 */
          )}

          <div className="flex gap-4 w-full mt-6">
            <button 
              onClick={handleManualWrite} 
              className="flex-1 bg-[#F0F7FF] text-[#3B82F6] py-6 rounded-2xl font-bold text-[22px] active:scale-95 transition-transform shadow-sm"
            >
              직접 쓰기
            </button>
            <button 
              onClick={handleConfirmVoice} 
              disabled={sttStatus === 'processing' || sttStatus === 'error'}
              className={`flex-1 py-6 rounded-2xl font-bold text-[22px] shadow-md transition-all duration-300 ${
                (sttStatus === 'processing' || sttStatus === 'error') 
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                  : 'bg-[#3B82F6] text-white active:scale-95'
              }`}
            >
              확인
            </button>
          </div>
        </div>
      )}

      {/* ④ 프리셋 추천 중 & ⑦ 경로 탐색 중 */}
      {(step === 'analyzing' || step === 'searching') && (
        <div className="flex-1 w-full px-6 flex flex-col items-center justify-center animate-pop-in">
          
          {/* [추가된 부분] 분석 중 에러가 발생했을 때 보여줄 경고 로딩 화면 */}
          {step === 'analyzing' && analyzeError ? (
            <>
              <div className="bg-[#EF4444] rounded-full p-8 shadow-lg mb-12 flex items-center justify-center">
                <AlertTriangle size={72} color="#FFF" strokeWidth={2.5} />
              </div>
              <h2 className="text-[32px] font-black text-gray-800 text-center mb-6 leading-tight break-keep">
                프리셋을 분석할 수<br/>없습니다
              </h2>
              <p className="text-[20px] text-[#EF4444] font-bold mb-12 text-center leading-relaxed">
                서버 연결에 실패했습니다.<br/>다시 시도해주세요.
              </p>
              <button 
                onClick={() => setStep('voice_confirm')} 
                className="w-full bg-[#3B82F6] text-white py-6 rounded-2xl font-bold text-[24px] shadow-md active:bg-blue-600 transition-colors mt-auto mb-6"
              >
                돌아가기
              </button>
            </>
          ) : (
            /* 기존의 정상적인 분석/탐색 로딩 화면 */
            <>
              <div className="bg-[#3B82F6] rounded-full p-8 shadow-lg mb-12 animate-pulse flex items-center justify-center">
                <Search size={72} color="#FFF" strokeWidth={2.5} className="mr-2" />
              </div>
              <h2 className="text-[32px] font-black text-gray-800 text-center mb-6 leading-tight break-keep">
                {step === 'analyzing' ? '프리셋을 분석하고\n있어요!' : '당신에게 딱 맞는\n경로를 찾고 있어요!'}
              </h2>
              <p className="text-[20px] text-gray-400 font-bold mb-12 text-center leading-relaxed">
                {step === 'analyzing' ? '당신의 말을 분석해서\n프리셋을 만들고 있어요!' : '조금만 기다려주세요...'}
              </p>
              <div className="flex gap-3">
                <div className="w-4 h-4 bg-[#3B82F6] rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                <div className="w-4 h-4 bg-[#8BB4F6] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-4 h-4 bg-[#D1E3FF] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
              </div>
            </>
          )}
        </div>
      )}

      {/* ⑤ 프리셋 확인 및 수정 */}
      {step === 'preset' && (
        <div className="absolute inset-0 bg-white z-20 flex flex-col pt-6 pb-6 px-6 animate-pop-in overflow-hidden">
          <div className="flex items-center gap-4 z-30 pt-4">
            <button onClick={() => { setRecognizedText(""); setStep('start'); }} className="w-14 h-14 bg-white rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform border border-gray-100">
              <ArrowLeft size={30} color="#333" />
            </button>
            <p className="text-[#1E88E5] font-black text-[26px]">추천 프리셋</p>
          </div>
          
          <div className="flex-1 w-full mt-6 overflow-y-auto pb-[130px]" style={{ scrollbarWidth: 'none' }}>
            <div className="bg-[#EBF5FF] p-6 rounded-[32px] mb-6">
              <p className="text-[18px] font-bold text-gray-700 mb-4">선택한 조건</p>
              <div className="flex flex-wrap gap-3">{activeTags.map(tag => renderTag(tag, 'active'))}</div>
            </div>

            <div className="bg-white border-[2.5px] border-green-50 p-6 rounded-[32px] mb-4 shadow-sm">
              <p className="text-[20px] font-bold text-gray-700 mb-5">이런 조건도 있어요!</p>
              <div className="flex flex-wrap gap-3">{inactiveTags.map(tag => renderTag(tag, 'inactive'))}</div>
            </div>
          </div>

          <div className="absolute bottom-8 left-6 right-6 flex flex-col z-30 pointer-events-none">
             <div className={`mb-3 text-center text-[#E74C3C] font-bold text-[18px] bg-[#FCECEC]/95 backdrop-blur-sm py-4 px-5 rounded-2xl border border-[#F5B7B1] transition-all duration-300 ${tagError ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              태그는 3개까지 선택해주세요!
            </div>
            
            <button onClick={handleSearchRoutes} className="w-full pointer-events-auto bg-[#0047AB] text-white py-6 rounded-2xl font-bold text-[24px] flex justify-center items-center gap-2 shadow-[0_10px_30px_rgba(0,71,171,0.3)] active:bg-[#003380] active:scale-[0.98] transition-transform">
              경로 추천받기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}