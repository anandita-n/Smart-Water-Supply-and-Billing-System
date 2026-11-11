# DEF-005: Whitespace-only full name accepted at registration

| Field | Value |
|---|---|
| Module | Authentication (`POST /api/auth/register`) |
| Found by | TC-A101 (API test), run 7 |
| Severity | Low |
| Priority | Medium |
| Status | **Open** |
| Reported by | Vivan Raj Belur |

## Description
The registration form rejects an empty full name, but a name made only of spaces passes validation. The
account is created with a blank display name, so the admin's customer list, bills and receipts show an empty
name for that customer.

## Steps to reproduce
1. `POST /api/auth/register` with `{"username": "blanky", "password": "secret1", "full_name": "    "}`.

## Expected result
HTTP 422: a full name must contain at least one visible character.

## Actual result
HTTP 201 Created; the customer is stored with a blank name.

## Evidence
`06_Test_Reports/run7_new_modules.xml`: `test_TC_A101_whitespace_only_name_rejected_at_registration` failed with
`assert 201 == 422`. The new profile endpoint (TC-A102) already rejects blank names, so only registration was affected.

## Root cause / proposed fix
`RegisterIn.full_name` only has `min_length=1`, which counts spaces. Strip the value and reject it if it is
empty after stripping, and store the stripped name.
