# Test Plan: Smart Water Supply and Billing System

| | |
|---|---|
| Version | 1.0 |
| Prepared by | S Anandita Narayan (1MS23IS105), Vivan Raj Belur (1MS23IS152) |
| Application under test | Smart Water Supply and Billing System (FastAPI + SQLite + single-page web UI) |

## 1. Introduction
The application lets a water utility register customers, set up metered connections, record meter
readings, generate bills using a tiered tariff, collect payments (with late fees) and raise
leak/high-usage alerts. This plan describes how the system is tested.

## 2. Application modules and functionalities to be tested
| # | Module | Functionality | Test levels |
|---|---|---|---|
| M1 | Authentication | Register, login, logout, token expiry, case-insensitive usernames, role-based access (ADMIN / CUSTOMER) | API, UI |
| M2 | Connections & customers | Create connection, unique meter number, ownership, listing; customer list with type filter and search; one customer's history (bills, payments, complaints, readings) | API, UI |
| M3 | Meter readings | Add reading; no decrease, no date going backwards, no future dates; reading list; per-meter status (ready to bill / billed) with the reason a button is disabled; Save and generate bill in one step | API, UI |
| M4 | Tariff & billing | Slab charges, commercial multiplier, fixed charge, bill generation, due date | Unit, API, UI |
| M5 | Payments | Exact-amount payment, late fee, double payment, ownership | Unit, API, UI |
| M6 | Alerts | High usage (> 100 kL) and spike (> 3x average) alerts | Unit, API |
| M7 | Web UI | Sign in/create account (HydroCore branding, light-blue wave), top navigation by role (admin: Dashboard, Customers, Readings, Bills, Feedback; customer: Dashboard, My bills, Payments, Feedback), popups, profile page with three-dots menu, sign out | UI (Selenium) |
| M8 | Payments & receipts | Payment record and receipt number, payment history, receipt breakdown, payment methods, access control | API, UI |
| M9 | Account security | Login lock-out after 5 failed attempts, profile update, password change, blank-name validation | API, UI |
| M11 | Dashboard | Landing page with a greeting band and one simple bar chart (admin: billed vs collected for the last 6 months; customer: usage of the last 6 bills). Admin: outstanding, collected and billed this month, a "needs attention" list that links to the right page, recent payments. Customer: amount due with Pay now, latest bill compared with the previous one, alerts from the last 30 days only | UI |
| M10 | Complaints | Customer files a complaint; admin moves it OPEN, IN_PROGRESS, RESOLVED with a resolution note | Unit, API, UI |

### Business rules (the test oracle)
- Slabs per month: 0-10 kL at Rs 5, 10-20 kL at Rs 8, 20-30 kL at Rs 12, above 30 kL at Rs 20.
- Commercial water charge = 1.5 x domestic. Fixed charge: Rs 50 domestic, Rs 150 commercial.
- Due date = bill date + 15 days. Late fee = Rs 25 + 2% of total if paid after the due date.
- Bill states: UNPAID, OVERDUE, PAID (PAID is final).
- Alert when usage > 100 kL, or usage > 3 x the average of earlier bills.
- Every payment creates one receipt (RCP-nnnnnn). Methods: UPI, Card, Net banking, Cash.
- Five failed sign-ins lock the account for 15 minutes; a successful sign-in resets the count.
- Complaint life cycle: OPEN, IN_PROGRESS, RESOLVED (cannot skip a step or go back); resolving needs a note of at least 3 characters; description 10 to 500 characters.
- Changing the password needs the current password, must differ from it, and signs out the other sessions.

## 3. Features not tested
Performance and load testing, real payment gateways, email/SMS notifications, and
browsers other than Microsoft Edge.

## 4. Test approach
| Technique | Applied to |
|---|---|
| Boundary value analysis | Tariff slab edges, username length, reading values, late-fee date, alert thresholds |
| Equivalence partitioning | Connection type, registration input classes, payment amount classes |
| Decision table | Leak / high-usage alert, payment acceptance |
| State transition | Bill lifecycle UNPAID / OVERDUE / PAID |
| Error guessing | `inf` / `nan` values, future dates, token misuse |
| Automation | pytest (unit + API), Selenium WebDriver (UI), pytest-cov (coverage) |

## 5. Entry and exit criteria
- **Entry:** application starts, database initialises, admin account is seeded.
- **Exit:** all planned test cases executed; no open Critical/High defects; every fixed defect retested;
  statement coverage of the `app` package at least 90%.

## 6. Test environment
Windows 11, Python 3.11, FastAPI 0.136, SQLite (fresh database per test), pytest 9, Selenium with Microsoft Edge (headless).

## 7. Deliverables
Test plan, test case design, execution log, defect reports, automation scripts, test summary report, screenshots, conclusion.

## 8. Roles
| Name | USN | Responsibilities |
|---|---|---|
| S Anandita Narayan | 1MS23IS105 | Test plan, billing/payment test design, API automation |
| Vivan Raj Belur | 1MS23IS152 | Auth/readings test design, UI automation, defect reporting |

## 9. Risks
| Risk | Mitigation |
|---|---|
| Date-dependent behaviour (overdue status) | Tests pass explicit dates in the API; the overdue test uses a fixed past due date |
| UI tests depend on browser/driver | Selenium Manager fetches the driver; UI tests are marked `ui` and can be run on their own |
| Float rounding in money calculations | Amounts rounded to 2 decimals; boundary tests use tolerance 0.005 |
