# STO ARSS 11251254.001-018-03 fire-protection thermal-property library

FIRE-UI2.2 adds a source-traced library for the table **«Теплофизические характеристики огнезащитных материалов»** supplied by the project owner from STO ARSS 11251254.001-018-03.

The source table defines:

- thermal conductivity: `lambda(t) = A + B*t`;
- heat capacity: `c(t) = C + D*t`;
- the printed dependencies are valid for `t >= 273 K`.

The package therefore stores the printed coefficients in their original **kelvin basis**. The SP554 thermal solver, whose state temperatures are represented in degrees Celsius, converts the intercepts algebraically before use:

- `A_degC = A_K + B*273.15`;
- `C_degC = C_K + D*273.15`;
- slopes `B` and `D` are unchanged.

No coefficient is silently reinterpreted as a Celsius-based source coefficient.

## Library rows

| Material | rho, kg/m3 | W, % | emissivity | lambda(t), W/(m K) | c(t), J/(kg K) |
| --- | ---: | ---: | ---: | --- | --- |
| Cement-sand plaster | 1930 | 2.0 | 0.87 | `0.96 - 0.00044*t` | `598 + 0.63*t` |
| Dry gypsum plaster (GKL/GVL/KNAUF-Fireboard) | 900 | 15.0 | 0.86 | `0.135 + 0.00035*t` | `849 + 0.59*t` |
| Cellular concrete / foam concrete | 600 | 2.0 | 0.80 | `0.041 + 0.00019*t` | `748 + 0.63*t` |
| Mineral-wool boards | **100** | 0.5 | 0.92 | `-0.107 + 0.00058*t` | `582 + 0.63*t` |

For mineral-wool boards the printed source density is **80-100 kg/m3**. By explicit project decision for FIRE-UI2.2 the active library value is fixed to **100 kg/m3**. The printed 80-100 range remains retained in the dataset provenance and is not presented as a free density field for the library row.

A capture of the source table supplied by the project owner is retained at:

`docs/source_evidence/STO_ARSS_11251254_001_018_03_thermal_properties_table_user_capture.jpg`

## Scope boundary

Selecting a STO ARSS library material supplies intrinsic material properties only. It does **not** fabricate SP554 clause 12.6 validation evidence for a generated fire-protection performance dataset. That validation gate remains independent and fail-closed.
