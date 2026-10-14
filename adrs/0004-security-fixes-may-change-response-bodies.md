# 0004 - Preserve endpoint contracts, allowing only security-driven changes

- Date: 2026-10-14
- Spec: 0001-repository-setup-and-conventions
- Status: accepted

## Context
The refactored apps must keep every original endpoint responding, but the projects expose passwords and secret keys in responses, store passwords in plain text or weak hashes, and ship endpoints that run arbitrary SQL or wipe the database. Ports 5000 (macOS AirPlay Receiver) and 3000 (another local server) are already in use on this machine, so the original hardcoded ports cannot be used for validation.

## Options considered
- A: Keep routes, methods and status codes; change response bodies only to remove sensitive data; hash passwords for real while keeping seed logins working; keep dangerous admin routes behind an admin token from the environment — fixes the CRITICAL findings without breaking clients.
- B: Remove dangerous routes — safest, but original endpoints stop existing (404).
- C: Identical contracts, no security change in bodies — leaves CRITICAL findings in place.

## Decision
"Manter e proteger" (Keep and protect) for admin routes and "Sim, só por segurança" (Yes, only for security) for response bodies — option A. The HTTP port becomes configurable through the `PORT` environment variable, keeping the original value as default.

## Consequences
The MVC guidelines and the playbook encode these preservation rules. Validation compares the status code of every original endpoint before and after the refactor on a free port; admin routes called without the token are the only allowed status-code difference (401/403), and they keep working when the token is sent.
