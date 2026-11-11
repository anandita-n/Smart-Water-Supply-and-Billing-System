# DEF-003: Login tokens never expire and cannot be revoked (no logout)

| Field | Value |
|---|---|
| Module | Authentication (`/api/auth/login`) |
| Found by | Review during test design; confirmed by TC-A56 (API test), run 3 |
| Severity | Medium |
| Priority | Medium |
| Status | **Open** |
| Reported by | Vivan Raj Belur |

## Description
Tokens are stored with no expiry time and there is no logout endpoint, so a token stays valid until the
database is deleted. Clicking **Logout** in the UI only reloaded the page; the token still worked. If a
token leaks (shared computer, logs), the account is exposed indefinitely.

## Steps to reproduce
1. Log in and copy the token.
2. Call `POST /api/auth/logout` with it.
3. Call `GET /api/me` with the same token.

## Expected result
Logout returns 200 and the token is rejected afterwards (HTTP 401). Tokens also expire after a fixed lifetime.

## Actual result
`POST /api/auth/logout` does not exist (404/405), so the token can never be revoked and never expires.

## Evidence
`06_Test_Reports/run3_new_tests.xml`: `test_TC_A56_logout_invalidates_token` failed.

## Root cause / proposed fix
The `tokens` table has no `expires_at` column and `current_user` never checks time. Add `expires_at`
(8 hours), reject expired tokens, and add `POST /api/auth/logout` that deletes the token.
