# 🚶‍♂️ Climate-based Navigation App

This is a code bundle for Climate-based Navigation App. The original project is available at [Figma Design Link](https://www.figma.com/design/MvemBSy8sGGAYZr9hq5Jth/Climate-based-Navigation-App).

기후 데이터를 기반으로 수지구의 쾌적한 도보 경로(그늘, 쉼터 등)를 추천해 주는 웹 어플리케이션의 프론트엔드입니다. 사용자의 음성을 인식하여 맞춤형 경로 추천 태그를 생성하고, 카카오맵 API를 통해 경로와 기상 정보를 시각적으로 제공합니다.

## 🔄 Intended Flow (핵심 워크플로우)

The intended flow is: 
`STT` ➡️ `GPT preset extraction` ➡️ `user confirmation/edit` ➡️ `tag-based route recommendation`.

## 🗄️ Backend / preset notes

- The backend now keeps the original Heat Score weights in `data/presets.json`.
- The new preset workflow uses `data/preset_catalog.json`, `data/route_tags.json`, and `data/preset_output_schema.json`.

---

## 🛠 Tech Stack (프론트엔드 기술 스택)

- **Framework:** React 18
- **Language:** TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Map:** Kakao Maps API
- **Audio:** WebRTC (MediaRecorder API)

---

## 🚀 Running the code (설치 및 실행 방법)

## 📦 새롭게 추가된 의존성 (Dependencies)
* `proj4`: 공공 기후/안전 데이터의 TM 좌표계(EPSG:5186)를 카카오맵이 인식할 수 있는 WGS84(위경도, EPSG:4326)로 변환하기 위해 사용됩니다.

## 🗺️ 지도 및 좌표계 안내 (Map & Coordinates)
* **좌표계 자동 변환:** 
  백엔드에서 내려주는 GeoJSON 데이터의 좌표가 `1000` 이상인 경우, 프론트엔드(`proj4`)에서 이를 **EPSG:5186 (TM 중부원점)**으로 간주하고 자동으로 위경도로 변환하여 카카오맵에 렌더링합니다.
* **열 지수(Heat Score) 시각화:** 
  지도에 표시되는 경로의 색상은 구간별 `heat_score`를 기준으로 결정됩니다.
  * 파랑 (#4A90D9): 20 미만 (매우 안전)
  * 초록 (#5DB87C): 20 ~ 22 미만 (안전)
  * 주황 (#F5A623): 22 ~ 24 미만 (주의)
  * 빨강 (#E74C3C): 24 이상 (위험)
* **미니맵 로드 방식 개선:**
  리스트 화면(`RouteResultScreen`) 렌더링 시 카카오맵 SDK를 동적으로 `<head>`에 주입(`script.src`)하여 비동기 환경에서도 지도가 안정적으로 노출되도록 개선했습니다.

### 1. Install Dependencies
Run `npm i` to install the dependencies.

*(참고: 워크스페이스 구성 시 아래 패키지들이 `package.json`에 포함되어 있어야 합니다. 누락된 경우 아래 명령어로 직접 설치하세요.)*
```bash
# 기본 모듈 설치
npm i

# UI 아이콘 패키지 (필수)
npm install lucide-react
