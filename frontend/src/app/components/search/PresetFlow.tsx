import { useState } from 'react';

interface Props {
  initialSelected: string[];
  initialSuggested: string[];
  onApply: (finalTags: string[]) => void;
}

function Tag({ label, color, onClick }: { label: string; color?: string; onClick?: () => void }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1 rounded-full text-sm mr-2 mb-2"
      style={{ background: color || '#D1FAE5' }}
    >
      {label}
    </button>
  );
}

export default function PresetFlow({ initialSelected, initialSuggested, onApply }: Props) {
  const [selected, setSelected] = useState<string[]>(initialSelected);
  const [suggested, setSuggested] = useState<string[]>(initialSuggested.filter(t => !initialSelected.includes(t)));

  function toggleTag(tag: string) {
    if (selected.includes(tag)) {
      setSelected(s => s.filter(x => x !== tag));
      setSuggested(s => [tag, ...s]);
    } else {
      setSelected(s => [tag, ...s].slice(0, 5));
      setSuggested(s => s.filter(x => x !== tag));
    }
  }

  return (
    <div className="flex-1 flex flex-col p-4">
      <h3 className="text-lg font-semibold">프리셋 확인 및 수정</h3>
      <div className="mt-4">
        <div className="text-sm text-gray-500 mb-2">선택된 조건</div>
        <div className="flex flex-wrap items-center">
          {selected.map(t => (
            <Tag key={t} label={t} color="#86efac" onClick={() => toggleTag(t)} />
          ))}
        </div>
      </div>

      <div className="mt-3">
        <div className="text-sm text-gray-500 mb-2">이런 조건도 있어요!</div>
        <div className="flex flex-wrap items-center">
          {suggested.map(t => (
            <Tag key={t} label={t} color="#bae6fd" onClick={() => toggleTag(t)} />
          ))}
        </div>
      </div>

      <div className="mt-auto pb-6">
        <button className="w-full py-3 rounded-xl bg-green-600 text-white" onClick={() => onApply(selected)}>
          경로 추천받기
        </button>
      </div>
    </div>
  );
}
