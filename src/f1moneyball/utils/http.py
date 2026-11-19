"""Polite HTTP client: rate limiting, retries with backoff, and a retrieval log.

Every successful download is recorded (URL, UTC time, status, SHA-256 of the body)
so each raw file can be traced back to when and where it came from.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import requests

log = logging.getLogger(__name__)


class SourceUnavailable(RuntimeError):
    """Raised when a source keeps failing after retries. The pipeline stops, nothing is published."""


@dataclass
class RateLimitedClient:
    min_interval: float = 0.35
    max_per_hour: int = 500
    max_retries: int = 4
    timeout: float = 30.0
    retrieval_log: Path | None = None
    user_agent: str = "f1-moneyball-research/0.1 (+https://github.com/)"
    sleep: Callable[[float], None] = time.sleep
    clock: Callable[[], float] = time.monotonic
    session: requests.Session = field(default_factory=requests.Session)
    _last: float = field(default=-1e9, init=False)
    _window: list[float] = field(default_factory=list, init=False)

    def _wait_turn(self) -> None:
        now = self.clock()
        gap = self.min_interval - (now - self._last)
        if gap > 0:
            self.sleep(gap)
            now = self.clock()
        # Sustained limit: keep a rolling one-hour window of request times.
        self._window = [t for t in self._window if now - t < 3600]
        if len(self._window) >= self.max_per_hour:
            wait = 3600 - (now - self._window[0]) + 1
            log.warning("Hourly limit reached, waiting %.0f s", wait)
            self.sleep(wait)
            now = self.clock()
        self._last = now
        self._window.append(now)

    def get_json(self, url: str, params: dict | None = None) -> dict:
        backoff = 2.0
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            self._wait_turn()
            try:
                resp = self.session.get(
                    url, params=params, timeout=self.timeout,
                    headers={"User-Agent": self.user_agent},
                )
            except requests.RequestException as exc:  # network error
                last_error = exc
                log.warning("Attempt %d failed for %s: %s", attempt, url, exc)
            else:
                if resp.status_code == 200:
                    self._log(resp)
                    return resp.json()
                if resp.status_code == 429:
                    # Rate limited: honour Retry-After if given, otherwise wait long enough for the
                    # burst window to clear, and slow every later request down for the rest of the run.
                    last_error = RuntimeError("HTTP 429")
                    retry_after = resp.headers.get("Retry-After", "")
                    wait = float(retry_after) if retry_after.replace(".", "", 1).isdigit() else 10.0 * attempt
                    self.min_interval = min(self.min_interval * 1.5, 2.0)
                    log.warning("Rate limited on %s; waiting %.0f s (attempt %d)", url, wait, attempt)
                    self.sleep(wait)
                    continue
                if resp.status_code in (500, 502, 503, 504):
                    last_error = RuntimeError(f"HTTP {resp.status_code}")
                    log.warning("Attempt %d got HTTP %s for %s", attempt, resp.status_code, url)
                else:
                    raise SourceUnavailable(f"HTTP {resp.status_code} for {resp.url}")
            self.sleep(backoff)
            backoff *= 2
        raise SourceUnavailable(f"Giving up on {url} after {self.max_retries} attempts: {last_error}")

    def _log(self, resp: requests.Response) -> None:
        if self.retrieval_log is None:
            return
        self.retrieval_log.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "url": resp.url,
            "retrieved_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "status": resp.status_code,
            "sha256": hashlib.sha256(resp.content).hexdigest(),
            "bytes": len(resp.content),
        }
        with open(self.retrieval_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
