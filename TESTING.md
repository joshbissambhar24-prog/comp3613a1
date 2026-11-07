# COMP 3613 Assignment 2 testing

## Setup

From the project root: `python -m pip install -r requirements.txt`

## pytest

- Unit: `python -m pytest tests/test_unit.py -v`
- Integration: `python -m pytest tests/test_integration.py -v`
- All: `python -m pytest tests -v`

The integration suite injects a fresh in-memory SQLite database per test and uses the FastAPI test client. It does not use the configured production database. Avoid running the real server pointing at a production database when demonstrating Postman tests.

## Postman

Run `python manage.py run` or `uvicorn app.main:app --port 5000` against a disposable local database. Create a student user using the registration page and seed an admin using the project's admin CLI (see `python manage.py --help`). Import `postman/COMP3613_A2.postman_collection.json`. Set `studentUsername`, `studentPassword`, `adminUsername`, and `adminPassword` collection variables. In Postman Runner, keep the requests in order and enable cookies and disable automatic redirects for the two login requests so the cookie assertion can inspect the 303 response. Run the collection and capture the run summary. Never commit actual passwords or tokens. 

## Evidence

Capture unit and integration terminal screenshots after both suites report success, a Postman Runner screenshot showing results, and a UAT session with an actual tester. Complete UAT's actual-result, pass/fail, tester/date fields honestly. PDF currently includes evidence placeholders and is not a claim that any unexecuted tests passed.

## Lecturer-aligned plans and UAT

See `assignment2_docs/LECTURER_ALIGNMENT.md`, `Test_Case_Matrix.csv`, and `UAT_execution_sheet.csv` for the exact lecturer-aligned test planning tables. UAT must be completed by a tester and reports must use real results.
