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
- A web UI and a REST API (interactive docs at `/docs`)

## Results at a glance
- **89 automated test runs**: 87 passed and 2 failed on run 1; all 89 passed after fixes
- **3 defects** logged (2 fixed and retested, 1 low-severity deferred)
- **99%** statement coverage of the `app` package

## Run the application
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 for the UI or http://127.0.0.1:8000/docs for the API.
A seeded admin account is created on first start: `admin` / `admin123` (demo only).

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
04_Defect_Reports/       DEF-001 to DEF-003
05_Test_Automation/      pytest unit/API tests and Selenium UI tests
06_Test_Reports/         JUnit XML results, coverage output, test summary report
07_Screenshots/          Selenium screenshots
Conclusion.md
```
