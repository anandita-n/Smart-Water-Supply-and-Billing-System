# Test Case Design

Test case IDs match the automated test names in `05_Test_Automation/` and the rows in
`03_Test_Execution/test_execution_log.md`. (`TC-U` = unit, `TC-A` = API, `TC-UI` = Selenium UI.)

## 1. Boundary Value Analysis: domestic tariff (TC-U01 to TC-U12)
Slab edges are 10, 20 and 30 kL, so each edge is tested at the edge and just above it.

| ID | Units (kL) | Expected water charge (Rs) | Calculation |
|---|---|---|---|
| TC-U01 | 0 | 0.00 | lower bound |
| TC-U02 | 0.01 | 0.05 | 0.01 x 5 |
| TC-U03 | 1 | 5.00 | 1 x 5 |
| TC-U04 | 10 | 50.00 | top of slab 1 |
| TC-U05 | 10.01 | 50.08 | 50 + 0.01 x 8 |
| TC-U06 | 20 | 130.00 | 50 + 10 x 8 |
| TC-U07 | 20.01 | 130.12 | 130 + 0.01 x 12 |
| TC-U08 | 30 | 250.00 | 130 + 10 x 12 |
| TC-U09 | 30.01 | 250.20 | 250 + 0.01 x 20 |
| TC-U10 | 50 | 650.00 | 250 + 20 x 20 |
| TC-U11 | -0.01 | ValueError | below the valid range |
| TC-U12 | type = INDUSTRIAL | ValueError | invalid class |

## 2. Equivalence Partitioning
| ID | Partition | Representative input | Expected |
|---|---|---|---|
| TC-U13 | Commercial connection | 20 kL, COMMERCIAL | water charge = 1.5 x domestic |
| TC-U14 | Zero usage, domestic / commercial | 0 kL | total 50 / 150 (fixed charge only) |
| TC-U15 | Domestic, normal usage | 25 kL | water 190 + fixed 50 = 240 |
| TC-A03 | Username too short (< 3) | `ab` | 422 |
| TC-A04 | Username too long (> 30) | 31 chars | 422 |
| TC-A05 | Username with illegal characters | `bad name!` | 422 |
| TC-A06 | Password too short (< 6) | `12345` | 422 |
| TC-A07 | Empty full name | `""` | 422 |
| TC-A01 | Valid registration | `bob_1` / `secret1` | 201 |
| TC-A21 | Connection type outside {DOMESTIC, COMMERCIAL} | INDUSTRIAL | 422 |
| TC-A51, A52, A53 | Calculator: negative / non-numeric / bad type | -1, `abc`, INDUSTRIAL | 422 |
| TC-A54 | Calculator: non-finite number | `inf` | 422 (found DEF-002) |

## 3. Boundary Value Analysis: other fields
| ID | Boundary | Input | Expected |
|---|---|---|---|
| TC-A08 | Username min length | 3 chars | 201 |
| TC-A09 | Username max length | 30 chars | 201 |
| TC-A24 | Reading just below previous | 99.99 after 100 | 400 |
| TC-A25 | Reading equal to previous | 100 after 100 | 201 |
| TC-A26 | Reading below zero | -1 | 422 |
| TC-A27 | Reading date before previous date | earlier date | 400 |
| TC-A29 | Reading date after today | 2999-01-01 | 400 (found DEF-001) |
| TC-U16 | Payment before due date | day -6 | late fee 0 |
| TC-U17 | Payment on due date | day 0 | late fee 0 |
| TC-U18 | Payment one day after due date | day +1 | late fee 25 + 2% |
| TC-U19 | Due date rule | bill date + 15 days | correct date |
| TC-A41, A42 | Payment on due date / one day late | day 0 / day +1 | no fee / fee required |
| TC-A43, A44 | Payment 0.01 below / above amount due | 239.99 / 240.01 | 400 |

## 4. Decision Table: alert rules (TC-U20 to TC-U25, TC-A37 to TC-A39)
| Rule | Usage > 100 kL | Previous bills exist and usage > 3 x average | Alert? | Test |
|---|---|---|---|---|
| R1 | N | N (or no history) | No | TC-U20, TC-U21 (exactly 100), TC-U23 (exactly 3x), TC-U25 (average 0) |
| R2 | Y | any | Yes | TC-U22 (100.01), TC-A37 |
| R3 | N | Y | Yes | TC-U24 (3x + 0.01), TC-A39 |

## 5. Decision Table: payment acceptance (TC-A40 to TC-A48)
| Rule | Bill status | Owner / admin | Amount = total + late fee | Result | Test |
|---|---|---|---|---|---|
| P1 | UNPAID, on time | Yes | Yes | 200 PAID | TC-A40, TC-A41 |
| P2 | UNPAID, late | Yes | No (fee missing) | 400 | TC-A42 |
| P3 | UNPAID, late | Yes | Yes | 200 PAID, fee stored | TC-A42 |
| P4 | UNPAID | Yes | No (under / over) | 400 | TC-A43, TC-A44 |
| P5 | OVERDUE | Yes | Yes | 200 PAID | TC-A48 |
| P6 | PAID | Yes | Yes | 409 | TC-A45 |
| P7 | any | Other customer | Yes | 403 | TC-A46 |
| P8 | Bill does not exist | any | any | 404 | TC-A47 |

## 6. State Transition: bill lifecycle
```
            pay                    due date passes
 UNPAID ------------> PAID     UNPAID ------------> OVERDUE
    |                   ^                               |
    +-------------------+          pay                  |
                        +--------------------------------+
```
| ID | From | Event | Expected |
|---|---|---|---|
| TC-U26 | UNPAID | pay | PAID |
| TC-U27 | UNPAID | due date passes | OVERDUE |
| TC-U28 | OVERDUE | pay | PAID |
| TC-U29 | PAID | pay | invalid transition |
| TC-U30 | PAID | due date passes | invalid transition |
| TC-A35 | UNPAID past due | list bills | status shown as OVERDUE |

## 7. Security and access control (role-based)
TC-A13 (no token), TC-A14 (garbage token), TC-A56 (logout revokes the token, DEF-003), TC-A57 (expired token rejected), TC-A55 and TC-A60 (usernames are case-insensitive, DEF-004), TC-A15 to TC-A17 (customer calling admin-only
endpoints), TC-A22 and TC-A34 (data isolation between customers), TC-A46 (paying another customer's bill).

## 8. Functional and integration (API)
TC-A02, A10 to A12 (auth), TC-A18 to A20 (connections), TC-A23, A28 (readings),
TC-A30 to A33, A36 (bill generation), TC-A31 (amounts and due date), TC-A49 (commercial bill),
TC-A50 (calculator), TC-A58 and TC-A59 (admin-only customer list).

## 9. UI test cases (Selenium, Microsoft Edge headless)
| ID | Scenario | Expected |
|---|---|---|
| TC-UI01 | Sign in with a wrong password | "Invalid username or password" is shown on the login screen |
| TC-UI02 | Estimate a bill for 25 kL | "Total: ₹240.00" is shown |
| TC-UI03 | Estimate with negative units | A validation error is shown |
| TC-UI04 | Admin signs in | Header shows System Administrator / admin and the Customers menu is visible |
| TC-UI05 | End to end: register; admin creates a connection, two readings and a bill; customer signs in, opens the payment dialog (₹240.00) and pays | Bill status changes from UNPAID to PAID |
| TC-UI06 | Sign out, then reload the page | Login screen is shown; the session is gone |
| TC-UI07 | Customer signs in | Admin-only menu items (Customers, Meter readings) are not shown |