# 바닐라 용어집 생성 가이드

## 개요

마인크래프트 공식 번역 파일을 사용하여 모든 모드팩 번역의 기본이 되는 바닐라 용어집을 생성합니다.

## 준비물

1. **마인크래프트 공식 언어 파일**

   - 마인크래프트 클라이언트에서 추출하거나 공식 리소스에서 다운로드
   - 필요한 파일:
     - `en_us.json` (원문 언어)
     - `ko_kr.json` (번역 언어)
     - 또는 원하는 다른 언어 조합
2. **언어 파일 위치 예시**

   ```
   .minecraft/assets/indexes/         # 인덱스 파일
   .minecraft/assets/objects/         # 실제 파일들
   ```

## 사용 방법

### 1. 바닐라 용어집 생성

```bash
# 기본 사용 (영어 -> 한국어)
# 자동으로 src/glossary/vanilla_glossaries/vanilla_glossary_en_us_ko_kr.json에 저장됨
uv run python tools/build_vanilla_glossary.py \
  --source path/to/en_us.json \
  --target path/to/ko_kr.json

# 다른 언어 조합 (예: 영어 -> 일본어)
# 자동으로 src/glossary/vanilla_glossaries/vanilla_glossary_en_us_ja_jp.json에 저장됨
uv run python tools/build_vanilla_glossary.py \
  --source path/to/en_us.json \
  --target path/to/ja_jp.json \
  --source-locale en_us \
  --target-locale ja_jp

# 커스텀 출력 위치 지정 (선택사항)
uv run python tools/build_vanilla_glossary.py \
  --source path/to/en_us.json \
  --target path/to/ko_kr.json \
  --output custom/path/glossary.json
```

### 2. 자동 저장 및 로드

용어집은 다음과 같이 자동 처리됩니다:

**저장 위치:**

```
src/glossary/vanilla_glossaries/
```

**파일명 규칙:**

```
vanilla_glossary_{source_locale}_{target_locale}.json
```

**예시:**

- `vanilla_glossary_en_us_ko_kr.json` - 영어 → 한국어
- `vanilla_glossary_en_us_ja_jp.json` - 영어 → 일본어
- `vanilla_glossary_en_us_zh_cn.json` - 영어 → 중국어

### 3. 자동 로드 확인

번역 시작 시:

- ✅ 현재 언어 쌍에 맞는 바닐라 용어집 자동 검색
- ✅ 발견되면 자동으로 로드하여 베이스로 사용
- ✅ 모드팩 전용 용어집을 LLM으로 생성
- ✅ 바닐라 + 모드팩 용어집 병합 (모드팩 용어가 우선)
- ✅ 일관된 바닐라 용어 번역 보장

## 용어집 구조

생성된 용어집은 다음 카테고리로 구성됩니다:

- **block**: 블록 관련 용어
- **item**: 아이템 관련 용어
- **entity**: 엔티티/몹 관련 용어
- **effect**: 효과/인챈트 관련 용어
- **biome**: 바이옴 관련 용어
- **ui**: GUI/메뉴 관련 용어
- **other**: 기타 용어

## 예시 출력

**파일명:** `vanilla_glossary_en_us_ko_kr.json`

```json
{
  "term_rules": [
    {
      "term_ko": "돌",
      "preferred_style": "Official Minecraft translation",
      "aliases": ["Stone"],
      "category": "block",
      "notes": "From vanilla: block.minecraft.stone"
    },
    {
      "term_ko": "다이아몬드 검",
      "preferred_style": "Official Minecraft translation",
      "aliases": ["Diamond Sword"],
      "category": "item",
      "notes": "From vanilla: item.minecraft.diamond_sword"
    }
  ],
  "proper_noun_rules": [],
  "formatting_rules": []
}
```

**다른 언어 쌍:**

- `vanilla_glossary_en_us_ja_jp.json` - 일본어 번역용
- `vanilla_glossary_en_us_zh_cn.json` - 중국어 번역용

## 고급 사용법

### Python 모듈로 직접 사용

```python
from pathlib import Path
from src.glossary.vanilla_builder import VanillaGlossaryBuilder

# 빌더 생성
builder = VanillaGlossaryBuilder(
    source_lang_file=Path("en_us.json"),
    target_lang_file=Path("ko_kr.json"),
    source_locale="en_us",
    target_locale="ko_kr"
)

# 용어집 빌드
glossary = builder.build(output_path=Path("vanilla_glossary.json"))

# 용어집 확인
print(f"Total terms: {len(glossary.term_rules)}")
```

### 용어집 수동 편집

생성 후 `vanilla_glossary.json`을 직접 편집하여:

- 불필요한 용어 제거
- 번역 스타일 조정
- 고유명사 규칙 추가 (`proper_noun_rules`)
- 포맷팅 규칙 추가 (`formatting_rules`)

## 마인크래프트 언어 파일 추출 방법

### 방법 1: 런처에서 추출

```bash
# .minecraft 폴더 찾기
# Windows: %APPDATA%\.minecraft
# macOS: ~/Library/Application Support/minecraft
# Linux: ~/.minecraft

# 버전별 에셋 인덱스 확인
cd .minecraft/assets/indexes

# 에셋 찾기 (해시 기반)
cd .minecraft/assets/objects
```

### 방법 2: 온라인 리소스

- [Minecraft Wiki](https://minecraft.wiki/)
- [Slicedlime&#39;s Translation Repository](https://github.com/slicedlime/translations)
- 커뮤니티 제공 언어 파일

### 방법 3: JAR에서 직접 추출

```bash
# 마인크래프트 JAR 파일 찾기
cd .minecraft/versions/1.20.1

# JAR 압축 해제
unzip 1.20.1.jar -d extracted/

# 언어 파일 위치
cd extracted/assets/minecraft/lang/
```

## 트러블슈팅

### 용어집이 로드되지 않음

1. 파일명 확인: `vanilla_glossary_{source}_{target}.json` 형식인지 확인
   - 예: `vanilla_glossary_en_us_ko_kr.json`
2. 파일 위치 확인: `src/glossary/vanilla_glossaries/` 디렉토리에 있는지 확인
3. 언어 쌍 일치: 번역 설정의 언어 쌍과 파일명이 일치하는지 확인
4. JSON 형식 유효성 검증
5. 로그 확인: "Loaded vanilla glossary" 또는 "No vanilla glossary found" 메시지

### 중복 용어 문제

- 바닐라 용어집의 용어는 모드팩 용어집에 의해 덮어쓰여집니다
- 모드팩별 커스텀 번역이 우선 적용됨

### 용어가 너무 많음

생성 후 수동으로 필터링:

```python
import json

with open("vanilla_glossary.json", "r", encoding="utf-8") as f:
    glossary = json.load(f)

# 특정 카테고리만 유지
filtered = {
    "term_rules": [
        term for term in glossary["term_rules"]
        if term["category"] in ["block", "item", "entity"]
    ],
    "proper_noun_rules": [],
    "formatting_rules": []
}

with open("vanilla_glossary_filtered.json", "w", encoding="utf-8") as f:
    json.dump(filtered, f, ensure_ascii=False, indent=2)
```

## 업데이트 주기

새로운 마인크래프트 버전 출시 시:

1. 최신 언어 파일 다운로드
2. 용어집 재생성
3. 기존 용어집과 병합 또는 교체

## 참고사항

- 용어집 크기: 일반적으로 3,000~5,000개 용어
