# src/handlers/ — Mod-Aware Content Handlers

Extract translatable strings from mod-specific file layouts. Priority-ordered manual registry.

## REGISTRY

`HandlerRegistry` (in `base.py`) — manual `registry.register(Handler())`, sorted by `priority` DESC. First `can_handle(path) == True` wins. Bootstrapped via `create_default_registry()`.

```
FTBQuestsHandler          priority=15   /ftbquests/, .snbt|.nbt
PatchouliHandler          priority=13   /patchouli_books/, .json
OriginsHandler            priority=12   /origins/, /powers/, .json
PuffishSkillsHandler      priority=11   /puffish_skills/, .json
TConstructHandler         priority=11   /tconstruct/, .json
TheVaultQuestHandler      priority=10   /the_vault/quest/, .json
LanguageHandler           priority= 9   xx_xx.json, .lang  (fallback)
```

## CONTRACT (`ContentHandler` ABC, `base.py`)

```python
class MyHandler(ContentHandler):
    name: ClassVar[str] = "my_mod"            # lowercase, matches filename
    priority: ClassVar[int] = 11              # higher = checked first
    path_patterns: ClassVar[tuple[str, ...]] = ("/my_mod/",)   # substring, case-insensitive, normalized to /
    extensions: ClassVar[tuple[str, ...]] = (".json",)         # fallback if path_patterns empty

    async def extract(self, path: Path) -> Mapping[str, str]: ...
    async def apply(self, path: Path, translations: Mapping[str, str], output_path: Path | None = None) -> None: ...
    # get_output_path() default: replace source_locale with target_locale in path string
```

`can_handle()` is provided — checks `path_patterns` first, falls back to `extensions`. Override only for custom logic (e.g., reading file headers).

## ADDING A NEW HANDLER

1. **Create** `src/handlers/my_mod.py` — subclass `ContentHandler`, set ClassVars, implement `extract`/`apply`.
2. **Delegate parsing** to `BaseParser.create_parser(path)` from `src/parsers` — never re-implement JSON/SNBT reading.
3. **Export** in `src/handlers/__init__.py` `__all__`.
4. **Register** in `base.py::create_default_registry()` with the right priority slot.
5. **Pick priority carefully** — generic formats (`.json`) need higher-priority mod handlers to claim them first. `LanguageHandler` (priority=9) is the JSON catch-all.

## KEY EXTRACTION

- Keys must be **stable across runs** so retries map back. Use a deterministic scheme: SNBT/NBT path (`quests[3].title`), JSON dot-path (`book.author`).
- `apply()` writes back **using the same keys** — never mutate the key set.
- `apply()` must `mkdir(parents=True, exist_ok=True)` on `output_path.parent` if writing to a new tree.

## ANTI-PATTERNS

- **Hardcoding `.json` parsing inside a handler** instead of using `BaseParser.create_parser()` — duplicates logic and breaks if a new JSON quirk appears.
- **Lowering priority below LanguageHandler (9)** for a mod-specific handler — it'll never get called for `.json` files; LanguageHandler claims them first.
- **Stateful handlers** — instances are reused across files; never store per-file state on `self`.
- **Skipping `path_patterns` and relying only on `extensions=(".json",)`** for a mod handler — collides with every other JSON consumer; you'll hijack vanilla lang files.
- **Translating placeholder-only strings or build artifacts** — return them in `extract()` filtered out, or the LLM wastes tokens on `§a%s§r`.
