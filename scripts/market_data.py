#!/usr/bin/env python3
"""Read-only price feeds for the paper desk. Stdlib only.

``PriceFeed.quote`` is the only method a feed may offer. This module posts
market data to one allowlisted public Hyperliquid ``/info`` URL, or reads a
local JSON file written by an outside process. It has no credentials, no
broker client, and no order, transfer, or cancel method.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Callable, Protocol
from urllib.parse import urlsplit


PINNED_HOST = "api.hyperliquid.xyz"
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
HYPERLIQUID_ORIGIN = "https://api.hyperliquid.xyz"
ALLOWED_SYMBOLS = frozenset({"BTC", "ETH"})
FEED_FILE = "file"
FEED_HYPERLIQUID = "hyperliquid"
DEFAULT_MAX_QUOTE_AGE_SECONDS = 300
QUOTE_FIELDS = ("symbol", "bid", "ask", "mark", "source", "fetched_at")
FUTURE_SKEW_SECONDS = 30


class FeedError(Exception):
    """A read failed closed. Nothing was sent to an exchange."""


class UnsupportedSymbol(FeedError):
    """The symbol is not BTC or ETH. Callers must not fall back for this."""


class PriceFeed(Protocol):
    """A read-only price source. Implementations must not place orders."""

    def quote(self, symbol: str) -> "Quote":
        """Return the latest bid, ask, and mark for ``symbol``."""


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: Decimal
    ask: Decimal
    mark: Decimal
    source: str
    feed: str
    fetched_at: datetime


def require_symbol(symbol: str) -> str:
    if symbol not in ALLOWED_SYMBOLS:
        raise UnsupportedSymbol(f"symbol {symbol!r} is not BTC or ETH")
    return symbol


class _RejectRedirect(urllib.request.HTTPRedirectHandler):
    """A 3xx Location is a second URL. Do not follow it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FeedError("refusing redirect from the pinned public info host")


def _pinned_opener():
    """Ignore environment proxies. They are not a trusted path to the pinned host."""
    return urllib.request.build_opener(_RejectRedirect, urllib.request.ProxyHandler({}))


def _assert_pinned(url: str) -> None:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise FeedError("refusing an unpinned URL") from exc
    if (
        parts.scheme != "https"
        or parts.hostname != PINNED_HOST
        or port not in (None, 443)
        or parts.username is not None
        or parts.password is not None
        or parts.path != "/info"
        or parts.query
        or parts.fragment
        or url != HYPERLIQUID_INFO_URL
    ):
        raise FeedError("refusing URL that is not the pinned public info host")


def post_public_info(payload: dict, timeout: float = 15.0, user_agent: str = "hypergrok-paper/1"):
    """POST JSON to the pinned public info URL and nowhere else."""
    return _post_allowlisted(HYPERLIQUID_INFO_URL, payload, timeout, user_agent)


def _post_allowlisted(url: str, payload: dict, timeout: float, user_agent: str, opener=None):
    _assert_pinned(url)
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": user_agent},
        method="POST",
    )
    opener = opener or _pinned_opener()
    with opener.open(request, timeout=timeout) as response:
        if getattr(response, "code", 200) not in (None, 200):
            raise FeedError("refusing a non-200 response from the pinned host")
        return json.load(response)


class HyperliquidInfoFeed:
    """Public ``/info`` book. The URL is a constant, not a constructor argument."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    def quote(self, symbol: str) -> Quote:
        symbol = require_symbol(symbol)
        book = post_public_info({"type": "l2Book", "coin": symbol}, timeout=self.timeout)
        levels = book.get("levels") if isinstance(book, dict) else None
        if not isinstance(levels, list) or len(levels) < 2 or not levels[0] or not levels[1]:
            raise FeedError("info book did not include a bid and an ask")
        bid = Decimal(str(levels[0][0]["px"]))
        ask = Decimal(str(levels[1][0]["px"]))
        mark = (bid + ask) / Decimal(2)
        _require_coherent(bid, ask, mark)
        return Quote(symbol, bid, ask, mark, FEED_HYPERLIQUID, FEED_HYPERLIQUID, datetime.now(timezone.utc))


class FileQuoteFeed:
    """Quotes from a local JSON file. No network and no broker SDK."""

    def __init__(self, path: str, max_age_seconds: int = DEFAULT_MAX_QUOTE_AGE_SECONDS, now: Callable[[], datetime] | None = None):
        if isinstance(path, str) and path.startswith(("http://", "https://")):
            raise FeedError("quotes_file must be a local path")
        if not isinstance(max_age_seconds, int) or isinstance(max_age_seconds, bool) or max_age_seconds <= 0:
            raise FeedError("max_quote_age_seconds must be a positive integer")
        self.path = path
        self.max_age_seconds = max_age_seconds
        self._now = now or (lambda: datetime.now(timezone.utc))

    def quote(self, symbol: str) -> Quote:
        symbol = require_symbol(symbol)
        for raw in _load_quotes(self.path):
            if isinstance(raw, dict) and raw.get("symbol") == symbol:
                return _parse_quote(raw, self.max_age_seconds, self._now(), feed=FEED_FILE)
        raise FeedError(f"no usable quote for {symbol}")


class FallbackFeed:
    """Try the configured feed, then the public info feed, for BTC and ETH only."""

    def __init__(self, primary: PriceFeed, fallback: PriceFeed):
        self.primary = primary
        self.fallback = fallback

    def quote(self, symbol: str) -> Quote:
        require_symbol(symbol)
        try:
            return self.primary.quote(symbol)
        except UnsupportedSymbol:
            raise
        except Exception:
            return self.fallback.quote(symbol)


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise FeedError("price config must be a JSON object")
    return data


def build_feed(config: dict, *, now: Callable[[], datetime] | None = None) -> PriceFeed:
    """Choose the read-only source. Fallback happens only when config asks for it."""
    source = config.get("price_source", "hyperliquid")
    fallback_name = config.get("fallback", "none")
    if fallback_name not in ("none", "hyperliquid"):
        raise FeedError("fallback must be none or hyperliquid")
    timeout = config.get("timeout", 15.0)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise FeedError("timeout must be a positive number")
    hyperliquid = HyperliquidInfoFeed(timeout=float(timeout))
    if source == "hyperliquid":
        return hyperliquid
    if source != "file":
        raise FeedError("price_source must be file or hyperliquid")
    quotes_file = config.get("quotes_file")
    if not isinstance(quotes_file, str) or not quotes_file:
        raise FeedError("quotes_file is required when price_source is file")
    max_age = config.get("max_quote_age_seconds", DEFAULT_MAX_QUOTE_AGE_SECONDS)
    primary = FileQuoteFeed(quotes_file, max_age, now=now)
    if fallback_name == "none":
        return primary
    return FallbackFeed(primary, hyperliquid)


def _load_quotes(path: str) -> list:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    rows = [data] if isinstance(data, dict) else data
    if not isinstance(rows, list) or not rows:
        raise FeedError("quotes file must be a quote object or a non-empty array")
    for raw in rows:
        if isinstance(raw, dict) and raw.get("symbol") not in ALLOWED_SYMBOLS:
            raise UnsupportedSymbol("quotes file contains a symbol other than BTC or ETH")
    return rows


def _money(value, name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise FeedError(f"{name} must be a finite decimal string")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise FeedError(f"{name} must be a finite decimal") from exc
    if not number.is_finite():
        raise FeedError(f"{name} must be finite")
    return number


def _require_coherent(bid: Decimal, ask: Decimal, mark: Decimal) -> None:
    if not (bid.is_finite() and ask.is_finite() and mark.is_finite()):
        raise FeedError("bid, ask and mark must be finite")
    if not (bid > 0 and ask > 0 and mark > 0 and bid <= mark <= ask):
        raise FeedError("mark must be finite and inside the bid/ask")


def _parse_quote(raw: dict, max_age_seconds: int, now: datetime, feed: str) -> Quote:
    if not isinstance(raw, dict):
        raise FeedError("quote must be an object")
    missing = [field for field in QUOTE_FIELDS if field not in raw or raw[field] in (None, "")]
    if missing:
        raise FeedError("missing field: " + ", ".join(missing))
    symbol = require_symbol(str(raw["symbol"]))
    if raw["source"] != "robinhood":
        raise FeedError("source must be robinhood")
    bid = _money(raw["bid"], "bid")
    ask = _money(raw["ask"], "ask")
    mark = _money(raw["mark"], "mark")
    _require_coherent(bid, ask, mark)
    fetched = _parse_time(raw["fetched_at"])
    age = (now - fetched).total_seconds()
    if age > max_age_seconds:
        raise FeedError("stale quote")
    if age < -FUTURE_SKEW_SECONDS:
        raise FeedError("quote fetched_at is too far in the future")
    return Quote(symbol, bid, ask, mark, "robinhood", feed, fetched)


def _parse_time(value) -> datetime:
    if not isinstance(value, str):
        raise FeedError("fetched_at must be an ISO8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FeedError("fetched_at is not ISO8601") from exc
    if parsed.tzinfo is None:
        raise FeedError("fetched_at must include a timezone")
    return parsed.astimezone(timezone.utc)
