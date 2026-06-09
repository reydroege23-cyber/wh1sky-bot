"""Local single-instance guard for polling Telegram bots."""

from __future__ import annotations

import hashlib
import socket


class SingleInstanceLock:
    """Hold a localhost socket open so duplicate local bot instances fail fast."""

    def __init__(self, token: str, host: str = "127.0.0.1") -> None:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        self.port = 20000 + (int(digest[:8], 16) % 30000)
        self.host = host
        self._socket: socket.socket | None = None

    def acquire(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            sock.bind((self.host, self.port))
            sock.listen(1)
        except OSError as exc:
            sock.close()
            raise RuntimeError(
                f"Another local bot instance appears to be running for this token "
                f"(lock {self.host}:{self.port}). Stop the duplicate process first."
            ) from exc
        self._socket = sock

    def release(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
