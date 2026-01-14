"""Locale helper functions for translation."""

from __future__ import annotations

# Comprehensive mapping of Minecraft locale codes to language names
LOCALE_NAMES: dict[str, dict[str, str]] = {
    # English variants
    "en_us": {"en": "English (US)", "native": "English (US)", "ko": "영어 (미국)"},
    "en_gb": {"en": "English (UK)", "native": "English (UK)", "ko": "영어 (영국)"},
    "en_au": {
        "en": "English (Australia)",
        "native": "English (Australia)",
        "ko": "영어 (호주)",
    },
    "en_ca": {
        "en": "English (Canada)",
        "native": "English (Canada)",
        "ko": "영어 (캐나다)",
    },
    # Korean
    "ko_kr": {"en": "Korean", "native": "한국어", "ko": "한국어"},
    # Japanese
    "ja_jp": {"en": "Japanese", "native": "日本語", "ko": "일본어"},
    # Chinese variants
    "zh_cn": {
        "en": "Chinese (Simplified)",
        "native": "简体中文",
        "ko": "중국어 (간체)",
    },
    "zh_tw": {
        "en": "Chinese (Traditional)",
        "native": "繁體中文",
        "ko": "중국어 (번체)",
    },
    "zh_hk": {
        "en": "Chinese (Hong Kong)",
        "native": "繁體中文 (香港)",
        "ko": "중국어 (홍콩)",
    },
    # Spanish variants
    "es_es": {
        "en": "Spanish (Spain)",
        "native": "Español (España)",
        "ko": "스페인어 (스페인)",
    },
    "es_mx": {
        "en": "Spanish (Mexico)",
        "native": "Español (México)",
        "ko": "스페인어 (멕시코)",
    },
    "es_ar": {
        "en": "Spanish (Argentina)",
        "native": "Español (Argentina)",
        "ko": "스페인어 (아르헨티나)",
    },
    # French variants
    "fr_fr": {
        "en": "French (France)",
        "native": "Français (France)",
        "ko": "프랑스어 (프랑스)",
    },
    "fr_ca": {
        "en": "French (Canada)",
        "native": "Français (Canada)",
        "ko": "프랑스어 (캐나다)",
    },
    # German
    "de_de": {"en": "German", "native": "Deutsch", "ko": "독일어"},
    "de_at": {
        "en": "German (Austria)",
        "native": "Deutsch (Österreich)",
        "ko": "독일어 (오스트리아)",
    },
    "de_ch": {
        "en": "German (Switzerland)",
        "native": "Deutsch (Schweiz)",
        "ko": "독일어 (스위스)",
    },
    # Italian
    "it_it": {"en": "Italian", "native": "Italiano", "ko": "이탈리아어"},
    # Portuguese variants
    "pt_pt": {
        "en": "Portuguese (Portugal)",
        "native": "Português (Portugal)",
        "ko": "포르투갈어 (포르투갈)",
    },
    "pt_br": {
        "en": "Portuguese (Brazil)",
        "native": "Português (Brasil)",
        "ko": "포르투갈어 (브라질)",
    },
    # Dutch
    "nl_nl": {"en": "Dutch", "native": "Nederlands", "ko": "네덜란드어"},
    "nl_be": {
        "en": "Dutch (Belgium)",
        "native": "Nederlands (België)",
        "ko": "네덜란드어 (벨기에)",
    },
    # Russian
    "ru_ru": {"en": "Russian", "native": "Русский", "ko": "러시아어"},
    # Polish
    "pl_pl": {"en": "Polish", "native": "Polski", "ko": "폴란드어"},
    # Swedish
    "sv_se": {"en": "Swedish", "native": "Svenska", "ko": "스웨덴어"},
    # Norwegian
    "no_no": {"en": "Norwegian", "native": "Norsk", "ko": "노르웨이어"},
    # Danish
    "da_dk": {"en": "Danish", "native": "Dansk", "ko": "덴마크어"},
    # Finnish
    "fi_fi": {"en": "Finnish", "native": "Suomi", "ko": "핀란드어"},
    # Greek
    "el_gr": {"en": "Greek", "native": "Ελληνικά", "ko": "그리스어"},
    # Turkish
    "tr_tr": {"en": "Turkish", "native": "Türkçe", "ko": "터키어"},
    # Czech
    "cs_cz": {"en": "Czech", "native": "Čeština", "ko": "체코어"},
    # Hungarian
    "hu_hu": {"en": "Hungarian", "native": "Magyar", "ko": "헝가리어"},
    # Romanian
    "ro_ro": {"en": "Romanian", "native": "Română", "ko": "루마니아어"},
    # Ukrainian
    "uk_ua": {"en": "Ukrainian", "native": "Українська", "ko": "우크라이나어"},
    # Thai
    "th_th": {"en": "Thai", "native": "ภาษาไทย", "ko": "태국어"},
    # Vietnamese
    "vi_vn": {"en": "Vietnamese", "native": "Tiếng Việt", "ko": "베트남어"},
    # Indonesian
    "id_id": {"en": "Indonesian", "native": "Bahasa Indonesia", "ko": "인도네시아어"},
    # Malay
    "ms_my": {"en": "Malay", "native": "Bahasa Melayu", "ko": "말레이어"},
    # Arabic
    "ar_sa": {"en": "Arabic", "native": "العربية", "ko": "아랍어"},
    # Hebrew
    "he_il": {"en": "Hebrew", "native": "עברית", "ko": "히브리어"},
    # Hindi
    "hi_in": {"en": "Hindi", "native": "हिन्दी", "ko": "힌디어"},
}


def get_language_name(locale_code: str, display_in: str = "en") -> str:
    """Get the language name for a locale code.

    Args:
        locale_code: Minecraft locale code (e.g., 'en_us', 'ko_kr')
        display_in: Language to display name in ('en', 'native', 'ko')

    Returns:
        Language name in the requested display language

    Examples:
        >>> get_language_name("ko_kr", "en")
        'Korean'
        >>> get_language_name("ko_kr", "native")
        '한국어'
        >>> get_language_name("ja_jp", "ko")
        '일본어'
    """
    locale_lower = locale_code.lower()

    # Check direct match
    if locale_lower in LOCALE_NAMES:
        return LOCALE_NAMES[locale_lower].get(display_in, locale_code)

    # Try without region (e.g., 'en' from 'en_us')
    base_lang = locale_lower.split("_")[0]
    default_locale = f"{base_lang}_{base_lang}"
    if default_locale in LOCALE_NAMES:
        return LOCALE_NAMES[default_locale].get(display_in, locale_code)

    # Fallback: capitalize the locale code
    return locale_code.replace("_", " ").title()
