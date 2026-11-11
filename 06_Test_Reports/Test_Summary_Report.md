# Test Execution Summary Report

**Application:** Smart Water Supply and Billing System ("AquaBill") v1.0.0
**Testers:** S Anandita Narayan (1MS23IS105), Vivan Raj Belur (1MS23IS152)
**Environment:** Windows 11, Python 3.11.9, FastAPI 0.136.1, pytest 9.1.1, Selenium + Microsoft Edge (headless)

## 1. Results by run

| Run | Description | Executed | Passed | Failed |
|---|---|---|---|---|
| Run 1 | Baseline (unit, API, first UI tests) | 89 | 87 | 2 |
| Run 2 | After fixing DEF-001 and DEF-002 | 89 | 89 | 0 |
| Run 3 | New tests TC-A55 and TC-A56 added; UI tests not run | 86 | 84 | 2 |
| Run 4 | After fixing DEF-003 and DEF-004, the first UI redesign and rewritten UI tests | 97 | 97 | 0 |
| Run 5 | Minimal sign-in page, top navigation, seed data (TC-A61, TC-A62), updated UI tests | 99 | 99 | 0 |
| Run 6 | New connection popup, light-blue top bar, UI test updated | 99 | 99 | 0 |
| Run 7 | New modules (payment receipts, login lock-out, complaints, profile and password) tested before any fix; UI tests not run | 149 | 148 | 1 |
| Run 8 | Final: DEF-005 fixed, UI tests for the new screens added | 160 | 160 | 0 |

Raw results: `run1_baseline.xml` to `run8_final.xml` (JUnit XML) and the `*_summary.txt` files.
Per-test results across all runs: `03_Test_Execution/test_execution_log.md`.

### Final test inventory (run 8)
| Level | Technique(s) | Test cases |
|---|---|---|
| Unit (`test_billing_unit.py`, `test_complaints.py`) | BVA, equivalence partitioning, decision table, state transition | 36 |
| API (`test_api.py`, `test_payments.py`, `test_account_security.py`, `test_complaints.py`, `test_seed.py`) | Equivalence partitioning, BVA, RBAC, decision table, state transition, error guessing | 113 |
| UI (`test_ui_selenium.py`) | Scenario-based, end to end | 11 |
| **Total** | | **160** |

Parameterised tests are counted per parameter set, because each set has its own test case ID.

## 2. Code coverage (pytest-cov, run 8)
| File | Statements | Missed | Coverage |
|---|---|---|---|
| app/billing.py | 48 | 0 | 100% |
| app/complaints.py | 9 | 0 | 100% |
| app/db.py | 21 | 3 | 86% |
| app/main.py | 318 | 2 | 99% |
| app/seed.py | 63 | 4 | 94% |
| **Total** | 459 | 9 | **98%** (exit criterion: at least 90%) |

The uncovered lines in `db.py` are the migration steps for databases created before a feature existed; the tests always start from an empty database.

## 3. Defects
| ID | Title | Severity | Found by | Status |
|---|---|---|---|---|
| DEF-001 | Future-dated meter reading accepted | Medium | TC-A29 | Closed, retested |
| DEF-002 | `units=inf` makes the calculator return HTTP 500 | Medium | TC-A54 | Closed, retested |
| DEF-003 | Login tokens never expire and cannot be revoked | Medium | TC-A56 | Closed, retested |
| DEF-004 | Usernames are case-sensitive, so look-alike accounts can be registered | Medium | TC-A55 | Closed, retested |
| DEF-005 | Whitespace-only full name accepted at registration | Low | TC-A101 | Closed, retested |

Details are in `04_Defect_Reports/`. The new modules (payments, lock-out, complaints, profile) produced one defect in 57 new non-UI test cases; the other 56 passed on the first run.

## 4. Exit criteria check
| Criterion | Met? |
|---|---|
| All planned test cases executed | Yes |
| No open Critical/High defects | Yes (4 Medium and 1 Low defect found, all closed) |
| Fixed defects retested | Yes (runs 2, 4 and 8) |
| Coverage of `app` at least 90% | Yes (98%) |

## 5. Known risks and recommendations
- The UI was tested in Edge only. During run 5 one UI test failed intermittently because the page re-rendered while the test was selecting a dropdown option (a test timing problem, not an application defect). The test now waits and retries, and the UI suite passed repeatedly afterwards.
- The lock-out lasts 15 minutes and is not tested by waiting that long; TC-A76 simulates expiry by editing the stored lock time.
- Receipts are shown and printed from the browser; there is no PDF generation, so print layout was checked only through the browser's print preview rules.
- No load or performance testing was done. Bill generation is a single-record operation, so the risk is low for this scope.
- Meter readings are entered manually by the admin; a real deployment would need automatic meter feeds and tests for those.
- Payments are recorded but no real payment gateway is connected.
