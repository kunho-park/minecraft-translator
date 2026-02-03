"""LLM prompts for the application."""

from __future__ import annotations

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
- aliases: List of {source_lang} source terms mapped to this translation.
- category: One of [item, block, ui, entity, effect, biome, other].
- notes: Brief note on usage.

# 2. Proper Noun Rules (proper_noun_rules)
Extract specific names (places, characters, mods) that require consistent translation.
- source_like: The original {source_lang} name.
- preferred_ko: The preferred {target_lang} translation.
- notes: Reasoning.

# 3. Formatting Rules (formatting_rules)
Extract general style guidelines (punctuation, placeholders, honorifics).
- rule_name: Short, descriptive name of the rule.
- description: Clear explanation of the rule.
- examples: List of valid examples.

# Constraints
- Only extract rules clearly supported by the text.
- Return empty lists if no rules are found for a category.
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
- aliases: List of {source_lang} source terms.
- category: One of [item, block, ui, entity, effect, biome, other].

# 2. Proper Noun Rules (proper_noun_rules)
Identify proper nouns and suggest translations.
- source_like: The {source_lang} proper noun.
- preferred_ko: Recommended {target_lang} form (transliteration or translation).

# 3. Formatting Rules (formatting_rules)
Suggest style guidelines based on the text structure.
- rule_name: Short name of the rule.
- description: Clear explanation.
- examples: Examples.

{lang_specific}

# Constraints
- Only propose rules relevant to the text.
- Return empty lists if uncertain.
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
1. **NEVER translate or modify placeholders marked with ⟦PH_xxx⟧**
2. **Copy placeholders EXACTLY as they appear** - including all characters between ⟦ and ⟧
3. **Do NOT abbreviate**: ⟦PH_0_java_format⟧ must stay as ⟦PH_0_java_format⟧, NOT ⟦PH...⟧
4. **Preserve placeholder position** in the translated text
5. **Example**:
   - Input: "Kill the ⟦PH_0_named_placeholder⟧"
   - Output: "⟦PH_0_named_placeholder⟧을(를) 처치하세요"
   - WRONG: "⟦PH...⟧을(를) 처치하세요"

## Translation Guidelines
<quality_standards>
- **Accuracy**: Preserve original meaning and game mechanics.
- **Naturalness**: Use fluent {target_lang} gaming terminology.
- **Consistency**: Apply glossary terms uniformly.
- **Completeness**: Translate ALL provided items.
</quality_standards>

<style_preferences>
- **Translate ALL game terms**: Do NOT keep English terms (e.g., "Experience", "Aptitudes") unless they are proper nouns without a clear translation.
- **No Parenthetical English**: Do NOT add English in parentheses (e.g., WRONG: "경험치 (Experience)", RIGHT: "경험치").
- **No Brackets**: NEVER use square brackets [] around translated terms (e.g., WRONG: "[철] [검]", RIGHT: "철 검").
- **Player Names**: Preserve ONLY actual player usernames (e.g., "Steve", "Alex").
</style_preferences>

<examples>
CORRECT: "보스 몬스터는 일반 몬스터보다 어렵습니다"
INCORRECT: "[보스] [몬스터]는 일반 [몬스터]보다 어렵습니다"

CORRECT: "철 검을 제작하려면 철 주괴가 필요합니다"
INCORRECT: "[철] [검]을 제작하려면 [철] [주괴]가 필요합니다"

CORRECT: "힘, 마법, 재주와 같은 적성은 경험치를 사용하여 획득할 수 있습니다."
INCORRECT: "힘, 마법, 재주와 같은 Aptitudes는 Experience (XP)를 사용하여 획득할 수 있습니다."
</examples>

## Translation Rules
1. Translate game terminology consistently using the provided glossary.
2. Use natural {target_lang} expressions.
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
    lines = [f"Translate the following texts to {target_lang}:", ""]

    for key, text in texts.items():
        lines.append(f'"{key}": "{text}"')

    lines.append("")
    lines.append(f"Return translated {target_lang} text as JSON for each key.")

    return "\n".join(lines)


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
