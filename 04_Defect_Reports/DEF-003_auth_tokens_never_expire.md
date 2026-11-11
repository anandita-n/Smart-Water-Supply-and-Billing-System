# DEF-003: Login tokens never expire and cannot be revoked

| Field | Value |
|---|---|
| Module | Authentication (`/api/auth/login`) |
| Found by | Exploratory review during test design (no automated test) |
| Severity | Low for this academic prototype (High in a real deployment) |
| Priority | Low |
| Status | **Open: deferred / known limitation** |
| Reported by | Vivan Raj Belur |

## Description
Tokens are stored in the `tokens` table with no expiry time, and there is no logout endpoint, so a token
stays valid until the database is deleted. Logging out in the UI only reloads the page.

## Steps to reproduce
1. Log in and copy the token.
2. Click **Logout**.
3. Call `GET /api/me` with the old token.

## Expected result
HTTP 401 after logout or after a fixed lifetime.

## Actual result
HTTP 200; the token still works.

## Decision
Deferred. It is listed in the Test Summary as a known risk and recommended for the next release
(`expires_at` column plus `POST /api/auth/logout`).
