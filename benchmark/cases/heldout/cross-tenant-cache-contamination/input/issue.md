# Tenant preferences endpoint returns another tenant's cached settings

`GET /api/preferences/` uses the `X-Tenant-Key` request header. After one tenant loads its preferences, a request from a different tenant can receive the first tenant's theme and support address. The response depends on request order and disappears temporarily when the application cache is cleared.

Preferences must remain isolated per tenant, repeated requests should still benefit from caching, and an unknown tenant must return 404 even when another tenant has warmed the cache.
