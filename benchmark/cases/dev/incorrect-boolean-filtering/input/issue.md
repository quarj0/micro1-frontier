# `active=false` returns active integrations

`GET /api/integrations/?active=false` should return only disabled integrations. It currently returns only active integrations, while an omitted `active` parameter correctly returns all integrations.

The endpoint must support the documented case-insensitive values `true` and `false`. Unsupported values must return HTTP 400 rather than silently selecting a group.

All benchmark data is synthetic.

