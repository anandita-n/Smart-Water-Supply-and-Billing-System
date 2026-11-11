# Conclusion

We built the Smart Water Supply and Billing System ("AquaBill": FastAPI, SQLite and a web UI) and then
tested it as a team. The testing covered a test plan, 173 designed and executed test cases, defect reporting,
and two automation tools (pytest and Selenium).

**What the testing showed**
- Boundary value analysis of the tariff slabs, late-fee date and alert thresholds confirmed the billing
  rules: all 30 billing unit tests passed on the first run.
- Error guessing and negative testing found five real defects (four Medium, one Low):
  - DEF-001: a future-dated meter reading was accepted.
  - DEF-002: `units=inf` crashed the calculator with HTTP 500.
  - DEF-003: login tokens never expired and could not be revoked (no logout).
  - DEF-004: usernames were case-sensitive, so look-alike accounts could be registered.
  - DEF-005: a name made only of spaces was accepted at registration.
- Every defect was fixed and retested. The suite went from 87/89 passing on run 1 to 173/173 on the final run.
- Statement coverage reached 98% of the `app` package.
- Four modules were added late (payment receipts, login lock-out, complaints, profile and password change).
  Writing their tests from the rules first meant 56 of the 57 new test cases passed immediately and the one
  failure pointed at an older, shared validation gap (DEF-005).

**What we learned**
- Designing tests from the business rules rather than from the code is what exposed the missing
  validations. The tests that failed were the ones written from the expected behaviour.
- Boundary values matter most in money calculations, where a single misplaced `<` versus `<=` changes a bill.
- State-transition thinking found real rules to test in three places: the bill life cycle, the complaint life
  cycle and the account lock-out.
- Automated regression tests made it quick to confirm each fix without breaking other behaviour, including
  when the UI was redesigned twice and the Selenium tests were updated.
- A subtle implementation detail matters for security rules: the failed-login counter had to be saved before
  the error was raised, otherwise the database rolled it back and the lock-out would never trigger. TC-A73
  would catch that mistake.

**Limitations and future work**
Browser coverage was limited to Edge, there was no load testing, meter readings are entered manually and no
real payment gateway is connected. Next steps would be PDF receipts, cross-browser UI tests and mutation testing.

Team: S Anandita Narayan (1MS23IS105), Vivan Raj Belur (1MS23IS152)
