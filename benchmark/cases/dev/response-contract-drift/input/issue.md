# Profile response field changed unexpectedly

`GET /api/profile/` still returns HTTP 200, but clients generated from our API contract can no longer read the user's display name.

Expected response:

```json
{"id": 7, "display_name": "Ada Lovelace", "email": "ada@example.test"}
```

Observed response:

```json
{"id": 7, "name": "Ada Lovelace", "email": "ada@example.test"}
```

Restore the established response contract without exposing additional profile fields.

