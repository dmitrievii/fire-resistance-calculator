# v0.59 / SP16-MECH2 release summary

- Explicit `AMBIENT_LOAD_CASE` and `FIRE_LOAD_CASE` introduced.
- Fire actions are either explicitly inherited from ambient or separately entered; silent equality is forbidden.
- Ambient and fire bimoments are independently resolved through the agreed direct-input yes/no policy.
- Machine-readable `SP16_APPLICABILITY_CENSUS` added before the fire action state.
- Action-driven checks are enumerated automatically; context-driven checks remain explicit instead of being silently dropped.
- `Qy` and `T` are visible to the census but remain fail-closed (`SP16-MECH3` / `SP16-MECH4`).
- Existing downstream SP554 scalar quantities remain the fire compatibility contract in this staged release.
- Full ambient `SP16_MECHANICAL_PASS` gate is not yet claimed closed.
