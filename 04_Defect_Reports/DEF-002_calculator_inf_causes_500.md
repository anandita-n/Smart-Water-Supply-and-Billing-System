# DEF-002: Tariff calculator crashes with HTTP 500 for `units=inf`

| Field | Value |
|---|---|
| Module | Tariff calculator (`GET /api/tariff/calculate`) |
| Found by | TC-A54 (API test), run 1 |
| Severity | Medium (unhandled server error, reachable without logging in) |
| Priority | Medium |
| Status | **Closed**: fixed and retested (run 2: TC-A54 passes) |
| Reported by | Vivan Raj Belur |

## Description
The `units` query parameter accepts the float values `inf` and `nan`. The charge becomes infinite and
the JSON response cannot be built, so the server raises an unhandled exception instead of returning a
validation error.

## Steps to reproduce
1. Open `GET /api/tariff/calculate?units=inf` (no login needed).

## Expected result
HTTP 422 validation error, the same as for `units=-1` or `units=abc`.

## Actual result
`ValueError: Out of range float values are not JSON compliant`, an HTTP 500 Internal Server Error.

## Evidence
`06_Test_Reports/run1_baseline.xml`: `test_calculator_invalid_inputs[TC-A54-params3-422]` failed.

## Root cause / proposed fix
Pydantic's float type allows infinity and NaN by default. Restrict the query parameter with
`allow_inf_nan=False` and apply the same restriction to meter reading values.
