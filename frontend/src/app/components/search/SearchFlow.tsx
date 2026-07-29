import { useState } from 'react';
import VoiceRecorder from './VoiceRecorder';
import ConfirmInput from './ConfirmInput';
import LoadingAnalysis from './LoadingAnalysis';
import PresetFlow from './PresetFlow';
import ResultsFlow from './ResultsFlow';

type FlowStep = 'start' | 'voice' | 'confirm' | 'analyzing' | 'preset' | 'results' | 'map';

export default function SearchFlow() {
  const [step, setStep] = useState<FlowStep>('start');
  const [transcript, setTranscript] = useState<string>('');
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);

  return (
    <div className="w-full h-full flex flex-col p-4">
      {step === 'start' && (
        <div className="flex-1 flex flex-col items-center justify-center gap-6">
          <h2 className="text-2xl font-bold">오늘은 어떤 길을 산책할까요?</h2>
          <p className="text-center text-sm text-gray-600 max-w-[300px]">음성으로 원하는 산책 조건을 말해주세요. 태그를 추출해 최적의 코스를 추천합니다.</p>
          <button
            className="mt-4 px-6 py-3 rounded-xl bg-green-600 text-white font-semibold"
            onClick={() => setStep('voice')}
          >
            시작하기
          </button>
        </div>
      )}

      {step === 'voice' && (
        <VoiceRecorder
          onCancel={() => setStep('start')}
          onComplete={(text) => {
            setTranscript(text);
            setStep('confirm');
          }}
        />
      )}

      {step === 'confirm' && (
        <ConfirmInput
          transcript={transcript}
          onBack={() => setStep('voice')}
          onConfirm={() => setStep('analyzing')}
        />
      )}

      {step === 'analyzing' && (
        <LoadingAnalysis
          transcript={transcript}
          onDone={(extractedTags: string[]) => {
            // placeholder: tags come from backend API in future
            setTags(extractedTags);
            setSelectedTags(extractedTags.slice(0, 3));
            setStep('preset');
          }}
        />
      )}

      {step === 'preset' && (
        <PresetFlow
          initialSelected={selectedTags}
          initialSuggested={tags}
          onApply={(finalTags) => {
            // send finalTags to backend to get route suggestions
            setSelectedTags(finalTags);
            setStep('results');
          }}
        />
      )}

      {step === 'results' && (
        <ResultsFlow
          tags={selectedTags}
          onSelectRoute={() => setStep('map')}
        />
      )}

      {step === 'map' && (
        <div className="flex-1 flex flex-col items-center justify-center">
          {/* Map preview is handled inside ResultsFlow / MapPreview in a full implementation. */}
          <h3 className="text-lg font-semibold">지도 미리보기(예시)</h3>
        </div>
      )}
    </div>
  );
}
