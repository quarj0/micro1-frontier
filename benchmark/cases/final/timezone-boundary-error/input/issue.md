# API regression: calendar day results cross local boundaries

`GET /api/events/?date=YYYY-MM-DD&timezone=Area/City` returns events from the previous local day and omits late-evening events for non-UTC users. The problem is especially visible on daylight-saving transition dates. The requested date represents a calendar day in the supplied IANA timezone; keep the existing response shape and UTC behavior.
