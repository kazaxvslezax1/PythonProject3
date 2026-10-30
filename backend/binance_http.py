"""PAPER-only HTTP boundary for the Binance calls owned by this project.

Only explicitly listed public market-data routes can reach the network. This
module does not offer an authenticated client or a LIVE-trading switch.
"""

from urllib.parse import parse_qsl, urlsplit

import requests

_PUBLIC_PARAMS = {
    "/api/v3/klines": frozenset({"symbol", "interval", "limit", "startTime", "endTime"}),
    "/api/v3/ticker/price": frozenset({"symbol"}),
    "/api/v3/ticker/24hr": frozenset({"symbol"}),
    "/api/v3/exchangeInfo": frozenset({"symbol"}),
}


class PaperOnlyBinanceError(PermissionError):
    """A Binance request was rejected before any network activity."""


def _blocked():
    # Never include URLs, parameters, headers or credentials in the exception.
    raise PaperOnlyBinanceError("Binance request blocked by PAPER-only policy")


def _new_session():
    """Own an anonymous transport; ignore netrc, proxy and CA environment settings."""
    session = requests.Session()
    session.trust_env = False
    return session


def request_public(method, url, *, params=None, timeout=(5, 20), **kwargs):
    """Send an allowlisted anonymous GET; reject every other Binance request."""
    if method != "GET" or not isinstance(url, str):
        _blocked()
    try:
        parsed = urlsplit(url)
        query = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        _blocked()
    if (
        parsed.scheme != "https"
        or parsed.netloc != "api.binance.com"
        or parsed.path not in _PUBLIC_PARAMS
        or parsed.fragment
        or kwargs
    ):
        _blocked()
    if params is not None:
        if not isinstance(params, dict):
            _blocked()
        query.extend(params.items())
    allowed = _PUBLIC_PARAMS[parsed.path]
    if any(not isinstance(key, str) or key not in allowed for key, _ in query):
        _blocked()
    # Binance redirects are not followed: the destination was not allowlisted.
    with _new_session() as session:
        response = session.get(url, params=params, timeout=timeout, allow_redirects=False)
    if 300 <= getattr(response, "status_code", 200) < 400:
        _blocked()
    return response


def get_public(url, *, params=None, timeout=(5, 20)):
    return request_public("GET", url, params=params, timeout=timeout)
