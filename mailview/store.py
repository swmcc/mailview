"""SQLite storage layer for captured emails."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import aiosqlite

if TYPE_CHECKING:
    from mailview.models import Attachment, Email


DEFAULT_DB_PATH = "/tmp/mailview/mailview.db"  # nosec B108 - intentional for dev tool


class EmailStore:
    """Async SQLite store for captured emails."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        """Initialize store with database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Create database and tables if they don't exist."""
        if self._initialized:
            return

        # Create directory if needed
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS emails (
                    id TEXT PRIMARY KEY,
                    sender TEXT,
                    recipients_to TEXT,
                    recipients_cc TEXT,
                    recipients_bcc TEXT,
                    subject TEXT,
                    html_body TEXT,
                    text_body TEXT,
                    headers TEXT,
                    created_at TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_id TEXT,
                    filename TEXT,
                    content_type TEXT,
                    size INTEGER,
                    content BLOB,
                    FOREIGN KEY (email_id) REFERENCES emails(id) ON DELETE CASCADE
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_attachments_email_id
                ON attachments(email_id)
            """)
            await db.commit()

        self._initialized = True

    async def save(self, email: Email) -> None:
        """Save an email to the store.

        Args:
            email: Email to save
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO emails
                (id, sender, recipients_to, recipients_cc, recipients_bcc,
                 subject, html_body, text_body, headers, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    email.id,
                    email.sender,
                    json.dumps(email.to),
                    json.dumps(email.cc),
                    json.dumps(email.bcc),
                    email.subject,
                    email.html_body,
                    email.text_body,
                    json.dumps(email.headers),
                    email.created_at.isoformat(),
                ),
            )

            # Delete existing attachments and re-insert
            await db.execute("DELETE FROM attachments WHERE email_id = ?", (email.id,))
            for attachment in email.attachments:
                await db.execute(
                    """
                    INSERT INTO attachments
                    (email_id, filename, content_type, size, content)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        email.id,
                        attachment.filename,
                        attachment.content_type,
                        attachment.size,
                        attachment.content,
                    ),
                )

            await db.commit()

    async def get_all(self) -> list[Email]:
        """Get all emails, ordered by created_at descending.

        Returns:
            List of emails (without attachment content)
        """

        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM emails ORDER BY created_at DESC
                """
            ) as cursor:
                rows = await cursor.fetchall()

        return [self._row_to_email(row) for row in rows]

    async def get_by_id(self, email_id: str) -> Email | None:
        """Get a single email by ID.

        Args:
            email_id: Email ID to fetch

        Returns:
            Email if found, None otherwise
        """
        from mailview.models import Attachment

        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(
                "SELECT * FROM emails WHERE id = ?", (email_id,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                return None

            email = self._row_to_email(row)

            # Load attachments with content
            async with db.execute(
                "SELECT * FROM attachments WHERE email_id = ?", (email_id,)
            ) as cursor:
                attachment_rows = await cursor.fetchall()

            email.attachments = [
                Attachment(
                    filename=a["filename"],
                    content_type=a["content_type"],
                    size=a["size"],
                    content=a["content"],
                )
                for a in attachment_rows
            ]

        return email

    async def get_attachment(self, email_id: str, filename: str) -> Attachment | None:
        """Get a specific attachment.

        Args:
            email_id: Email ID
            filename: Attachment filename

        Returns:
            Attachment if found, None otherwise
        """
        from mailview.models import Attachment

        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM attachments
                WHERE email_id = ? AND filename = ?
                """,
                (email_id, filename),
            ) as cursor:
                row = await cursor.fetchone()

        if row is None:
            return None

        return Attachment(
            filename=row["filename"],
            content_type=row["content_type"],
            size=row["size"],
            content=row["content"],
        )

    async def delete(self, email_id: str) -> bool:
        """Delete a single email.

        Args:
            email_id: Email ID to delete

        Returns:
            True if deleted, False if not found
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            cursor = await db.execute("DELETE FROM emails WHERE id = ?", (email_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def delete_all(self) -> int:
        """Delete all emails.

        Returns:
            Number of emails deleted
        """
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM emails")
            await db.execute("DELETE FROM attachments")
            await db.commit()
            return cursor.rowcount

    async def count(self) -> int:
        """Get total email count.

        Returns:
            Number of stored emails
        """
        await self._ensure_initialized()

        async with (
            aiosqlite.connect(self.db_path) as db,
            db.execute("SELECT COUNT(*) FROM emails") as cursor,
        ):
            row = await cursor.fetchone()
            return row[0] if row else 0

    def _row_to_email(self, row: aiosqlite.Row) -> Email:
        """Convert database row to Email object."""
        from mailview.models import Email

        # Use from_dict to ensure created_at is parsed to datetime
        return Email.from_dict(
            {
                "id": row["id"],
                "sender": row["sender"] or "",
                "to": json.loads(row["recipients_to"] or "[]"),
                "cc": json.loads(row["recipients_cc"] or "[]"),
                "bcc": json.loads(row["recipients_bcc"] or "[]"),
                "subject": row["subject"] or "",
                "html_body": row["html_body"],
                "text_body": row["text_body"],
                "headers": json.loads(row["headers"] or "{}"),
                "created_at": row["created_at"],
            }
        )
