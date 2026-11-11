# DEF-004: Usernames are case-sensitive, so look-alike accounts can be registered

| Field | Value |
|---|---|
| Module | Authentication (`POST /api/auth/register`, `POST /api/auth/login`) |
| Found by | TC-A55 (API test), run 3 |
| Severity | Medium |
| Priority | Medium |
| Status | **Open** |
| Reported by | S Anandita Narayan |

## Description
`alice` and `Alice` are treated as two different usernames. A person can register an account that looks
the same as an existing customer's (or as `Admin`), which makes impersonation and support mix-ups easy.

## Steps to reproduce
1. Register `alice` with password `secret1`. The result is 201.
2. Register `Alice` with any password.

## Expected result
HTTP 409 "Username already exists", because usernames should be unique ignoring case.

## Actual result
HTTP 201 Created; two accounts now exist.

## Evidence
`06_Test_Reports/run3_new_tests.xml`: `test_TC_A55_username_is_case_insensitive` failed with `assert 201 == 409`.

## Root cause / proposed fix
Usernames are stored and compared exactly as typed. Normalise them to lower case on registration and login.
