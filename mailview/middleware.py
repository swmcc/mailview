"""ASGI middleware for mailview.

Mounts the mailview API at a configurable path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from starlette.routing import Router

from mailview.env import is_mailview_enabled
from mailview.paths import normalize_mount_path
from mailview.router import MailviewRouter
from mailview.store import EmailStore

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Receive, Scope, Send


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
        self.mount_path = normalize_mount_path(mount_path)
        self.enabled = enabled if enabled is not None else is_mailview_enabled()

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

    @property
    def mailview_store(self) -> EmailStore | None:
        """Get the EmailStore instance for email capture integration."""
        return self.store if self.enabled else None
