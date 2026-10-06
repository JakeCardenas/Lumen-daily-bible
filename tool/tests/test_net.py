import ssl
import tempfile
import unittest
from pathlib import Path

from lumen_data.net import BudgetExhausted, Fetcher, ssl_context


class FetcherTest(unittest.TestCase):
    def test_returns_cached_body_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "page.html"
            cache.write_bytes(b"cached")
            fetcher = Fetcher()
            self.assertEqual(fetcher.get("https://invalid.example/page", cache), b"cached")
            self.assertEqual(fetcher.network_requests, 0)

    def test_tls_always_verifies_and_has_trusted_roots(self):
        context = ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
        self.assertGreater(len(context.get_ca_certs()), 0)

    def test_cached_404_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "missing.html"
            cache.write_bytes(b"__lumen_404__")
            self.assertIsNone(Fetcher().get("https://invalid.example/missing", cache))

    def test_a_spent_budget_still_serves_the_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "page.html"
            cache.write_bytes(b"cached")
            fetcher = Fetcher(max_network=0)
            self.assertEqual(fetcher.get("https://invalid.example/page", cache), b"cached")
            with self.assertRaises(BudgetExhausted):
                fetcher.get("https://invalid.example/other", Path(tmp) / "other.html")
            self.assertEqual(fetcher.network_requests, 0)
