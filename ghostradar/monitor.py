"""Background monitor: re-check watched companies and cities so lifecycles build up over time.

Reposts, removals and excess lifetimes only become visible through repeated
observation, so the watchlist is what turns snapshots into evidence.

Run once from the command line:  python -m ghostradar.monitor
"""
from __future__ import annotations

import asyncio
import logging

from . import db
from .config import settings
from .http import PoliteClient
from .services import run_watch_item
from .util import parse_datetime, utcnow

log = logging.getLogger("ghostradar.monitor")


async def run_due(client: PoliteClient, force: bool = False) -> list[dict]:
    results = []
    interval = settings.monitor_interval_hours * 3600
    for item in db.watch_list():
        last = parse_datetime(item.get("last_run"))
        if not force and last and (utcnow() - last).total_seconds() < interval:
            continue
        try:
            result = await run_watch_item(client, item)
            results.append({"id": item["id"], "query": item["query"], "result": result})
        except Exception as exc:  # keep the loop alive; record the failure on the item
            log.exception("watch item %s failed", item["id"])
            db.watch_mark_run(item["id"], {"error": str(exc)})
    return results


async def loop(client: PoliteClient) -> None:
    await asyncio.sleep(30)  # let the server start first
    while True:
        try:
            await run_due(client)
        except Exception:
            log.exception("monitor pass failed")
        await asyncio.sleep(15 * 60)


async def _main() -> None:
    db.init_db()
    client = PoliteClient()
    try:
        for item in await run_due(client, force=True):
            print(item)
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(_main())
