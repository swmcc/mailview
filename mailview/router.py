"""API router for mailview UI.

Provides endpoints for listing, viewing, and managing captured emails.
"""

from __future__ import annotations

from pathlib import Path

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.routing import Route

from mailview.paths import normalize_mount_path
from mailview.store import EmailStore

# Path to UI assets
UI_DIR = Path(__file__).parent / "ui"

# Cache UI HTML at import time to avoid per-request disk I/O
_UI_HTML_CACHE: str | None = None


def _load_ui_html() -> str:
    """Load and cache the UI HTML."""
    global _UI_HTML_CACHE
    if _UI_HTML_CACHE is None:
        index_path = UI_DIR / "index.html"
        if index_path.exists():
            _UI_HTML_CACHE = index_path.read_text(encoding="utf-8")
        else:
            _UI_HTML_CACHE = ""
    return _UI_HTML_CACHE


class MailviewRouter:
    """Router for mailview API endpoints.

    Routes are prefixed with {mount_path}/api/emails.
    """

    def __init__(
        self,
        store: EmailStore | None = None,
        mount_path: str = "/_mail",
    ) -> None:
        """Initialize router with optional store.

        Args:
            store: EmailStore instance. Creates default if not provided.
            mount_path: URL path prefix for routes (default: /_mail)
        """
        self.store = store or EmailStore()
        self.mount_path = normalize_mount_path(mount_path)

    @property
    def routes(self) -> list[Route]:
        """Get list of Starlette routes."""
        p = f"{self.mount_path}/api/emails"
        return [
            # UI route
            Route(self.mount_path, self.index, methods=["GET"]),
            Route(f"{self.mount_path}/", self.index, methods=["GET"]),
            # API routes
            Route(p, self.list_emails, methods=["GET"]),
            Route(p, self.delete_all_emails, methods=["DELETE"]),
            Route(f"{p}/{{email_id}}", self.get_email, methods=["GET"]),
            Route(f"{p}/{{email_id}}", self.delete_email, methods=["DELETE"]),
            Route(f"{p}/{{email_id}}/html", self.get_email_html, methods=["GET"]),
            Route(
                f"{p}/{{email_id}}/attachments/{{filename:path}}",
                self.get_attachment,
                methods=["GET"],
            ),
        ]

    async def index(self, request: Request) -> HTMLResponse:
        """Serve the inbox UI."""
        html = _load_ui_html()
        if not html:
            return HTMLResponse("<h1>UI not found</h1>", status_code=404)
        return HTMLResponse(html)

    async def list_emails(self, request: Request) -> JSONResponse:
        """List all captured emails.

        Returns JSON array of email summaries (without bodies or attachments).
        """
        emails = await self.store.get_all()
        attachment_counts = await self.store.get_attachment_counts()
        summaries = []
        for email in emails:
            data = email.to_dict(include_bodies=False)
            # get_all() doesn't populate attachments; remove misleading empty list
            data.pop("attachments", None)
            # Add attachment count for UI display
            data["attachment_count"] = attachment_counts.get(email.id, 0)
            summaries.append(data)
        return JSONResponse({"emails": summaries})

    async def get_email(self, request: Request) -> JSONResponse:
        """Get a single email by ID.

        Returns full email including bodies.
        """
        email_id = request.path_params["email_id"]
        email = await self.store.get_by_id(email_id)

        if email is None:
            return JSONResponse({"error": "Email not found"}, status_code=404)

        return JSONResponse({"email": email.to_dict(include_bodies=True)})

    async def get_email_html(self, request: Request) -> Response:
        """Get HTML body for iframe rendering.

        Returns raw HTML with text/html content type.
        """
        email_id = request.path_params["email_id"]
        email = await self.store.get_by_id(email_id)

        if email is None:
            return JSONResponse({"error": "Email not found"}, status_code=404)

        if not email.html_body:
            return Response(
                content="<p>No HTML content</p>",
                media_type="text/html",
            )

        return Response(content=email.html_body, media_type="text/html")

    async def get_attachment(self, request: Request) -> Response:
        """Download an attachment.

        Returns attachment content with appropriate content type.
        """
        email_id = request.path_params["email_id"]
        filename = request.path_params["filename"]

        # Check email exists first for clearer error messages
        email = await self.store.get_by_id(email_id)
        if email is None:
            return JSONResponse({"error": "Email not found"}, status_code=404)

        attachment = await self.store.get_attachment(email_id, filename)
        if attachment is None:
            return JSONResponse({"error": "Attachment not found"}, status_code=404)

        # Sanitize filename for Content-Disposition header
        safe_filename = (
            attachment.filename.replace("\r", "").replace("\n", "").replace('"', '\\"')
        )
        return Response(
            content=attachment.content,
            media_type=attachment.content_type,
            headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
        )

    async def delete_email(self, request: Request) -> JSONResponse:
        """Delete a single email."""
        email_id = request.path_params["email_id"]
        deleted = await self.store.delete(email_id)

        if not deleted:
            return JSONResponse({"error": "Email not found"}, status_code=404)

        return JSONResponse({"deleted": True})

    async def delete_all_emails(self, request: Request) -> JSONResponse:
        """Delete all captured emails."""
        count = await self.store.delete_all()
        return JSONResponse({"deleted": count})


def create_routes(
    store: EmailStore | None = None,
    mount_path: str = "/_mail",
) -> list[Route]:
    """Create mailview API routes.

    Convenience function for getting routes without instantiating router.

    Args:
        store: Optional EmailStore instance
        mount_path: URL path prefix for routes (default: /_mail)

    Returns:
        List of Starlette Route objects
    """
    router = MailviewRouter(store=store, mount_path=mount_path)
    return router.routes
