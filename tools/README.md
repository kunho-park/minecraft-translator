# 바닐라 용어집 생성 도구

## 빠른 시작

```bash
# 마인크래프트 언어 파일로 바닐라 용어집 생성
uv run python tools/build_vanilla_glossary.py \
  --source path/to/en_us.json \
  --target path/to/ko_kr.json
```

**자동으로 다음 위치에 저장됩니다:**
```
src/glossary/vanilla_glossaries/vanilla_glossary_en_us_ko_kr.json
```

## 다른 언어 쌍

```bash
# 영어 → 일본어
uv run python tools/build_vanilla_glossary.py \
  --source path/to/en_us.json \
  --target path/to/ja_jp.json \
  --source-locale en_us \
  --target-locale ja_jp
# 저장 위치: src/glossary/vanilla_glossaries/vanilla_glossary_en_us_ja_jp.json

# 영어 → 중국어 간체
uv run python tools/build_vanilla_glossary.py \
  --source path/to/en_us.json \
  --target path/to/zh_cn.json \
  --source-locale en_us \
  --target-locale zh_cn
# 저장 위치: src/glossary/vanilla_glossaries/vanilla_glossary_en_us_zh_cn.json
```

## 작동 방식

1. **용어집 생성**: 마인크래프트 공식 번역에서 용어 추출
2. **자동 저장**: `vanilla_glossary_{source}_{target}.json` 형식으로 저장
3. **자동 로드**: 번역 시 해당 언어 쌍의 용어집 자동 사용

## 상세 가이드

`VANILLA_GLOSSARY_GUIDE.md` 참고
