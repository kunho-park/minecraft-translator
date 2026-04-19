from __future__ import annotations

from collections.abc import Callable, Mapping

type ProgressStats = Mapping[str, object]
type ProgressCallback = Callable[[str, int, int, ProgressStats | None], None]
type ScanProgressCallback = Callable[[str, int, int, str], None]
type CancelCheck = Callable[[], bool]
