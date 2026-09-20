# FIRE-UI1 web frontend

Package-free TypeScript presentation layer for the local FIRE-UI application.

Build with the TypeScript compiler already used by development tooling:

```bash
cd fire_ui1_web
tsc -p tsconfig.json
```

Runtime assets are `index.html`, `styles.css` and materialized `dist/app.js`.
They contain no normative calculation equations and communicate only with the
same-origin `/api/*` adapter from `standard_core.fire_ui1_http`.

SP16-MECH1 (v0.58): primary load authoring uses SP16 Mx/My/Qx/Qy with member axis s; conditional B is entered in a separate guided step. Qy and T remain fail-closed in this release.
