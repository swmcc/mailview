"""Test app to verify mailview works end-to-end with FastAPI."""

from email.message import EmailMessage

from fastapi import FastAPI

from mailview import MailviewBackend, MailviewMiddleware

# Create app
app = FastAPI()

# Create backend - it will use the same default db_path as middleware
backend = MailviewBackend()


@app.get("/")
async def home():
    """Home page."""
    return {"message": "Visit /_mail to see the inbox UI, /send to send a test email"}


@app.get("/send")
async def send_test_email():
    """Send a test email through the backend (simulates app sending email)."""
    # Create a standard Python email message
    msg = EmailMessage()
    msg["From"] = "app@example.com"
    msg["To"] = "user@example.com"
    msg["Subject"] = "Test from FastAPI app"
    msg.set_content("This is a plain text email sent through MailviewBackend.")

    # Send through mailview backend (captures instead of sending)
    email = await backend.send(msg)

    return {"captured": email.id, "subject": email.subject}


@app.get("/send-html")
async def send_html_email():
    """Send an HTML email with attachment."""
    msg = EmailMessage()
    msg["From"] = "notifications@myapp.com"
    msg["To"] = "customer@example.com"
    msg["Cc"] = "support@myapp.com"
    msg["Subject"] = "Your order has shipped!"

    # Set HTML content
    msg.add_alternative(
        """
        <html>
        <body>
            <h1>Order Shipped!</h1>
            <p>Your order <strong>#12345</strong> is on its way.</p>
            <p>Expected delivery: March 15, 2026</p>
        </body>
        </html>
        """,
        subtype="html",
    )

    # Add an attachment
    msg.add_attachment(
        b"Order #12345\nItem: Widget\nQty: 2\nTotal: $49.99",
        maintype="text",
        subtype="plain",
        filename="invoice.txt",
    )

    email = await backend.send(msg)
    return {"captured": email.id, "subject": email.subject, "has_attachment": True}


# Wrap with middleware - uses same default db_path as backend
app = MailviewMiddleware(app, enabled=True)
