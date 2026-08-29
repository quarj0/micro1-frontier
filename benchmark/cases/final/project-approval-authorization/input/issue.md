# API regression: managers can approve expenses outside their project

`POST /api/expenses/{id}/approve/` allows some managers to approve an expense belonging to another project in the same tenant. Manager authority is project-specific: membership in one project must not grant approval rights in a sibling project. Preserve approval for managers assigned to the expense's project, tenant isolation, and the existing response contract.
