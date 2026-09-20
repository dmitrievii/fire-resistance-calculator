"""Stage N2 interim section/profile catalog for СП 16.13330.2017 workflows.

The catalog is intentionally split into two provenance layers:

* the *row data* are imported from the historical NormCAD profile MDB so existing
  calculation branches can be exercised now;
* quantities that are mathematical/normative derivatives are recomputed at runtime
  and never copied blindly from known-corrupt NormCAD fields.

Every imported profile remains ``PENDING_ORIGINAL_GOST_AUDIT``.  The deferred audit
against the original product standards is a release gate for the final SP16 package,
not for this Stage N2 runtime integration.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from .section_model import CURRENT_SP16_SOURCE_SHA256, SectionPropertyModel


INTERIM_CATALOG_STATUS = "INTERIM_IMPORTED_FROM_NORMCAD_PENDING_ORIGINAL_GOST_AUDIT"
ORIGINAL_GOST_AUDIT_COMPLETE = False

TABLE7_COEFFICIENTS: dict[str, dict[str, float]] = {
    "a": {"alpha": 0.03, "beta": 0.06, "phi_cap_lambda_bar_threshold": 3.8},
    "b": {"alpha": 0.04, "beta": 0.09, "phi_cap_lambda_bar_threshold": 4.4},
    "c": {"alpha": 0.04, "beta": 0.14, "phi_cap_lambda_bar_threshold": 5.8},
}


def _default_data_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "profile_catalog_interim_v0_28_stage_n2.json"


def _default_registry_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "profile_family_registry_v0_28_stage_n2.json"


def _finite_positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0.0


def _numbers(text: str) -> list[float]:
    return [float(token.replace(",", ".")) for token in re.findall(r"\d+(?:[\.,]\d+)?", text)]


def _table7_bundle(section_type: str, *, rule: str, evidence: str) -> dict[str, Any]:
    if section_type not in TABLE7_COEFFICIENTS:
        raise ValueError(f"unsupported Table 7 section type: {section_type!r}")
    return {
        "section_type": section_type,
        **TABLE7_COEFFICIENTS[section_type],
        "classification_rule": rule,
        "evidence": evidence,
        "normative_reference": "СП 16.13330.2017, 7.1.3, таблица 7 (ред. Изменения №6)",
        "source_sha256": CURRENT_SP16_SOURCE_SHA256,
    }


class InterimProfileCatalog:
    """
    Summary:
        Runtime-capable interim profile catalog imported from the historical NormCAD section database.

    Standard reference:
        СП 16.13330.2017 Table 7 and Annex D are used only for quantities recomputed by this adapter;
        profile-row geometry/properties remain pending reconciliation with their original product standards.

    Fields:
        data_path and registry_path identify the frozen interim catalog and family-classification datasets;
        resolved bundles expose source identity, catalog properties, recomputed quantities and Table 7 routing.

    Validation:
        Stage N2 verifies 4069 rows across 37 families, duplicate-key fail-closed behavior, positive runtime
        quantities, recomputed mass/radii/torsion policies and representative Table 7 assignments.

    Used by:
        standard_core.runner profile_catalog_resolve and profile_ref hydration for existing SP16 calculation routes.
    """

    def __init__(self, data_path: str | Path | None = None, registry_path: str | Path | None = None) -> None:
        self.data_path = Path(data_path) if data_path is not None else _default_data_path()
        self.registry_path = Path(registry_path) if registry_path is not None else _default_registry_path()
        self._payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        self._registry_payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        if self._payload.get("status") != INTERIM_CATALOG_STATUS:
            raise ValueError("unexpected interim profile catalog status")
        if self._payload.get("original_gost_audit_complete") is not False:
            raise ValueError("interim catalog must preserve the deferred original-GOST audit gate")
        if self._payload.get("profile_count") != 4069 or self._payload.get("family_count") != 37:
            raise ValueError("unexpected interim profile catalog cardinality")
        self._families = {int(x["family_id"]): x for x in self._registry_payload["families"]}
        self._rows: dict[tuple[int, str], list[Mapping[str, Any]]] = {}
        for row in self._payload["profiles"]:
            key = (int(row["family_id"]), str(row["designation"]))
            self._rows.setdefault(key, []).append(row)

    @property
    def profile_count(self) -> int:
        return int(self._payload["profile_count"])

    @property
    def family_count(self) -> int:
        return len(self._families)

    def list_families(self) -> list[dict[str, Any]]:
        return [deepcopy(self._families[k]) for k in sorted(self._families)]

    def list_profiles(self, family_id: int) -> list[dict[str, Any]]:
        """List selectable rows, preserving source-row identity for duplicate designations."""
        fid = int(family_id)
        if fid not in self._families:
            raise KeyError(f"unknown family_id={fid}")
        result: list[dict[str, Any]] = []
        for (row_fid, designation), rows in self._rows.items():
            if row_fid != fid:
                continue
            for row in rows:
                result.append({
                    "designation": designation,
                    "source_row_id": int(row["source_row_id"]),
                    "h_mm": row["h_mm"], "b_mm": row["b_mm"],
                    "tw_mm": row["tw_mm"], "tf_mm": row["tf_mm"],
                })
        return sorted(result, key=lambda x: (x["designation"], x["source_row_id"]))

    def family(self, family_id: int) -> dict[str, Any]:
        try:
            return deepcopy(self._families[int(family_id)])
        except KeyError as exc:
            raise KeyError(f"unknown family_id={family_id}") from exc

    def _row(self, family_id: int, designation: str, source_row_id: int | None = None) -> dict[str, Any]:
        key = (int(family_id), str(designation))
        rows = self._rows[key] if key in self._rows else []
        if not rows:
            raise KeyError(f"profile not found: family_id={family_id}, designation={designation!r}")
        if source_row_id is not None:
            rows = [r for r in rows if int(r["source_row_id"]) == int(source_row_id)]
            if not rows:
                raise KeyError(
                    f"profile row not found: family_id={family_id}, designation={designation!r}, source_row_id={source_row_id}"
                )
        if len(rows) != 1:
            ids = [int(r["source_row_id"]) for r in rows]
            raise ValueError(
                f"ambiguous profile designation: family_id={family_id}, designation={designation!r}; "
                f"specify source_row_id from {ids}"
            )
        return deepcopy(dict(rows[0]))

    @staticmethod
    def _alpha_f(shape_group: str, row: Mapping[str, Any]) -> tuple[float | None, float | None, str | None]:
        h = float(row["h_mm"])
        b = float(row["b_mm"])
        tw = float(row["tw_mm"])
        tf = float(row["tf_mm"])
        if shape_group == "I_ROLLED_DSYMM" or shape_group == "CHANNEL":
            hw = h - 2.0 * tf
            if hw <= 0.0:
                return None, None, None
            ax = tf * b / (tw * hw)
            ay = tw * hw / (2.0 * tf * b)
            return ax, ay, "Af/Aw from nominal flange/web dimensions; x: b*tf/[tw*(h-2tf)], y: reciprocal two-flange convention"
        if shape_group == "TEE":
            hw = h - tf
            if hw <= 0.0:
                return None, None, None
            ax = tf * b / (tw * hw)
            ay = tw * hw / (tf * b)
            return ax, ay, "Af/Aw from nominal tee flange/web dimensions"
        if shape_group == "RHS_SHS":
            ax = tf * b / (2.0 * tw * h)
            ay = tw * h / (2.0 * tf * b)
            return ax, ay, "Af/Aw box-section convention from nominal dimensions"
        return None, None, None

    @staticmethod
    def _open_thinwall_it_from_designation(shape_group: str, designation: str) -> dict[str, Any] | None:
        nums = _numbers(designation)
        if shape_group == "ANGLE":
            if len(nums) == 2:
                leg, t = nums
                a, b = leg, leg
            elif len(nums) >= 3:
                a, b, t = nums[-3], nums[-2], nums[-1]
            else:
                return None
            centerline_sum = a + b - t
        elif shape_group == "Z_SECTION":
            if len(nums) < 3:
                return None
            h, b, t = nums[-3], nums[-2], nums[-1]
            centerline_sum = h + 2.0 * b - 2.0 * t
        elif shape_group == "C_LIPPED_SECTION":
            if len(nums) < 4:
                return None
            h, b, lip, t = nums[-4], nums[-3], nums[-2], nums[-1]
            centerline_sum = h + 2.0 * b + 2.0 * lip - 4.0 * t
        else:
            return None
        if min(centerline_sum, t) <= 0.0:
            return None
        return {
            "torsional_inertia_mm4": centerline_sum * t**3 / 3.0,
            "torsion_policy": "GEOMETRY_DERIVED_OPEN_THIN_WALL_APPROXIMATION_PENDING_ORIGINAL_GOST_AUDIT",
            "calculation_detail": {"centerline_length_sum_mm": centerline_sum, "thickness_mm": t},
        }

    @staticmethod
    def _closed_rhs_it(row: Mapping[str, Any]) -> dict[str, Any] | None:
        h = float(row["h_mm"])
        b = float(row["b_mm"])
        tw = float(row["tw_mm"])
        tf = float(row["tf_mm"])
        bm = b - tw
        hm = h - tf
        denom = 2.0 * bm / tf + 2.0 * hm / tw
        am = bm * hm
        if min(bm, hm, denom, am) <= 0.0:
            return None
        return {
            "torsional_inertia_mm4": 4.0 * am**2 / denom,
            "torsion_policy": "GEOMETRY_DERIVED_CLOSED_THIN_WALL_BREDT_APPROXIMATION_PENDING_ORIGINAL_GOST_AUDIT",
            "calculation_detail": {"median_width_mm": bm, "median_height_mm": hm, "wall_integral_sum_s_over_t": denom},
        }

    @classmethod
    def _torsion(cls, family: Mapping[str, Any], row: Mapping[str, Any]) -> dict[str, Any]:
        group = str(family["shape_group"])
        h = float(row["h_mm"])
        b = float(row["b_mm"])
        tw = float(row["tw_mm"])
        tf = float(row["tf_mm"])

        if group == "I_ROLLED_DSYMM":
            result = SectionPropertyModel.annex_d_free_torsion_inertia_mm4(
                "i_doubly_symmetric", [(h - 2.0 * tf, tw), (b, tf), (b, tf)]
            )
            return {
                "torsional_inertia_mm4": result["I_t_sp16_annex_d_mm4"],
                "torsion_policy": "CURRENT_SP16_ANNEX_D_FORMULA",
                "annex_d_k": result["k"],
                "calculation_detail": result,
            }
        if group == "TEE":
            result = SectionPropertyModel.annex_d_free_torsion_inertia_mm4(
                "tee", [(h - tf, tw), (b, tf)]
            )
            return {
                "torsional_inertia_mm4": result["I_t_sp16_annex_d_mm4"],
                "torsion_policy": "CURRENT_SP16_ANNEX_D_FORMULA",
                "annex_d_k": result["k"],
                "calculation_detail": result,
            }
        if group == "CHANNEL":
            result = SectionPropertyModel.annex_d_free_torsion_inertia_mm4(
                "channel", [(h - 2.0 * tf, tw), (b, tf), (b, tf)]
            )
            return {
                "torsional_inertia_mm4": result["I_t_sp16_annex_d_mm4"],
                "torsion_policy": "CURRENT_SP16_ANNEX_D_FORMULA",
                "annex_d_k": result["k"],
                "calculation_detail": result,
            }
        if group == "CHS":
            # For a circular section, polar second moment J = Ix + Iy exactly.
            return {
                "torsional_inertia_mm4": float(row["Ix_mm4"]) + float(row["Iy_mm4"]),
                "torsion_policy": "GEOMETRY_IDENTITY_CIRCULAR_J_EQUALS_IX_PLUS_IY",
                "annex_d_k": None,
                "calculation_detail": None,
            }
        if group == "RHS_SHS":
            computed = cls._closed_rhs_it(row)
            if computed is not None:
                computed["annex_d_k"] = None
                return computed
        computed_open = cls._open_thinwall_it_from_designation(group, str(row["designation"]))
        if computed_open is not None:
            computed_open["annex_d_k"] = None
            return computed_open

        legacy = row.get("historical_it_mm4")
        if _finite_positive(legacy) and float(legacy) < 1e12:
            return {
                "torsional_inertia_mm4": float(legacy),
                "torsion_policy": "INTERIM_HISTORICAL_CATALOG_FALLBACK_PENDING_ORIGINAL_GOST_AUDIT",
                "annex_d_k": None,
                "calculation_detail": None,
            }
        return {
            "torsional_inertia_mm4": None,
            "torsion_policy": "UNRESOLVED_FAIL_CLOSED",
            "annex_d_k": None,
            "calculation_detail": None,
        }

    @staticmethod
    def _table7_for_axis(family: Mapping[str, Any], row: Mapping[str, Any], axis: str) -> dict[str, Any]:
        axis_norm = str(axis).lower()
        if axis_norm not in {"x", "y"}:
            raise ValueError("axis must be 'x' or 'y'")
        rule = family["table7_rule"]
        if rule == "ROLLED_I_X_B_OR_A_GT500_Y_C":
            if axis_norm == "x":
                section_type = "a" if float(row["h_mm"]) > 500.0 else "b"
                evidence = "Table 7 rolled-I web-plane mapping with Note 1 h>500 override"
            else:
                section_type = "c"
                evidence = "Table 7 rolled-I minor-stiffness-plane mapping shown by the normative section forms"
        else:
            section_type = str(family[f"table7_type_{axis_norm}"])
            evidence = str(family["table7_evidence"])
        return _table7_bundle(section_type, rule=str(rule), evidence=evidence)

    def resolve(self, family_id: int, designation: str, *, source_row_id: int | None = None) -> dict[str, Any]:
        row = self._row(family_id, designation, source_row_id)
        family = self.family(family_id)
        area = float(row["A_mm2"])
        ix = float(row["Ix_mm4"])
        iy = float(row["Iy_mm4"])
        if not all(_finite_positive(v) for v in (area, ix, iy)):
            raise ValueError("interim profile has invalid primary A/I data")
        rx = SectionPropertyModel.radius_of_gyration_mm(ix, area)
        ry = SectionPropertyModel.radius_of_gyration_mm(iy, area)
        alpha_x, alpha_y, alpha_note = self._alpha_f(str(family["shape_group"]), row)
        torsion = self._torsion(family, row)
        result = {
            "profile_ref": {
                "family_id": int(family_id), "designation": str(designation),
                "source_row_id": int(row["source_row_id"]),
            },
            "catalog_status": INTERIM_CATALOG_STATUS,
            "original_gost_audit_complete": False,
            "original_gost_audit_gate": "DEFERRED_TO_FINAL_PACKAGE_PROFILE_AUDIT",
            "source": {
                "imported_from": "NormCAD historical profile MDB capture",
                "normcad_source_sha256": self._payload["normcad_source_sha256"],
                "row_id": row["source_row_id"],
                "family_caption": family["caption"],
                "product_standard_label_unverified": family.get("product_standard_label_unverified"),
            },
            "family": family,
            "designation": row["designation"],
            "shape_group": family["shape_group"],
            "dimensions": {
                "h_mm": row["h_mm"], "b_mm": row["b_mm"], "tw_mm": row["tw_mm"],
                "tf_mm": row["tf_mm"], "r_mm": row.get("r_mm"),
            },
            "catalog_properties_interim": {
                "A_mm2": area,
                "Ix_mm4": ix,
                "Iy_mm4": iy,
                "Wx1_mm3": row["Wx1_mm3"], "Wx2_mm3": row["Wx2_mm3"],
                "Wy1_mm3": row["Wy1_mm3"], "Wy2_mm3": row["Wy2_mm3"],
                "Sx_mm3": row.get("Sx_mm3"), "Sy_mm3": row.get("Sy_mm3"),
            },
            "derived_properties": {
                "mass_kg_m_at_7850": SectionPropertyModel.mass_kg_m_from_area(area),
                "radius_x_mm": rx,
                "radius_y_mm": ry,
                "minimum_radius_mm": min(rx, ry),
                "minimum_section_modulus_x_mm3": min(float(row["Wx1_mm3"]), float(row["Wx2_mm3"])),
                "minimum_section_modulus_y_mm3": min(float(row["Wy1_mm3"]), float(row["Wy2_mm3"])),
                "alpha_f_x": alpha_x,
                "alpha_f_y": alpha_y,
                "alpha_f_calculation_note": alpha_note,
                **torsion,
            },
            "sp16_table7": {
                "x": self._table7_for_axis(family, row, "x"),
                "y": self._table7_for_axis(family, row, "y"),
            },
            "historical_fields_not_used_as_runtime_truth": {
                "mass_kg_m_db": row.get("historical_mass_kg_m"),
                "It_mm4_db": row.get("historical_it_mm4"),
                "afwx_db": row.get("historical_afwx"),
                "afwy_db": row.get("historical_afwy"),
            },
        }
        return result

    def resolve_for_axis(
        self, family_id: int, designation: str, axis: str = "x", *, source_row_id: int | None = None
    ) -> dict[str, Any]:
        bundle = self.resolve(family_id, designation, source_row_id=source_row_id)
        axis_norm = axis.lower()
        if axis_norm not in {"x", "y"}:
            raise ValueError("axis must be 'x' or 'y'")
        p = bundle["catalog_properties_interim"]
        d = bundle["derived_properties"]
        t7 = bundle["sp16_table7"][axis_norm]
        inertia = p["Ix_mm4"] if axis_norm == "x" else p["Iy_mm4"]
        radius = d["radius_x_mm"] if axis_norm == "x" else d["radius_y_mm"]
        modulus = d["minimum_section_modulus_x_mm3"] if axis_norm == "x" else d["minimum_section_modulus_y_mm3"]
        return {
            **bundle,
            "selected_axis": axis_norm,
            "selected_axis_properties": {
                "second_moment_mm4": inertia,
                "radius_of_gyration_mm": radius,
                "minimum_section_modulus_mm3": modulus,
                "table7_section_type": t7["section_type"],
                "table7_alpha": t7["alpha"],
                "table7_beta": t7["beta"],
            },
        }


def hydrate_case_with_profile(
    case_data: Mapping[str, Any],
    profile_bundle: Mapping[str, Any],
    *,
    axis: str = "x",
    overwrite: bool = False,
    use_gross_as_net: bool = False,
    allowed_fields: set[str] | None = None,
) -> dict[str, Any]:
    """
    Summary:
        Hydrate only section-derived inputs of an existing calculation case from an explicitly selected profile.

    Standard reference:
        СП 16.13330.2017 section-property symbols, Table 7 section-type coefficients and Annex D torsion route;
        imported profile values themselves remain pending original product-standard audit.

    Parameters:
        case_data: Existing action input mapping.
        profile_bundle: Result returned by InterimProfileCatalog.resolve/resolve_for_axis.
        axis: Selected x or y section axis.
        overwrite: Whether existing section-derived case fields may be replaced.
        use_gross_as_net: Explicit caller assertion that gross properties may be used as net properties.
        allowed_fields: Optional action-schema field whitelist.

    Returns:
        A new dictionary with permitted section-derived values added; non-section engineering inputs are untouched.

    Assumptions:
        The caller has selected the intended profile row and is responsible for any net-section/weakening assertion.

    Sign convention:
        Section magnitudes are positive; no load/action signs are generated by this function.

    Unit convention:
        Geometry uses mm, area mm2, section moduli mm3 and second/torsional moments mm4.

    Applicability:
        Existing runner actions whose schemas expose compatible section-property fields.

    Limitations:
        Does not infer loads, effective lengths, material strengths, working-condition factors, applicability or
        original-GOST validity of the selected interim profile row.

    Raises:
        ValueError for an unsupported axis or incompatible profile bundle content.

    Examples:
        ``hydrate_case_with_profile(case, catalog.resolve(35, "15К4"), axis="x")``

    Tests:
        tests/test_stage_n2_interim_profile_catalog.py

    Implementation notes:
        Hydration is fail-closed for absent/ambiguous profile rows and writes only explicit schema-allowed fields.
    """

    out = dict(case_data)
    p = profile_bundle["catalog_properties_interim"]
    d = profile_bundle["derived_properties"]
    dims = profile_bundle["dimensions"]
    t7 = profile_bundle["sp16_table7"]
    axis_norm = axis.lower()
    if axis_norm not in {"x", "y"}:
        raise ValueError("axis must be 'x' or 'y'")

    ix = float(p["Ix_mm4"]); iy = float(p["Iy_mm4"])
    rx = float(d["radius_x_mm"]); ry = float(d["radius_y_mm"])
    selected_i = ix if axis_norm == "x" else iy
    selected_r = rx if axis_norm == "x" else ry
    major_i, minor_i = (ix, iy) if ix >= iy else (iy, ix)
    major_r, minor_r = (rx, ry) if ix >= iy else (ry, rx)

    common = {
        "gross_area_mm2": p["A_mm2"],
        "gross_or_reduced_area_mm2": p["A_mm2"],
        "area_mm2": p["A_mm2"],
        "major_axis_inertia_mm4": major_i,
        "minor_axis_inertia_mm4": minor_i,
        "major_inertia_mm4": major_i,
        "gross_second_moment_area_mm4": selected_i,
        "gross_section_moment_inertia_mm4": selected_i,
        "inertia_x_mm4": ix,
        "inertia_y_mm4": iy,
        "compressed_section_modulus_x_mm3": d["minimum_section_modulus_x_mm3"],
        "compressed_section_modulus_y_mm3": d["minimum_section_modulus_y_mm3"],
        "compressed_major_section_modulus_mm3": max(d["minimum_section_modulus_x_mm3"], d["minimum_section_modulus_y_mm3"]),
        "compressed_minor_section_modulus_mm3": min(d["minimum_section_modulus_x_mm3"], d["minimum_section_modulus_y_mm3"]),
        "compressed_fibre_section_modulus_mm3": d["minimum_section_modulus_x_mm3"] if axis_norm == "x" else d["minimum_section_modulus_y_mm3"],
        "section_height_mm": dims["h_mm"],
        "web_thickness_mm": dims["tw_mm"],
        "full_web_height_mm": max(float(dims["h_mm"]) - 2.0 * float(dims["tf_mm"]), 1e-12),
        "flange_width_mm": dims["b_mm"],
        "flange_thickness_mm": dims["tf_mm"],
        "major_axis_radius_mm": major_r,
        "minor_axis_radius_mm": minor_r,
        "radius_x_mm": rx,
        "radius_y_mm": ry,
        "table7_section_type_x": t7["x"]["section_type"],
        "table7_section_type_y": t7["y"]["section_type"],
        "radius_of_gyration_mm": selected_r,
        "selected_radius_of_gyration_mm": selected_r,
        "torsional_inertia_mm4": d["torsional_inertia_mm4"],
        "first_moment_area_x_mm3": p["Sx_mm3"],
        "first_moment_area_y_mm3": p["Sy_mm3"],
        "first_moment_area_mm3": p["Sx_mm3"] if axis_norm == "x" else p["Sy_mm3"],
        "web_area_mm2": float(dims["tw_mm"]) * max(float(dims["h_mm"]) - 2.0 * float(dims["tf_mm"]), 1e-12),
        "one_flange_area_mm2": float(dims["b_mm"]) * float(dims["tf_mm"]),
        "flange_axis_spacing_mm": max(float(dims["h_mm"]) - float(dims["tf_mm"]), 1e-12),
        "effective_web_height_mm": max(
            float(dims["h_mm"]) - 2.0 * (float(dims["tf_mm"]) + float(dims.get("r_mm") or 0.0)),
            1e-12,
        ) if profile_bundle.get("shape_group") == "I_ROLLED_DSYMM" else max(float(dims["h_mm"]) - 2.0 * float(dims["tf_mm"]), 1e-12),
        "section_type": t7[axis_norm]["section_type"],
        "branch_section_type": t7[axis_norm]["section_type"],
        "flange_to_web_area_ratio": d["alpha_f_x"] if axis_norm == "x" else d["alpha_f_y"],
        "annex_d2_flange_to_web_area_ratio_x": d["alpha_f_x"],
        "annex_d2_flange_to_web_area_ratio_y": d["alpha_f_y"],
    }

    if use_gross_as_net:
        common.update({
            "net_area_mm2": p["A_mm2"],
            "minimum_net_section_modulus_x_mm3": d["minimum_section_modulus_x_mm3"],
            "minimum_net_section_modulus_y_mm3": d["minimum_section_modulus_y_mm3"],
            "net_inertia_x_mm4": ix,
            "net_inertia_y_mm4": iy,
            "high_strength_gross_area_mm2": p["A_mm2"],
            "high_strength_net_area_mm2": p["A_mm2"],
        })

    action = str(out["action"]) if "action" in out else ""
    if action == "crane_runway_and_bending_stability":
        web_h = max(float(dims["h_mm"]) - 2.0 * float(dims["tf_mm"]), 0.0)
        common.update({
            "web_area_mm2": float(dims["tw_mm"]) * web_h,
            "compressed_flange_area_mm2": float(dims["b_mm"]) * float(dims["tf_mm"]),
            "compressed_flange_width_mm": dims["b_mm"],
            "compressed_flange_thickness_mm": dims["tf_mm"],
            "compressed_flange_radius_of_gyration_mm": minor_r,
        })

    for key, value in common.items():
        if value is None:
            continue
        if allowed_fields is not None and key not in allowed_fields:
            continue
        if overwrite or key not in out:
            out[key] = value
    return out

