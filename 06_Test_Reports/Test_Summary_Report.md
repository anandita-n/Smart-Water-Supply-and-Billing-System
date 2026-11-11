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
| Run 4 | After fixing DEF-003 and DEF-004, the redesigned UI and rewritten UI tests | 97 | 97 | 0 |

Raw results: `run1_baseline.xml`, `run2_after_fixes.xml`, `run3_new_tests.xml`, `run4_final.xml` (JUnit XML) and the `*_summary.txt` files.
Per-test results across all runs: `03_Test_Execution/test_execution_log.md`.

### Final test inventory (run 4)
| Level | Technique(s) | Test cases |
|---|---|---|
| Unit (`test_billing_unit.py`) | BVA, equivalence partitioning, decision table, state transition | 30 |
| API (`test_api.py`) | Equivalence partitioning, BVA, RBAC, error guessing | 60 |
| UI (`test_ui_selenium.py`) | Scenario-based, end to end | 7 |
| **Total** | | **97** |

## 2. Code coverage (pytest-cov, run 4)
| File | Statements | Missed | Coverage |
|---|---|---|---|
| app/billing.py | 48 | 0 | 100% |
| app/db.py | 15 | 1 | 93% |
| app/main.py | 204 | 1 | 99% |
| **Total** | 267 | 2 | **99%** (exit criterion: at least 90%) |

## 3. Defects
| ID | Title | Severity | Found by | Status |
|---|---|---|---|---|
| DEF-001 | Future-dated meter reading accepted | Medium | TC-A29 | Closed, retested |
| DEF-002 | `units=inf` makes the calculator return HTTP 500 | Medium | TC-A54 | Closed, retested |
| DEF-003 | Login tokens never expire and cannot be revoked | Medium | TC-A56 | Closed, retested |
| DEF-004 | Usernames are case-sensitive, so look-alike accounts can be registered | Medium | TC-A55 | Closed, retested |

Details are in `04_Defect_Reports/`.

## 4. Exit criteria check
| Criterion | Met? |
|---|---|
| All planned test cases executed | Yes |
| No open Critical/High defects | Yes (4 Medium defects found, all closed) |
| Fixed defects retested | Yes (runs 2 and 4) |
| Coverage of `app` at least 90% | Yes (99%) |

## 5. Known risks and recommendations
- The UI was tested in Edge only. UI tests UI06 and UI07 rely on the customer created in UI05, so they run in file order.
- No load or performance testing was done. Bill generation is a single-record operation, so the risk is low for this scope.
- Meter readings are entered manually by the admin; a real deployment would need automatic meter feeds and tests for those.
- Passwords are hashed with PBKDF2, but there is no lock-out after repeated failed logins. This is a candidate for a future test and fix.
