# Minecraft Modpack Translator

AI 기반 마인크래프트 모드팩 자동 번역 도구

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

---

## 📖 소개

마인크래프트 모드팩의 퀘스트, 아이템, UI 등을 LLM(대규모 언어 모델)을 활용하여 자동으로 번역하는 도구입니다.

### 주요 기능

- 🤖 **AI 자동 번역**: OpenAI, Anthropic, Google, Ollama 등 다양한 LLM 지원
- 📦 **다양한 모드 지원**: FTB Quests, KubeJS, Patchouli, Origins 등
- 📚 **용어 사전**: 바닐라 마인크래프트 용어 사전으로 일관된 번역
- 🎨 **GUI 애플리케이션**: 직관적인 인터페이스로 쉬운 사용
- 🌐 **웹 플랫폼**: 번역 공유 및 다운로드 커뮤니티
- 🔄 **자동 배치 처리**: 대량의 텍스트를 효율적으로 번역

---

## 🌐 웹사이트

**[https://mct.2odk.com](https://mct.2odk.com)**

웹사이트에서 다음 기능을 이용할 수 있습니다:

- 📥 **번역 팩 다운로드**: 다른 사용자들이 만든 번역을 다운로드
- 📤 **번역 공유**: 내가 만든 번역을 커뮤니티와 공유
- ⭐ **리뷰 작성**: 번역 품질 평가 및 피드백
- 🔍 **모드팩 검색**: CurseForge 태그로 필터링

### AI 번역으로 커뮤니티에 참여하기

1. 이 GUI 도구로 모드팩을 AI 번역
2. [웹사이트](https://mct.2odk.com)에 번역 업로드
3. 다른 사용자들과 번역 공유 및 피드백 받기

---

## 📥 다운로드

### Windows 실행 파일 (추천)

**[GitHub Releases](https://github.com/kunho-park/minecraft-translator/releases)** 페이지에서 최신 버전을 다운로드하세요.

1. Releases 페이지로 이동
2. 최신 릴리즈에서 `AutoTranslate-X.X.X-windows.exe` 파일 다운로드
3. 다운로드한 `.exe` 파일 실행

> **Windows Defender 경고**: 처음 실행 시 "알 수 없는 앱" 경고가 나타날 수 있습니다.
> "추가 정보" → "실행"을 클릭하여 실행하세요.

### Python 소스 코드

```bash
# 저장소 클론
git clone https://github.com/kunho-park/minecraft-translator.git
cd minecraft-translator

# 의존성 설치
uv sync

# GUI 실행
uv run python -m gui
```

---

## 🚀 빠른 시작

### 1. API 키 설정

LLM 서비스의 API 키가 필요합니다:

- **OpenAI**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Anthropic (Claude)**: [Anthropic Console](https://console.anthropic.com/)
- **Google (Gemini)**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Ollama**: 로컬 설치 (무료)

### 2. 모드팩 선택

1. GUI에서 **모드팩 선택** 버튼 클릭
2. 번역할 모드팩 폴더 선택
3. 번역할 카테고리 선택 (퀘스트, 스크립트 등)

### 3. 번역 설정

- **LLM 제공자**: 사용할 AI 서비스 선택
- **모델**: GPT-4, Claude 3.5 Sonnet 등
- **Temperature**: 번역의 창의성 (0.0 ~ 1.0, 권장: 0.3)
- **Batch Size**: 한 번에 번역할 텍스트 수

### 4. 번역 시작

- **번역 시작** 버튼 클릭
- 진행 상황을 실시간으로 확인
- 완료 후 리소스팩 및 덮어쓰기 파일 다운로드

### 5. 커뮤니티에 공유 (선택사항)

- 웹사이트에 업로드하여 다른 사용자들과 공유
- 피드백을 받고 번역 품질 향상

---

## 📦 지원하는 모드/시스템

### 퀘스트 모드

- ✅ **FTB Quests**: 퀘스트, 챕터, 리워드
- ✅ **HQM (Hardcore Questing Mode)**

### 스크립트/프로그래밍

- ✅ **KubeJS**: JavaScript 스크립트
- ✅ **Origins**: 오리진 설명 및 파워

### 문서/가이드북

- ✅ **Patchouli**: 게임 내 가이드북
- ✅ **Paxi**: 데이터팩 리소스

### 기타

- ✅ **Tinkers' Construct**: 도구 및 재료
- ✅ **Pufferfish's Skills**: 스킬 설명
- ✅ **리소스팩 텍스트**
- ✅ **언어 파일 (.lang, .json)**

---

## 🛠️ 고급 기능

### 용어 사전

바닐라 마인크래프트 용어를 일관되게 번역:

```python
from src.glossary.vanilla_builder import build_vanilla_glossary

# 용어 사전 생성
glossary = build_vanilla_glossary("en_us", "ko_kr")

# 번역에 적용
translator.set_glossary(glossary)
```

### 배치 번역

```python
from src.translator.batch_translator import BatchTranslator

translator = BatchTranslator(
    provider="openai",
    model="gpt-4",
    batch_size=10
)

results = await translator.translate_batch(texts)
```

### CLI 모드

```bash
# 명령줄에서 번역
uv run python main.py translate \
  --modpack ./modpack \
  --output ./output \
  --provider openai \
  --model gpt-4
```

---

## 🌍 지원 언어

- 🇺🇸 **English** (en_us)
- 🇰🇷 **한국어** (ko_kr)
- 🇯🇵 **日本語** (ja_jp)
- 🇨🇳 **简体中文** (zh_cn)
- 🇹🇼 **繁體中文** (zh_tw)

다른 언어도 추가 가능합니다!

---

## 🤝 기여하기

이슈 제보, Pull Request, 번역 공유 모두 환영합니다!

### 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/kunho-park/minecraft-translator.git
cd minecraft-translator

# 의존성 설치
uv sync

# 개발 모드로 실행
uv run python -m gui

# 웹 개발 서버
cd web
bun install
bun run dev
```

### 커밋 컨벤션

- `feat:` 새로운 기능
- `fix:` 버그 수정
- `docs:` 문서 업데이트
- `style:` 코드 포맷팅
- `refactor:` 코드 리팩토링
- `test:` 테스트 추가/수정
- `chore:` 빌드/설정 변경

---

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

---

## 🙏 감사의 말

- [LangChain](https://github.com/langchain-ai/langchain) - LLM 통합 프레임워크
- [PySide6](https://wiki.qt.io/Qt_for_Python) - GUI 프레임워크
- [Next.js](https://nextjs.org/) - 웹 프레임워크
- [CurseForge API](https://docs.curseforge.com/) - 모드팩 정보

---

## 💬 커뮤니티

- **웹사이트**: [https://mct.2odk.com](https://mct.2odk.com)
- **GitHub**: [Issues](https://github.com/kunho-park/minecraft-translator/issues)
- **Discord**: [https://discord.gg/UBkvjNgvYX](https://discord.gg/UBkvjNgvYX)

---

## 📊 프로젝트 구조

```
minecraft-translator/
├── gui/                    # GUI 애플리케이션
│   ├── views/             # 화면 구성
│   ├── widgets/           # UI 컴포넌트
│   └── workers/           # 백그라운드 작업
├── src/                   # 핵심 로직
│   ├── translator/        # 번역 엔진
│   ├── handlers/          # 모드별 처리기
│   ├── parsers/           # 파일 파서
│   ├── glossary/          # 용어 사전
│   └── output/            # 출력 생성
├── web/                   # 웹 애플리케이션
│   ├── src/app/          # Next.js 페이지
│   ├── prisma/           # 데이터베이스 스키마
│   └── public/           # 정적 파일
└── tools/                # 개발 도구
    ├── migrate_old_data.py
    └── build_vanilla_glossary.py
```

---

**Made with ❤️ by 2odk**
