#!/usr/bin/env python3
"""Paper-only guarantees: no live order path, and the simulator enforces its rules."""

from __future__ import annotations

import ast
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
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
from paper_sim import PaperError, submit  # noqa: E402


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
        return Quote(
            symbol, Decimal("100"), Decimal("101"), Decimal("100.5"),
            self.source, NOW,
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

    def test_hyperliquid_feed_refuses_every_other_url(self):
        captured = {}

        class Response(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            return Response(b'{"ok": true}')

        original = market_data.urllib.request.urlopen
        market_data.urllib.request.urlopen = fake_urlopen
        try:
            self.assertEqual(market_data.post_public_info({"type": "allMids"}), {"ok": True})
        finally:
            market_data.urllib.request.urlopen = original
        self.assertEqual(captured["url"], HYPERLIQUID_INFO_URL)
        for url in (
            "https://api.hyperliquid.xyz/exchange",
            "https://api.hyperliquid-testnet.xyz/info",
            "https://example.com/info",
        ):
            with self.assertRaises(FeedError):
                market_data._post_allowlisted(url, {}, 1, "test")

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
        self.assertEqual(feed.quote("BTC").source, "robinhood")

    def test_stale_file_falls_back_to_hyperliquid_but_not_for_other_symbols(self):
        feed = FallbackFeed(Boom(), FixedFeed())
        self.assertEqual(feed.quote("BTC").source, "hyperliquid")
        with self.assertRaises(UnsupportedSymbol):
            feed.quote("DOGE")
        with self.assertRaises(FeedError):
            build_feed({"price_source": "broker", "fallback": "hyperliquid"})


class TestSimulatorRules(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.journal = os.path.join(self.directory.name, "journal.jsonl")
        self.feed = FixedFeed()

    def order(self, **overrides):
        order = {
            "symbol": "BTC",
            "side": "buy",
            "entry": "100",
            "size": "0.01",
            "take_profit": "300",
            "trailing_stop": {"distance": "100"},
        }
        order.update(overrides)
        return order

    def test_accepts_a_rule_following_order_and_appends(self):
        event = submit(self.order(), journal_path=self.journal, feed=self.feed)
        self.assertEqual(event["type"], "accepted")
        self.assertEqual(event["quote"]["source"], "hyperliquid")
        lines = Path(self.journal).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])["event"]["symbol"], "BTC")

    def test_rejects_missing_stop_poor_payoff_excess_risk_and_other_coins(self):
        bare = self.order()
        del bare["trailing_stop"]
        with self.assertRaisesRegex(PaperError, "trailing stop"):
            submit(bare, journal_path=self.journal, feed=self.feed)
        with self.assertRaisesRegex(PaperError, "under 2:1"):
            submit(self.order(take_profit="150"), journal_path=self.journal, feed=self.feed)
        with self.assertRaisesRegex(PaperError, "over 1%"):
            submit(self.order(size="0.02"), journal_path=self.journal, feed=self.feed)
        with self.assertRaises(PaperError):
            submit(self.order(symbol="SOL"), journal_path=self.journal, feed=self.feed)
        self.assertFalse(os.path.exists(self.journal))

    def test_rules_ignore_a_caller_supplied_equity_and_cannot_be_skipped(self):
        bribe = self.order(size="0.02", equity="1000000", force=True)
        with self.assertRaisesRegex(PaperError, "over 1%"):
            submit(bribe, journal_path=self.journal, feed=self.feed)
        parameters = inspect.signature(submit).parameters
        self.assertEqual(set(parameters), {"order", "journal_path", "feed"})
        with self.assertRaisesRegex(PaperError, "transfer"):
            submit({"type": "withdraw", "symbol": "BTC"}, journal_path=self.journal, feed=self.feed)

    def test_split_orders_cannot_exceed_one_percent_and_the_journal_is_append_only(self):
        submit(self.order(), journal_path=self.journal, feed=self.feed)
        first = Path(self.journal).read_bytes()
        with self.assertRaisesRegex(PaperError, "over 1%"):
            submit(self.order(symbol="ETH", size="0.001", trailing_stop={"distance": "1"}), journal_path=self.journal, feed=self.feed)
        self.assertEqual(Path(self.journal).read_bytes(), first)
        flipped = bytearray(first)
        flipped[-4] = flipped[-4] ^ 1
        Path(self.journal).write_bytes(flipped)
        with self.assertRaisesRegex(PaperError, "hash chain"):
            submit(self.order(size="0.001", trailing_stop={"distance": "1"}, take_profit="400"), journal_path=self.journal, feed=self.feed)
        self.assertEqual(Path(self.journal).read_bytes(), bytes(flipped))


if __name__ == "__main__":
    unittest.main()
