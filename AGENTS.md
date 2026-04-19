# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-19 15:20 KST
**Commit:** `8122ade`
**Branch:** `main`
**Version:** 2.5.1

## OVERVIEW

`auto-translate` — Minecraft modpack translator. Async Python 3.13+ pipeline + PySide6 desktop GUI. Multi-provider LLM (OpenAI/Anthropic/Google/Ollama/Grok/DeepSeek) via LangChain. Ships as Windows `.exe` (PyInstaller). Talks to web platform at `mcat.2odk.com` over HTTP API.

## STRUCTURE

```
.
├── src/                       # Core translation engine — see src/AGENTS.md
│   ├── pipeline.py            # Orchestrator: TranslationPipeline, PipelineConfig, PipelineResult
│   ├── prompts.py             # LLM prompt templates (KR/JP/CN style rules embedded)
│   ├── handlers/              # Mod-aware extractors — see src/handlers/AGENTS.md
│   ├── parsers/               # File-format parsers — see src/parsers/AGENTS.md
│   ├── llm/, translator/, scanner/, glossary/, validator/, reviewer/, output/, models/, utils/
│   └── assets/vanilla_minecraft_assets/versions/1.21.5/  # ~1MB JSON ref data, NOT code
├── gui/                       # PySide6+qfluentwidgets app — see gui/AGENTS.md
├── tools/                     # bump_version.py, build_vanilla_glossary.py
├── test/modpack/              # KubeJS fixture (NOT a test runner — manual integration)
├── main.py                    # CLI/example entry, NOT prod entrypoint
├── gui_build.spec             # PyInstaller spec → AutoTranslate.exe
└── Makefile                   # `make release v=vX.Y.Z` only
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add a new mod handler | `src/handlers/AGENTS.md` |
| Add a new file format parser | `src/parsers/AGENTS.md` |
| Modify translation prompts / language rules | `src/prompts.py` |
| Tune batching / concurrency | `src/pipeline.py` (`PipelineConfig`), `src/translator/batch_translator.py` |
| Add LLM provider | `src/llm/client.py` (`LLMProvider` enum + `_create_chat_model`) |
| Fix placeholder corruption (`§`, `%s`, `{x}`, `<tag>`) | `src/translator/placeholder.py` |
| Change validation severity | `src/validator/translation_validator.py` |
| Add GUI screen / step | `gui/views/AGENTS.md` |
| Add background job | `gui/workers/AGENTS.md` |
| Add UI string | `gui/i18n/translations/{ko,en}.json` + `translator.t("key")` |
| Bump version | `make release v=vX.Y.Z` (NEVER hand-edit the 3 version strings) |
| Build Windows exe | `uv run pyinstaller --clean --noconfirm gui_build.spec` |

## PIPELINE

```
ModpackScanner → GlossaryBuilder → handlers.extract() → BatchTranslator
  → PlaceholderProtector(protect→LLM→restore) → Validator → LLMReviewer
  → ResourcePackGenerator / JarModGenerator
```

## CONVENTIONS

- **Python 3.13+ only.** `from __future__ import annotations` everywhere. Full type hints. Google-style docstrings.
- **Package manager: `uv`.** Never `pip install` / `python -m venv`. Use `uv sync`, `uv run python ...`, `uv add`.
- **Async-first.** All I/O (file, LLM, HTTP) is `async`. Handlers/parsers expose `async def extract/apply/parse/dump`.
- **Pydantic v2** for all data shapes (translation, glossary, validation, config). No raw dicts crossing module boundaries.
- **Logging: `colorlog`** with module-level `logger = logging.getLogger(__name__)`. No `print()` in `src/` (CLI-only `print` lives in `main.py`).
- **Locale code format: `xx_yy` lowercase** (`en_us`, `ko_kr`, `ja_jp`, `zh_cn`, `zh_tw`). Used in file paths, glossary filenames, config.
- **Version sync (3 files MUST match):** `pyproject.toml` `version`, `src/__init__.py` `__version__`, `gui/__init__.py` `__version__`. Use `tools/bump_version.py` — do NOT hand-edit.
- **Commit prefixes:** `feat: / fix: / docs: / style: / refactor: / test: / chore:` (per README).
- **Vanilla glossary filename:** `vanilla_glossary_{source_locale}_{target_locale}.json` in `src/glossary/vanilla_glossaries/`. Auto-loaded by locale pair.
- **Config persistence:** `platformdirs.user_config_dir("auto-translate", "mcat")` — never write next to source.

## ANTI-PATTERNS (THIS PROJECT)

- **NEVER** modify `⟦PH1⟧`-style placeholders. They wrap `§`-color codes, `%s`/`%1$s` format specifiers, `{name}`, `<tag>`, `\n` during LLM calls. Mismatch → `PlaceholderError` → entry rejected.
- **NEVER** translate Korean output with English in parens (`경험치 (Experience)`) or square brackets (`[철] [검]`). Hard-coded violations in `src/prompts.py:178-180`.
- **NEVER** deviate from glossary terms. If glossary maps `Enchanting Table → 마법 부여대`, every occurrence MUST use it. Glossary overrides LLM judgment.
- **NEVER** add a test framework, linter, or formatter without asking. None exist intentionally — `pyproject.toml` has only runtime + `pyinstaller`+`ty`. `pytest` is in PyInstaller `excludes`.
- **NEVER** use `pip` or hand-edit `uv.lock`. Use `uv add <pkg>`.
- **NEVER** hand-edit `src/glossary/vanilla_glossaries/*.json` (57k+ lines, generated). Regenerate with `tools/build_vanilla_glossary.py`.
- **NEVER** suppress `PlaceholderError` to "make it pass" — corrupted placeholders break the game silently.
- **NEVER** commit `DEPLOYMENT.md`, `RELEASE_GUIDE.md`, `tools/MIGRATION_GUIDE.md` (in `.gitignore` — internal docs).
- **NEVER** `pip install pytest` to "run tests" — `test/modpack/` is a **manual fixture**, not a unit-test suite. Run `uv run python main.py` against it.
- **No docstring or comment may include emojis in code files.** README/docs only.

## UNIQUE STYLES

- **Two registry systems** with different conventions (do not unify):
  - `src/handlers/` — manual `registry.register()` ordered by `priority` ClassVar (higher first).
  - `src/parsers/` — auto-registers via `__init_subclass__`, looked up by file extension.
- **Pipeline result is mutable across stages.** `regenerate_outputs(result, ...)` and `retry_failed(result)` mutate the same `PipelineResult`. Don't copy/freeze it mid-pipeline.
- **Separate `__version__` in `src/` and `gui/`** despite single project — both must change together via `tools/bump_version.py`.
- **GUI navigation = `QStackedWidget` + central state dict on `MainWindow`**, not a router/state-management lib. Views emit signals, `MainWindow._on_*` slots route.

## COMMANDS

```bash
uv sync                                    # Install deps (Python 3.13 required)
uv run python -m gui                       # Run GUI (preferred entrypoint)
uv run python main.py                      # CLI demo against ./test/modpack
uv run python tools/build_vanilla_glossary.py --source en_us.json --target ko_kr.json
uv run pyinstaller --clean --noconfirm gui_build.spec   # Build Windows exe
make release v=v2.5.2                      # Bump version + tag + push (triggers GH Action)
```

No `make test`, `make lint`, `make fmt` — none configured. CI = `.github/workflows/release.yml` only (build on `v*.*.*` tag).

## NOTES

- **No tests.** None. `test/` is fixture data for manual `main.py` runs. Don't pretend otherwise.
- **No linter/formatter.** Don't introduce ruff/black/isort without asking.
- **Web platform is private.** `mcat.2odk.com` source lives elsewhere. Desktop app talks to it via `src/output/uploader.py` + `gui/auth.py` (OAuth-via-browser-redirect, local HTTP callback).
- **Windows-first.** `gui_build.spec` produces `.exe`. macOS/Linux work for dev (`uv run python -m gui`) but no release artifact.
- **Console window stays open** in built exe (`console=True` in `gui_build.spec`) — intentional for log visibility.
- **All user-facing strings in GUI** must go through `gui/i18n/translator.t("key")`. Do not hard-code KR/EN.
