"""Spotify Web API client. No client-credentials grant."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx

log = logging.getLogger("catalog_pipeline")

API_BASE = "https://api.spotify.com/v1"
ACCOUNTS_BASE = "https://accounts.spotify.com"
DROP_FIELDS = {"popularity", "followers"}


class SpotifyError(RuntimeError):
    def __init__(self, status: int, path: str, body: str = "") -> None:
        self.status = status
        self.path = path
        super().__init__(f"{status} {path}")
        self.body = body


def _path_of(url: str) -> str:
    return urlparse(url).path


def strip_restricted(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: strip_restricted(v) for k, v in obj.items() if k not in DROP_FIELDS}
    if isinstance(obj, list):
        return [strip_restricted(item) for item in obj]
    return obj


class SpotifyClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str | None = None,
        *,
        api_base: str = API_BASE,
        accounts_base: str = ACCOUNTS_BASE,
        timeout: float = 30.0,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.api_base = api_base.rstrip("/")
        self.accounts_base = accounts_base.rstrip("/")
        self.timeout = timeout
        self._access_token: str | None = None
        self._http = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()

    def ensure_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        return self.refresh_access_token()

    def refresh_access_token(self) -> str:
        if not self.refresh_token:
            raise SpotifyError(0, "/api/token", "missing refresh token")
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = self._http.post(f"{self.accounts_base}/api/token", data=data)
        log.info("%s %s", response.status_code, "/api/token")
        if response.status_code != 200:
            raise SpotifyError(response.status_code, "/api/token", response.text)
        token = response.json().get("access_token")
        if not token:
            raise SpotifyError(response.status_code, "/api/token", "no access_token")
        self._access_token = token
        return token

    def exchange_code(self, code: str, redirect_uri: str) -> dict[str, Any]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = self._http.post(f"{self.accounts_base}/api/token", data=data)
        log.info("%s %s", response.status_code, "/api/token")
        if response.status_code != 200:
            raise SpotifyError(response.status_code, "/api/token", response.text)
        return response.json()

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None) -> Any:
        url = path if path.startswith("http") else f"{self.api_base}{path}"
        last_error: Exception | None = None
        refreshed = False
        retried_429 = False
        for attempt in range(3):
            headers = {"Authorization": f"Bearer {self.ensure_access_token()}"}
            try:
                response = self._http.request(method, url, params=params, headers=headers)
            except httpx.TimeoutException as exc:
                last_error = exc
                time.sleep(0.5 * (attempt + 1))
                continue
            path_log = _path_of(str(response.url))
            log.info("%s %s", response.status_code, path_log)
            if response.status_code == 401 and not refreshed:
                self._access_token = None
                self.refresh_access_token()
                refreshed = True
                continue
            if response.status_code == 401:
                raise SpotifyError(401, path_log, response.text)
            if response.status_code == 429:
                if retried_429:
                    raise SpotifyError(429, path_log, response.text)
                wait = int(response.headers.get("Retry-After", "1"))
                time.sleep(wait)
                retried_429 = True
                continue
            if response.status_code >= 400:
                raise SpotifyError(response.status_code, path_log, response.text)
            payload = response.json() if response.content else None
            return strip_restricted(payload)
        raise last_error or SpotifyError(0, url, "exhausted retries")

    def paginate(self, path: str, *, params: dict[str, Any] | None = None, items_key: str = "items") -> list[Any]:
        collected: list[Any] = []
        query = dict(params or {})
        next_path: str | None = path
        first = True
        while next_path:
            body = self.request("GET", next_path, params=query if first else None)
            first = False
            collected.extend(body.get(items_key) or [])
            next_path = body.get("next")
            query = {}
        return collected

    def get_artist(self, artist_id: str) -> dict[str, Any]:
        return self.request("GET", f"/artists/{artist_id}")

    def get_artist_albums(self, artist_id: str) -> list[dict[str, Any]]:
        return self.paginate(f"/artists/{artist_id}/albums", params={"limit": 50, "include_groups": "album,single"})

    def get_album(self, album_id: str) -> dict[str, Any]:
        return self.request("GET", f"/albums/{album_id}")

    def get_album_tracks(self, album_id: str) -> list[dict[str, Any]]:
        return self.paginate(f"/albums/{album_id}/tracks", params={"limit": 50})

    def get_track(self, track_id: str) -> dict[str, Any]:
        return self.request("GET", f"/tracks/{track_id}")

    def get_me_playlists(self) -> list[dict[str, Any]]:
        return self.paginate("/me/playlists", params={"limit": 50})

    def get_playlist(self, playlist_id: str) -> dict[str, Any]:
        return self.request("GET", f"/playlists/{playlist_id}", params={"fields": "id,name,collaborative"})

    def get_playlist_items(self, playlist_id: str) -> list[dict[str, Any]]:
        return self.paginate(f"/playlists/{playlist_id}/items", params={"limit": 50})

    def search(self, query: str, *, types: str = "artist", limit: int = 10) -> dict[str, Any]:
        capped = min(max(limit, 1), 10)
        return self.request("GET", "/search", params={"q": query, "type": types, "limit": capped})
