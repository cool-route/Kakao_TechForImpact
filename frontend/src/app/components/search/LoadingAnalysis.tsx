import { useEffect } from 'react';
import { analyzeTranscript } from '../../api/searchApi';

interface Props {
  transcript: string;
  onDone: (tags: string[]) => void;
}

export default function LoadingAnalysis({ transcript, onDone }: Props) {
  useEffect(() => {
    let mounted = true;
    analyzeTranscript(transcript).then((res) => {
      if (!mounted) return;
      onDone(res.tags);
    }).catch(() => {
      if (!mounted) return;
      onDone([]);
    });

    return () => { mounted = false; };
  }, [transcript, onDone]);

  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4">
      <h3 className="text-lg font-semibold">프리셋을 분석하고 있어요!</h3>
      <p className="text-sm text-gray-500">당신의 말을 분석해서 프리셋을 만들고 있어요.</p>
      <div className="mt-6">
        <div className="loader" />
      </div>
      <button className="mt-8 text-sm text-gray-400">건너뛰기</button>
    </div>
  );
}
