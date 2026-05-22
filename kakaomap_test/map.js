// 1. 지도를 담을 DOM 영역을 선택합니다.
const container = document.getElementById('map');

// 2. 지도의 중심 좌표와 확대 수준(레벨)을 설정합니다.
// 기획서 기준 타겟 지역인 '수지구청'의 위경도입니다.
const options = {
    center: new kakao.maps.LatLng(37.3219, 127.0972), // 수지구청 좌표
    level: 5 // 확대 수준 (숫자가 작을수록 확대, 클수록 축소)
};

// 3. 지도를 생성합니다.
const map = new kakao.maps.Map(container, options);

console.log("카카오맵 로드 완료! 중심 좌표: 수지구청");
