# gui/ — PySide6 Desktop App

Fluent Design wizard wrapping `src/` translation pipeline. Multi-step `QStackedWidget` flow, `QThread` workers, JSON i18n.

## STRUCTURE

```
gui/
├── __main__.py          # `python -m gui` entry
├── main.py              # logging + theme setup, QApplication boot
├── app.py               # MainWindow: QStackedWidget nav + central state dict + signal routing
├── config.py            # AppConfig: persistent JSON via platformdirs (mcat/auto-translate/config.json)
├── auth.py              # DesktopAuth: OAuth-via-browser + local HTTP callback on free port
├── views/               # 8 wizard steps — see views/AGENTS.md
├── widgets/             # ModpackTreeWidget (paginated), ProgressCard, ScanStatsCard, dialogs
├── workers/             # QThread + asyncio integration — see workers/AGENTS.md
├── i18n/                # Custom JSON translator (NOT QTranslator/gettext)
│   └── translations/{ko,en}.json
└── styles/app.qss       # Single QSS, loaded at startup
```

## NAVIGATION MODEL

- `MainWindow` owns `QStackedWidget` with all 8 views indexed 0–7.
- `MainWindow.state: dict` is the **single source of truth** between views (modpack path, scan result, settings, translation result).
- Views emit Qt signals (`modpackSelected`, `settingsConfirmed`, `cancelled`, ...) → `MainWindow._on_*` slots mutate state and call `self._go_to_step(n)`.
- **No router library, no Redux-style store.** Plain dict + signals.

## THREADING

- **All blocking work runs in `QThread` workers** (see `workers/AGENTS.md`). Never `await` from a view slot — views are pure-sync GUI code.
- **`TranslationWorker` runs an asyncio event loop inside `QThread.run()`** to drive `TranslationPipeline.run(...)`. This is the sole bridge between Qt and `src/`'s async world.
- **Throttle progress updates** to ~100ms intervals to avoid repaint storms with hundreds of mods.

## I18N

- `gui.i18n.translator` is a **module-level singleton** with `t(key, **fmt)` and `set_language(lang_code)`.
- All user-facing strings: `from gui.i18n import translator; label.setText(translator.t("welcome.title"))`.
- Adding a string: add the key to **both** `ko.json` and `en.json`. Korean first (default), then English.
- On language change, `MainWindow._on_language_changed()` rebuilds all views in place — views must read text via `t()` in their constructor and again on `retranslate()` if they cache.

## CONFIG PERSISTENCE

`AppConfig` (in `config.py`) — dot-notation accessor (`cfg.get("llm.model")`, `cfg.set("llm.temperature", 0.3)`). Persists to:

- Linux/macOS: `~/.config/mcat/auto-translate/config.json`
- Windows: `%LOCALAPPDATA%\mcat\auto-translate\config.json`

Defaults are merged on load — adding a new key with a default in `AppConfig._DEFAULTS` is safe for existing users.

## AUTH

`DesktopAuth.login()`:
1. Find a free port (random) → start local `aiohttp` HTTP server.
2. `webbrowser.open(...)` to `mcat.2odk.com/oauth?redirect=http://localhost:{port}/callback`.
3. Browser hits the local callback with `?token=...`.
4. Server captures token, shuts down, emits `loginComplete(token)`.

Token persisted in `config.json` under `auth.token`. **Never log the token.**

## ANTI-PATTERNS

- **Importing `src.*` deeply** (`from src.translator.batch_translator import ...`) — use `from src import ...` (the public API).
- **`asyncio.run(...)` from a view slot** — blocks the GUI thread. Always go through a `QThread` worker.
- **Hardcoded UI strings** in any language — must go through `translator.t("...")`. Caught easily in PR review.
- **Reading `AppConfig` from inside a worker** — pass values through the worker's `__init__`. Workers must be self-contained for thread safety.
- **Adding a state-management library** (Redux, MobX, etc.) — the dict-on-MainWindow pattern is intentional. 8 views don't need a store.
- **Touching Qt widgets from worker threads** — emit signals; let the main thread update the UI.
- **Console removal in PyInstaller spec** — `console=True` is intentional in `gui_build.spec` for visible logs in the built `.exe`.
