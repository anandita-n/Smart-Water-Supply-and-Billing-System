# Defect Summary

| ID | Title | Severity | Found by | Fixed in | Status | Owner for explanation |
|---|---|---|---|---|---|---|
| [DEF-001](DEF-001_future_dated_reading_accepted.md) | Future-dated meter reading accepted | Medium | TC-A29 (run 1) | `add_reading` date check | Closed | S Anandita Narayan |
| [DEF-004](DEF-004_username_case_sensitive_duplicates.md) | Usernames are case-sensitive, so look-alike accounts can be registered | Medium | TC-A55 (run 3) | usernames lower-cased in `register` and `login` | Closed | S Anandita Narayan |
| [DEF-002](DEF-002_calculator_inf_causes_500.md) | `units=inf` makes the calculator return HTTP 500 | Medium | TC-A54 (run 1) | `allow_inf_nan=False` on numeric inputs | Closed | Vivan Raj Belur |
| [DEF-003](DEF-003_auth_tokens_never_expire.md) | Login tokens never expire and cannot be revoked | Medium | TC-A56 (run 3) | `expires_at` + `POST /api/auth/logout` | Closed | Vivan Raj Belur |
| [DEF-005](DEF-005_blank_name_accepted_at_registration.md) | Whitespace-only full name accepted at registration | Low | TC-A101 (run 7) | strip and validate `full_name` | Closed | Vivan Raj Belur |
