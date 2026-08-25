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

### 1. Install Dependencies
Run `npm i` to install the dependencies.

*(참고: 워크스페이스 구성 시 아래 패키지들이 `package.json`에 포함되어 있어야 합니다. 누락된 경우 아래 명령어로 직접 설치하세요.)*
```bash
# 기본 모듈 설치
npm i

# UI 아이콘 패키지 (필수)
npm install lucide-react
