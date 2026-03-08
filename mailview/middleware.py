"""ASGI middleware for mailview.

Mounts the mailview API at a configurable path.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from starlette.routing import Router

from mailview.router import MailviewRouter
from mailview.store import EmailStore

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


def is_dev_environment() -> bool:
    """Check if running in a development environment.

    Checks common environment indicators:
    - DEBUG env var is set and truthy
    - ENVIRONMENT/ENV is "development" or "dev"
    - FASTAPI_ENV is "development"
    - FLASK_ENV is "development"

    Returns:
        True if development environment detected
    """
    # Check DEBUG flag
    debug = os.environ.get("DEBUG", "").lower()
    if debug in ("1", "true", "yes"):
        return True

    # Check various ENV variables
    for var in ("ENVIRONMENT", "ENV", "FASTAPI_ENV", "FLASK_ENV"):
        env = os.environ.get(var, "").lower()
        if env in ("development", "dev"):
            return True

    return False


class MailviewMiddleware:
    """ASGI middleware that mounts mailview API.

    Example:
        from fastapi import FastAPI
        from mailview import MailviewMiddleware

        app = FastAPI()
        app.add_middleware(MailviewMiddleware)
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        mount_path: str = "/_mail",
        db_path: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        """Initialize middleware.

        Args:
            app: The ASGI application to wrap
            mount_path: URL path to mount mailview (default: /_mail)
            db_path: Custom database path (default: /tmp/mailview/mailview.db)
            enabled: Force enable/disable. If None, auto-detect dev environment.
        """
        self.app = app
        self.mount_path = self._normalize_mount_path(mount_path)
        self.enabled = enabled if enabled is not None else is_dev_environment()

        if self.enabled:
            # Create store and router
            self.store = EmailStore(db_path=db_path) if db_path else EmailStore()
            self.router = MailviewRouter(store=self.store, mount_path=self.mount_path)

            # Create mounted router for API
            api_routes = self.router.routes
            self._mailview_app: ASGIApp = Router(routes=api_routes)
        else:
            self._mailview_app = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Handle ASGI request."""
        if not self.enabled:
            await self.app(scope, receive, send)
            return

        if scope["type"] == "http":
            path = scope.get("path", "")

            # Check if request is for mailview (boundary-aware)
            if path == self.mount_path or path.startswith(self.mount_path + "/"):
                # Route to mailview app
                await self._mailview_app(scope, receive, send)
                return

        # Pass through to wrapped app
        await self.app(scope, receive, send)

    @staticmethod
    def _normalize_mount_path(mount_path: str) -> str:
        """Normalize and validate mount_path."""
        path = mount_path.strip().rstrip("/")
        if not path or path == "/":
            raise ValueError("mount_path must be a non-empty, non-root path")
        if not path.startswith("/"):
            path = "/" + path
        return path

    @property
    def mailview_store(self) -> EmailStore | None:
        """Get the EmailStore instance for email capture integration."""
        return self.store if self.enabled else None
