# API regression: unrelated accounts collide on idempotency keys

`POST /api/charges/` occasionally returns an existing charge on a customer's first request. Reports occur when two independent accounts use the same `Idempotency-Key`, which is common with SDK-generated retry counters. A key must deduplicate retries within one tenant without allowing another tenant's request to reuse that charge. Preserve the existing same-tenant replay behavior and response contract.
