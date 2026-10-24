"""Polite HTTP access: domain policy, robots.txt, per-host rate limits and a response cache.

Hard rules, taken from the research report's legal findings:
- never fetch from sites whose terms ban robots (the user pastes the ad text instead);
- obey robots.txt for everything else;
- never solve captchas, log in, rotate IPs or retry around blocks.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
import urllib.robotparser
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

import httpx

from . import db
from .config import settings

# (domains, reason shown to the user)
BLOCKED_DOMAINS: list[tuple[tuple[str, ...], str]] = [
    (("linkedin.com",), "LinkedIn's User Agreement and robots.txt prohibit automated access."),
    (("indeed.com", "indeed.de"), "Indeed's terms prohibit bots and scrapers without written permission."),
    (("stepstone.de", "stepstone.at", "stepstone.com"), "StepStone's robots.txt prohibits any other use of robots."),
    (("glassdoor.com", "glassdoor.de"), "Glassdoor's terms prohibit scraping."),
    (
        ("arbeitsagentur.de",),
        "The Bundesagentur's terms of use (§2a(3), version of 8 July 2026) ban robots and reading out "
        "interfaces for data collection; automated use needs the BA's permission.",
    ),
    (("kununu.com",), "kununu offers no lawful automated access route."),
    (("monster.de", "monster.com"), "Monster serves a bot challenge; automated access is not attempted."),
    (("xing.com",), "XING's terms for automated access could not be verified, so it is not fetched."),
    (("adzuna.de", "adzuna.com"), "Adzuna listing pages are only used through Adzuna's official API."),
    (("google.com", "google.de"), "Google pages are not fetched automatically."),
]

# hosts that ask for slower request rates
HOST_INTERVALS = {
    "api.gdeltproject.org": 6.0,
    "nominatim.openstreetmap.org": 1.2,
    "www.arbeitnow.com": 2.0,
    "rest.arbeitsagentur.de": 1.0,
    "localhost": 0.0,
    "127.0.0.1": 0.0,
}


class FetchError(Exception):
    """A request failed in a way the caller should report, not retry around."""


class Blocked(FetchError):
    def __init__(self, url: str, reason: str):
        super().__init__(reason)
        self.url = url
        self.reason = reason


@dataclass
class Response:
    url: str
    status: int
    content_type: str
    body: bytes
    from_cache: bool = False

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8-sig"))

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


def blocked_reason(url: str) -> str | None:
    host = (urlsplit(url).hostname or "").lower()
    for domains, reason in BLOCKED_DOMAINS:
        for domain in domains:
            if host == domain or host.endswith("." + domain):
                return reason
    return None


class PoliteClient:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self._client = httpx.AsyncClient(
            headers={"User-Agent": settings.user_agent, "Accept-Language": "de,en;q=0.8"},
            timeout=settings.request_timeout,
            follow_redirects=False,
            transport=transport,
        )
        self._host_locks: dict[str, asyncio.Lock] = {}
        self._host_last: dict[str, float] = {}
        self._robots: dict[str, tuple[float, urllib.robotparser.RobotFileParser | None]] = {}

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------ internals

    async def _wait_turn(self, host: str) -> asyncio.Lock:
        lock = self._host_locks.setdefault(host, asyncio.Lock())
        await lock.acquire()
        interval = HOST_INTERVALS.get(host, settings.min_host_interval)
        wait = self._host_last.get(host, 0.0) + interval - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        return lock

    def _release(self, host: str, lock: asyncio.Lock) -> None:
        self._host_last[host] = time.monotonic()
        lock.release()

    async def _robots_for(self, url: str) -> urllib.robotparser.RobotFileParser | None:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        cached = self._robots.get(origin)
        if cached and time.time() - cached[0] < 24 * 3600:
            return cached[1]
        parser: urllib.robotparser.RobotFileParser | None
        host = parts.hostname or ""
        lock = await self._wait_turn(host)
        try:
            resp = await self._client.get(origin + "/robots.txt")
            if resp.status_code >= 500:
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(["User-agent: *", "Disallow: /"])  # server trouble: stay away for now
            elif resp.status_code >= 400:
                parser = None  # no robots.txt: everything allowed
            else:
                parser = urllib.robotparser.RobotFileParser()
                parser.parse(resp.text.splitlines())
        except httpx.HTTPError:
            parser = None
        finally:
            self._release(host, lock)
        self._robots[origin] = (time.time(), parser)
        return parser

    async def _allowed_by_robots(self, url: str) -> bool:
        parser = await self._robots_for(url)
        if parser is None:
            return True
        return parser.can_fetch(settings.robots_agent, url)

    # ------------------------------------------------------------------ public API

    async def request(
        self,
        method: str,
        url: str,
        *,
        params: dict | None = None,
        json_body: Any = None,
        headers: dict | None = None,
        ttl: int | None = None,
        check_robots: bool = True,
        max_redirects: int = 5,
        cache_check: Callable[[Response], bool] | None = None,
        allow_blocked: bool = False,
    ) -> Response:
        """allow_blocked is only passed by connectors the user switched on explicitly (e.g. BA_JOBSUCHE)."""
        if params:
            url = str(httpx.URL(url, params={k: v for k, v in params.items() if v is not None}))
        cache_key = hashlib.sha1(
            f"{method} {url} {json.dumps(json_body, sort_keys=True) if json_body is not None else ''}".encode()
        ).hexdigest()
        ttl = settings.cache_ttl_seconds if ttl is None else ttl
        if ttl > 0:
            hit = db.cache_get(cache_key)
            if hit and time.time() - hit["fetched_at"] < ttl:
                return Response(hit["final_url"], hit["status"], hit["content_type"] or "", hit["body"], True)

        current = url
        for _ in range(max_redirects + 1):
            reason = blocked_reason(current)
            if reason and not allow_blocked:
                raise Blocked(current, reason)
            if check_robots and not await self._allowed_by_robots(current):
                raise Blocked(current, "robots.txt disallows this URL for automated tools.")
            host = urlsplit(current).hostname or ""
            lock = await self._wait_turn(host)
            try:
                resp = await self._client.request(method, current, json=json_body, headers=headers)
            except httpx.HTTPError as exc:
                raise FetchError(f"Could not reach {host}: {exc.__class__.__name__}") from exc
            finally:
                self._release(host, lock)
            if resp.status_code in (301, 302, 303, 307, 308) and "location" in resp.headers:
                current = urljoin(current, resp.headers["location"])
                if resp.status_code == 303:
                    method, json_body = "GET", None
                continue
            result = Response(str(resp.url), resp.status_code, resp.headers.get("content-type", ""), resp.content)
            cacheable = resp.status_code in (200, 404, 410) and (cache_check is None or cache_check(result))
            if ttl > 0 and cacheable:
                db.cache_put(cache_key, resp.status_code, result.content_type, result.url, result.body, time.time())
            return result
        raise FetchError("Too many redirects.")

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post_json(self, url: str, body: Any, **kwargs: Any) -> Response:
        return await self.request("POST", url, json_body=body, **kwargs)
