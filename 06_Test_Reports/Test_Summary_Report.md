# Test Execution Summary Report

**Application:** Smart Water Supply and Billing System v1.0.0
**Testers:** S Anandita Narayan (1MS23IS105), Vivan Raj Belur (1MS23IS152)
**Environment:** Windows 11, Python 3.11.9, FastAPI 0.136.1, pytest 9.1.1, Selenium + Microsoft Edge (headless)

## 1. Results

| Run | Description | Executed | Passed | Failed | Pass rate |
|---|---|---|---|---|---|
| Run 1 | Baseline, before any fixes | 89 | 87 | 2 | 97.8% |
| Run 2 | After fixing DEF-001 and DEF-002 | 89 | 89 | 0 | 100% |

Raw results: `run1_baseline.xml`, `run2_after_fixes.xml` (JUnit XML) and the `*_summary.txt` files.
Per-test results: `03_Test_Execution/test_execution_log.md`.

### By level (run 2)
| Level | Technique(s) | Test cases |
|---|---|---|
| Unit (`test_billing_unit.py`) | BVA, equivalence partitioning, decision table, state transition | 30 |
| API (`test_api.py`) | Equivalence partitioning, BVA, RBAC, error guessing | 54 |
| UI (`test_ui_selenium.py`) | Scenario-based, end to end | 5 |

Parameterised tests are counted per parameter set, because each set has its own test case ID.

## 2. Code coverage (pytest-cov, run 2)
| File | Statements | Missed | Coverage |
|---|---|---|---|
| app/billing.py | 48 | 0 | 100% |
| app/db.py | 12 | 0 | 100% |
| app/main.py | 192 | 2 | 99% |
| **Total** | 252 | 2 | **99%** (exit criterion: at least 90%) |

## 3. Defects
| ID | Title | Severity | Found by | Status |
|---|---|---|---|---|
| DEF-001 | Future-dated meter reading accepted | Medium | TC-A29 | Closed, retested |
| DEF-002 | `units=inf` makes the calculator return HTTP 500 | Medium | TC-A54 | Closed, retested |
| DEF-003 | Login tokens never expire and cannot be revoked | Low (prototype) | Exploratory | Open, deferred |

Details are in `04_Defect_Reports/`.

## 4. Exit criteria check
| Criterion | Met? |
|---|---|
| All planned test cases executed | Yes |
| No open Critical/High defects | Yes (none found; one Low open) |
| Fixed defects retested | Yes (run 2) |
| Coverage of `app` at least 90% | Yes (99%) |

## 5. Known risks and recommendations
- DEF-003 should be fixed before real use (token expiry and logout).
- The UI was tested in Edge only.
- No load or performance testing was done. Bill generation is a single-record operation, so the risk is low for this scope.
- The meter-reading step is manual (admin entry); a real deployment would need automatic meter feeds and tests for those.
