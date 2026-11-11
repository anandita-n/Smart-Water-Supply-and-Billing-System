# DEF-005: Whitespace-only full name accepted at registration

| Field | Value |
|---|---|
| Module | Authentication (`POST /api/auth/register`) |
| Found by | TC-A101 (API test), run 7 |
| Severity | Low |
| Priority | Medium |
| Status | **Closed**: fixed and retested (run 8: TC-A101 and TC-A102 pass) |
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

## Fix applied
`app/main.py`: a `field_validator("full_name")` on `RegisterIn` strips the value and raises a validation error
(HTTP 422) when nothing is left. The stripped name is what gets stored.

## Retest
TC-A101 now returns 422. TC-A102 (profile update with a blank name) still passes.
