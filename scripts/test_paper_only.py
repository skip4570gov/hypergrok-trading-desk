#!/usr/bin/env python3
"""Paper-only guarantees: no live order path, and the simulator enforces its rules."""

from __future__ import annotations

import ast
import http.client
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.response
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import market_data  # noqa: E402
import paper_sim  # noqa: E402
from market_data import (  # noqa: E402
    HYPERLIQUID_INFO_URL,
    FallbackFeed,
    FeedError,
    FileQuoteFeed,
    HyperliquidInfoFeed,
    Quote,
    UnsupportedSymbol,
    build_feed,
)
from paper_sim import PaperError, close, mark, reset, submit  # noqa: E402


NOW = datetime(2026, 11, 8, 0, 20, tzinfo=timezone.utc)
FORBIDDEN = (
    "HYPERLIQUID_PRIVATE_KEY",
    "api-wallet.key",
    "eth_account",
    "privateKeyToAccount",
    "ExchangeClient",
    "from hyperliquid",
    "import hyperliquid",
    "@nktkas/hyperliquid",
    "api.robinhood.com",
    "robin_stocks",
)
ORDER_WORDS = ("transfer", "withdraw", "deposit", "place_order", "usd_transfer")


def fresh_quote(**overrides):
    quote = {
        "symbol": "BTC",
        "bid": "100000",
        "ask": "100010",
        "mark": "100005",
        "source": "robinhood",
        "fetched_at": NOW.isoformat().replace("+00:00", "Z"),
    }
    quote.update(overrides)
    return quote


class FixedFeed:
    def __init__(self, source="hyperliquid"):
        self.source = source

    def quote(self, symbol):
        feed = "file" if self.source == "robinhood" else "hyperliquid"
        return Quote(
            symbol, Decimal("100"), Decimal("101"), Decimal("100.5"),
            self.source, feed, NOW,
        )


class Boom:
    def quote(self, symbol):
        raise FeedError("stale quote")


class TestLiveOrdersImpossible(unittest.TestCase):
    def test_execution_trader_and_writers_are_gone(self):
        self.assertFalse((ROOT / "agents" / "execution-trader.md").exists())
        for path in (ROOT / "agents").glob("*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("writes_to_exchange: false", text)
            self.assertNotIn("writes_to_exchange: true", text)

    def test_operational_files_have_no_signer_or_robinhood_client(self):
        roots = [ROOT / "skills", ROOT / "agents", ROOT / "scripts"]
        offenders = []
        for root in roots:
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix not in {".py", ".md"}:
                    continue
                if path.name.startswith("test_"):
                    continue
                text = path.read_text(encoding="utf-8")
                for token in FORBIDDEN:
                    if token in text:
                        offenders.append(f"{path.relative_to(ROOT)}: {token}")
                if path.suffix == ".py" and path.name not in {"market_data.py"}:
                    if "\"/exchange\"" in text or "'/exchange'" in text or ".xyz/exchange" in text:
                        offenders.append(f"{path.relative_to(ROOT)}: exchange write URL")
        self.assertEqual(offenders, [])

    def test_simulator_module_has_no_exchange_or_broker_method(self):
        source = (SCRIPTS / "paper_sim.py").read_text(encoding="utf-8")
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/exchange", source)
        tree = ast.parse(source)
        names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue(set(ORDER_WORDS).isdisjoint(names))
        self.assertIn("submit", names)

    def test_hyperliquid_feed_pins_the_host_and_refuses_redirects(self):
        captured = {}

        class Response(io.BytesIO):
            code = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        class Opener:
            def open(self, request, timeout=None):
                captured["url"] = request.full_url
                return Response(b'{"ok": true}')

        original = market_data._pinned_opener
        market_data._pinned_opener = lambda: Opener()
        try:
            self.assertEqual(market_data.post_public_info({"type": "allMids"}), {"ok": True})
        finally:
            market_data._pinned_opener = original
        self.assertEqual(captured["url"], HYPERLIQUID_INFO_URL)
        for url in (
            "https://api.hyperliquid.xyz/exchange",
            "https://api.hyperliquid-testnet.xyz/info",
            "https://example.com/info",
            "https://user:pw@api.hyperliquid.xyz/info",
            "https://api.hyperliquid.xyz:8443/info",
        ):
            with self.assertRaises(FeedError):
                market_data._post_allowlisted(url, {}, 1, "test")
        os.environ["https_proxy"] = "http://127.0.0.1:9"
        try:
            opener = market_data._pinned_opener()
        finally:
            os.environ.pop("https_proxy", None)
        proxy_handlers = [handler for handler in opener.handlers if isinstance(handler, urllib.request.ProxyHandler)]
        self.assertEqual(proxy_handlers, [])
        self.assertFalse(any(getattr(handler, "proxies", None) for handler in opener.handlers))
        calls = []

        class FirstHop(urllib.request.BaseHandler):
            def https_open(self, request):
                calls.append(request.full_url)
                headers = http.client.HTTPMessage()
                headers["Location"] = "https://evil.example/info"
                response = urllib.response.addinfourl(io.BytesIO(b""), headers, request.full_url, 302)
                response.code = 302
                response.msg = "Found"
                return response

        redirecting = urllib.request.OpenerDirector()
        redirecting.add_handler(FirstHop())
        redirecting.add_handler(market_data._RejectRedirect())
        redirecting.add_handler(urllib.request.HTTPErrorProcessor())
        with self.assertRaises(FeedError):
            market_data._post_allowlisted(HYPERLIQUID_INFO_URL, {"type": "allMids"}, 1, "test", opener=redirecting)
        self.assertEqual(calls, [HYPERLIQUID_INFO_URL])

    def test_read_scripts_reject_base_url_and_testnet(self):
        for script in ("opening_bell.py", "account_read.py", "desk_doctor.py", "stop_cost.py", "research_dataset.py"):
            for flag in ("--base-url", "https://example.com"), ("--testnet",):
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / script), *flag, "--json"],
                    capture_output=True, text=True, cwd=ROOT,
                )
                self.assertEqual(result.returncode, 2, (script, flag, result.stderr, result.stdout))
                self.assertIn("unrecognized arguments", result.stderr + result.stdout)


class TestFileQuotes(unittest.TestCase):
    def feed(self, payload, max_age=300):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(payload, handle)
        handle.close()
        self.addCleanup(os.remove, handle.name)
        return FileQuoteFeed(handle.name, max_age, now=lambda: NOW)

    def test_accepts_btc_and_eth_robinhood_quotes(self):
        eth = fresh_quote(symbol="ETH", bid="3000", ask="3001", mark="3000.5")
        quote = self.feed([fresh_quote(), eth]).quote("ETH")
        self.assertEqual(quote.symbol, "ETH")
        self.assertEqual(quote.source, "robinhood")
        self.assertEqual(quote.feed, "file")
        self.assertEqual(quote.mark, Decimal("3000.5"))

    def test_rejects_stale_missing_and_other_symbols(self):
        stale = fresh_quote(fetched_at=(NOW - timedelta(minutes=6)).isoformat())
        with self.assertRaisesRegex(FeedError, "stale"):
            self.feed(stale).quote("BTC")
        missing = fresh_quote()
        del missing["bid"]
        with self.assertRaisesRegex(FeedError, "missing field"):
            self.feed(missing).quote("BTC")
        with self.assertRaises(UnsupportedSymbol):
            self.feed(fresh_quote(symbol="SOL")).quote("BTC")
        with self.assertRaises(UnsupportedSymbol):
            self.feed(fresh_quote()).quote("SOL")
        with self.assertRaisesRegex(FeedError, "source"):
            self.feed(fresh_quote(source="other")).quote("BTC")
        with self.assertRaisesRegex(FeedError, "finite"):
            self.feed(fresh_quote(mark="NaN")).quote("BTC")
        with self.assertRaisesRegex(FeedError, "finite"):
            self.feed(fresh_quote(bid="Infinity")).quote("BTC")
        with self.assertRaisesRegex(FeedError, "inside"):
            self.feed(fresh_quote(mark="100020")).quote("BTC")

    def test_default_max_age_is_five_minutes_and_config_selects_the_source(self):
        self.assertEqual(market_data.DEFAULT_MAX_QUOTE_AGE_SECONDS, 300)
        self.assertIsInstance(build_feed({"price_source": "hyperliquid"}), HyperliquidInfoFeed)
        path = self.feed(fresh_quote()).path
        feed = build_feed({
            "price_source": "file",
            "quotes_file": path,
            "max_quote_age_seconds": 300,
            "fallback": "hyperliquid",
        }, now=lambda: NOW)
        self.assertIsInstance(feed, FallbackFeed)
        self.assertEqual(feed.quote("BTC").feed, "file")
        plain = build_feed({
            "price_source": "file",
            "quotes_file": path,
            "fallback": "none",
        }, now=lambda: NOW)
        self.assertNotIsInstance(plain, FallbackFeed)
        self.assertEqual(plain.quote("BTC").feed, "file")

    def test_fallback_is_explicit_and_records_the_feed_that_answered(self):
        stale = self.feed(fresh_quote(mark="NaN"))
        quiet = build_feed({"price_source": "file", "quotes_file": stale.path, "fallback": "none"}, now=lambda: NOW)
        with self.assertRaises(FeedError):
            quiet.quote("BTC")
        answered = FallbackFeed(Boom(), FixedFeed())
        quote = answered.quote("BTC")
        self.assertEqual(quote.feed, "hyperliquid")
        self.assertNotEqual(quote.feed, "file")
        with self.assertRaises(UnsupportedSymbol):
            answered.quote("DOGE")
        with self.assertRaises(FeedError):
            build_feed({"price_source": "broker", "fallback": "hyperliquid"})


class MutableFeed:
    def __init__(self, bid, ask, mark):
        self.bid, self.ask, self.mark = Decimal(bid), Decimal(ask), Decimal(mark)

    def quote(self, symbol):
        return Quote(symbol, self.bid, self.ask, self.mark, "hyperliquid", "hyperliquid", NOW)

    def set(self, bid, ask, mark):
        self.bid, self.ask, self.mark = Decimal(bid), Decimal(ask), Decimal(mark)


class TestSimulatorRules(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.state = os.path.join(self.directory.name, "state")
        self.feed = FixedFeed()
        reset(self.state)
        self.journal = os.path.join(self.state, "journal.jsonl")

    def order(self, **overrides):
        order = {
            "symbol": "BTC",
            "side": "buy",
            "entry": "100.5",
            "size": "0.005",
            "take_profit": "400",
            "trailing_stop": {"distance": "100"},
        }
        order.update(overrides)
        return order

    def test_uses_the_quote_and_rejects_nonsense_prices(self):
        event = submit(self.order(), state_dir=self.state, feed=self.feed)
        self.assertEqual(event["type"], "open")
        self.assertNotEqual(Decimal(event["fill"]), Decimal("1"))
        self.assertEqual(event["quote"]["feed"], "hyperliquid")
        self.assertGreater(Decimal(event["fill"]), Decimal("100"))
        with self.assertRaisesRegex(PaperError, "outside the quote"):
            submit(self.order(symbol="ETH", entry="1"), state_dir=self.state, feed=self.feed)
        for bad in ("0", "-1", "NaN", "Infinity"):
            with self.assertRaisesRegex(PaperError, "above zero"):
                submit(self.order(symbol="ETH", side="sell", take_profit=bad, entry="100.5"), state_dir=self.state, feed=self.feed)

    def test_trailing_stop_moves_and_stop_target_and_close_change_equity(self):
        prices = MutableFeed("100", "101", "100.5")
        opened = submit(self.order(size="0.001", trailing_stop={"distance": "1"}, take_profit="110"), state_dir=self.state, feed=prices)
        start_equity = Decimal(opened["equity_after"])
        self.assertLess(start_equity, Decimal("100"))
        prices.set("104", "106", "105")
        trailed = mark(self.state, "BTC", prices)
        self.assertEqual(trailed["type"], "trail")
        self.assertGreater(Decimal(trailed["stop"]), Decimal(opened["stop"]))
        prices.set("102", "104", "103")
        stopped = mark(self.state, "BTC", prices)
        self.assertEqual(stopped["reason"], "stop")
        self.assertNotEqual(Decimal(stopped["equity_after"]), Decimal("100"))
        self.assertIn("pnl", stopped)
        prices.set("100", "101", "100.5")
        submit(self.order(size="0.001", trailing_stop={"distance": "1"}, take_profit="110"), state_dir=self.state, feed=prices)
        prices.set("109", "111", "110")
        targeted = mark(self.state, "BTC", prices)
        self.assertEqual(targeted["reason"], "target")
        self.assertGreater(Decimal(targeted["pnl"]), 0)
        prices.set("100", "101", "100.5")
        submit(self.order(symbol="ETH", size="0.001", trailing_stop={"distance": "1"}, take_profit="110"), state_dir=self.state, feed=prices)
        closed = close(self.state, "ETH", prices)
        self.assertEqual(closed["reason"], "close")
        self.assertEqual(closed["quote"]["feed"], "hyperliquid")

    def test_rejects_missing_stop_poor_payoff_excess_risk_and_other_coins(self):
        before = Path(self.journal).read_bytes()
        bare = self.order()
        del bare["trailing_stop"]
        with self.assertRaisesRegex(PaperError, "trailing stop"):
            submit(bare, state_dir=self.state, feed=self.feed)
        with self.assertRaisesRegex(PaperError, "under 2:1"):
            submit(self.order(take_profit="102"), state_dir=self.state, feed=self.feed)
        with self.assertRaisesRegex(PaperError, "over 1%"):
            submit(self.order(size="0.02"), state_dir=self.state, feed=self.feed)
        with self.assertRaises(PaperError):
            submit(self.order(symbol="SOL"), state_dir=self.state, feed=self.feed)
        self.assertEqual(Path(self.journal).read_bytes(), before)

    def test_equity_comes_from_the_journal_and_deletion_is_not_a_reset(self):
        bribe = self.order(size="0.02", equity="1000000", force=True)
        with self.assertRaisesRegex(PaperError, "over 1%"):
            submit(bribe, state_dir=self.state, feed=self.feed)
        parameters = inspect.signature(submit).parameters
        self.assertEqual(set(parameters), {"order", "state_dir", "feed"})
        os.remove(self.journal)
        with self.assertRaisesRegex(PaperError, "journal is missing"):
            submit(self.order(), state_dir=self.state, feed=self.feed)
        self.assertFalse(os.path.exists(self.journal))
        event = reset(self.state)
        self.assertEqual(event["type"], "reset")
        self.assertEqual(event["equity"], "100")
        recorded = json.loads(Path(self.journal).read_text(encoding="utf-8").splitlines()[0])["event"]
        self.assertEqual(recorded["type"], "reset")

    def test_overlapping_submits_cannot_both_pass_the_risk_check(self):
        orders = [
            self.order(symbol="BTC", size="0.01", trailing_stop={"distance": "60"}, take_profit="400"),
            self.order(symbol="ETH", size="0.01", trailing_stop={"distance": "60"}, take_profit="400"),
        ]
        results = []
        errors = []

        def once(order):
            try:
                results.append(submit(order, state_dir=self.state, feed=self.feed))
            except PaperError as exc:
                errors.append(exc.code)

        threads = [threading.Thread(target=once, args=(order,)) for order in orders]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(results), 1)
        self.assertEqual(errors, ["risk_limit"])

    def test_split_orders_cannot_exceed_one_percent_and_the_journal_is_append_only(self):
        submit(self.order(size="0.009"), state_dir=self.state, feed=self.feed)
        first = Path(self.journal).read_bytes()
        with self.assertRaisesRegex(PaperError, "over 1%"):
            submit(self.order(symbol="ETH", size="0.003"), state_dir=self.state, feed=self.feed)
        self.assertEqual(Path(self.journal).read_bytes(), first)
        flipped = bytearray(first)
        flipped[-4] = flipped[-4] ^ 1
        Path(self.journal).write_bytes(flipped)
        with self.assertRaisesRegex(PaperError, "hash chain"):
            submit(self.order(symbol="ETH", size="0.001", trailing_stop={"distance": "1"}, take_profit="400"), state_dir=self.state, feed=self.feed)
        self.assertEqual(Path(self.journal).read_bytes(), bytes(flipped))


class TestInstallPin(unittest.TestCase):
    def test_install_entries_use_this_repo_and_an_immutable_commit(self):
        from install_pin import COMMIT, REPOSITORY
        self.assertEqual(REPOSITORY, "https://github.com/skip4570gov/hypergrok-trading-desk")
        self.assertRegex(COMMIT, r"^[0-9a-f]{40}$")
        files = [
            ROOT / "README.md",
            ROOT / "SETUP.md",
            ROOT / "skills/hypergrok-bootstrap/SKILL.md",
            ROOT / "template/grok-bot.json",
            ROOT / ".grok-plugin/marketplace.json",
            ROOT / ".agents/plugins/marketplace.json",
            ROOT / "docs/hyperliquid-cursor.md",
        ]
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn(COMMIT, text, path.name)
            self.assertNotIn("galleonlabs/hypergrok-trading-desk", text, path.name)
            self.assertNotIn("x.ai/bot", text, path.name)
            self.assertNotIn("--branch paper-only", text, path.name)


if __name__ == "__main__":
    unittest.main()
