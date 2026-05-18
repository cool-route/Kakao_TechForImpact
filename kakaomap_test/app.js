// 1. 더미 데이터
const routeSpecs = [
    { id: 1, mode: "노약자", name: "수지구청 -> 죽전역 쉼터 경유", start: [37.3219, 127.0972], end: [37.3247, 127.1245] },
    { id: 2, mode: "노약자", name: "수지도서관 -> 죽전역", start: [37.3232, 127.101], end: [37.3247, 127.1245] },
    { id: 3, mode: "반려동물", name: "탄천 강아지 산책로", start: [37.32, 127.10], end: [37.33, 127.11] }
];
const sampleNodeData = { utci: 27.220548, heat: 30.070146, shade: 0.600020, wind: 2.572554, score: 19.532003 };

let currentMode = '전체';

// 2. DOM 요소 선택
const container = document.getElementById('route-list-container');
const filterButtons = document.querySelectorAll('.mode-filters button');
const bottomSheet = document.getElementById('bottom-sheet');
const closeSheetBtn = document.getElementById('close-sheet-btn');

// 3. 경로 리스트 렌더링 함수
function renderRoutes(mode) {
    container.innerHTML = ''; // 기존 목록 초기화
    
    // 모드 필터링
    const filteredRoutes = mode === '전체' ? routeSpecs : routeSpecs.filter(route => route.mode === mode);
    
    if (filteredRoutes.length === 0) {
        container.innerHTML = '<p>해당 조건의 경로가 없습니다.</p>';
        return;
    }

    // HTML 생성하여 추가
    filteredRoutes.forEach(route => {
        const card = document.createElement('div');
        card.className = 'route-card';
        card.innerHTML = `
            <h3>${route.name}</h3>
            <span class="badge">${route.mode} 맞춤</span>
            <button class="select-btn" onclick="showRouteDetails(${route.id})">이 경로 선택</button>
        `;
        container.appendChild(card);
    });
}

// 4. 모드 필터 버튼 클릭 이벤트
filterButtons.forEach(button => {
    button.addEventListener('click', (e) => {
        // 활성화된 버튼 색상 변경
        filterButtons.forEach(btn => btn.classList.remove('active'));
        e.target.classList.add('active');
        
        // 데이터 다시 그리기 및 패널 닫기
        currentMode = e.target.dataset.mode;
        renderRoutes(currentMode);
        bottomSheet.style.display = 'none'; 
    });
});

// 5. 바텀 시트 열기 (경로 클릭 시 호출됨)
window.showRouteDetails = function(id) {
    document.getElementById('ui-utci').innerText = sampleNodeData.utci.toFixed(1);
    document.getElementById('ui-shade').innerText = (sampleNodeData.shade * 100).toFixed(0);
    document.getElementById('ui-wind').innerText = sampleNodeData.wind.toFixed(1);
    document.getElementById('ui-score').innerText = sampleNodeData.score.toFixed(0);
    
    bottomSheet.style.display = 'block';
};

// 바텀 시트 닫기
closeSheetBtn.addEventListener('click', () => {
    bottomSheet.style.display = 'none';
});

// 초기 실행
renderRoutes(currentMode);
