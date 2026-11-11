# Conclusion

We built the Smart Water Supply and Billing System ("AquaBill": FastAPI, SQLite and a web UI) and then
tested it as a team. The testing covered a test plan, 97 designed and executed test cases, defect reporting,
and two automation tools (pytest and Selenium).

**What the testing showed**
- Boundary value analysis of the tariff slabs, late-fee date and alert thresholds confirmed the billing
  rules: all 30 unit tests passed on the first run.
- Error guessing and negative testing found four real defects, all Medium severity:
  - DEF-001: a future-dated meter reading was accepted.
  - DEF-002: `units=inf` crashed the calculator with HTTP 500.
  - DEF-003: login tokens never expired and could not be revoked (no logout).
  - DEF-004: usernames were case-sensitive, so look-alike accounts could be registered.
- Every defect was fixed and retested. The suite went from 87/89 passing on run 1 to 97/97 on the final run.
- Statement coverage reached 99% of the `app` package.

**What we learned**
- Designing tests from the business rules rather than from the code is what exposed the missing
  validations. The tests that failed were the ones written from the expected behaviour.
- Boundary values matter most in money calculations, where a single misplaced `<` versus `<=` changes a bill.
- Automated regression tests made it quick to confirm each fix without breaking other behaviour, including
  when the whole UI was redesigned and the Selenium tests were updated.

**Limitations and future work**
Browser coverage was limited to Edge, there was no load testing, and meter readings are entered manually.
Next steps would be login lock-out after repeated failures, cross-browser UI tests and mutation testing.

Team: S Anandita Narayan (1MS23IS105), Vivan Raj Belur (1MS23IS152)
