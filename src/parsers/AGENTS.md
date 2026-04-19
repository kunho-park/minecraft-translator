# src/parsers/ — File-Format Parsers

Read/write translatable text by file extension. Auto-registry via `__init_subclass__`.

## REGISTRY

Class-level `_registry: dict[str, type[BaseParser]]`. A subclass with `file_extensions = (".foo",)` auto-registers on class definition (no manual call). Lookup: `BaseParser.create_parser(path)` → instance or `None`.

```
JSONParser    .json   (with optional should_handle filter)
LangParser    .lang
SNBTParser    .snbt
NBTParser     .nbt
JSParser      .js
XMLParser     .xml
TextParser    .txt
```

## CONTRACT (`BaseParser` ABC, `base.py`)

```python
class FooParser(BaseParser):
    file_extensions: ClassVar[tuple[str, ...]] = (".foo",)   # auto-register key

    async def parse(self) -> Mapping[str, str]: ...    # raise ParseError on failure
    async def dump(self, data: Mapping[str, str]) -> None: ...    # raise DumpError on failure

    # Optional class method — return False to abstain (e.g., JSONParser checks locale-shaped filename)
    @classmethod
    def should_handle(cls, path: Path) -> bool: ...
```

Constructor: `__init__(self, path: Path, original_path: Path | None = None)`. `original_path` is the source file when `path` is the output destination — used by formats that preserve structure (NBT, SNBT, XML) by reading the original and re-emitting with translated strings.

## EXCEPTIONS

```
ParserError                  base
├── ParseError(path, msg)    raised by parse()
└── DumpError(path, msg)     raised by dump()
```

Both wrap `OSError` and parse-library errors. **Never raise raw `Exception`** from `parse`/`dump`.

## ADDING A NEW PARSER

1. **Create** `src/parsers/my_format.py` — subclass `BaseParser`, set `file_extensions`, implement `parse`/`dump`.
2. **Use `aiofiles`** for I/O — all parsers are async.
3. **Wrap errors** in `ParseError(self.path, ...)` / `DumpError(self.path, ...)`.
4. **Export** in `src/parsers/__init__.py` `__all__`.
5. **Done.** Auto-registers — no need to touch `base.py` or any handler.

## STRUCTURE-PRESERVING FORMATS

NBT, SNBT, XML, JSON-with-comments preserve non-translatable bytes. Pattern:

- `parse()` reads `self.path`, returns `{key: source_text}` for translatable strings only.
- `dump()` reads `self.original_path` (or `self.path` if `original_path is None`), substitutes translated values at the same keys, writes back.

For `.lang` (flat key=value) and `.txt` (line-numbered), no `original_path` is needed.

## JSONParser SPECIAL CASE

`JSONParser.should_handle(path)` filters to **locale-shaped filenames only** (`xx_xx.json` like `en_us.json`). Plain `config.json` files are rejected — handlers must claim them via `path_patterns`. This prevents the JSON parser from hijacking every config file in a modpack.

## ANTI-PATTERNS

- **Synchronous I/O** (`open(...)`) — must be `aiofiles.open(...)`. Will block the event loop and starve other batches.
- **Parsing in `__init__`** — `parse()` is async, `__init__` is not. Lazy-parse only inside `parse()`.
- **Mutating `_registry` manually** — let `__init_subclass__` handle it. Manual edits cause double-registration when modules reload.
- **Returning `dict` with non-string values** — keys and values are both `str`. Stringify upstream.
- **Catching `ParseError`/`DumpError` and re-raising as `Exception`** — handlers and pipeline depend on the specific types to log file paths cleanly.
