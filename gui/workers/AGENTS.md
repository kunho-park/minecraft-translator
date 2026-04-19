# gui/workers/ — QThread Background Jobs

Bridge between Qt's signal/slot world and `src/`'s async world. All blocking work lives here.

## WORKERS

```
scanner_worker.py      ScannerWorker      drives ModpackScanner.scan()
translation_worker.py  TranslationWorker  drives TranslationPipeline.run() — runs asyncio loop inside run()
upload_worker.py       UploadWorker       posts to mcat.2odk.com via aiohttp
update_worker.py       UpdateWorker       polls GitHub releases for newer version tag
```

## WORKER CONTRACT

```python
class FooWorker(QThread):
    progressUpdate = Signal(int, str)       # (percent, label) — throttle to ~100ms
    complete = Signal(object)               # result payload (Pydantic model or dict)
    error = Signal(str)                     # human-readable message

    def __init__(self, **inputs):
        super().__init__()
        # Capture ALL inputs by value. Never hold a reference to MainWindow/views/AppConfig.
        self._inputs = inputs
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            # sync: do work, emit signals
            # async: asyncio.new_event_loop().run_until_complete(self._async_main())
            ...
            self.complete.emit(result)
        except Exception as e:
            logger.exception("Worker failed")
            self.error.emit(str(e))
```

## ASYNCIO IN QTHREAD

`TranslationWorker.run()` does:

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    result = loop.run_until_complete(self._run_pipeline())
finally:
    loop.close()
```

**Each worker creates its own event loop.** Never reuse loops across workers. Never `asyncio.get_event_loop()` (deprecated semantics in 3.13).

## CANCELLATION

- `cancel()` sets a flag; `run()` checks it at safe points (between batches, between files).
- For async pipelines, periodically check `self._cancelled` inside the awaited coroutine and raise `asyncio.CancelledError` to abort.
- Always emit a final `complete` (with partial result) or `error` — never let `run()` exit silently. The view waits for one.

## PROGRESS SIGNALS

`TranslationPipeline` accepts a `progress_callback: Callable[[ProgressEvent], None]`. `TranslationWorker` passes a callback that emits `progressUpdate.emit(percent, label_text)` — but **throttled to ~100ms** (compare `time.monotonic()` since last emit). Without throttling, fast pipelines fire thousands of signals/sec and freeze the UI.

## ADDING A NEW WORKER

1. Create `gui/workers/my_worker.py` subclassing `QThread`.
2. Define signals: at minimum `complete` and `error`. Add domain-specific signals as needed.
3. Capture inputs in `__init__` — **never** store widgets or `MainWindow`.
4. Wire the worker in the relevant view: instantiate, connect signals, `worker.start()`. Keep a reference (`self.worker = worker`) so it isn't garbage-collected mid-run.
5. Connect `MainWindow._on_*` to the `complete` signal for step transition.

## ANTI-PATTERNS

- **Touching Qt widgets from `run()`** — Qt widgets are not thread-safe. Emit signals; let the main thread update UI.
- **`asyncio.run(...)` inside `run()`** — works once, but breaks on cancellation/cleanup. Use `loop = asyncio.new_event_loop()` + `loop.run_until_complete()` pattern.
- **Sharing `LLMClient` instances across workers** — each worker should construct its own from `LLMConfig`. The client holds connection pools that don't survive thread boundaries cleanly.
- **Storing `AppConfig` reference on the worker** — pass primitive values through `__init__`. Workers should not depend on the GUI config singleton.
- **`worker.start()` without keeping a reference** — Python GC will collect a local-scope `QThread`, mid-run, leading to a hard crash. Always assign to `self.<name>_worker`.
- **Emitting `progressUpdate` per item** — must be throttled. A modpack with 50k entries × no throttling = unusable UI.
