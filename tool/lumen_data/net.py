"""Polite, cached HTTP fetching for the data build."""
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "LumenDataBuild/1.0 (one-time data build for an offline Catholic Scripture app)"
_MISSING = b"__lumen_404__"
_SYSTEM_ROOTS = Path("/etc/ssl/cert.pem")   # macOS's bundle; python.org builds ship without roots


def ssl_context() -> ssl.SSLContext:
    """A verifying TLS context that also works on Python builds missing their own root certificates."""
    context = ssl.create_default_context()
    if not context.get_ca_certs() and _SYSTEM_ROOTS.exists():
        context.load_verify_locations(cafile=str(_SYSTEM_ROOTS))
    return context


class Fetcher:
    """Fetches each URL once, caching bodies on disk. Network requests are spaced by min_interval seconds."""

    def __init__(self, min_interval: float = 0.0):
        self.min_interval = min_interval
        self.network_requests = 0
        self._last = 0.0

    def get(self, url: str, cache_file: Path, headers: dict[str, str] | None = None) -> bytes | None:
        """Returns the body, or None when the server answered 404. Other HTTP errors raise."""
        if cache_file.exists():
            data = cache_file.read_bytes()
            return None if data == _MISSING else data
        wait = self.min_interval - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
        self.network_requests += 1
        try:
            with urllib.request.urlopen(request, timeout=60, context=ssl_context()) as response:
                data = response.read()
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            data = _MISSING
        finally:
            self._last = time.monotonic()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_bytes(data)
        return None if data == _MISSING else data
