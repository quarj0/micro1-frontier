# Order list database queries grow with every result

`GET /api/orders/` still returns the correct JSON, but query tracing shows the endpoint now performs additional customer and item queries for every order. A synthetic 25-order request executes roughly 51 queries, creating a large latency regression.

Keep the existing response contract and ordering. The number of database queries should remain effectively constant as the number of returned orders grows.
