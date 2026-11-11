# Test Execution Log

Generated from the JUnit XML files in `06_Test_Reports/`. `-` means the test case did not exist or was not run in that run.

| Run | What was executed | Executed | Passed | Failed |
|---|---|---|---|---|
| Run 1 | Baseline: unit, API and the first version of the UI tests | 89 | 87 | 2 |
| Run 2 | After fixing DEF-001 and DEF-002 (same tests) | 89 | 89 | 0 |
| Run 3 | Two new API tests added (TC-A55, TC-A56); UI tests not run in this run | 86 | 84 | 2 |
| Run 4 | After fixing DEF-003 and DEF-004; first UI redesign and rewritten UI tests (TC-UI01 to TC-UI07) | 97 | 97 | 0 |
| Run 5 | Second UI redesign (top navigation, minimal sign-in page), seed data and seed tests (TC-A61, TC-A62); UI tests updated | 99 | 99 | 0 |
| Run 6 | Final: New connection popup, light-blue top bar, regular-weight status text; UI test updated for the popup | 99 | 99 | 0 |
| Run 7 | New modules built (payment receipts, login lock-out, complaints, profile/password); their tests run before the DEF-005 fix. UI tests not run | 149 | 148 | 1 |
| Run 8 | Final: DEF-005 fixed, new UI pages and UI tests TC-UI08 to TC-UI11, seed data extended with complaints | 160 | 160 | 0 |
| Run 9 | Final: customer history page, type filter, readings table and popup, three-dots profile, captions removed; reading-list API tests and UI tests TC-UI12 to TC-UI16 | 169 | 169 | 0 |
| Run 10 | Final: dashboards for admin and customer (landing page); UI tests TC-UI17 to TC-UI19; existing UI tests adjusted to start from the dashboard | 172 | 172 | 0 |
| Run 11 | Final: Readings page explains disabled buttons and offers Save and generate bill; UI test TC-UI20 | 173 | 173 | 0 |

Executed with `python -m pytest`; Selenium tests ran in headless Microsoft Edge.

| Test ID | Description | Run 1 | Run 2 | Run 3 | Run 4 | Run 5 | Run 6 | Run 7 | Run 8 | Run 9 | Run 10 | Run 11 | Defect |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-U01 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U02 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U03 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U04 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U05 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U06 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U07 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U08 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U09 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U10 | domestic water charge boundaries | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U11 | negative units rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U12 | invalid connection type rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U13 | commercial is 1 5x domestic | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U14 | fixed charges | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U15 | total is water plus fixed | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U16 | no fee before due date | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U17 | no fee on due date | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U18 | fee one day late | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U19 | due date is 15 days after bill date | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U20 | leak detection decision table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U21 | leak detection decision table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U22 | leak detection decision table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U23 | leak detection decision table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U24 | leak detection decision table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U25 | leak detection decision table | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U26 | unpaid to paid | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U27 | unpaid to overdue | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U28 | overdue to paid | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U29 | paid is terminal | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U30 | paid cannot become overdue | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-U31 | open to in progress | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-U32 | in progress to resolved | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-U33 | cannot skip in progress | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-U34 | resolved is final | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-U35 | cannot move backwards | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-U36 | allowed next states | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A01 | register valid customer | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A02 | register duplicate username | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A03 | register invalid input | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A04 | register invalid input | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A05 | register invalid input | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A06 | register invalid input | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A07 | register invalid input | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A08 | register username length boundaries accepted | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A09 | register username length boundaries accepted | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A10 | login success returns token | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A11 | login failures | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A12 | login failures | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A13 | protected endpoint requires token | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A14 | garbage token rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A15 | customer cannot create connection | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A16 | customer cannot add reading | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A17 | customer cannot generate bill | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A18 | create connection ok | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A19 | duplicate meter number | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A20 | connection for unknown customer | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A21 | connection invalid type | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A22 | customer sees only own connections | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A23 | first reading ok | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A24 | reading lower than previous rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A25 | reading equal to previous accepted | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A26 | negative reading rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A27 | reading date before previous rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A28 | reading for unknown connection | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A29 | future dated reading rejected | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | DEF-001 |
| TC-A30 | bill needs two readings | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A31 | bill amounts and due date | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A32 | duplicate bill for same reading rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A33 | bill unknown connection | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A34 | customer sees own bill only | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A35 | unpaid bill past due listed as overdue | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A36 | get unknown bill | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A37 | high usage creates alert | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A38 | normal usage no alert | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A39 | spike vs history creates alert | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A40 | pay on time exact amount | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A41 | pay on due date has no late fee | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A42 | pay late requires fee | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A43 | underpayment rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A44 | overpayment rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A45 | double payment rejected | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A46 | cannot pay someone elses bill | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A47 | pay unknown bill | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A48 | overdue bill can be paid | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A49 | commercial bill uses multiplier | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A50 | calculator ok | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A51 | calculator invalid inputs | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A52 | calculator invalid inputs | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A53 | calculator invalid inputs | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A54 | calculator invalid inputs | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | DEF-002 |
| TC-A55 | username is case insensitive | - | - | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | DEF-004 |
| TC-A56 | logout invalidates token | - | - | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | DEF-003 |
| TC-A57 | expired token rejected | - | - | - | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A58 | admin lists customers | - | - | - | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A59 | customer cannot list customers | - | - | - | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A60 | login works with any username case | - | - | - | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A61 | seed loads six customers including team members | - | - | - | - | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A62 | seed is idempotent and customers can sign in | - | - | - | - | PASS | PASS | PASS | PASS | PASS | PASS | PASS |  |
| TC-A63 | payment creates record with receipt number | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A64 | customer sees only own payments | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A65 | admin sees all payments with customer name | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A66 | receipt shows full breakdown | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A67 | cannot view someone elses receipt | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A68 | unknown receipt | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A69 | invalid payment method rejected | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A70 | payment history requires login | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A71 | late payment record includes late fee | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A72 | rejected or repeated payment creates no extra record | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A73 | account locks on fifth failed attempt | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A74 | correct password rejected while locked | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A75 | successful login resets the failure counter | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A76 | lock expires after the lock period | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A77 | unknown username is never reported as locked | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A78 | lockout affects only the targeted account | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A79 | customer files complaint for own connection | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A80 | complaint description length boundaries | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A81 | invalid category rejected | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A82 | cannot file against someone elses connection | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A83 | customer sees only own complaints | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A84 | admin sees all complaints with customer name | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A85 | admin moves open to in progress | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A86 | resolving requires a resolution note | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A87 | resolve with note | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A88 | cannot resolve an open complaint directly | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A89 | resolved complaint cannot change again | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A90 | customer cannot update complaints | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A91 | admin cannot file complaints | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A92 | unknown complaint | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A93 | update full name | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A94 | empty full name rejected | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A95 | change password success | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A96 | wrong current password rejected | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A97 | new password must differ from current | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A98 | new password too short | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A99 | password change signs out other sessions | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A100 | profile endpoints require login | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A101 | whitespace only name rejected at registration | - | - | - | - | - | - | FAIL | PASS | PASS | PASS | PASS | DEF-005 |
| TC-A102 | whitespace only name rejected in profile | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A103 | complaint description length boundaries | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A104 | complaint description length boundaries | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A105 | complaint description length boundaries | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A106 | status open is not an allowed target | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A107 | complaint without a connection is allowed | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A108 | new password of minimum length accepted | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A109 | every supported payment method is accepted | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A110 | every supported payment method is accepted | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A111 | every supported payment method is accepted | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A112 | every supported payment method is accepted | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A113 | complaints require login | - | - | - | - | - | - | PASS | PASS | PASS | PASS | PASS |  |
| TC-A114 | admin lists readings in order with meter number | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-A115 | readings can be filtered by connection | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-A116 | customer cannot list readings | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-A117 | readings require login | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-UI01 | invalid login shows error | PASS | PASS | - | PASS | PASS | PASS | - | PASS | PASS | PASS | PASS |  |
| TC-UI02 | bill estimator | PASS | PASS | - | PASS | PASS | PASS | - | PASS | PASS | PASS | PASS |  |
| TC-UI03 | estimator negative units rejected | PASS | PASS | - | PASS | PASS | PASS | - | PASS | PASS | PASS | PASS |  |
| TC-UI04 | admin login shows admin menu | PASS | PASS | - | PASS | PASS | PASS | - | PASS | PASS | PASS | PASS |  |
| TC-UI05 | end to end billing and payment | PASS | PASS | - | PASS | PASS | PASS | - | PASS | PASS | PASS | PASS |  |
| TC-UI06 | logout returns to login and session is gone | - | - | - | PASS | PASS | PASS | - | PASS | PASS | PASS | PASS |  |
| TC-UI07 | customer does not see admin menu | - | - | - | PASS | PASS | PASS | - | PASS | PASS | PASS | PASS |  |
| TC-UI08 | payment creates a receipt | - | - | - | - | - | - | - | PASS | PASS | PASS | PASS |  |
| TC-UI09 | complaint raised by customer and updated by admin | - | - | - | - | - | - | - | PASS | PASS | PASS | PASS |  |
| TC-UI10 | customer changes password | - | - | - | - | - | - | - | PASS | PASS | PASS | PASS |  |
| TC-UI11 | account locks after five failed sign ins | - | - | - | - | - | - | - | PASS | PASS | PASS | PASS |  |
| TC-UI12 | profile name is edited through the menu | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-UI13 | clicking a customer name opens their history | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-UI14 | customers can be filtered by connection type | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-UI15 | pages have no caption under the heading | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-UI16 | reading page enables billing only when a new reading exists | - | - | - | - | - | - | - | - | PASS | PASS | PASS |  |
| TC-UI17 | admin dashboard is the landing page with essentials | - | - | - | - | - | - | - | - | - | PASS | PASS |  |
| TC-UI18 | customer dashboard shows amount due and pays from there | - | - | - | - | - | - | - | - | - | PASS | PASS |  |
| TC-UI19 | dashboard attention link opens the overdue bills filter | - | - | - | - | - | - | - | - | - | PASS | PASS |  |
| TC-UI20 | save reading and generate bill in one step | - | - | - | - | - | - | - | - | - | - | PASS |  |
