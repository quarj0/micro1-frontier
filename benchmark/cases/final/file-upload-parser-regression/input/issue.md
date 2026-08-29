# API regression: multipart document uploads return 415

`POST /api/uploads/` stopped accepting normal browser and SDK file uploads after an API parser cleanup. Requests use `multipart/form-data` with a required `file` part and now receive HTTP 415 before validation. Restore the documented upload behavior without changing the list response or stored metadata contract.
