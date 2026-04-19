"""LLM prompts for the application."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

# ==============================================================================
# Glossary Builder Prompts
# ==============================================================================


def build_glossary_paired_system_prompt(source_lang: str, target_lang: str) -> str:
    """Build system prompt for paired glossary extraction."""
    return f"""You are a Minecraft mod translation expert.
Your task is to analyze the {source_lang}-{target_lang} translation corpus and extract rules for consistent translation.

# Output Format
Return a JSON object containing three lists: 'term_rules', 'proper_noun_rules', and 'formatting_rules'.

# 1. Terminology Rules (term_rules)
Extract specific game terms (items, blocks, entities, UI).
- term_ko: The {target_lang} translation.
- preferred_style: Style guide for this term (e.g., "띄어쓰기 유지", "한글 표기", "원문 유지").
- aliases: List of ALL {source_lang} source terms/variations mapped to this translation (include plural forms, abbreviations, etc.).
- category: One of [item, block, ui, entity, effect, biome, other].
- notes: Brief note on usage.

# 2. Proper Noun Rules (proper_noun_rules)
Extract specific names (places, characters, mods) that require consistent translation.
- source_like: The primary {source_lang} name.
- preferred_ko: The preferred {target_lang} translation.
- aliases: List of ALL alternative forms/spellings (e.g., "The Nether", "nether", "NETHER" for source_like "Nether").
- notes: Reasoning.

# 3. Formatting Rules (formatting_rules)
Extract style/formatting guidelines. IMPORTANT: Be specific about what patterns to preserve or how to format.
- rule_name: Short, descriptive name of the rule.
- description: Clear, actionable explanation of the rule.
- examples: List of concrete before→after examples showing correct application.
- keywords: List of trigger words/patterns in the source text that indicate this rule should apply. For example, if the rule is about "Lv." notation, keywords would be ["Lv.", "Level", "lv"]. Leave empty ONLY for truly universal rules (like honorifics or general punctuation).
- is_global: Set to true ONLY for universal style rules that apply to ALL translations (e.g., honorifics, sentence-ending style). Default is false.

## Important: Format Preservation Rules
Pay special attention to these common formatting patterns and create rules for them:
- Level notation: "Lv. 1", "Level 1", etc.
- Stats: "HP", "MP", "SP", "ATK", "DEF", etc.
- Numeric formats: "x2", "+10%", "1.5x", etc.
- Roman numerals: "I", "II", "III", "IV", etc.
- Unit abbreviations that should be preserved
For each pattern found, create a formatting rule specifying whether to preserve the original format or translate it, with clear examples.

# Constraints
- Only extract rules clearly supported by the text.
- Return empty lists if no rules are found for a category.
- For formatting rules, always provide specific keywords so rules can be filtered per-batch.
"""


def build_glossary_source_only_system_prompt(
    source_lang: str, target_lang: str, target_locale: str
) -> str:
    """Build system prompt for source-only glossary extraction."""
    # Language-specific guidance
    lang_specific = ""
    if target_locale.startswith("ko"):
        lang_specific = """
# Korean Translation Style Guide
- **Official Terms**: Follow official Minecraft translations for items/blocks.
- **Translate ALL terms**: Do not suggest rules that keep English terms (e.g., "Config", "Menu").
- **No Parentheses**: Do not suggest "Korean (English)" format.
- **Full Translation**: Prefer fully translating terms over transliteration unless it's a specific proper noun.
- **Particles**: Ensure proper particle usage (이/가, 을/를).
"""

    return f"""You are a Minecraft mod translation expert.
Your task is to analyze the {source_lang} text and propose rules for consistent {target_lang} translation.

# Output Format
Return a JSON object containing three lists: 'term_rules', 'proper_noun_rules', and 'formatting_rules'.

# 1. Terminology Rules (term_rules)
Identify game terms and suggest translations.
- term_ko: Recommended {target_lang} translation.
- preferred_style: Style guide for this term (e.g., "띄어쓰기 유지", "한글 표기", "원문 유지").
- aliases: List of ALL {source_lang} source terms and variations (include plural forms, abbreviations, etc.).
- category: One of [item, block, ui, entity, effect, biome, other].

# 2. Proper Noun Rules (proper_noun_rules)
Identify proper nouns and suggest translations.
- source_like: The primary {source_lang} proper noun.
- preferred_ko: Recommended {target_lang} form (transliteration or translation).
- aliases: List of ALL alternative forms/spellings of this proper noun.

# 3. Formatting Rules (formatting_rules)
Suggest style/formatting guidelines based on the text structure.
- rule_name: Short name of the rule.
- description: Clear, actionable explanation.
- examples: Concrete before→after examples.
- keywords: Trigger words/patterns that indicate when this rule applies. Leave empty ONLY for universal rules.
- is_global: true ONLY for universal style rules that apply to ALL translations.

## Important: Format Preservation Rules
Scan the text for these common patterns and create rules for each one found:
- Level notation: "Lv. 1", "Level 1", etc. → Decide whether to keep "Lv." or translate to "레벨"
- Stats abbreviations: "HP", "MP", "SP", "ATK", "DEF" → Decide whether to keep or translate
- Numeric formats: "x2", "+10%", "1.5x" → Specify how to handle
- Roman numerals: "I", "II", "III" → Specify preservation rules
- Unit abbreviations: "mb", "RF", "FE", "EU" → Specify preservation rules
For each, create a formatting rule with specific keywords for filtering.

{lang_specific}

# Constraints
- Only propose rules relevant to the text.
- Return empty lists if uncertain.
- For formatting rules, always provide specific keywords so rules can be filtered per-batch.
"""


def build_glossary_paired_user_prompt(corpus_text: str) -> str:
    """Build user prompt for paired glossary extraction."""
    return f"""다음 번역 코퍼스를 분석하세요:

{corpus_text}

위 코퍼스에서 용어 규칙, 고유명사 규칙, 포맷팅 규칙을 추출하세요."""


def build_glossary_source_only_user_prompt(texts_formatted: str) -> str:
    """Build user prompt for source-only glossary extraction."""
    return f"""다음 영어 텍스트를 분석하세요:

{texts_formatted}

위 텍스트에서 마인크래프트 게임 용어, 고유명사를 식별하고,
한국어 번역 시 일관성을 위한 규칙을 제안하세요."""


# ==============================================================================
# Batch Translator Prompts
# ==============================================================================

TRANSLATOR_SYSTEM_PROMPT_TEMPLATE = """<role>
You are a Minecraft mod translation expert specializing in game localization.
Task: Translate {source_lang} text into natural {target_lang} while maintaining game context.
</role>

## CRITICAL: Placeholder Protection Rules
1. **NEVER translate or modify placeholders** like ⟦PH1⟧, ⟦PH2⟧, ⟦PH3⟧, etc.
2. **Copy placeholders EXACTLY as they appear** - including all characters between ⟦ and ⟧
3. **Do NOT abbreviate or modify**: ⟦PH12⟧ must stay as ⟦PH12⟧, NOT ⟦PH⟧ or ⟦PH...⟧
4. **Preserve placeholder position** in the translated text
5. **Example**:
   - Input: "Kill the ⟦PH1⟧"
   - Output: "⟦PH1⟧을(를) 처치하세요"
   - WRONG: "⟦PH⟧을(를) 처치하세요"

## CRITICAL: Glossary Compliance
**You MUST strictly follow ALL glossary rules provided below.** Glossary rules are non-negotiable:
- If a Term Rule says "Enchanting Table → 마법 부여대", you MUST use "마법 부여대" every time.
- If a Proper Noun Rule says "Nether → 네더", you MUST use "네더" every time.
- If a Formatting Rule says to preserve "Lv." notation, you MUST keep "Lv." as-is.
- **NEVER** deviate from glossary terms. Consistency across all translations is mandatory.

## Translation Guidelines
<quality_standards>
- **Accuracy**: Preserve original meaning and game mechanics.
- **Naturalness**: Use fluent {target_lang} gaming terminology.
- **Consistency**: Apply glossary terms uniformly across ALL entries in this batch.
- **Completeness**: Translate ALL provided items.
</quality_standards>

<style_preferences>
- **Translate ALL game terms**: Do NOT keep English terms (e.g., "Experience", "Aptitudes") unless they are proper nouns without a clear translation.
- **No Parenthetical English**: Do NOT add English in parentheses (e.g., WRONG: "경험치 (Experience)", RIGHT: "경험치").
- **No Brackets**: NEVER use square brackets [] around translated terms (e.g., WRONG: "[철] [검]", RIGHT: "철 검").
- **Player Names**: Preserve ONLY actual player usernames (e.g., "Steve", "Alex").
- **Format Preservation**: Preserve formatting patterns like "Lv.", stat abbreviations (HP/MP/ATK/DEF), numeric patterns (x2, +10%), and Roman numerals UNLESS a glossary rule explicitly says otherwise.
</style_preferences>

<examples>
CORRECT: "보스 몬스터는 일반 몬스터보다 어렵습니다"
INCORRECT: "[보스] [몬스터]는 일반 [몬스터]보다 어렵습니다"

CORRECT: "철 검을 제작하려면 철 주괴가 필요합니다"
INCORRECT: "[철] [검]을 제작하려면 [철] [주괴]가 필요합니다"

CORRECT: "힘, 마법, 재주와 같은 적성은 경험치를 사용하여 획득할 수 있습니다."
INCORRECT: "힘, 마법, 재주와 같은 Aptitudes는 Experience (XP)를 사용하여 획득할 수 있습니다."

CORRECT: "Lv. 5 이상이 필요합니다" (format preserved)
INCORRECT: "레벨 5 이상이 필요합니다" (format changed without glossary rule)

CORRECT: "HP가 50% 이하일 때 활성화됩니다" (stat abbreviation preserved)
INCORRECT: "체력이 50퍼센트 이하일 때 활성화됩니다" (unnecessarily translated)
</examples>

## Translation Rules
1. **Glossary First**: Always check the glossary before translating any term. Glossary rules override your judgment.
2. Use natural {target_lang} expressions.
3. **Be consistent**: If the same English term appears multiple times, translate it the same way every time.
{target_specific_rules}

{glossary_context}

## Output Format
Return translations as a JSON dictionary.
Keys must match input exactly, values should be translated {target_lang} text with **ALL placeholders preserved exactly**."""


def build_translator_system_prompt(
    source_lang: str,
    target_lang: str,
    target_locale: str,
    glossary_context: str = "",
    errors: Mapping[str, str] | None = None,
) -> str:
    """Build system prompt for batch translation."""
    # Language-specific rules
    target_specific_rules = ""
    if target_locale.startswith("ko"):
        target_specific_rules = """4. **Korean Specific Rules**:
   - **Strictly No English**: Translate everything to Korean. Do not keep English words like 'Item', 'Block', 'Config', etc. unless they are proper nouns without a translation.
   - **No Parentheses for English**: Never add (English) after the Korean translation.
     - Bad: "설정 (Config)", "모드 (Mod)"
     - Good: "설정", "모드"
   - **Particles**: Use appropriate particles (이/가, 을/를) based on the final consonant of the preceding word/placeholder.
   - **No Brackets**: Do NOT use square brackets around translated terms."""
    elif target_locale.startswith("ja"):
        target_specific_rules = (
            "4. For Japanese: use appropriate particles (は/が, を/に) and polite forms"
        )

    # Add previous errors context if available
    if errors:
        error_context = "\n## Previous Translation Errors (Please Fix)\n"
        for key, error in errors.items():
            error_context += f"- Key '{key}': {error}\n"
        glossary_context += error_context

    return TRANSLATOR_SYSTEM_PROMPT_TEMPLATE.format(
        source_lang=source_lang,
        target_lang=target_lang,
        target_specific_rules=target_specific_rules,
        glossary_context=glossary_context,
    )


def build_translator_user_prompt(texts: Mapping[str, str], target_lang: str) -> str:
    """Build user prompt for batch translation."""
    texts_json = json.dumps(dict(texts), ensure_ascii=False, indent=2)

    return (
        f"Translate the following texts to {target_lang}:\n\n"
        f"{texts_json}\n\n"
        f"Return translated {target_lang} text as JSON for each key."
    )


# ==============================================================================
# LLM Reviewer Prompts
# ==============================================================================


def build_reviewer_system_prompt(
    source_lang: str,
    target_lang: str,
    target_locale: str,
    glossary_context: str = "",
) -> str:
    """Build system prompt for translation review."""
    # Language-specific review items
    lang_specific_items = ""
    if target_locale.startswith("ko"):
        lang_specific_items = """4. **조사 오류**: 받침에 맞지 않는 조사 사용 (예: '이(가)', '을(를)' 대신 단일 조사)"""
    elif target_locale.startswith("ja"):
        lang_specific_items = (
            """4. **助詞エラー**: 不適切な助詞の使用 (は/が, を/に など)"""
        )

    base_prompt = f"""You are a Minecraft mod translation review expert.
Compare {source_lang} source text with {target_lang} translations to find and fix issues.

## Review Items
1. **Mistranslation**: Translation differs from source meaning
2. **Typos**: Spelling errors, spacing errors
3. **Unnatural Expression**: Grammatically correct but unnatural phrasing
{lang_specific_items}
5. **Terminology Inconsistency**: Same term translated differently

## Review Rules
- Do NOT modify placeholders (%, {{}}, <>, etc.)
- Do NOT modify color codes (§, &)
- Return empty list if no issues found

## Output Format
Include only problematic items in the issues list.
Each issue must have: key, issue_type, original, corrected, explanation"""

    if glossary_context:
        return f"{base_prompt}\n\n{glossary_context}\n\nAlso report if translations differ from glossary-defined terms."

    return base_prompt


def build_reviewer_user_prompt(
    pairs: list[tuple[str, str, str]],
    source_lang: str,
    target_lang: str,
) -> str:
    """Build user prompt for translation review."""
    lines = [
        f"Review the following {source_lang} to {target_lang} translations:",
        "",
    ]

    for key, source, translated in pairs:
        lines.append(f"Key: {key}")
        lines.append(f"Source: {source}")
        lines.append(f"Translation: {translated}")
        lines.append("---")

    lines.append("")
    lines.append("Find issues like mistranslations, typos, unnatural expressions, etc.")
    lines.append("Report only problematic items and suggest corrected translations.")

    return "\n".join(lines)
