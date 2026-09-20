# FIRE-UI2.1 selector audit — v0.54

- Status: **PASS**
- Generic selector fields audited: **129**
- Boolean selector fields: **41**
- Enum selector fields: **88**
- Decision selector fields: **66**
- Empty generic option sets: **0**
- Missing option values/labels: **0**
- Duplicate option-value sets: **0**
- Profile catalog dynamic selectors: **37 families / 4069 profiles / 0 empty families**
- Material-strength dynamic selectors: **5 product forms / 0 empty grade sets / 0 empty thickness-interval sets**

The originally reported `section_is_constant` and `moment_plane_is_symmetry` fields now carry explicit `Да/Нет` options in the generated UI contract. The browser also keeps a boolean-specific fallback so an empty legacy `enum_values` array cannot shadow those choices.

`Qy` and torsion `T` remain unimplemented as general production mechanics. In the primary signed-load UI both are visible but disabled and fixed to zero. Non-UI nonzero values remain protected by the existing fail-closed route; no `Qy -> Qz` or `T -> B` substitution is introduced.
