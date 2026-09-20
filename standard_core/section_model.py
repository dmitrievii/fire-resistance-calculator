"""Stage N2 section-property model and historical NormCAD catalog adapter.

The module separates three different concepts that must not be conflated:

1. exact/analytic properties derived from an explicitly supplied 2-D geometry;
2. catalogue properties coming from an external product standard;
3. СП 16 computational section quantities, in particular the Annex D value of
   ``I_t = (k/3) * sum(b_i*t_i**3)`` used by the normative stability routes.

NormCAD data exposed by :class:`HistoricalNormCADProfileCatalog` are historical
secondary-oracle evidence only and are fail-closed for production use.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CURRENT_SP16_SOURCE_SHA256 = "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


@dataclass(frozen=True)
class GrossSectionProperties:
    """
    Summary:
        Canonical gross-section property bundle derived from explicit idealized geometry.

    Standard reference:
        Geometric support model for СП 16 section-property inputs; it is not a product-standard catalog row.

    Fields:
        Area, second moments, section moduli, optional static moments/radii/mass, geometry-model identity and provenance.

    Validation:
        Stage N2 analytic identities are checked for rectangle, RHS/SHS, I-section, solid circle and CHS models.

    Used by:
        SectionPropertyModel geometry routines and downstream validation/comparison helpers.
    """

    area_mm2: float
    ix_mm4: float
    iy_mm4: float
    wx_pos_mm3: float
    wx_neg_mm3: float
    wy_pos_mm3: float
    wy_neg_mm3: float
    sx_mm3: float | None = None
    sy_mm3: float | None = None
    radius_x_mm: float | None = None
    radius_y_mm: float | None = None
    mass_kg_m_at_7850: float | None = None
    geometry_model: str = ""
    provenance: str = "GEOMETRY_DERIVED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SectionPropertyModel:
    """
    Summary:
        Deterministic section-property primitives and explicit current-SP16 Annex D torsion calculations for Stage N2.

    Standard reference:
        СП 16.13330.2017 section-property notation and Annex D expression It=(k/3)Σ(b_i t_i^3); analytic geometry
        helpers are mathematical identities, not substitutes for product-standard catalog certification.

    Fields:
        Steel density constant and Annex D k-registry for supported open-section families.

    Validation:
        Stage N2 unit tests exercise exact geometric identities, domains, k mapping, It separation and provenance.

    Used by:
        InterimProfileCatalog, historical comparator evidence and downstream SP16 section-property hydration.
    """

    STEEL_DENSITY_KG_M3 = 7850.0
    _ANNEX_D_K = {
        "i_doubly_symmetric": 1.29,
        "i_singly_symmetric": 1.25,
        "tee": 1.20,
        "channel": 1.12,
        "p_section": 1.12,
    }

    @staticmethod
    def _positive(name: str, value: float) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric")
        result = float(value)
        if not math.isfinite(result) or result <= 0.0:
            raise ValueError(f"{name} must be finite and > 0")
        return result

    @classmethod
    def radius_of_gyration_mm(cls, second_moment_mm4: float, area_mm2: float) -> float:
        """Return ``sqrt(I/A)`` for a positive area and second moment."""

        inertia = cls._positive("second_moment_mm4", second_moment_mm4)
        area = cls._positive("area_mm2", area_mm2)
        return math.sqrt(inertia / area)

    @classmethod
    def mass_kg_m_from_area(cls, area_mm2: float, density_kg_m3: float | None = None) -> float:
        """Convert cross-sectional area to linear mass using an explicit density."""

        area = cls._positive("area_mm2", area_mm2)
        density = cls.STEEL_DENSITY_KG_M3 if density_kg_m3 is None else cls._positive("density_kg_m3", density_kg_m3)
        return area * 1e-6 * density

    @classmethod
    def rectangle(cls, width_mm: float, height_mm: float) -> GrossSectionProperties:
        b = cls._positive("width_mm", width_mm)
        h = cls._positive("height_mm", height_mm)
        area = b * h
        ix = b * h**3 / 12.0
        iy = h * b**3 / 12.0
        return GrossSectionProperties(
            area_mm2=area,
            ix_mm4=ix,
            iy_mm4=iy,
            wx_pos_mm3=2.0 * ix / h,
            wx_neg_mm3=2.0 * ix / h,
            wy_pos_mm3=2.0 * iy / b,
            wy_neg_mm3=2.0 * iy / b,
            sx_mm3=b * h**2 / 8.0,
            sy_mm3=h * b**2 / 8.0,
            radius_x_mm=cls.radius_of_gyration_mm(ix, area),
            radius_y_mm=cls.radius_of_gyration_mm(iy, area),
            mass_kg_m_at_7850=cls.mass_kg_m_from_area(area),
            geometry_model="rectangle_exact",
        )

    @classmethod
    def rectangular_hollow_sharp(
        cls,
        width_mm: float,
        height_mm: float,
        wall_thickness_mm: float,
    ) -> GrossSectionProperties:
        """Exact sharp-corner RHS/SHS model with uniform wall thickness."""

        b = cls._positive("width_mm", width_mm)
        h = cls._positive("height_mm", height_mm)
        t = cls._positive("wall_thickness_mm", wall_thickness_mm)
        if 2.0 * t >= min(b, h):
            raise ValueError("wall_thickness_mm leaves no positive hollow core")
        bi = b - 2.0 * t
        hi = h - 2.0 * t
        area = b * h - bi * hi
        ix = (b * h**3 - bi * hi**3) / 12.0
        iy = (h * b**3 - hi * bi**3) / 12.0
        return GrossSectionProperties(
            area_mm2=area,
            ix_mm4=ix,
            iy_mm4=iy,
            wx_pos_mm3=2.0 * ix / h,
            wx_neg_mm3=2.0 * ix / h,
            wy_pos_mm3=2.0 * iy / b,
            wy_neg_mm3=2.0 * iy / b,
            radius_x_mm=cls.radius_of_gyration_mm(ix, area),
            radius_y_mm=cls.radius_of_gyration_mm(iy, area),
            mass_kg_m_at_7850=cls.mass_kg_m_from_area(area),
            geometry_model="rhs_shs_sharp_corner_exact",
        )

    @classmethod
    def doubly_symmetric_i_sharp(
        cls,
        height_mm: float,
        flange_width_mm: float,
        web_thickness_mm: float,
        flange_thickness_mm: float,
    ) -> GrossSectionProperties:
        """Exact sharp-corner doubly symmetric I-section properties.

        Fillets are intentionally excluded.  This is therefore an analytic geometry
        oracle and must not be substituted for a certified rolled-profile catalogue
        row when the product standard includes fillet area/inertia.
        """

        h = cls._positive("height_mm", height_mm)
        b = cls._positive("flange_width_mm", flange_width_mm)
        tw = cls._positive("web_thickness_mm", web_thickness_mm)
        tf = cls._positive("flange_thickness_mm", flange_thickness_mm)
        if 2.0 * tf >= h:
            raise ValueError("flange_thickness_mm leaves no positive web height")
        if tw >= b:
            raise ValueError("web_thickness_mm must be smaller than flange_width_mm")
        hw = h - 2.0 * tf
        area = 2.0 * b * tf + tw * hw
        ix = 2.0 * (b * tf**3 / 12.0 + b * tf * (h / 2.0 - tf / 2.0) ** 2) + tw * hw**3 / 12.0
        iy = 2.0 * (tf * b**3 / 12.0) + hw * tw**3 / 12.0
        # Static first moments of the material on one side of the centroidal axes.
        sx = b * tf * (h / 2.0 - tf / 2.0) + tw * hw**2 / 8.0
        sy = b**2 * tf / 4.0 + hw * tw**2 / 8.0
        return GrossSectionProperties(
            area_mm2=area,
            ix_mm4=ix,
            iy_mm4=iy,
            wx_pos_mm3=2.0 * ix / h,
            wx_neg_mm3=2.0 * ix / h,
            wy_pos_mm3=2.0 * iy / b,
            wy_neg_mm3=2.0 * iy / b,
            sx_mm3=sx,
            sy_mm3=sy,
            radius_x_mm=cls.radius_of_gyration_mm(ix, area),
            radius_y_mm=cls.radius_of_gyration_mm(iy, area),
            mass_kg_m_at_7850=cls.mass_kg_m_from_area(area),
            geometry_model="i_doubly_symmetric_sharp_corner_exact",
        )

    @classmethod
    def solid_circle(cls, diameter_mm: float) -> GrossSectionProperties:
        d = cls._positive("diameter_mm", diameter_mm)
        area = math.pi * d**2 / 4.0
        inertia = math.pi * d**4 / 64.0
        modulus = math.pi * d**3 / 32.0
        static = d**3 / 12.0
        radius = cls.radius_of_gyration_mm(inertia, area)
        return GrossSectionProperties(
            area_mm2=area,
            ix_mm4=inertia,
            iy_mm4=inertia,
            wx_pos_mm3=modulus,
            wx_neg_mm3=modulus,
            wy_pos_mm3=modulus,
            wy_neg_mm3=modulus,
            sx_mm3=static,
            sy_mm3=static,
            radius_x_mm=radius,
            radius_y_mm=radius,
            mass_kg_m_at_7850=cls.mass_kg_m_from_area(area),
            geometry_model="solid_circle_exact",
        )

    @classmethod
    def circular_hollow(cls, outer_diameter_mm: float, wall_thickness_mm: float) -> GrossSectionProperties:
        d_outer = cls._positive("outer_diameter_mm", outer_diameter_mm)
        t = cls._positive("wall_thickness_mm", wall_thickness_mm)
        d_inner = d_outer - 2.0 * t
        if d_inner <= 0.0:
            raise ValueError("wall_thickness_mm leaves no positive hollow core")
        area = math.pi * (d_outer**2 - d_inner**2) / 4.0
        inertia = math.pi * (d_outer**4 - d_inner**4) / 64.0
        modulus = 2.0 * inertia / d_outer
        static = (d_outer**3 - d_inner**3) / 12.0
        radius = cls.radius_of_gyration_mm(inertia, area)
        return GrossSectionProperties(
            area_mm2=area,
            ix_mm4=inertia,
            iy_mm4=inertia,
            wx_pos_mm3=modulus,
            wx_neg_mm3=modulus,
            wy_pos_mm3=modulus,
            wy_neg_mm3=modulus,
            sx_mm3=static,
            sy_mm3=static,
            radius_x_mm=radius,
            radius_y_mm=radius,
            mass_kg_m_at_7850=cls.mass_kg_m_from_area(area),
            geometry_model="circular_hollow_exact",
        )

    @classmethod
    def plate_sum_b_t3_mm4(cls, plate_terms: Iterable[Sequence[float]]) -> float:
        """Return ``sum(b_i*t_i^3)`` from explicit ``(b_i, t_i)`` plate terms."""

        total = 0.0
        count = 0
        for term in plate_terms:
            if len(term) != 2:
                raise ValueError("each plate term must contain exactly (b_i_mm, t_i_mm)")
            b_i = cls._positive("b_i_mm", term[0])
            t_i = cls._positive("t_i_mm", term[1])
            total += b_i * t_i**3
            count += 1
        if count == 0:
            raise ValueError("at least one plate term is required")
        return total

    @classmethod
    def annex_d_k(cls, section_type: str) -> float:
        try:
            return cls._ANNEX_D_K[section_type]
        except KeyError as exc:
            supported = ", ".join(sorted(cls._ANNEX_D_K))
            raise ValueError(f"unsupported Annex D section_type {section_type!r}; supported: {supported}") from exc

    @classmethod
    def annex_d_free_torsion_inertia_mm4(
        cls,
        section_type: str,
        plate_terms: Iterable[Sequence[float]],
    ) -> dict[str, Any]:
        """Evaluate the current СП 16 Annex D computational value ``I_t``.

        Normative expression (Annex D, note to D.1/D.2):
        ``I_t = (k/3) * sum(b_i*t_i^3)``.

        This is a *normative computational quantity for the СП 16 routes that cite
        Annex D*.  It is deliberately not labelled an exact Saint-Venant torsion
        constant and is kept separate from any catalogue ``I_t`` field.
        """

        k = cls.annex_d_k(section_type)
        sum_b_t3 = cls.plate_sum_b_t3_mm4(plate_terms)
        return {
            "section_type": section_type,
            "k": k,
            "sum_b_i_t_i3_mm4": sum_b_t3,
            "I_t_sp16_annex_d_mm4": (k / 3.0) * sum_b_t3,
            "normative_reference": "СП 16.13330.2017, приложение Д, примечание к формулам Д.1-Д.2",
            "source_sha256": CURRENT_SP16_SOURCE_SHA256,
            "provenance": "CURRENT_SP16_FORMULA_RESULT",
        }

    @classmethod
    def annex_d_it_for_doubly_symmetric_i_mm4(
        cls,
        height_mm: float,
        flange_width_mm: float,
        web_thickness_mm: float,
        flange_thickness_mm: float,
    ) -> dict[str, Any]:
        """Convenience wrapper for a sharp-plate doubly symmetric I-section."""

        h = cls._positive("height_mm", height_mm)
        b = cls._positive("flange_width_mm", flange_width_mm)
        tw = cls._positive("web_thickness_mm", web_thickness_mm)
        tf = cls._positive("flange_thickness_mm", flange_thickness_mm)
        if 2.0 * tf >= h:
            raise ValueError("flange_thickness_mm leaves no positive web height")
        return cls.annex_d_free_torsion_inertia_mm4(
            "i_doubly_symmetric",
            [(h - 2.0 * tf, tw), (b, tf), (b, tf)],
        )


class HistoricalNormCADProfileCatalog:
    """
    Summary:
        Read-only adapter for the frozen Stage N2 static capture of the historical NormCAD profile database.

    Standard reference:
        Secondary-oracle evidence only; current СП 16 remains normative and original profile product standards are deferred.

    Fields:
        Frozen NormCAD source SHA-256, expected profile/family cardinality and explicit non-normative source role.

    Validation:
        Capture audit verifies 4069 profile rows, 37 families, deterministic decoding and known anomaly preservation.

    Used by:
        Stage N2 comparison tests and discrepancy evidence; production access is denied unless historical inspection is explicit.
    """

    EXPECTED_SOURCE_SHA256 = "f7f967e5f22382eb0e20606be73189d2bc6db8f86588d66584fd49b5c4deb4e8"
    EXPECTED_PROFILE_COUNT = 4069
    EXPECTED_FAMILY_COUNT = 37
    SOURCE_ROLE = "HISTORICAL_SECONDARY_ORACLE_NOT_NORMATIVE"

    def __init__(self, capture_path: str | Path) -> None:
        self.capture_path = Path(capture_path)
        self._payload = json.loads(self.capture_path.read_text(encoding="utf-8"))
        if self._payload.get("source_sha256") != self.EXPECTED_SOURCE_SHA256:
            raise ValueError("unexpected NormCAD profile MDB source identity")
        if self._payload.get("profile_row_count") != self.EXPECTED_PROFILE_COUNT:
            raise ValueError("unexpected NormCAD profile-row count")
        if self._payload.get("family_count") != self.EXPECTED_FAMILY_COUNT:
            raise ValueError("unexpected NormCAD profile-family count")
        self._families = {int(item["family_id"]): item for item in self._payload["families"]}
        self._rows_by_key: dict[tuple[int, str], list[Mapping[str, Any]]] = {}
        for row in self._payload["rows"]:
            self._rows_by_key.setdefault((int(row["family_id"]), str(row["designation"])), []).append(row)

    @property
    def profile_count(self) -> int:
        return int(self._payload["profile_row_count"])

    @property
    def family_count(self) -> int:
        return int(self._payload["family_count"])

    def family(self, family_id: int) -> dict[str, Any]:
        try:
            return dict(self._families[int(family_id)])
        except (KeyError, ValueError) as exc:
            raise KeyError(f"unknown historical NormCAD family_id={family_id}") from exc

    def lookup(self, family_id: int, designation: str, *, allow_historical_inspection: bool = False) -> dict[str, Any]:
        if not allow_historical_inspection:
            raise PermissionError(
                "NormCAD profile data are historical/unverified and are forbidden as a production section catalog"
            )
        key = (int(family_id), str(designation))
        rows = self._rows_by_key[key] if key in self._rows_by_key else []
        if not rows:
            raise KeyError(f"historical NormCAD profile not found: family_id={family_id}, designation={designation!r}")
        if len(rows) != 1:
            raise ValueError(f"historical NormCAD profile key is ambiguous: {key!r}, rows={len(rows)}")
        out = dict(rows[0])
        out["family_caption"] = self._families[int(family_id)]["caption"]
        out["source_role"] = self.SOURCE_ROLE
        out["production_eligible"] = False
        return out
