# COMP 3613 Assignment 2 — Lecturer alignment

**Lecture 3 (Testing.pdf, pages 6–8):** unit tests isolate components using mocks and fixtures; integration tests use a real test database; API tests verify request bodies, response bodies and status codes.

**Tutorial 4 (Test Planning.pdf, page 4):** UAT test form columns are Test Case, Pre-conditions, Test Steps, Test Criteria, Success. `UAT_execution_sheet.csv` preserves these and adds actual result, tester, date and comments for the final report. UAT must be performed with a tester; do not premark success.

**Tutorial 5 (Test implementation.pdf, pages 1–2):** an integration test writes/reads persistent data; test descriptions name the dependencies; the API specification should list description, HTTP method, URL, headers/body, response body and status code.

**Tutorial 3 (SQLAlchemy Revision.pdf, pages 3–4):** entity relationship diagrams should show primary/foreign keys and relationships. Original Assignment 1 schema and diagrams are retained.

**System Design Notes (pages 1–4):** system design diagrams represent hosted application and database, not code libraries, repositories or tests. Assignment 2 asks for use-case diagram, ERD and wireframe, not a new deployment/system architecture diagram.

## Execution

`python -m pip install -r requirements.txt`

`python -m pytest tests/test_unit.py -v`

`python -m pytest tests/test_integration.py -v`

`python -m pytest tests -v`

Follow `TESTING.md` for Postman. Capture actual terminal and Postman Runner screenshots and perform UAT with a real user. No fake screenshots are included.
