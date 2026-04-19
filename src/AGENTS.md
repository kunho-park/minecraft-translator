# src/ — Translation Engine

Async translation pipeline. Public API surfaces in `__init__.py`.

## STRUCTURE

```
src/
├── pipeline.py            # TranslationPipeline orchestrator + PipelineConfig + PipelineResult
├── prompts.py             # System prompt templates with KR/JP/CN style rules (DO NOT add language-rules elsewhere)
├── handlers/              # Mod-aware extractors (priority registry) — see handlers/AGENTS.md
├── parsers/               # File-format parsers (auto-registry) — see parsers/AGENTS.md
├── llm/                   # client.py: LLMProvider enum, LLMConfig, LLMClient (LangChain wrapper)
├── translator/            # batch_translator.py + placeholder.py (⟦PHn⟧ protect/restore)
├── scanner/               # modpack_scanner.py: discovers translatable files, pairs source↔target
├── glossary/              # builder.py (LLM-driven), vanilla_builder.py, vanilla_glossaries/ (data)
├── validator/             # translation_validator.py: ERROR/WARNING severity per rule
├── reviewer/              # llm_reviewer.py: post-translation LLM review pass
├── output/                # resource_pack.py, jar_mod.py, uploader.py (HTTP to mcat.2odk.com)
├── models/                # Pydantic v2: translation, glossary, glossary_filter, validation
├── utils/                 # locale_helper.py only — KEEP it minimal
└── assets/                # Vanilla MC 1.21.5 JSON ref data (NOT code)
```

## PUBLIC API (from `src/__init__.py`)

```python
from src import (
    TranslationPipeline, PipelineConfig, PipelineResult, run_pipeline,
    ModpackScanner, ScanResult, scan_modpack,
    ContentHandler, HandlerRegistry, create_default_registry,
    LLMClient, LLMConfig, LLMProvider,
    Glossary, TranslationTask,
)
```

External consumers (GUI, CLI, tools) MUST import from `src`, not deep paths.

## PIPELINE STAGES (in order)

1. **Scan** — `ModpackScanner.scan(modpack_path)` extracts JARs/ZIPs, pairs source↔target by locale.
2. **Glossary build** — `GlossaryBuilder.build_from_pairs(...)` merges vanilla + LLM-extracted modpack terms.
3. **Task creation** — Per file, pick handler by priority, `handler.extract()` → `{key: source_text}`.
4. **Batch translate** — `BatchTranslator` chunks by `batch_size` (30) AND `max_batch_chars` (8000). Skips placeholder-only.
5. **Validate** — `TranslationValidator` checks placeholder count/order, color codes, length ratio, glossary compliance.
6. **Review** (optional, `skip_review=False`) — `LLMReviewer` corrects in batches of 50.
7. **Output** — `ResourcePackGenerator` (zip), `JarModGenerator` (jar), `Uploader` (HTTP).

`PipelineResult` is **mutable**. `pipeline.retry_failed(result)` and `pipeline.regenerate_outputs(result, ...)` mutate in-place. Do not deepcopy.

## CONCURRENCY

- File-level: 3 parallel workers (hardcoded, see `pipeline.py`).
- LLM-level: `max_concurrent` semaphore (default 15).
- Rate limiting: optional `requests_per_minute` + `tokens_per_minute` via `langchain_core.rate_limiters.InMemoryRateLimiter` + custom `TokenBucketTPM`.

## CRITICAL RULES (this directory)

- **All language-specific rules (KR particles, JP polite forms, CN style) live in `prompts.py`.** Do not scatter into handlers.
- **`prompts.py` lines 178-180 are HARD rules.** Never weaken: no English-in-parens, no square-bracketed terms, full Korean translation.
- **Token tracking** — Every LLM call emits a callback into `LLMClient`'s cumulative counter. New providers MUST wire token callbacks (Ollama uses fallback estimation).
- **Placeholder roundtrip is sacred.** `PlaceholderProtector.protect()` → LLM → `restore()` → `PlaceholderError` if mismatch. Never bypass.
- **Glossary takes precedence over LLM judgment.** If `term_rules` says `Stone → 돌`, the validator flags any other rendering.

## ANTI-PATTERNS

- Adding a new module under `src/` for one-off utility code → put it in the closest existing module. `utils/` is for cross-cutting only.
- Using `print()` anywhere in `src/` — use `logger`. `print()` is reserved for `main.py` user prompts.
- Returning raw `dict` from a public function — use Pydantic models from `src/models/`.
- Catching `PlaceholderError` and discarding the entry silently — surface it as a failed entry on `TranslationResult`.
