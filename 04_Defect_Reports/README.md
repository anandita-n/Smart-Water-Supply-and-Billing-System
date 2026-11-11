# Defect Summary

| ID | Title | Severity | Found by | Fixed in | Status | Owner for explanation |
|---|---|---|---|---|---|---|
| [DEF-001](DEF-001_future_dated_reading_accepted.md) | Future-dated meter reading accepted | Medium | TC-A29 (run 1) | `add_reading` date check | Closed | S Anandita Narayan |
| [DEF-004](DEF-004_username_case_sensitive_duplicates.md) | Usernames are case-sensitive, so look-alike accounts can be registered | Medium | TC-A55 (run 3) | usernames lower-cased in `register` and `login` | Closed | S Anandita Narayan |
| [DEF-002](DEF-002_calculator_inf_causes_500.md) | `units=inf` makes the calculator return HTTP 500 | Medium | TC-A54 (run 1) | `allow_inf_nan=False` on numeric inputs | Closed | Vivan Raj Belur |
| [DEF-003](DEF-003_auth_tokens_never_expire.md) | Login tokens never expire and cannot be revoked | Medium | TC-A56 (run 3) | `expires_at` + `POST /api/auth/logout` | Closed | Vivan Raj Belur |

## One-line explanations for the viva
- **DEF-001:** the system never compared a reading date with today, so a reading dated 2999 pushed the bill's due date into the future and the bill could never be late. Fix: reject dates after today (HTTP 400).
- **DEF-004:** `Alice` and `alice` were two accounts, which allows look-alike impersonation. Fix: store and compare usernames in lower case.
- **DEF-002:** `inf` is a valid float, so the charge became infinity and JSON could not encode it, which gave an HTTP 500. Fix: reject infinity and NaN at validation, giving HTTP 422.
- **DEF-003:** tokens had no lifetime and there was no logout, so a leaked token worked forever. Fix: 8-hour expiry stored in the database, an expiry check on every request and a logout endpoint that deletes the token.
