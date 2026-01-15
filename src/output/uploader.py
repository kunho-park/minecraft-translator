"""
웹사이트 업로드 모듈

번역 파이프라인에서 생성된 결과물을 웹사이트에 업로드합니다.
"""

import logging
from pathlib import Path
from typing import TypedDict

import aiohttp

logger = logging.getLogger(__name__)


class TranslationConfig(TypedDict, total=False):
    """번역 설정 정보"""

    source_lang: str
    target_lang: str
    llm_model: str
    temperature: float
    batch_size: int
    used_glossary: bool
    reviewed: bool


class TranslationStats(TypedDict, total=False):
    """번역 통계 정보"""

    file_count: int  # 번역된 파일 개수
    total_entries: int  # 총 항목 수
    translated_entries: int  # 번역된 항목 수
    input_tokens: int  # 입력 토큰 수
    output_tokens: int  # 출력 토큰 수
    total_tokens: int  # 총 토큰 수
    handler_stats: dict[
        str, int
    ]  # 핸들러별 사용 횟수 {"kubejs": 5, "ftbquests": 10, ...}
    duration_seconds: float  # 번역 소요 시간 (초)


class UploadResult(TypedDict):
    """업로드 결과"""

    success: bool
    pack_id: str | None
    message: str


async def upload_to_website(
    curseforge_id: int,
    modpack_version: str,
    resource_pack_path: Path | None = None,
    override_path: Path | None = None,
    translation_config: TranslationConfig | None = None,
    translation_stats: TranslationStats | None = None,
    api_url: str = "https://mct.2odk.com/api",
    anonymous: bool = True,
) -> UploadResult:
    """
    번역 결과를 웹사이트에 업로드합니다.

    Args:
        curseforge_id: CurseForge 모드팩 ID
        modpack_version: 모드팩 버전 (예: "1.20.1-2.0.0")
        resource_pack_path: 리소스팩 ZIP 파일 경로 (선택)
        override_path: 덮어쓰기 파일 ZIP 경로 (선택)
        translation_config: 번역 설정 정보
        translation_stats: 번역 통계 정보
        api_url: 웹사이트 API URL
        anonymous: 익명 업로드 여부

    Returns:
        UploadResult: 업로드 결과

    Raises:
        ValueError: 필수 파일이 모두 없는 경우
        aiohttp.ClientError: 네트워크 오류

    Example:
        >>> result = await upload_to_website(
        ...     curseforge_id=123456,
        ...     modpack_version="1.20.1-2.0.0",
        ...     resource_pack_path=Path("output/resourcepack.zip"),
        ...     override_path=Path("output/override.zip"),
        ...     translation_config={
        ...         "source_lang": "en_us",
        ...         "target_lang": "ko_kr",
        ...         "llm_model": "gpt-4",
        ...         "temperature": 0.3,
        ...         "batch_size": 50,
        ...         "used_glossary": True,
        ...         "reviewed": True,
        ...     },
        ...     translation_stats={
        ...         "file_count": 10,
        ...         "total_entries": 1000,
        ...         "translated_entries": 950,
        ...         "total_tokens": 50000,
        ...         "handler_stats": {"kubejs": 5, "ftbquests": 3},
        ...     }
        ... )
        >>> print(result)
        {'success': True, 'pack_id': '...', 'message': 'Upload successful'}
    """
    if not resource_pack_path and not override_path:
        raise ValueError("At least one file (resource_pack or override) is required")

    config = translation_config or {}
    stats = translation_stats or {}

    # FormData 준비
    data = aiohttp.FormData()
    data.add_field("curseforgeId", str(curseforge_id))
    data.add_field("modpackVersion", modpack_version)
    data.add_field("sourceLang", config.get("source_lang", "en_us"))
    data.add_field("targetLang", config.get("target_lang", "ko_kr"))
    data.add_field("anonymous", str(anonymous).lower())

    if "llm_model" in config:
        data.add_field("llmModel", config["llm_model"])
    if "temperature" in config:
        data.add_field("temperature", str(config["temperature"]))
    if "batch_size" in config:
        data.add_field("batchSize", str(config["batch_size"]))
    data.add_field("usedGlossary", str(config.get("used_glossary", False)).lower())
    data.add_field("reviewed", str(config.get("reviewed", False)).lower())

    # 통계 데이터 추가
    if "file_count" in stats:
        data.add_field("fileCount", str(stats["file_count"]))
    if "total_entries" in stats:
        data.add_field("totalEntries", str(stats["total_entries"]))
    if "translated_entries" in stats:
        data.add_field("translatedEntries", str(stats["translated_entries"]))
    if "input_tokens" in stats:
        data.add_field("inputTokens", str(stats["input_tokens"]))
    if "output_tokens" in stats:
        data.add_field("outputTokens", str(stats["output_tokens"]))
    if "total_tokens" in stats:
        data.add_field("totalTokens", str(stats["total_tokens"]))
    if "handler_stats" in stats:
        import json

        data.add_field("handlerStats", json.dumps(stats["handler_stats"]))
    if "duration_seconds" in stats:
        data.add_field("durationSeconds", str(stats["duration_seconds"]))

    # 파일 추가
    if resource_pack_path and resource_pack_path.exists():
        with open(resource_pack_path, "rb") as f:
            data.add_field(
                "resourcePack",
                f.read(),
                filename=resource_pack_path.name,
                content_type="application/zip",
            )
        logger.info(f"리소스팩 파일 추가: {resource_pack_path}")

    if override_path and override_path.exists():
        with open(override_path, "rb") as f:
            data.add_field(
                "overrideFile",
                f.read(),
                filename=override_path.name,
                content_type="application/zip",
            )
        logger.info(f"덮어쓰기 파일 추가: {override_path}")

    # 업로드 요청
    url = f"{api_url}/translations"
    logger.info(f"업로드 시작: {url}")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            result = await response.json()

            if response.status == 200:
                logger.info(f"업로드 성공: {result.get('packId')}")
                return UploadResult(
                    success=True,
                    pack_id=result.get("packId"),
                    message=result.get("message", "Upload successful"),
                )
            else:
                error_msg = result.get("error", f"HTTP {response.status}")
                logger.error(f"업로드 실패: {error_msg}")
                return UploadResult(success=False, pack_id=None, message=error_msg)


async def check_modpack_exists(
    curseforge_id: int, api_url: str = "https://mct.2odk.com/api"
) -> dict | None:
    """
    CurseForge ID로 모드팩 정보를 조회합니다.

    Args:
        curseforge_id: CurseForge 모드팩 ID
        api_url: 웹사이트 API URL

    Returns:
        모드팩 정보 딕셔너리 또는 None
    """
    url = f"{api_url}/curseforge/{curseforge_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None
