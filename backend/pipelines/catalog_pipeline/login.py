"""One-time Authorization Code login. Prints the refresh token once."""

from __future__ import annotations

import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from catalog_pipeline.config import ROOT, load_config
from catalog_pipeline.spotify_client import SpotifyClient

SCOPES = "playlist-read-private playlist-read-collaborative"


def run_login() -> None:
    cfg = load_config(require_database=False, require_spotify_app=True)
    parsed = urllib.parse.urlparse(cfg.spotify_redirect_uri)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8888
    path = parsed.path or "/callback"
    result: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            incoming = urllib.parse.urlparse(self.path)
            if incoming.path != path:
                self.send_response(404)
                self.end_headers()
                return
            qs = urllib.parse.parse_qs(incoming.query)
            if "error" in qs:
                result["error"] = qs["error"][0]
            if "code" in qs:
                result["code"] = qs["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"You can close this tab and return to the terminal.")

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = HTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    params = {
        "client_id": cfg.spotify_client_id,
        "response_type": "code",
        "redirect_uri": cfg.spotify_redirect_uri,
        "scope": SCOPES,
    }
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    print("Open this URL if the browser does not start:")
    print(url)
    webbrowser.open(url)
    print("Waiting for callback...")
    while "code" not in result and "error" not in result:
        threading.Event().wait(0.2)
    server.shutdown()
    if "error" in result:
        raise SystemExit(f"Spotify login error: {result['error']}")
    client = SpotifyClient(cfg.spotify_client_id, cfg.spotify_client_secret)
    try:
        tokens = client.exchange_code(result["code"], cfg.spotify_redirect_uri)
    finally:
        client.close()
    refresh = tokens.get("refresh_token")
    if not refresh:
        raise SystemExit("No refresh_token in token response. Re-authorize the app.")
    env_path = ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    written = False
    new_lines = []
    for line in lines:
        if line.startswith("SPOTIFY_REFRESH_TOKEN="):
            new_lines.append(f"SPOTIFY_REFRESH_TOKEN={refresh}")
            written = True
        else:
            new_lines.append(line)
    if not written:
        new_lines.append(f"SPOTIFY_REFRESH_TOKEN={refresh}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("SPOTIFY_REFRESH_TOKEN written to .env")
