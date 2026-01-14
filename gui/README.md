# 모드팩 번역기 GUI

PySide6 + qfluentwidgets를 사용한 아름다운 Fluent Design GUI입니다.

## 기능

### 주요 기능
- 🎨 **Fluent Design**: 모던하고 아름다운 Windows 11 스타일 UI
- 🌍 **다중 언어 지원**: 한국어/영어 UI (쉽게 확장 가능)
- 🚀 **성능 최적화**: 수백 개 모드 처리를 위한 최적화
  - 가상 스크롤링 트리뷰
  - 백그라운드 스레딩
  - 100ms 진행률 업데이트 throttling
- 🔄 **자동 런처 감지**: CurseForge, Prism Launcher, MultiMC
- 📊 **실시간 진행률**: 번역 진행 상황 실시간 모니터링
- 🔁 **재시도 시스템**: 실패한 번역 자동 재시도
- 📤 **웹 업로드**: 번역 결과를 웹사이트에 바로 업로드

### 번역 워크플로우
1. **시작 화면**: 번역 또는 다운로드 선택
2. **모드팩 선택**: 자동 감지 또는 수동 선택
3. **스캔 & 설정**: 언어 및 LLM 설정
4. **파일 선택**: 번역할 파일/카테고리 선택
5. **번역 진행**: 실시간 진행률 모니터링
6. **재시도**: 실패한 번역 처리
7. **리뷰**: LLM 기반 번역 품질 검토
8. **업로드**: 웹사이트에 업로드 (선택)
9. **완료**: 최종 통계 및 파일 위치

## 실행 방법

### GUI 실행
```bash
# 모듈로 실행
uv run python -m gui

# 또는 직접 실행
uv run python gui/main.py
```

### 언어 변경
GUI는 설정에 따라 한국어/영어를 지원합니다. 언어는 첫 실행 시 자동으로 한국어로 설정됩니다.

설정 파일 위치:
- Windows: `C:\Users\<사용자>\AppData\Local\mcat\auto-translate\config.json`
- Linux: `~/.config/mcat/auto-translate/config.json`

설정에서 `"language": "en"` 또는 `"language": "ko"`로 변경 가능합니다.

## 구조

```
gui/
├── __init__.py
├── __main__.py          # 모듈 진입점
├── main.py              # 앱 진입점
├── app.py               # MainWindow & 네비게이션
├── config.py            # 설정 관리
│
├── i18n/                # 다중 언어 지원
│   ├── __init__.py
│   ├── translator.py    # 번역 시스템
│   └── translations/
│       ├── ko.json      # 한국어
│       └── en.json      # 영어
│
├── views/               # 각 단계별 뷰
│   ├── welcome.py       # 시작 화면
│   ├── modpack_select.py # 모드팩 선택
│   ├── scan_result.py   # 스캔 결과 & 설정
│   ├── category_select.py # 파일 선택
│   ├── translation_progress.py # 번역 진행
│   ├── retry.py         # 재시도
│   ├── review.py        # 리뷰
│   ├── upload.py        # 업로드
│   └── completion.py    # 완료
│
├── workers/             # 백그라운드 작업
│   ├── scanner_worker.py # 스캔 워커
│   ├── translation_worker.py # 번역 워커
│   └── upload_worker.py # 업로드 워커
│
├── widgets/             # 커스텀 위젯
│   ├── modpack_tree.py  # 가상 스크롤링 트리
│   ├── progress_card.py # 진행률 카드
│   └── stats_card.py    # 통계 카드
│
└── styles/              # QSS 스타일
    └── app.qss          # 커스텀 스타일
```

## 성능 최적화

### 가상 스크롤링 트리
- 수백 개의 파일을 효율적으로 렌더링
- 보이는 영역만 렌더링하여 메모리 절약
- 모드별 그룹화로 구조화된 뷰

### 백그라운드 스레딩
- 모든 무거운 작업은 별도 스레드에서 실행
- UI는 항상 반응성 유지
- QThread 기반 워커 패턴

### 진행률 업데이트 Throttling
- 100ms 간격으로 UI 업데이트 제한
- 불필요한 리페인트 방지
- 부드러운 애니메이션

## 기술 스택

- **PySide6**: Qt 6 Python 바인딩
- **qfluentwidgets**: Fluent Design 위젯 라이브러리
- **platformdirs**: 크로스 플랫폼 설정 디렉토리
- **기존 번역 파이프라인**: 완벽하게 통합

## 스크린샷

(GUI 스크린샷은 실행 후 추가 예정)

## 라이선스

이 프로젝트는 기존 auto-translate 프로젝트의 일부입니다.
