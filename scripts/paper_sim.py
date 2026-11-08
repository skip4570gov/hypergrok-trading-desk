#!/usr/bin/env python3
"""Local paper simulator. The only order path in this checkout.

A $100 wallet, BTC and ETH only. Every order needs a trailing stop, at least
2:1 reward-to-risk, and risk at or under 1% of equity including open paper
risk. The journal is append-only and hash-chained. There is no flag that
skips a rule, no private key, and no exchange write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from decimal import Decimal, InvalidOperation
from typing import Callable

from market_data import FeedError, PriceFeed, build_feed, load_config, require_symbol


STARTING_EQUITY = Decimal("100")
MAX_RISK_FRACTION = Decimal("0.01")
MIN_REWARD_TO_RISK = Decimal("2")
GENESIS = "GENESIS"


class PaperError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def submit(order: dict, *, journal_path: str, feed: PriceFeed) -> dict:
    """Validate one paper order and append it. Equity and the rules are not inputs."""
    if not isinstance(order, dict):
        raise PaperError("invalid_order", "order must be an object")
    if order.get("type") in {"transfer", "withdraw", "deposit", "send"} or "transfer" in order:
        raise PaperError("transfer_forbidden", "this simulator cannot transfer, withdraw, or deposit")
    try:
        symbol = require_symbol(str(order.get("symbol", "")))
        side = order.get("side")
        entry = _decimal(order.get("entry"), "entry")
        size = _decimal(order.get("size"), "size")
        take_profit = _decimal(order.get("take_profit"), "take_profit")
        trailing = order.get("trailing_stop")
        if not isinstance(trailing, dict) or "distance" not in trailing:
            raise PaperError("trailing_stop_required", "every order needs a trailing stop distance")
        distance = _decimal(trailing.get("distance"), "trailing_stop.distance")
    except FeedError as exc:
        raise PaperError("symbol", str(exc)) from exc
    if side not in ("buy", "sell"):
        raise PaperError("invalid_order", "side must be buy or sell")
    if entry <= 0 or size <= 0 or distance <= 0:
        raise PaperError("invalid_order", "entry, size, and trailing distance must be positive")
    if side == "buy" and take_profit <= entry:
        raise PaperError("reward_to_risk", "a buy take-profit must be above the entry")
    if side == "sell" and take_profit >= entry:
        raise PaperError("reward_to_risk", "a sell take-profit must be below the entry")
    risk = size * distance
    reward = size * abs(take_profit - entry)
    ratio = reward / risk
    if ratio < MIN_REWARD_TO_RISK:
        raise PaperError("reward_to_risk", f"reward-to-risk {ratio} is under 2:1")
    _verify_chain(journal_path)
    equity = STARTING_EQUITY
    if risk > equity * MAX_RISK_FRACTION or _open_risk(journal_path) + risk > equity * MAX_RISK_FRACTION:
        raise PaperError("risk_limit", "risk is over 1% of the $100 paper equity")
    try:
        quote = feed.quote(symbol)
    except FeedError as exc:
        raise PaperError("price", str(exc)) from exc
    if quote.symbol != symbol:
        raise PaperError("price", "price feed returned a different symbol")
    event = {
        "type": "accepted",
        "symbol": symbol,
        "side": side,
        "entry": str(entry),
        "size": str(size),
        "take_profit": str(take_profit),
        "trail_distance": str(distance),
        "risk_usd": str(risk),
        "reward_to_risk": str(ratio),
        "equity_usd": str(equity),
        "quote": {
            "bid": str(quote.bid),
            "ask": str(quote.ask),
            "mark": str(quote.mark),
            "source": quote.source,
            "fetched_at": quote.fetched_at.isoformat(),
        },
    }
    _append(journal_path, event)
    return event


def _decimal(value, name: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PaperError("invalid_order", f"{name} must be a decimal") from exc
    if not number.is_finite():
        raise PaperError("invalid_order", f"{name} must be finite")
    return number


def _open_risk(path: str) -> Decimal:
    total = Decimal(0)
    for record in _records(path):
        event = record["event"]
        if event.get("type") == "accepted":
            total += Decimal(event["risk_usd"])
    return total


def _records(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _verify_chain(path: str) -> None:
    previous = GENESIS
    for record in _records(path):
        body = json.dumps(record["event"], sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256((previous + body).encode("utf-8")).hexdigest()
        if record.get("prev") != previous or record.get("hash") != digest:
            raise PaperError("journal", "append-only journal failed its hash chain")
        previous = digest


def _append(path: str, event: dict) -> None:
    _verify_chain(path)
    previous = GENESIS
    records = _records(path)
    if records:
        previous = records[-1]["hash"]
    body = json.dumps(event, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256((previous + body).encode("utf-8")).hexdigest()
    line = json.dumps({"prev": previous, "hash": digest, "event": event}, sort_keys=True) + "\n"
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def _feed_from_config(path: str, now: Callable | None = None) -> PriceFeed:
    return build_feed(load_config(path), now=now)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Append one local paper order. No exchange write.")
    parser.add_argument("command", choices=("submit",))
    parser.add_argument("--config", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--side", required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--size", required=True)
    parser.add_argument("--take-profit", required=True)
    parser.add_argument("--trail-distance", required=True)
    args = parser.parse_args(argv)
    order = {
        "symbol": args.symbol,
        "side": args.side,
        "entry": args.entry,
        "size": args.size,
        "take_profit": args.take_profit,
        "trailing_stop": {"distance": args.trail_distance},
    }
    try:
        event = submit(order, journal_path=args.journal, feed=_feed_from_config(args.config))
    except (PaperError, FeedError, OSError, json.JSONDecodeError) as exc:
        code = getattr(exc, "code", "rejected")
        print(json.dumps({"accepted": False, "code": code, "message": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"accepted": True, "event": event}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
