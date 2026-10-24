"""Background tasks with step-by-step progress, so the dashboard can show a real progress bar."""
from __future__ import annotations

import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable

from pydantic import BaseModel

KEEP_SECONDS = 15 * 60


class Progress:
    """Ordered steps with states pending → running → done | failed | skipped."""

    def __init__(self, title: str):
        self.title = title
        self.steps: dict[str, dict[str, Any]] = {}
        self.started = time.time()

    def add(self, key: str, label: str, detail: str | None = None) -> None:
        self.steps.setdefault(key, {"key": key, "label": label, "state": "pending", "detail": detail})

    def set(self, key: str, state: str, detail: str | None = None, label: str | None = None) -> None:
        step = self.steps.setdefault(key, {"key": key, "label": label or key, "state": "pending", "detail": None})
        step["state"] = state
        if detail is not None:
            step["detail"] = detail
        if label:
            step["label"] = label

    @asynccontextmanager
    async def step(self, key: str, label: str):
        """Mark a step running for the duration of a block; failures are recorded, not swallowed."""
        self.set(key, "running", label=label)
        try:
            yield self.steps[key]
        except Exception as exc:
            self.set(key, "failed", detail=str(exc)[:200])
            raise
        else:
            if self.steps[key]["state"] == "running":
                self.set(key, "done")

    def snapshot(self) -> dict[str, Any]:
        steps = list(self.steps.values())
        finished = sum(1 for s in steps if s["state"] in {"done", "failed", "skipped"})
        running = sum(1 for s in steps if s["state"] == "running")
        fraction = (finished + 0.5 * running) / len(steps) if steps else 0.0
        return {"title": self.title, "steps": steps, "fraction": round(min(1.0, fraction), 3),
                "elapsed": round(time.time() - self.started, 1)}


_TASKS: dict[str, dict[str, Any]] = {}


def start(title: str, work: Callable[[Progress], Awaitable[Any]]) -> str:
    """Run `work(progress)` in the background and return a task id to poll."""
    now = time.time()
    for task_id in [k for k, v in _TASKS.items() if now - v["created"] > KEEP_SECONDS]:
        _TASKS.pop(task_id, None)
    progress = Progress(title)
    task_id = uuid.uuid4().hex[:12]
    entry: dict[str, Any] = {"progress": progress, "created": now, "state": "running", "result": None, "error": None}

    async def runner() -> None:
        try:
            result = await work(progress)
            entry["result"] = result.model_dump(mode="json") if isinstance(result, BaseModel) else result
            entry["state"] = "done"
        except Exception as exc:  # reported to the dashboard
            entry["error"] = str(exc) or exc.__class__.__name__
            entry["state"] = "failed"

    entry["task"] = asyncio.create_task(runner())
    _TASKS[task_id] = entry
    return task_id


def status(task_id: str) -> dict[str, Any] | None:
    entry = _TASKS.get(task_id)
    if entry is None:
        return None
    return {
        "id": task_id,
        "state": entry["state"],
        "progress": entry["progress"].snapshot(),
        "result": entry["result"] if entry["state"] == "done" else None,
        "error": entry["error"],
    }
