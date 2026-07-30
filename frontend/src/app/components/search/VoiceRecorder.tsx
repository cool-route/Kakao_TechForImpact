import { useEffect, useState } from 'react';

interface Props {
  onCancel: () => void;
  onComplete: (text: string) => void;
}

export default function VoiceRecorder({ onCancel, onComplete }: Props) {
  const [listening, setListening] = useState(true);
  const [partial, setPartial] = useState('');

  useEffect(() => {
    // Placeholder: integrate Web Speech API or other recorder
    let mounted = true;
    // Simulate listening and partial transcript
    const timer = setTimeout(() => {
      if (!mounted) return;
      setPartial('한강 근처 30분 코스 추천해줘');
    }, 1200);

    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, []);

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4">
      <h2 className="text-xl font-bold">음성 입력 중</h2>
      <div className="w-32 h-32 rounded-full bg-green-100 flex items-center justify-center">
        <div className="w-20 h-20 rounded-full bg-green-500" />
      </div>
      <div className="text-sm text-gray-600">듣고 있어요...</div>
      <div className="p-3 rounded-lg bg-white/80 shadow-md mt-4">{partial || '...'}</div>

      <div className="flex gap-3 mt-6">
        <button className="px-4 py-2 rounded-md bg-gray-200" onClick={() => { setListening(false); onCancel(); }}>
          입력 중지
        </button>
        <button className="px-4 py-2 rounded-md bg-green-600 text-white" onClick={() => { setListening(false); onComplete(partial || ''); }}>
          완료 (테스트)
        </button>
      </div>
    </div>
  );
}
