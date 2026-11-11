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
TC-A50 (calculator), TC-A58 and TC-A59 (admin-only customer list), TC-A114 to TC-A117 (reading list for the Readings and customer history screens: admin only, ordered, filter by connection), TC-A61 and TC-A62 (demo data loader: 6 customers incl. S Anandita Narayan and Vivan Raj Belur, safe to run twice, customers can sign in).

## 9. Payments and receipts (TC-A63 to TC-A72, TC-A109 to TC-A112)
| ID | Technique | Scenario | Expected |
|---|---|---|---|
| TC-A63 | Functional | Pay a bill by card | One payment record, receipt RCP-000001 |
| TC-A64, A65 | Access control | Customer lists payments / admin lists payments | Customer sees only their own; admin sees all with customer name |
| TC-A66 | Functional | Open the receipt | Water 190, fixed 50, late fee 0, amount 240, address and units correct |
| TC-A67, A68 | Access control | Another customer opens the receipt / unknown receipt | 403 / 404 |
| TC-A69 | Equivalence partitioning | Payment method BITCOIN | 422 and no payment record |
| TC-A70 | Security | Payment history without login | 401 |
| TC-A71 | BVA (late fee) | Pay one day after the due date | Record holds late fee 29.80 and amount 269.80 |
| TC-A72 | Error guessing | Wrong amount, then correct, then a repeat payment | Exactly one payment record |
| TC-A109 to A112 | Equivalence partitioning | Each valid method: UPI, CARD, NETBANKING, CASH | 200 |

## 10. Login lock-out (TC-A73 to TC-A78)
| ID | Technique | Scenario | Expected |
|---|---|---|---|
| TC-A73 | BVA | 5 wrong passwords in a row | 401, 401, 401, 401, then 423 (locked) |
| TC-A74 | Decision table | Correct password while locked | 423 |
| TC-A75 | BVA | 4 failures, one success, then 4 more failures | Never locked (counter reset) |
| TC-A76 | State transition | Lock period expires | Login works again |
| TC-A77 | Error guessing | Repeated attempts for an unknown username | Always 401, never "locked" (no account to lock) |
| TC-A78 | Equivalence partitioning | One account locked | A different account still signs in |

| Failed attempts so far | Locked? | Password correct? | Result |
|---|---|---|---|
| 0 to 3 | No | No | 401, counter +1 |
| 4 | No | No | 423, account locked |
| any | No | Yes | 200, counter reset |
| any | Yes | Yes or No | 423 |

## 11. Complaints
| ID | Technique | Scenario | Expected |
|---|---|---|---|
| TC-U31 to U35 | State transition | OPEN to IN_PROGRESS, IN_PROGRESS to RESOLVED valid; OPEN to RESOLVED, backwards, and any change after RESOLVED invalid | Valid ones succeed, others raise an error |
| TC-U36 | State transition | Allowed next states | OPEN: [IN_PROGRESS], IN_PROGRESS: [RESOLVED], RESOLVED: [] |
| TC-A79, A107 | Functional | File a complaint with / without a connection | 201, status OPEN |
| TC-A80, A103, A104, A105 | BVA (description length 10 to 500) | 9, 10, 500, 501 characters | 422, 201, 201, 422 |
| TC-A81, A106 | Equivalence partitioning | Invalid category / status OPEN as an update target | 422 |
| TC-A82 | Access control | Complaint on another customer's connection | 403 |
| TC-A83, A84 | Access control | Customer list / admin list | Own only / all with customer name |
| TC-A85 to A89 | State transition | IN_PROGRESS; resolve without note (400); resolve with note; skip a step (409); change after RESOLVED (409) | As listed |
| TC-A90, A91, A92, A113 | Access control | Customer updates (403), admin files (403), unknown id (404), no login (401) | As listed |

## 12. Profile and password
| ID | Technique | Scenario | Expected |
|---|---|---|---|
| TC-A93, A94 | Equivalence partitioning | Update name with spaces around it / empty name | Trimmed name saved / 422 |
| TC-A95 | Functional | Change password | Old password stops working, new one works |
| TC-A96, A97 | Decision table | Wrong current password / new equals current | 400, password unchanged |
| TC-A98, A108 | BVA (min length 6) | 5 characters / 6 characters | 422 / 200 |
| TC-A99 | Security | Change password while a second session is open | Other session signed out, current one kept |
| TC-A100 | Security | Profile calls without login | 401 |
| TC-A101, A102 | Error guessing | Name made only of spaces at registration / in profile | 422 (A101 found DEF-005) |
## 13. UI test cases (Selenium, Microsoft Edge headless)
| ID | Scenario | Expected |
|---|---|---|
| TC-UI01 | Sign in with a wrong password | "Invalid username or password" is shown on the login screen |
| TC-UI02 | Customer opens Estimate and enters 25 kL | "Total: ₹240.00" is shown |
| TC-UI03 | Customer estimates with negative units | A validation error is shown |
| TC-UI04 | Admin signs in | Header shows System Administrator / admin; the menu is exactly Customers, Readings, Bills |
| TC-UI05 | End to end: register; admin opens the New connection popup and creates a connection, uses Add reading twice on the Readings table and generates the bill; customer signs in, opens the payment dialog (₹240.00) and pays | Bill status changes from UNPAID to PAID |
| TC-UI06 | Sign out, then reload the page | Login screen is shown; the session is gone |
| TC-UI07 | Customer signs in | The menu is exactly My bills, Estimate; admin items are not shown |
| TC-UI08 | Customer pays a bill by card, then opens Payments and the receipt | Receipt number, card method, amount ₹240.00 and the meter are shown |
| TC-UI09 | Customer files a leak complaint through the popup; admin opens Complaints, sees all three statuses with only the next one enabled, and moves it forward | Customer sees Open; the dialog lists Open (current, disabled), In progress, Resolved (disabled); the row then shows In progress |
| TC-UI10 | Customer opens Profile, three-dots menu, Change password (first with a mismatching confirmation) | "do not match" message, then a "Password changed" notice; sign-in with the new password works |
| TC-UI11 | Five wrong sign-ins for one account, then the correct password | "locked" message; the correct password is still refused |
| TC-UI12 | Customer opens Profile, three-dots menu, Edit name | New name appears on the profile and in the top bar |
| TC-UI13 | Admin clicks a customer's name on the Customers page | Customer history opens (name, bills, meter readings tab); Back returns to the list |
| TC-UI14 | Admin filters customers by connection type | Commercial shows only commercial customers; Domestic shows only domestic ones |
| TC-UI15 | Admin visits Customers, Readings, Bills, Payments, Complaints | No caption line is shown under any page heading |
| TC-UI16 | Admin opens Readings for a meter that is already billed, then adds a new reading | Generate bill is disabled while billed, enabled after the new reading |
