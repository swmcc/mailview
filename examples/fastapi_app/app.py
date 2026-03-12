"""Example FastAPI app demonstrating mailview.

Run with: uvicorn app:app --reload
Visit: http://localhost:8000/send to send a test email
       http://localhost:8000/_mail to view captured emails
"""

from email.message import EmailMessage

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from mailview import EmailStore, MailviewBackend, MailviewMiddleware

# Shared database path ensures middleware and backend use the same data
DB_PATH = "/tmp/mailview/example.db"

# Create FastAPI app
app = FastAPI(title="Mailview Example")

# Add mailview middleware (serves UI at /_mail)
app.add_middleware(MailviewMiddleware, enabled=True, db_path=DB_PATH)

# Create backend for capturing emails (uses same db_path as middleware)
store = EmailStore(db_path=DB_PATH)
backend = MailviewBackend(store=store)


@app.get("/")
async def home():
    """Home page with links."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mailview Example</title>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            a { color: #0066cc; }
            code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>Mailview Example</h1>
        <p>This is a demo FastAPI app showing mailview in action.</p>
        <ul>
            <li><a href="/send">Send a test email</a></li>
            <li><a href="/send-html">Send an HTML email</a></li>
            <li><a href="/send-multipart">Send a multipart email</a></li>
            <li><a href="/_mail">View captured emails</a></li>
        </ul>
    </body>
    </html>
    """)


@app.get("/send")
async def send_email():
    """Send a simple plaintext test email."""
    msg = EmailMessage()
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = "Hello from Mailview!"
    msg.set_content("This is a test email captured by mailview.")

    email = await backend.send(msg)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Email Sent</title></head>
    <body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1>Email Sent!</h1>
        <p>Email ID: <code>{email.id}</code></p>
        <p><a href="/_mail">View in Mailview</a> | <a href="/">Back home</a></p>
    </body>
    </html>
    """)


@app.get("/send-html")
async def send_html_email():
    """Send an HTML email."""
    msg = EmailMessage()
    msg["From"] = "newsletter@example.com"
    msg["To"] = "subscriber@example.com"
    msg["Subject"] = "Your Weekly Newsletter"
    msg.add_alternative("""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px;">
            <h1 style="color: #333;">Weekly Newsletter</h1>
            <p>Hello there!</p>
            <p>Here's what's new this week:</p>
            <ul>
                <li>Feature updates</li>
                <li>Bug fixes</li>
                <li>Performance improvements</li>
            </ul>
            <a href="#" style="display: inline-block; background: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Read More</a>
        </div>
    </body>
    </html>
    """, subtype="html")

    email = await backend.send(msg)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>HTML Email Sent</title></head>
    <body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1>HTML Email Sent!</h1>
        <p>Email ID: <code>{email.id}</code></p>
        <p><a href="/_mail">View in Mailview</a> | <a href="/">Back home</a></p>
    </body>
    </html>
    """)


@app.get("/send-multipart")
async def send_multipart_email():
    """Send a multipart email with both HTML and plaintext."""
    msg = EmailMessage()
    msg["From"] = "support@example.com"
    msg["To"] = "customer@example.com"
    msg["Cc"] = "manager@example.com"
    msg["Subject"] = "Your Support Ticket #12345"

    # Add plaintext version
    msg.set_content("""
Support Ticket #12345

Hi there,

Your support ticket has been received. We'll get back to you within 24 hours.

Ticket Details:
- ID: #12345
- Status: Open
- Priority: Normal

Thanks,
Support Team
    """)

    # Add HTML version
    msg.add_alternative("""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Support Ticket #12345</h2>
        <p>Hi there,</p>
        <p>Your support ticket has been received. We'll get back to you within 24 hours.</p>
        <table style="border-collapse: collapse; margin: 20px 0;">
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>ID</strong></td><td style="padding: 8px; border: 1px solid #ddd;">#12345</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Status</strong></td><td style="padding: 8px; border: 1px solid #ddd;">Open</td></tr>
            <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Priority</strong></td><td style="padding: 8px; border: 1px solid #ddd;">Normal</td></tr>
        </table>
        <p>Thanks,<br>Support Team</p>
    </body>
    </html>
    """, subtype="html")

    email = await backend.send(msg)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Multipart Email Sent</title></head>
    <body style="font-family: system-ui, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1>Multipart Email Sent!</h1>
        <p>Email ID: <code>{email.id}</code></p>
        <p>This email has both HTML and plaintext versions.</p>
        <p><a href="/_mail">View in Mailview</a> | <a href="/">Back home</a></p>
    </body>
    </html>
    """)
