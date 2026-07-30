interface Props {
  transcript: string;
  onBack: () => void;
  onConfirm: () => void;
}

export default function ConfirmInput({ transcript, onBack, onConfirm }: Props) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 p-6">
      <div className="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center">
        <div className="w-14 h-14 rounded-full bg-green-500 text-white flex items-center justify-center">✓</div>
      </div>
      <h2 className="text-xl font-bold">입력 완료</h2>
      <div className="p-4 bg-white rounded-xl shadow-sm max-w-[320px] text-center">
        <div className="text-sm text-gray-700 font-medium">인식된 내용</div>
        <div className="mt-2 text-gray-600">"{transcript}"</div>
      </div>
      <div className="flex gap-3 mt-6">
        <button className="px-4 py-2 rounded-md bg-gray-200" onClick={onBack}>다시 말하기</button>
        <button className="px-4 py-2 rounded-md bg-green-600 text-white" onClick={onConfirm}>확인</button>
      </div>
    </div>
  );
}
