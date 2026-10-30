"""No test in this module sends a request to Binance."""

import logging

import binance_http
import pytest
import requests
from binance_http import PaperOnlyBinanceError, get_public, request_public
from requests.adapters import BaseAdapter


def mock_transport(monkeypatch, getter):
    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url, **kwargs):
            return getter(url, **kwargs)

    monkeypatch.setattr(binance_http, "_new_session", Session)


@pytest.mark.parametrize(
    "path,params",
    [
        ("/api/v3/klines", {"symbol": "BTCUSDT", "interval": "1h", "limit": 100}),
        ("/api/v3/ticker/price", {"symbol": "BTCUSDT"}),
        ("/api/v3/ticker/24hr", {"symbol": "BTCUSDT"}),
        ("/api/v3/exchangeInfo", {"symbol": "BTCUSDT"}),
    ],
)
def test_public_market_data_reaches_only_anonymous_get(monkeypatch, path, params):
    calls = []

    class Response:
        status_code = 200

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    mock_transport(monkeypatch, fake_get)
    result = get_public(f"https://api.binance.com{path}", params=params)
    assert result.status_code == 200
    assert calls == [
        (
            f"https://api.binance.com{path}",
            {"params": params, "timeout": (5, 20), "allow_redirects": False},
        )
    ]


@pytest.mark.parametrize(
    "method,url",
    [
        ("POST", "https://api.binance.com/api/v3/order"),
        ("DELETE", "https://api.binance.com/api/v3/order"),
        ("POST", "https://api.binance.com/api/v3/klines"),
        ("GET", "https://api.binance.com/api/v3/account"),
        ("GET", "https://fapi.binance.com/fapi/v1/order"),
        ("GET", "https://api.binance.com/api/v3/%6frder"),
        ("GET", "http://api.binance.com/api/v3/klines"),
    ],
)
def test_trading_and_unknown_routes_blocked_before_network(monkeypatch, method, url):
    def forbidden(*args, **kwargs):
        raise AssertionError("network was reached")

    mock_transport(monkeypatch, forbidden)
    with pytest.raises(PaperOnlyBinanceError, match="PAPER-only policy"):
        request_public(method, url)


def test_credentials_never_sent_or_logged(monkeypatch, caplog):
    secret = "sentinel-secret-for-test"
    monkeypatch.setenv("BINANCE_API_KEY", secret)
    monkeypatch.setenv("BINANCE_API_SECRET", secret)
    calls = []

    class Response:
        status_code = 200

    def fake_get(url, **kwargs):
        calls.append(kwargs)
        return Response()

    mock_transport(monkeypatch, fake_get)
    get_public("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(PaperOnlyBinanceError) as error:
            request_public(
                "POST",
                "https://api.binance.com/api/v3/order",
                headers={"X-MBX-APIKEY": secret},
            )
        with pytest.raises(PaperOnlyBinanceError):
            request_public(
                "GET",
                "https://api.binance.com/api/v3/ticker/price",
                headers={"X-MBX-APIKEY": secret},
            )
        with pytest.raises(PaperOnlyBinanceError):
            get_public("https://api.binance.com/api/v3/klines?signature=forbidden")
    assert len(calls) == 1
    assert "headers" not in calls[0] and "auth" not in calls[0]
    assert secret not in str(error.value)
    assert secret not in caplog.text


def test_redirect_never_followed(monkeypatch):
    class Response:
        status_code = 302

    def fake_get(url, **kwargs):
        assert kwargs["allow_redirects"] is False
        return Response()

    mock_transport(monkeypatch, fake_get)
    with pytest.raises(PaperOnlyBinanceError):
        get_public("https://api.binance.com/api/v3/klines")


def test_arbitrary_session_cannot_be_supplied(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("transport created")

    monkeypatch.setattr(binance_http, "_new_session", forbidden)
    with pytest.raises(TypeError):
        get_public("https://api.binance.com/api/v3/exchangeInfo", session=object())
    with pytest.raises(PaperOnlyBinanceError):
        request_public("GET", "https://api.binance.com/api/v3/exchangeInfo", session=object())


def test_owned_session_ignores_netrc_and_environment_credentials(monkeypatch, tmp_path, caplog):
    secret = "test-only-credential-sentinel"
    netrc = tmp_path / ".netrc"
    netrc.write_text(f"machine api.binance.com login trader password {secret}\n")
    netrc.chmod(0o600)
    monkeypatch.setenv("NETRC", str(netrc))
    monkeypatch.setenv("HTTPS_PROXY", f"http://trader:{secret}@proxy.invalid:8080")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(tmp_path / "missing-ca.pem"))
    monkeypatch.setenv("BINANCE_API_KEY", secret)
    monkeypatch.setenv("BINANCE_API_SECRET", secret)
    captured = []

    class Adapter(BaseAdapter):
        def send(self, request, **kwargs):
            captured.append((request, kwargs))
            response = requests.Response()
            response.status_code = 200
            response._content = b"{}"
            response.url = request.url
            return response

        def close(self):
            pass

    original_new_session = binance_http._new_session

    def controlled_transport():
        session = original_new_session()
        assert session.trust_env is False
        assert session.auth is None
        session.mount("https://api.binance.com/", Adapter())
        return session

    monkeypatch.setattr(binance_http, "_new_session", controlled_transport)
    with caplog.at_level(logging.DEBUG):
        get_public("https://api.binance.com/api/v3/ticker/price", params={"symbol": "BTCUSDT"})
        with pytest.raises(PaperOnlyBinanceError):
            request_public("POST", "https://api.binance.com/api/v3/order", headers={"X-MBX-APIKEY": secret})
    assert len(captured) == 1
    request, kwargs = captured[0]
    assert "Authorization" not in request.headers
    assert "Proxy-Authorization" not in request.headers
    assert "X-MBX-APIKEY" not in request.headers
    assert kwargs["proxies"] == {}
    assert kwargs["verify"] is True
    assert secret not in str(request.headers)
    assert secret not in caplog.text
