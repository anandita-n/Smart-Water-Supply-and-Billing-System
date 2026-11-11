# DEF-001: Future-dated meter reading is accepted

| Field | Value |
|---|---|
| Module | Meter Readings (`POST /api/readings`) |
| Found by | TC-A29 (API test), run 1 |
| Severity | Medium |
| Priority | High |
| Status | **Closed**: fixed and retested (run 2: TC-A29 passes) |
| Reported by | S Anandita Narayan |

## Description
An admin can record a meter reading dated years in the future. The next bill then gets a due date
in the future, so the bill can never become overdue and no late fee is ever charged.

## Steps to reproduce
1. Log in as `admin`, create a customer and a connection.
2. `POST /api/readings` with `{"connection_id": 1, "reading": 100, "read_on": "2999-01-01"}`.

## Expected result
HTTP 400 with a message that the reading date cannot be in the future.

## Actual result
HTTP 201 Created; the reading is stored with the date 2999-01-01.

## Evidence
`06_Test_Reports/run1_baseline.xml`: `test_TC_A29_future_dated_reading_rejected` failed with `assert 201 == 400`.

## Root cause / proposed fix
`add_reading` in `app/main.py` only compares the date to the previous reading. Add a check that
`read_on <= date.today()`.
