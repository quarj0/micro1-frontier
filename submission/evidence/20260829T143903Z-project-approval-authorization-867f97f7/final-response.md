Fixed the approval authorization regression on branch `fix-project-scoped-expense-approval`.

Changes:

- Scoped manager membership checks to the expense’s project in [api/views.py](/tmp/ari-project-approval-authorization-ehbjsqxf/workspace/api/views.py:25).
- Added regression coverage for sibling-project denial and tenant isolation in [api/tests.py](/tmp/ari-project-approval-authorization-ehbjsqxf/workspace/api/tests.py:39).
- Strengthened the successful approval test to verify the complete existing response contract.

Validation: `python manage.py test -v 2` — all 3 tests passed. `git diff --check` also passed. No dev server was started.