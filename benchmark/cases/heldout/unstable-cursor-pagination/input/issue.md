# Audit export cursor skips events with identical timestamps

Clients following `next_cursor` from `GET /api/audit-events/` sometimes finish without receiving every event. This happens when several events share the same `created_at` value, which is common after batch imports. Replaying the same traversal should return every event exactly once in a deterministic newest-first order.

The endpoint uses a page size of two and returns:

```json
{"results": [...], "next_cursor": "..."}
```

Malformed cursors should continue to return HTTP 400.
