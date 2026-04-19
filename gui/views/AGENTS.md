# gui/views/ — Wizard Step Views

8-step linear workflow inside `MainWindow`'s `QStackedWidget`. Each view is a `QWidget` subclass.

## STEPS (in order)

```
0  welcome.py              WelcomeView              translate vs download choice
1  modpack_select.py       ModpackSelectionView     auto-detect launchers + manual pick
2  scan_result.py          ScanResultView           ScanStatsCard + LLM/locale settings
3  category_select.py      CategorySelectionView    ModpackTreeWidget filter/select
4  translation_progress.py TranslationProgressView  live progress + ETA + token counter
5  retry.py                RetryView                failed-entry retry UI
6  upload.py               UploadView               (auth + form + UploadWorker)
7  completion.py           CompletionView           final stats + open-folder buttons
```

(Optional `review.py` is wired into the pipeline, not as its own step — review runs during step 4 unless `skip_review=True`.)

## VIEW CONTRACT

```python
class FooView(QWidget):
    fooConfirmed = Signal(object)   # snake_case data signal name

    def __init__(self, main_window: "MainWindow"):
        super().__init__()
        self.main_window = main_window
        self._build_ui()
        self._connect_signals()
```

- **Constructor takes `main_window`** — used to read `main_window.state` and dispatch.
- **All text via `translator.t("view.foo.title")`** — namespace under `view.<view_name>.*` in `i18n/translations/{ko,en}.json`.
- **Forward navigation = emit signal** → `MainWindow._on_*` slot decides next step.
- **Backward navigation = `MainWindow._go_to_step(n - 1)`** via shared back-button slot.

## ADDING A NEW STEP

1. Create `gui/views/my_step.py` with `MyStepView(QWidget)`.
2. Add i18n keys to **both** `ko.json` and `en.json` under `view.my_step.*`.
3. In `gui/app.py::MainWindow.__init__`:
   - Instantiate and `addWidget` to the stack.
   - Wire signals to a new `_on_my_step_*` slot.
   - Update step count and any progress indicator at the top of the window.
4. Update the surrounding views' "next" wiring to route through your new step.

## STATE FLOW

Views **read** from `main_window.state` (dict) and **write** by emitting signals carrying data — `MainWindow` mutates state in slot handlers. No view writes to `state` directly.

Common state keys: `modpack_path`, `scan_result`, `pipeline_config`, `selected_files`, `translation_result`, `auth_token`.

## WIDGETS USED

- **`qfluentwidgets`** primitives: `CardWidget`, `PushButton`, `PrimaryPushButton`, `LineEdit`, `BodyLabel`, `TitleLabel`, `ComboBox`, `SwitchButton`, `IndeterminateProgressBar`, `ProgressBar`, `FluentIcon`.
- **Custom widgets** from `gui/widgets/`: `ModpackTreeWidget` (step 3), `ScanStatsCard` (step 2), `ProgressCard` (step 4).

## ANTI-PATTERNS

- **Doing work in the view** (file I/O, scanning, translation) — delegate to a `QThread` worker. Views are pure presentation.
- **Hardcoding step indices** in view code (`self.main_window._go_to_step(4)`) — define step constants in `app.py` if you must, but prefer named transitions via signals.
- **Storing pipeline data on `self`** in a view — use `main_window.state`. Views are recreated on language change; instance attrs are lost.
- **Importing other views directly** — sibling views never reference each other. All cross-view data flows through `main_window.state`.
- **Adding a "review" view** — review runs as a stage of `TranslationWorker`, not as a separate step. The `review.py` view file is internal scaffolding, not a wizard step.
