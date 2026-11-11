# Test Execution Log

Generated from the JUnit XML files in `06_Test_Reports/`. `-` means the test case did not exist or was not run in that run.

| Run | What was executed | Executed | Passed | Failed |
|---|---|---|---|---|
| Run 1 | Baseline: unit, API and the first version of the UI tests | 89 | 87 | 2 |
| Run 2 | After fixing DEF-001 and DEF-002 (same tests) | 89 | 89 | 0 |
| Run 3 | Two new API tests added (TC-A55, TC-A56); UI tests not run in this run | 86 | 84 | 2 |
| Run 4 | After fixing DEF-003 and DEF-004; new UI redesign and rewritten UI tests (TC-UI01 to TC-UI07) | 97 | 97 | 0 |

Executed with `python -m pytest`; Selenium tests ran in headless Microsoft Edge.

| Test ID | Description | Run 1 | Run 2 | Run 3 | Run 4 | Defect |
|---|---|---|---|---|---|---|
| TC-U01 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U02 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U03 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U04 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U05 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U06 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U07 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U08 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U09 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U10 | domestic water charge boundaries | PASS | PASS | PASS | PASS |  |
| TC-U11 | negative units rejected | PASS | PASS | PASS | PASS |  |
| TC-U12 | invalid connection type rejected | PASS | PASS | PASS | PASS |  |
| TC-U13 | commercial is 1 5x domestic | PASS | PASS | PASS | PASS |  |
| TC-U14 | fixed charges | PASS | PASS | PASS | PASS |  |
| TC-U15 | total is water plus fixed | PASS | PASS | PASS | PASS |  |
| TC-U16 | no fee before due date | PASS | PASS | PASS | PASS |  |
| TC-U17 | no fee on due date | PASS | PASS | PASS | PASS |  |
| TC-U18 | fee one day late | PASS | PASS | PASS | PASS |  |
| TC-U19 | due date is 15 days after bill date | PASS | PASS | PASS | PASS |  |
| TC-U20 | leak detection decision table | PASS | PASS | PASS | PASS |  |
| TC-U21 | leak detection decision table | PASS | PASS | PASS | PASS |  |
| TC-U22 | leak detection decision table | PASS | PASS | PASS | PASS |  |
| TC-U23 | leak detection decision table | PASS | PASS | PASS | PASS |  |
| TC-U24 | leak detection decision table | PASS | PASS | PASS | PASS |  |
| TC-U25 | leak detection decision table | PASS | PASS | PASS | PASS |  |
| TC-U26 | unpaid to paid | PASS | PASS | PASS | PASS |  |
| TC-U27 | unpaid to overdue | PASS | PASS | PASS | PASS |  |
| TC-U28 | overdue to paid | PASS | PASS | PASS | PASS |  |
| TC-U29 | paid is terminal | PASS | PASS | PASS | PASS |  |
| TC-U30 | paid cannot become overdue | PASS | PASS | PASS | PASS |  |
| TC-A01 | register valid customer | PASS | PASS | PASS | PASS |  |
| TC-A02 | register duplicate username | PASS | PASS | PASS | PASS |  |
| TC-A03 | register invalid input | PASS | PASS | PASS | PASS |  |
| TC-A04 | register invalid input | PASS | PASS | PASS | PASS |  |
| TC-A05 | register invalid input | PASS | PASS | PASS | PASS |  |
| TC-A06 | register invalid input | PASS | PASS | PASS | PASS |  |
| TC-A07 | register invalid input | PASS | PASS | PASS | PASS |  |
| TC-A08 | register username length boundaries accepted | PASS | PASS | PASS | PASS |  |
| TC-A09 | register username length boundaries accepted | PASS | PASS | PASS | PASS |  |
| TC-A10 | login success returns token | PASS | PASS | PASS | PASS |  |
| TC-A11 | login failures | PASS | PASS | PASS | PASS |  |
| TC-A12 | login failures | PASS | PASS | PASS | PASS |  |
| TC-A13 | protected endpoint requires token | PASS | PASS | PASS | PASS |  |
| TC-A14 | garbage token rejected | PASS | PASS | PASS | PASS |  |
| TC-A15 | customer cannot create connection | PASS | PASS | PASS | PASS |  |
| TC-A16 | customer cannot add reading | PASS | PASS | PASS | PASS |  |
| TC-A17 | customer cannot generate bill | PASS | PASS | PASS | PASS |  |
| TC-A18 | create connection ok | PASS | PASS | PASS | PASS |  |
| TC-A19 | duplicate meter number | PASS | PASS | PASS | PASS |  |
| TC-A20 | connection for unknown customer | PASS | PASS | PASS | PASS |  |
| TC-A21 | connection invalid type | PASS | PASS | PASS | PASS |  |
| TC-A22 | customer sees only own connections | PASS | PASS | PASS | PASS |  |
| TC-A23 | first reading ok | PASS | PASS | PASS | PASS |  |
| TC-A24 | reading lower than previous rejected | PASS | PASS | PASS | PASS |  |
| TC-A25 | reading equal to previous accepted | PASS | PASS | PASS | PASS |  |
| TC-A26 | negative reading rejected | PASS | PASS | PASS | PASS |  |
| TC-A27 | reading date before previous rejected | PASS | PASS | PASS | PASS |  |
| TC-A28 | reading for unknown connection | PASS | PASS | PASS | PASS |  |
| TC-A29 | future dated reading rejected | FAIL | PASS | PASS | PASS | DEF-001 |
| TC-A30 | bill needs two readings | PASS | PASS | PASS | PASS |  |
| TC-A31 | bill amounts and due date | PASS | PASS | PASS | PASS |  |
| TC-A32 | duplicate bill for same reading rejected | PASS | PASS | PASS | PASS |  |
| TC-A33 | bill unknown connection | PASS | PASS | PASS | PASS |  |
| TC-A34 | customer sees own bill only | PASS | PASS | PASS | PASS |  |
| TC-A35 | unpaid bill past due listed as overdue | PASS | PASS | PASS | PASS |  |
| TC-A36 | get unknown bill | PASS | PASS | PASS | PASS |  |
| TC-A37 | high usage creates alert | PASS | PASS | PASS | PASS |  |
| TC-A38 | normal usage no alert | PASS | PASS | PASS | PASS |  |
| TC-A39 | spike vs history creates alert | PASS | PASS | PASS | PASS |  |
| TC-A40 | pay on time exact amount | PASS | PASS | PASS | PASS |  |
| TC-A41 | pay on due date has no late fee | PASS | PASS | PASS | PASS |  |
| TC-A42 | pay late requires fee | PASS | PASS | PASS | PASS |  |
| TC-A43 | underpayment rejected | PASS | PASS | PASS | PASS |  |
| TC-A44 | overpayment rejected | PASS | PASS | PASS | PASS |  |
| TC-A45 | double payment rejected | PASS | PASS | PASS | PASS |  |
| TC-A46 | cannot pay someone elses bill | PASS | PASS | PASS | PASS |  |
| TC-A47 | pay unknown bill | PASS | PASS | PASS | PASS |  |
| TC-A48 | overdue bill can be paid | PASS | PASS | PASS | PASS |  |
| TC-A49 | commercial bill uses multiplier | PASS | PASS | PASS | PASS |  |
| TC-A50 | calculator ok | PASS | PASS | PASS | PASS |  |
| TC-A51 | calculator invalid inputs | PASS | PASS | PASS | PASS |  |
| TC-A52 | calculator invalid inputs | PASS | PASS | PASS | PASS |  |
| TC-A53 | calculator invalid inputs | PASS | PASS | PASS | PASS |  |
| TC-A54 | calculator invalid inputs | FAIL | PASS | PASS | PASS | DEF-002 |
| TC-A55 | username is case insensitive | - | - | FAIL | PASS | DEF-004 |
| TC-A56 | logout invalidates token | - | - | FAIL | PASS | DEF-003 |
| TC-A57 | expired token rejected | - | - | - | PASS |  |
| TC-A58 | admin lists customers | - | - | - | PASS |  |
| TC-A59 | customer cannot list customers | - | - | - | PASS |  |
| TC-A60 | login works with any username case | - | - | - | PASS |  |
| TC-UI01 | invalid login shows error | PASS | PASS | - | PASS |  |
| TC-UI02 | bill estimator | PASS | PASS | - | PASS |  |
| TC-UI03 | estimator negative units rejected | PASS | PASS | - | PASS |  |
| TC-UI04 | admin login shows admin menu | PASS | PASS | - | PASS |  |
| TC-UI05 | end to end billing and payment | PASS | PASS | - | PASS |  |
| TC-UI06 | logout returns to login and session is gone | - | - | - | PASS |  |
| TC-UI07 | customer does not see admin menu | - | - | - | PASS |  |
