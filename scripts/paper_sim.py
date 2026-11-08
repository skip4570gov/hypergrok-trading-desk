#!/usr/bin/env python3
"""Local paper simulator. The only order path in this checkout.

State lives in one directory owned by this program. Equity is replayed from
the journal. A missing journal is not a fresh wallet: submit refuses until
an explicit reset writes a reset record. There is no private key and no
exchange write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from market_data import FEED_FILE, FEED_HYPERLIQUID, FeedError, PriceFeed, Quote, build_feed, load_config, require_symbol

try:
    import fcntl
except ImportError:  # pragma: no cover - this checkout runs on Linux
    fcntl = None


RESET_EQUITY = Decimal("100")
MAX_RISK_FRACTION = Decimal("0.01")
MIN_REWARD_TO_RISK = Decimal("2")
FEE_RATE = Decimal("0.00045")
SLIPPAGE = Decimal("0.0005")
OWNER_NAME = "paper_sim"
GENESIS = "GENESIS"
JOURNAL_NAME = "journal.jsonl"
OWNER_FILE = "owner"
LOCK_NAME = "owner.lock"


class PaperError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass
class Position:
    symbol: str
    side: str
    size: Decimal
    fill: Decimal
    distance: Decimal
    target: Decimal
    stop: Decimal
    risk: Decimal


@dataclass
class Book:
    equity: Decimal
    positions: dict


def reset(state_dir: str) -> dict:
    """Create the journal only when it is missing, and record that fact."""

    def act():
        path = _journal_path(state_dir)
        if os.path.exists(path):
            raise PaperError("journal_exists", "refusing to discard an existing journal")
        _write_owner(state_dir)
        event = {"type": "reset", "equity": str(RESET_EQUITY), "owner": OWNER_NAME}
        _append_unlocked(path, event)
        return event

    return _transaction(state_dir, act)


def submit(order: dict, *, state_dir: str, feed: PriceFeed) -> dict:
    """Validate one paper order against the quote and commit it under the lock."""

    def act():
        path = _require_ready(state_dir)
        symbol, side, entry, size, take_profit, distance = _order_fields(order)
        book = _replay(path)
        if symbol in book.positions:
            raise PaperError("already_open", f"{symbol} already has an open paper position")
        try:
            quote = feed.quote(symbol)
        except FeedError as exc:
            raise PaperError("price", str(exc)) from exc
        _require_quote(quote, symbol)
        if not (quote.bid <= entry <= quote.ask):
            raise PaperError("incoherent_entry", "entry is outside the quote bid/ask and is ignored")
        fill = _entry_fill(side, quote)
        stop = _initial_stop(side, fill, distance)
        risk, ratio = _payoff(side, fill, stop, take_profit, size)
        if ratio < MIN_REWARD_TO_RISK:
            raise PaperError("reward_to_risk", f"reward-to-risk {ratio} is under 2:1 after fees and slippage")
        if risk > book.equity * MAX_RISK_FRACTION or _open_risk(book) + risk > book.equity * MAX_RISK_FRACTION:
            raise PaperError("risk_limit", "risk is over 1% of journal equity")
        fee = fill * size * FEE_RATE
        equity_after = book.equity - fee
        if equity_after <= 0:
            raise PaperError("risk_limit", "fees would consume the paper wallet")
        event = {
            "type": "open",
            "symbol": symbol,
            "side": side,
            "entry": str(entry),
            "fill": str(fill),
            "size": str(size),
            "take_profit": str(take_profit),
            "trail_distance": str(distance),
            "stop": str(stop),
            "fee": str(fee),
            "risk_usd": str(risk),
            "reward_to_risk": str(ratio),
            "equity_after": str(equity_after),
            "quote": _quote_record(quote),
        }
        _append_unlocked(path, event)
        return event

    return _transaction(state_dir, act)


def mark(state_dir: str, symbol: str, feed: PriceFeed) -> dict:
    """Move the trailing stop and fill a stop or target when the quote says so."""

    def act():
        path = _require_ready(state_dir)
        symbol_name = require_symbol(symbol)
        book = _replay(path)
        position = book.positions.get(symbol_name)
        if position is None:
            raise PaperError("flat", f"no open paper position in {symbol_name}")
        try:
            quote = feed.quote(symbol_name)
        except FeedError as exc:
            raise PaperError("price", str(exc)) from exc
        _require_quote(quote, symbol_name)
        return _on_quote(path, book, position, quote)

    return _transaction(state_dir, act)


def close(state_dir: str, symbol: str, feed: PriceFeed) -> dict:
    """Close an open paper position at the quote, with fees and slippage."""

    def act():
        path = _require_ready(state_dir)
        symbol_name = require_symbol(symbol)
        book = _replay(path)
        position = book.positions.get(symbol_name)
        if position is None:
            raise PaperError("flat", f"no open paper position in {symbol_name}")
        try:
            quote = feed.quote(symbol_name)
        except FeedError as exc:
            raise PaperError("price", str(exc)) from exc
        _require_quote(quote, symbol_name)
        raw = quote.bid if position.side == "buy" else quote.ask
        return _close_at(path, book, position, raw, "close", quote)

    return _transaction(state_dir, act)


def _on_quote(path: str, book: Book, position: Position, quote: Quote) -> dict:
    if position.side == "buy":
        trailed = max(position.stop, quote.mark - position.distance)
        if quote.mark <= position.stop:
            return _close_at(path, book, position, position.stop, "stop", quote)
        if quote.mark >= position.target:
            return _close_at(path, book, position, position.target, "target", quote)
    else:
        trailed = min(position.stop, quote.mark + position.distance)
        if quote.mark >= position.stop:
            return _close_at(path, book, position, position.stop, "stop", quote)
        if quote.mark <= position.target:
            return _close_at(path, book, position, position.target, "target", quote)
    if trailed == position.stop:
        return {"type": "unchanged", "symbol": position.symbol, "stop": str(position.stop), "quote": _quote_record(quote)}
    if trailed <= 0:
        raise PaperError("invalid_price", "trailing stop would be zero or negative")
    event = {
        "type": "trail",
        "symbol": position.symbol,
        "stop": str(trailed),
        "mark": str(quote.mark),
        "quote": _quote_record(quote),
    }
    _append_unlocked(path, event)
    return event


def _close_at(path: str, book: Book, position: Position, raw_exit: Decimal, reason: str, quote: Quote) -> dict:
    exit_fill = _exit_fill(position.side, raw_exit)
    if exit_fill <= 0:
        raise PaperError("invalid_price", "exit price must be above zero")
    direction = Decimal(1) if position.side == "buy" else Decimal(-1)
    fee = exit_fill * position.size * FEE_RATE
    pnl = (exit_fill - position.fill) * position.size * direction - fee
    equity_after = book.equity + pnl
    event = {
        "type": "close",
        "symbol": position.symbol,
        "reason": reason,
        "exit": str(exit_fill),
        "fee": str(fee),
        "pnl": str(pnl),
        "equity_after": str(equity_after),
        "quote": _quote_record(quote),
    }
    _append_unlocked(path, event)
    return event


def _order_fields(order: dict):
    if not isinstance(order, dict):
        raise PaperError("invalid_order", "order must be an object")
    if order.get("type") in {"transfer", "withdraw", "deposit", "send"} or "transfer" in order:
        raise PaperError("transfer_forbidden", "this simulator cannot transfer, withdraw, or deposit")
    try:
        symbol = require_symbol(str(order.get("symbol", "")))
    except FeedError as exc:
        raise PaperError("symbol", str(exc)) from exc
    side = order.get("side")
    if side not in ("buy", "sell"):
        raise PaperError("invalid_order", "side must be buy or sell")
    entry = _price(order.get("entry"), "entry")
    size = _price(order.get("size"), "size")
    take_profit = _price(order.get("take_profit"), "take_profit")
    trailing = order.get("trailing_stop")
    if not isinstance(trailing, dict) or "distance" not in trailing:
        raise PaperError("trailing_stop_required", "every order needs a trailing stop distance")
    distance = _price(trailing.get("distance"), "trailing_stop.distance")
    return symbol, side, entry, size, take_profit, distance


def _price(value, name: str) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise PaperError("invalid_price", f"{name} must be a finite decimal above zero")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise PaperError("invalid_price", f"{name} must be a finite decimal above zero") from exc
    if not number.is_finite() or number <= 0:
        raise PaperError("invalid_price", f"{name} must be a finite decimal above zero")
    return number


def _require_quote(quote: Quote, symbol: str) -> None:
    if quote.symbol != symbol or quote.feed not in (FEED_FILE, FEED_HYPERLIQUID):
        raise PaperError("price", "price feed returned an unidentified quote")
    for name, value in (("bid", quote.bid), ("ask", quote.ask), ("mark", quote.mark)):
        if not value.is_finite() or value <= 0 or not (quote.bid <= quote.mark <= quote.ask):
            raise PaperError("price", f"quote {name} is not a finite price inside the spread")


def _entry_fill(side: str, quote: Quote) -> Decimal:
    raw = quote.ask if side == "buy" else quote.bid
    fill = raw * (Decimal(1) + SLIPPAGE) if side == "buy" else raw * (Decimal(1) - SLIPPAGE)
    if fill <= 0:
        raise PaperError("invalid_price", "fill price must be above zero")
    return fill


def _exit_fill(side: str, raw: Decimal) -> Decimal:
    slipped = raw * (Decimal(1) - SLIPPAGE) if side == "buy" else raw * (Decimal(1) + SLIPPAGE)
    return slipped


def _initial_stop(side: str, fill: Decimal, distance: Decimal) -> Decimal:
    stop = fill - distance if side == "buy" else fill + distance
    if stop <= 0:
        raise PaperError("invalid_price", "stop would be zero or negative")
    if side == "buy" and stop >= fill:
        raise PaperError("invalid_price", "a long stop must be below the fill")
    if side == "sell" and stop <= fill:
        raise PaperError("invalid_price", "a short stop must be above the fill")
    return stop


def _payoff(side: str, fill: Decimal, stop: Decimal, target: Decimal, size: Decimal):
    if side == "buy" and target <= fill:
        raise PaperError("reward_to_risk", "a buy target must be above the fill")
    if side == "sell" and target >= fill:
        raise PaperError("reward_to_risk", "a sell target must be below the fill")
    entry_fee = fill * size * FEE_RATE
    stop_exit = _exit_fill(side, stop)
    target_exit = _exit_fill(side, target)
    if stop_exit <= 0 or target_exit <= 0:
        raise PaperError("invalid_price", "exit price must be above zero")
    direction = Decimal(1) if side == "buy" else Decimal(-1)
    risk = -((stop_exit - fill) * size * direction - stop_exit * size * FEE_RATE - entry_fee)
    reward = (target_exit - fill) * size * direction - target_exit * size * FEE_RATE - entry_fee
    if risk <= 0 or reward <= 0:
        raise PaperError("reward_to_risk", "fees and slippage leave no positive reward or risk")
    return risk, reward / risk


def _quote_record(quote: Quote) -> dict:
    return {
        "bid": str(quote.bid),
        "ask": str(quote.ask),
        "mark": str(quote.mark),
        "source": quote.source,
        "feed": quote.feed,
        "fetched_at": quote.fetched_at.isoformat(),
    }


def _open_risk(book: Book) -> Decimal:
    return sum((position.risk for position in book.positions.values()), Decimal(0))


def _replay(path: str) -> Book:
    _verify_chain(path)
    equity = None
    positions: dict[str, Position] = {}
    for record in _records(path):
        event = record["event"]
        kind = event.get("type")
        if kind == "reset":
            equity = Decimal(event["equity"])
            positions = {}
        elif kind == "open":
            equity = Decimal(event["equity_after"])
            positions[event["symbol"]] = Position(
                event["symbol"], event["side"], Decimal(event["size"]), Decimal(event["fill"]),
                Decimal(event["trail_distance"]), Decimal(event["take_profit"]), Decimal(event["stop"]),
                Decimal(event["risk_usd"]),
            )
        elif kind == "trail":
            positions[event["symbol"]].stop = Decimal(event["stop"])
        elif kind == "close":
            equity = Decimal(event["equity_after"])
            positions.pop(event["symbol"], None)
        else:
            raise PaperError("journal", "unknown journal event")
    if equity is None:
        raise PaperError("journal_missing", "journal has no reset record")
    return Book(equity, positions)


def _require_ready(state_dir: str) -> str:
    path = _journal_path(state_dir)
    if not os.path.exists(path):
        raise PaperError("journal_missing", "journal is missing; run reset before any order")
    owner = _read_owner(state_dir)
    if owner != OWNER_NAME:
        raise PaperError("owner", "state directory has no paper_sim owner")
    return path


def _journal_path(state_dir: str) -> str:
    return os.path.join(state_dir, JOURNAL_NAME)


def _write_owner(state_dir: str) -> None:
    os.makedirs(state_dir, exist_ok=True)
    path = os.path.join(state_dir, OWNER_FILE)
    fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    try:
        os.write(fd, (OWNER_NAME + "\n").encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_owner(state_dir: str) -> str:
    path = os.path.join(state_dir, OWNER_FILE)
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as handle:
        return handle.read().strip()


def _transaction(state_dir: str, action):
    if fcntl is None:
        raise PaperError("lock", "this checkout cannot lock the paper state")
    os.makedirs(state_dir, exist_ok=True)
    lock_fd = os.open(os.path.join(state_dir, LOCK_NAME), os.O_CREAT | os.O_RDWR, 0o600)
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    try:
        return action()
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


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


def _append_unlocked(path: str, event: dict) -> None:
    if os.path.exists(path):
        _verify_chain(path)
    previous = GENESIS
    records = _records(path)
    if records:
        previous = records[-1]["hash"]
    body = json.dumps(event, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256((previous + body).encode("utf-8")).hexdigest()
    line = json.dumps({"prev": previous, "hash": digest, "event": event}, sort_keys=True) + "\n"
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local paper state. No exchange write.")
    parser.add_argument("command", choices=("reset", "submit", "mark", "close"))
    parser.add_argument("--state", required=True)
    parser.add_argument("--config")
    parser.add_argument("--symbol")
    parser.add_argument("--side")
    parser.add_argument("--entry")
    parser.add_argument("--size")
    parser.add_argument("--take-profit")
    parser.add_argument("--trail-distance")
    args = parser.parse_args(argv)
    try:
        if args.command == "reset":
            event = reset(args.state)
        else:
            if not args.config or not args.symbol:
                raise PaperError("invalid_order", "config and symbol are required")
            feed = build_feed(load_config(args.config))
            if args.command == "mark":
                event = mark(args.state, args.symbol, feed)
            elif args.command == "close":
                event = close(args.state, args.symbol, feed)
            else:
                event = submit({
                    "symbol": args.symbol,
                    "side": args.side,
                    "entry": args.entry,
                    "size": args.size,
                    "take_profit": args.take_profit,
                    "trailing_stop": {"distance": args.trail_distance},
                }, state_dir=args.state, feed=feed)
    except (PaperError, FeedError, OSError, json.JSONDecodeError) as exc:
        code = getattr(exc, "code", "rejected")
        print(json.dumps({"accepted": False, "code": code, "message": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps({"accepted": True, "event": event}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
