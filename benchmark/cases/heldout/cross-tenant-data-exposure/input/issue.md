# Project detail endpoint exposes another tenant's record

Backend logs show that a user in one tenant can request a known project ID belonging to a different tenant and receive HTTP 200 with that project's data. The request includes the caller's tenant in `X-Tenant-ID`, and normal same-tenant project retrieval must continue to work.

Reproduction observed in staging with synthetic tenants:

```text
GET /api/projects/<beta-project-id>/
X-Tenant-ID: <alpha-tenant-id>
=> 200 with Beta project fields
```

Cross-tenant and nonexistent project IDs should both return 404 without exposing project content.
