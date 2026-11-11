# Smart Water Supply and Billing System

Software Testing portfolio (Other Component), with the application under test and its complete test deliverables.

## Student details
| Name | USN |
|---|---|
| S Anandita Narayan | 1MS23IS105 |
| Vivan Raj Belur | 1MS23IS152 |

**Subject:** Software Testing

## Objectives
- Select a real-world application and identify its modules and functionalities.
- Prepare a test plan and design test cases with standard techniques (BVA, equivalence partitioning, decision tables, state transition).
- Execute the test cases, record actual results, and document defects.
- Automate testing with pytest (unit and API) and Selenium WebDriver (UI), and measure coverage.
- Keep a GitHub portfolio with meaningful commits that show progress.

## Project description
A water utility system with:
- Customer registration and login (roles: ADMIN, CUSTOMER)
- Metered connections (domestic or commercial)
- Monthly meter readings
- Tiered tariff billing: Rs 5, 8, 12 and 20 per kL by slab; commercial charges 1.5x; fixed monthly charge
- Bill lifecycle UNPAID, OVERDUE, PAID, with a due date 15 days after the bill date and a late fee
- Payments (exact amount, late fee included)
- Leak / high-usage alerts
- A web app (sign-in page, top navigation, bills, readings, payment dialog) and a REST API (interactive docs at `/docs`)

## Screenshots
| Sign in | Customer bills |
|---|---|
| ![Sign in](07_Screenshots/Demo01_sign_in.png) | ![Customer bills](07_Screenshots/Demo05_customer_bills.png) |

| Admin: customers + New connection popup | |
|---|---|
| ![Popup](07_Screenshots/Demo07_new_connection_popup.png) | |

| Admin: all bills | Payment dialog |
|---|---|
| ![Admin bills](07_Screenshots/Demo03_admin_bills.png) | ![Payment](07_Screenshots/Demo06_payment_dialog.png) |

More are in `07_Screenshots/`.

## Results at a glance
- **99 automated test cases** (30 unit, 62 API, 7 Selenium UI): 87 of 89 passed on run 1; all 99 pass on the final run
- **4 defects** found by the tests, all fixed and retested (see `04_Defect_Reports/README.md`)
- **98%** statement coverage of the `app` package

## Run the application
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 for the UI or http://127.0.0.1:8000/docs for the API.
An admin account is created on first start: `admin` / `admin123` (demo only).

### Load the demo data (6 customers, 18 bills)
```bash
python -m app.seed
```
Customers: `anandita`, `vivan`, `rohan`, `priya`, `karthik`, `meera`, all with the password `water123`.
The data has paid, unpaid and overdue bills, a late payment with a fee, and a high-usage alert (karthik).

## Run the tests
```bash
python -m pytest                               # everything (UI tests need Microsoft Edge)
python -m pytest -m "not ui"                   # unit + API only
python -m pytest --cov=app --cov-report=term   # with coverage
```

## Repository structure
```
README.md
app/                     Application source (FastAPI backend + static UI)
01_Test_Plan/            Test plan
02_Test_Case_Design/     Test cases: BVA, equivalence partitioning, decision tables, state transition
03_Test_Execution/       Execution log (run 1 vs run 2)
04_Defect_Reports/       DEF-001 to DEF-004 with a summary table
05_Test_Automation/      pytest unit/API tests and Selenium UI tests
06_Test_Reports/         JUnit XML for 4 runs, coverage output, test summary report
07_Screenshots/          Selenium screenshots
Conclusion.md
```
