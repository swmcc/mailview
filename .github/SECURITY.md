# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| latest  | :white_check_mark: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@swm.cc**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (if you have them)

You should receive a response within 48 hours. If the issue is confirmed, we'll work on a fix and coordinate disclosure with you.

## Security Considerations

Mailview is designed for **development use only** and includes safeguards:

- Refuses to activate in production environments by default
- Checks for `DEBUG` environment variables
- Requires explicit `MAILVIEW_ENABLED=true` to force-enable

**Never enable mailview in production.** It exposes all captured emails through a web interface with no authentication.
