# Conclusion

We built the Smart Water Supply and Billing System (FastAPI, SQLite and a single-page web UI) and then
tested it as a team. The testing covered a test plan, 89 designed and executed test runs, defect reporting,
and two automation tools (pytest and Selenium).

**What the testing showed**
- Boundary value analysis of the tariff slabs, late-fee date and alert thresholds confirmed the billing
  rules: all 30 unit tests passed on the first run.
- Error guessing found two real defects: a future-dated meter reading was accepted (DEF-001), and
  `units=inf` crashed the calculator with HTTP 500 (DEF-002). Both were fixed and retested, taking the
  suite from 87/89 passing to 89/89.
- A review during test design found that login tokens never expire (DEF-003). We kept this open as a
  known limitation and recommended a fix.
- Statement coverage reached 99% of the `app` package.

**What we learned**
- Designing tests from the business rules first (before looking at the code) is what exposed the missing
  validations. The tests that failed were the ones we wrote from the expected behaviour.
- Boundary values matter most in money calculations, where a single misplaced `<` versus `<=` changes a bill.
- Automated regression tests made it quick to confirm each fix without breaking other behaviour.

**Limitations and future work**
Browser coverage was limited to Edge, there was no load testing, and meter readings are entered manually.
Next steps would be token expiry and logout, cross-browser UI tests and mutation testing.

Team: S Anandita Narayan (1MS23IS105), Vivan Raj Belur (1MS23IS152)
