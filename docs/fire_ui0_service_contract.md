# FIRE-UI0 local service contract

FIRE-UI0 intentionally has no FastAPI/Streamlit dependency. `GuidedCalculationService`
is the application service to expose later through a thin local HTTP adapter.

Recommended future routes:

```text
GET  /api/ui-contract
POST /api/sessions
GET  /api/sessions/{id}
POST /api/sessions/{id}/answer
PUT  /api/sessions/{id}/answers/{node_id}
GET  /api/sessions/{id}/ledger
GET  /api/sessions/{id}/trace
POST /api/sessions/{id}/report
```

The browser frontend must not contain SP16/SP554 formula implementations.
It only renders the returned question cards, ledger and trace.

Deployment target for the first usable calculator:

```text
local launcher
  → Python process on 127.0.0.1
  → thin HTTP adapter
  → browser React/TypeScript UI
```

No public server is required for sequential acceptance testing.
