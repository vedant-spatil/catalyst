from __future__ import annotations

import respx
from httpx import Response

from catalog_pipeline.spotify_client import SpotifyClient, SpotifyError

API = "https://api.test.local"
ACCOUNTS = "https://accounts.test.local"


def _client() -> SpotifyClient:
    return SpotifyClient("id", "secret", "refresh", api_base=API, accounts_base=ACCOUNTS)


def _token_ok():
    return respx.post(f"{ACCOUNTS}/api/token").mock(
        return_value=Response(200, json={"access_token": "tok"})
    )


@respx.mock
def test_auth1_refresh_keeps_token_in_memory():
    _token_ok()
    respx.get(f"{API}/artists/abc").mock(
        return_value=Response(200, json={"id": "abc", "name": "A", "popularity": 99, "followers": {"total": 1}})
    )
    client = _client()
    body = client.get_artist("abc")
    assert body["id"] == "abc"
    assert "popularity" not in body
    assert "followers" not in body
    assert client._access_token == "tok"
    client.close()


@respx.mock
def test_auth2_invalid_grant():
    respx.post(f"{ACCOUNTS}/api/token").mock(
        return_value=Response(400, json={"error": "invalid_grant"})
    )
    client = _client()
    try:
        client.refresh_access_token()
        assert False, "expected error"
    except SpotifyError as exc:
        assert exc.status == 400
        assert exc.path == "/api/token"
    client.close()


@respx.mock
def test_401_refresh_once():
    _token_ok()
    route = respx.get(f"{API}/artists/abc")
    route.side_effect = [
        Response(401, json={}),
        Response(200, json={"id": "abc", "name": "A"}),
    ]
    client = _client()
    body = client.get_artist("abc")
    assert body["id"] == "abc"
    client.close()


@respx.mock
def test_429_retry_after_once(monkeypatch):
    _token_ok()
    slept: list[int] = []
    monkeypatch.setattr("catalog_pipeline.spotify_client.time.sleep", lambda s: slept.append(int(s)))
    route = respx.get(f"{API}/artists/abc")
    route.side_effect = [
        Response(429, headers={"Retry-After": "2"}, json={}),
        Response(200, json={"id": "abc", "name": "A"}),
    ]
    client = _client()
    body = client.get_artist("abc")
    assert body["id"] == "abc"
    assert slept == [2]
    client.close()


@respx.mock
def test_search_caps_limit():
    _token_ok()
    route = respx.get(f"{API}/search").mock(return_value=Response(200, json={"artists": {"items": []}}))
    client = _client()
    client.search("query", limit=50)
    assert route.calls.last.request.url.params["limit"] == "10"
    client.close()
