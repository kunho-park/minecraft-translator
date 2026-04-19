"""Desktop OAuth login via browser redirect with local callback server."""

from __future__ import annotations

import logging
import socket
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from .config import AppConfig

logger = logging.getLogger(__name__)

WEB_BASE_URL = "https://mcat.2odk.com"


class AuthResult:
    """Result of an OAuth login attempt."""

    def __init__(
        self,
        token: str,
        user_name: str,
        discord_id: str,
    ) -> None:
        self.token = token
        self.user_name = user_name
        self.discord_id = discord_id


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback token."""

    auth_result: AuthResult | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        token = params.get("token", [None])[0]
        name = params.get("name", ["Unknown"])[0]
        discord_id = params.get("discord_id", [""])[0]

        if token:
            _CallbackHandler.auth_result = AuthResult(
                token=token,
                user_name=name,
                discord_id=discord_id,
            )
            self._send_success_page()
        else:
            self._send_error_page()

    def _send_success_page(self) -> None:
        html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>로그인 완료</title></head>
<body style="background:#0a0a0a;color:#fff;font-family:system-ui;display:flex;
align-items:center;justify-content:center;min-height:100vh;margin:0">
<div style="text-align:center">
<h1 style="color:#4ade80">로그인 완료!</h1>
<p style="color:#aaa">앱으로 돌아가주세요. 이 창은 닫아도 됩니다.</p>
</div></body></html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_error_page(self) -> None:
        html = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>로그인 실패</title></head>
<body style="background:#0a0a0a;color:#fff;font-family:system-ui;display:flex;
align-items:center;justify-content:center;min-height:100vh;margin:0">
<div style="text-align:center">
<h1 style="color:#f87171">로그인 실패</h1>
<p style="color:#aaa">토큰을 수신하지 못했습니다. 다시 시도해주세요.</p>
</div></body></html>"""
        self.send_response(400)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format: str, *args: object) -> None:
        logger.debug("Auth callback server: %s", format % args)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class DesktopAuth(QObject):
    """Manages desktop OAuth login flow.

    Starts a local HTTP server, opens the browser for Discord login,
    and waits for the callback with the API token.
    """

    loginComplete = Signal(str, str, str)  # token, user_name, discord_id
    loginFailed = Signal(str)  # error message

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self._server: HTTPServer | None = None
        self._thread: Thread | None = None

    @property
    def is_logged_in(self) -> bool:
        return bool(self.config.get("auth.token"))

    @property
    def user_name(self) -> str:
        return self.config.get("auth.user_name", "")

    def start_login(self) -> None:
        """Open browser for Discord OAuth and start local callback server."""
        _CallbackHandler.auth_result = None
        port = _find_free_port()

        self._server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
        self._server.timeout = 300  # 5 min timeout

        login_url = f"{WEB_BASE_URL}/auth/desktop-login?port={port}"
        logger.info("Opening browser for login: %s", login_url)
        webbrowser.open(login_url)

        self._thread = Thread(target=self._wait_for_callback, daemon=True)
        self._thread.start()

    def _wait_for_callback(self) -> None:
        """Block until the callback is received or timeout."""
        server = self._server
        if not server:
            return

        try:
            server.handle_request()

            result = _CallbackHandler.auth_result
            if result:
                self.config.set("auth.token", result.token)
                self.config.set("auth.user_name", result.user_name)
                self.config.set("auth.discord_id", result.discord_id)
                self.config.save()
                logger.info("Login successful: %s", result.user_name)
                self.loginComplete.emit(
                    result.token, result.user_name, result.discord_id
                )
            else:
                self.loginFailed.emit("콜백에서 토큰을 수신하지 못했습니다.")
        except Exception as e:
            logger.exception("Login callback error: %s", e)
            self.loginFailed.emit(str(e))
        finally:
            try:
                server.server_close()
            except Exception:
                pass
            self._server = None

    def logout(self) -> None:
        """Clear stored auth credentials."""
        self.config.set("auth.token", "")
        self.config.set("auth.user_name", "")
        self.config.set("auth.discord_id", "")
        self.config.save()
        logger.info("Logged out")
