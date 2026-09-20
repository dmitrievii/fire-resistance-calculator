"""Bolted and friction-connection checks for clauses 14.2 and 14.3."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Sequence

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_TABLE_40 = json.loads((_DATA_DIR / "table_40_bolt_spacing.json").read_text(encoding="utf-8"))
_TABLE_41 = json.loads((_DATA_DIR / "table_41_bolted_connection_working_factors.json").read_text(encoding="utf-8"))
_TABLE_42 = json.loads((_DATA_DIR / "table_42_friction_connection_coefficients.json").read_text(encoding="utf-8"))

IMPLEMENTED_PROCEDURE_IDS: tuple[str, ...] = (
    "SP16-PROC-14.2.1-BOLT-STANDARD-ROUTE",
    "SP16-PROC-14.2.2-14.2.8-DETAILING",
    "SP16-PROC-14.2.10-LONG-JOINT",
    "SP16-PROC-14.2.11-MOMENT-DISTRIBUTION",
    "SP16-PROC-14.2.12-FORCE-MOMENT-DISTRIBUTION",
    "SP16-PROC-14.2.14-BOLT-COUNT-INCREASE",
    "SP16-PROC-14.2.15-ANCHOR-EXTERNAL-ROUTE",
    "SP16-PROC-14.3.1-14.3.2-APPLICATION",
    "SP16-PROC-14.3.4-GAMMA-B",
    "SP16-PROC-14.3.5-FORCE-MOMENT-DISTRIBUTION",
    "SP16-PROC-14.3.6-TENSION-REDUCTION",
    "SP16-PROC-14.3.7-DIAMETER-CHECK",
    "SP16-PROC-14.3.8-14.3.9-DOCUMENTATION-ACCESS",
    "SP16-PROC-14.3.10-WASHER",
    "SP16-PROC-14.3.11-EFFECTIVE-AREA",
)

def _real(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    value=float(value)
    if not math.isfinite(value): raise ValueError(f"{name} must be finite")
    return value

def _positive(value: float, name: str) -> float:
    value=_real(value,name)
    if value<=0: raise ValueError(f"{name} must be greater than zero")
    return value

def _nonnegative(value: float, name: str) -> float:
    value=_real(value,name)
    if value<0: raise ValueError(f"{name} must be non-negative")
    return value

def _choice(value: str, allowed: set[str], name: str) -> str:
    if not isinstance(value,str): raise TypeError(f"{name} must be a string")
    if value not in allowed: raise ValueError(f"{name} must be one of {sorted(allowed)}")
    return value

def _count(value: int, name: str) -> int:
    if isinstance(value,bool) or not isinstance(value,int): raise TypeError(f"{name} must be an integer")
    if value<=0: raise ValueError(f"{name} must be greater than zero")
    return value


def table_40_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited bolt-spacing and hole-diameter catalogue.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.2 and 14.2.8
        Annex: None
        Equation/Table: Table 40
        Audit ID: SP16-TBL-40
        Normative status: normative

    Mathematical form:
        Exact printed multipliers and hole-diameter rules.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-TBL-40

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_40, ensure_ascii=False))

def table_40_hole_diameter(bolt_diameter_mm: float, accuracy_class: str, *, overhead_line_switchyard_or_contact_network: bool = False, clearance_mm: float | None = None) -> float:
    """
    Summary:
        Determine the nominal bolt-hole diameter from Table 40 Note 1.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.8
        Annex: None
        Equation/Table: Table 40 Note 1
        Audit ID: SP16-TBL-40
        Normative status: normative

    Mathematical form:
        d=db for class A; d=db+1 mm for the named special class-B structures; otherwise d=db+(1,2,or3 mm).

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-TBL-40

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    db=_positive(bolt_diameter_mm,"bolt_diameter_mm")
    accuracy=_choice(accuracy_class,{"A","B"},"accuracy_class")
    if accuracy=="A":
        if clearance_mm is not None and _real(clearance_mm,"clearance_mm")!=0.0: raise ValueError("Class A holes equal the bolt diameter")
        return db
    if overhead_line_switchyard_or_contact_network:
        if clearance_mm is not None and _real(clearance_mm,"clearance_mm")!=1.0: raise ValueError("The special Class B route requires 1 mm clearance")
        return db+1.0
    if clearance_mm is None: raise ValueError("Class B requires explicit 1, 2, or 3 mm clearance")
    clearance=_real(clearance_mm,"clearance_mm")
    if clearance not in {1.0,2.0,3.0}: raise ValueError("Class B clearance must be 1, 2, or 3 mm")
    return db+clearance

def table_40_distance_requirements(hole_diameter_mm: float, outer_element_thickness_mm: float, normative_yield_resistance_n_mm2: float, *, friction_connection: bool = False, friction_planes: int = 2, edge_type: str = "cut", stress_state: str = "tension", row_location: str = "middle_or_edge_with_angles", transverse_row_spacing_mm: float = 0.0) -> dict[str, float]:
    """
    Summary:
        Calculate the Table 40 minimum and maximum bolt-layout distances.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.2 and 14.2.8
        Annex: None
        Equation/Table: Table 40
        Audit ID: SP16-TBL-40
        Normative status: normative

    Mathematical form:
        Printed multipliers of hole diameter d and outer-element thickness t; alternatives use the smaller maximum.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-TBL-40

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    d=_positive(hole_diameter_mm,"hole_diameter_mm"); t=_positive(outer_element_thickness_mm,"outer_element_thickness_mm"); ryn=_positive(normative_yield_resistance_n_mm2,"normative_yield_resistance_n_mm2")
    edge=_choice(edge_type,{"cut","rolled"},"edge_type"); stress=_choice(stress_state,{"tension","compression"},"stress_state"); row=_choice(row_location,{"edge_without_angles","middle_or_edge_with_angles"},"row_location")
    if isinstance(friction_planes,bool) or not isinstance(friction_planes,int) or friction_planes<1: raise ValueError("friction_planes must be a positive integer")
    min_center=(2.5 if ryn<540.0 else 3.0)*d
    if friction_connection and friction_planes==1 and ryn>375.0: min_center=max(min_center,3.0*d)
    if row=="edge_without_angles": max_center=min(8.0*d,12.0*t)
    elif stress=="tension": max_center=min(16.0*d,24.0*t)
    else: max_center=min(12.0*d,18.0*t)
    return {
     "minimum_center_spacing_mm":min_center,
     "maximum_center_spacing_mm":max_center,
     "minimum_edge_along_force_mm":(2.0 if ryn<540.0 else 2.5)*d,
     "minimum_edge_transverse_force_mm":(1.5 if edge=="cut" else 1.2)*d,
     "maximum_edge_distance_mm":min(4.0*d,8.0*t),
     "minimum_friction_edge_distance_mm":1.3*d,
     "minimum_staggered_longitudinal_spacing_mm":_nonnegative(transverse_row_spacing_mm,"transverse_row_spacing_mm")+1.5*d,
    }

def table_40_check_layout(actual_center_spacing_mm: float, actual_edge_along_force_mm: float, actual_edge_transverse_force_mm: float, requirements: dict[str, float], *, friction_connection: bool = False) -> dict[str, Any]:
    """
    Summary:
        Check actual bolt distances against an audited Table 40 requirement bundle.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.2 and 14.2.8
        Annex: None
        Equation/Table: Table 40
        Audit ID: SP16-PROC-14.2.2-14.2.8-DETAILING
        Normative status: normative

    Mathematical form:
        Each actual distance is compared with its applicable minimum and maximum.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.2.2-14.2.8-DETAILING

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    center=_positive(actual_center_spacing_mm,"actual_center_spacing_mm"); along=_positive(actual_edge_along_force_mm,"actual_edge_along_force_mm"); transverse=_positive(actual_edge_transverse_force_mm,"actual_edge_transverse_force_mm")
    for key in ("minimum_center_spacing_mm","maximum_center_spacing_mm","minimum_edge_along_force_mm","minimum_edge_transverse_force_mm","maximum_edge_distance_mm","minimum_friction_edge_distance_mm"):
        if key not in requirements: raise ValueError(f"requirements missing {key}")
    if not isinstance(friction_connection, bool):
        raise TypeError("friction_connection must be bool")
    min_edge=max(float(requirements["minimum_edge_along_force_mm"]), float(requirements["minimum_friction_edge_distance_mm"]) if friction_connection else 0.0)
    checks={"center_min":center>=float(requirements["minimum_center_spacing_mm"]),"center_max":center<=float(requirements["maximum_center_spacing_mm"]),"edge_along_min":along>=min_edge,"edge_along_max":along<=float(requirements["maximum_edge_distance_mm"]),"edge_transverse_min":transverse>=max(float(requirements["minimum_edge_transverse_force_mm"]),float(requirements["minimum_friction_edge_distance_mm"]) if friction_connection else 0.0),"edge_transverse_max":transverse<=float(requirements["maximum_edge_distance_mm"])}
    # Preserve the v0.25 public call shape. A staggered-layout caller may attach
    # explicit layout evidence to the requirements bundle. This keeps existing
    # clients source-compatible while making the Table 40 u+1.5d check executable.
    if bool(requirements["staggered_layout"]) if "staggered_layout" in requirements else False:
        if "minimum_staggered_longitudinal_spacing_mm" not in requirements:
            raise ValueError("requirements missing minimum_staggered_longitudinal_spacing_mm")
        if "actual_staggered_longitudinal_spacing_mm" not in requirements:
            raise ValueError("requirements missing actual_staggered_longitudinal_spacing_mm for staggered layout")
        staggered = _positive(requirements["actual_staggered_longitudinal_spacing_mm"], "actual_staggered_longitudinal_spacing_mm")
        checks["staggered_longitudinal_min"] = staggered >= float(requirements["minimum_staggered_longitudinal_spacing_mm"])
    return {"checks":checks,"pass":all(checks.values())}

def table_41_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited bolted-connection working-condition factors.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.9
        Annex: None
        Equation/Table: Table 41
        Audit ID: SP16-TBL-41
        Normative status: normative

    Mathematical form:
        Accuracy-class factor multiplied by the bearing-geometry factor; combined value is not greater than 1.0.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-TBL-41

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_41, ensure_ascii=False))

def table_41_connection_factor(accuracy_class: str, *, multi_bolt: bool, bearing_geometry: str = "standard", interpolation_fraction: float | None = None) -> float:
    """
    Summary:
        Determine the Table 41 connection working-condition factor gamma_b.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.9
        Annex: None
        Equation/Table: Table 41
        Audit ID: SP16-TBL-41
        Normative status: normative

    Mathematical form:
        gamma_b=min(1, gamma_accuracy*gamma_geometry); 0.8 at a=1.5d,s=2d and 1.0 at standard geometry.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - The standard states linear interpolation but does not define a unique two-variable path; an explicit verified interpolation fraction is therefore required.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-TBL-41

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    accuracy=_choice(accuracy_class,{"A","B"},"accuracy_class")
    geometry=_choice(bearing_geometry,{"standard","a_1_5d_s_2d","intermediate"},"bearing_geometry")
    accuracy_factor=(1.0 if accuracy=="A" else 0.9) if multi_bolt else 1.0
    if geometry=="standard": geometry_factor=1.0
    elif geometry=="a_1_5d_s_2d": geometry_factor=0.8
    else:
        if interpolation_fraction is None: raise ValueError("Intermediate geometry requires an explicit verified interpolation_fraction")
        f=_real(interpolation_fraction,"interpolation_fraction")
        if not 0.0<f<1.0: raise ValueError("interpolation_fraction must be strictly between 0 and 1")
        geometry_factor=0.8+0.2*f
    return min(1.0,accuracy_factor*geometry_factor)

def bolt_shear_capacity_eq186(bolt_shear_resistance_n_mm2: float, gross_bolt_area_mm2: float, shear_planes: int, connection_factor: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate the shear resistance of one bolt.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.9
        Annex: None
        Equation/Table: Equation (186)
        Audit ID: SP16-EQ-186
        Normative status: normative

    Mathematical form:
        N_bs=R_bs*A_b*n_s*gamma_b*gamma_c.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-EQ-186

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    r=_positive(bolt_shear_resistance_n_mm2,"bolt_shear_resistance_n_mm2"); a=_positive(gross_bolt_area_mm2,"gross_bolt_area_mm2"); ns=_count(shear_planes,"shear_planes"); gb=_positive(connection_factor,"connection_factor"); gc=_positive(working_condition_factor,"working_condition_factor")
    if gb>1.0: raise ValueError("connection_factor must not exceed 1.0")
    return r*a*ns*gb*gc

def bolt_bearing_capacity_eq187(bearing_resistance_n_mm2: float, bolt_diameter_mm: float, summed_bearing_thickness_mm: float, connection_factor: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate the bearing resistance governed by one bolt.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.9
        Annex: None
        Equation/Table: Equation (187)
        Audit ID: SP16-EQ-187
        Normative status: normative

    Mathematical form:
        N_bp=R_bp*d_b*sum(t)*gamma_b*gamma_c.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-EQ-187

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    r=_positive(bearing_resistance_n_mm2,"bearing_resistance_n_mm2"); d=_positive(bolt_diameter_mm,"bolt_diameter_mm"); t=_positive(summed_bearing_thickness_mm,"summed_bearing_thickness_mm"); gb=_positive(connection_factor,"connection_factor"); gc=_positive(working_condition_factor,"working_condition_factor")
    if gb>1.0: raise ValueError("connection_factor must not exceed 1.0")
    return r*d*t*gb*gc

def bolt_tension_capacity_eq188(bolt_tension_resistance_n_mm2: float, net_thread_area_mm2: float, working_condition_factor: float) -> float:
    """
    Summary:
        Calculate the tensile resistance of one bolt.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.9
        Annex: None
        Equation/Table: Equation (188)
        Audit ID: SP16-EQ-188
        Normative status: normative

    Mathematical form:
        N_bt=R_bt*A_bn*gamma_c.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-EQ-188

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    r=_positive(bolt_tension_resistance_n_mm2,"bolt_tension_resistance_n_mm2"); a=_positive(net_thread_area_mm2,"net_thread_area_mm2"); gc=_positive(working_condition_factor,"working_condition_factor")
    return r*a*gc

def long_joint_reduction_factor_14_2_10(joint_length_along_shear_mm: float, hole_diameter_mm: float, *, load_applied_over_full_length: bool = False) -> float:
    """
    Summary:
        Calculate the long-joint bolt-count reduction coefficient beta.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.10
        Annex: None
        Equation/Table: Unnumbered expression after equation (189)
        Audit ID: SP16-PROC-14.2.10-LONG-JOINT
        Normative status: normative

    Mathematical form:
        beta=max(0.75, 1-0.005*(l1/d-16)); beta=1 when l1<=16d or load acts over the full connection length.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.2.10-LONG-JOINT

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    l1=_positive(joint_length_along_shear_mm,"joint_length_along_shear_mm"); d=_positive(hole_diameter_mm,"hole_diameter_mm")
    if load_applied_over_full_length or l1<=16.0*d: return 1.0
    return max(0.75,1.0-0.005*(l1/d-16.0))

def required_bolt_count_eq189(design_force_n: float, shear_capacity_n: float, bearing_capacity_n: float, tension_capacity_n: float, *, applicable_modes: Sequence[str] = ("shear", "bearing"), long_joint_reduction_factor: float = 1.0) -> dict[str, Any]:
    """
    Summary:
        Determine the required number of bolts under a centroidal force.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.10
        Annex: None
        Equation/Table: Equation (189)
        Audit ID: SP16-EQ-189
        Normative status: normative

    Mathematical form:
        n>=N/N_b,min, increased by division by beta for a long joint.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-EQ-189

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    force=_nonnegative(design_force_n,"design_force_n"); capacities={"shear":_positive(shear_capacity_n,"shear_capacity_n"),"bearing":_positive(bearing_capacity_n,"bearing_capacity_n"),"tension":_positive(tension_capacity_n,"tension_capacity_n")}
    modes=list(applicable_modes)
    if not modes or any(m not in capacities for m in modes): raise ValueError("applicable_modes must contain shear, bearing, and/or tension")
    beta=_positive(long_joint_reduction_factor,"long_joint_reduction_factor")
    if beta>1.0 or beta<0.75: raise ValueError("long_joint_reduction_factor must be in [0.75,1.0]")
    governing=min((capacities[m],m) for m in modes)
    continuous=force/governing[0]/beta
    return {"governing_mode":governing[1],"governing_capacity_n":governing[0],"continuous_required_bolts":continuous,"required_bolts":max(1,math.ceil(continuous))}

def bolt_group_force_distribution_14_2_11_12(bolt_coordinates_mm: Sequence[Sequence[float]], force_x_n: float, force_y_n: float, moment_z_n_mm: float) -> dict[str, Any]:
    """
    Summary:
        Distribute in-plane force and moment to a bolt group.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.11-14.2.12 and 14.3.5
        Annex: None
        Equation/Table: Normative proportional-distribution procedure
        Audit ID: SP16-PROC-14.2.11-MOMENT-DISTRIBUTION
        Normative status: normative

    Mathematical form:
        Direct shear is uniform; moment shear is tangential and proportional to radius, with components M*(-y,x)/sum(r^2).

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force and moment components use a right-handed signed in-plane convention.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.2.11-MOMENT-DISTRIBUTION

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(bolt_coordinates_mm,Sequence) or len(bolt_coordinates_mm)<1: raise ValueError("At least one bolt coordinate is required")
    coords=[]
    for i,p in enumerate(bolt_coordinates_mm):
        if not isinstance(p,Sequence) or len(p)!=2: raise ValueError(f"bolt coordinate {i} must contain x and y")
        coords.append((_real(p[0],f"x[{i}]"),_real(p[1],f"y[{i}]")))
    fx=_real(force_x_n,"force_x_n"); fy=_real(force_y_n,"force_y_n"); mz=_real(moment_z_n_mm,"moment_z_n_mm")
    cx=sum(x for x,_ in coords)/len(coords); cy=sum(y for _,y in coords)/len(coords)
    rel=[(x-cx,y-cy) for x,y in coords]; polar=sum(x*x+y*y for x,y in rel)
    if mz!=0.0 and polar<=0.0: raise ValueError("A moment requires a bolt group with nonzero polar coordinate sum")
    results=[]
    for i,(x,y) in enumerate(rel):
        qx=fx/len(coords)+(-mz*y/polar if mz else 0.0); qy=fy/len(coords)+(mz*x/polar if mz else 0.0)
        results.append({"index":i,"x_from_centroid_mm":x,"y_from_centroid_mm":y,"force_x_n":qx,"force_y_n":qy,"resultant_n":math.hypot(qx,qy)})
    return {"centroid_mm":[cx,cy],"bolt_forces":results,"maximum_resultant_n":max(r["resultant_n"] for r in results),"governing_bolt_index":max(range(len(results)),key=lambda i:results[i]["resultant_n"])}

def bolt_shear_tension_interaction_eq190(bolt_shear_force_n: float, bolt_tension_force_n: float, shear_capacity_n: float, tension_capacity_n: float) -> float:
    """
    Summary:
        Check combined shear and tension in the most highly stressed bolt.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.13
        Annex: None
        Equation/Table: Equation (190)
        Audit ID: SP16-EQ-190
        Normative status: normative

    Mathematical form:
        sqrt((N_s/N_bs)^2+(N_t/N_bt)^2)<=1.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-EQ-190

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    ns=_nonnegative(abs(_real(bolt_shear_force_n,"bolt_shear_force_n")),"bolt_shear_force_n"); nt=_nonnegative(abs(_real(bolt_tension_force_n,"bolt_tension_force_n")),"bolt_tension_force_n"); nbs=_positive(shear_capacity_n,"shear_capacity_n"); nbt=_positive(tension_capacity_n,"tension_capacity_n")
    return math.sqrt((ns/nbs)**2+(nt/nbt)**2)

def bolt_count_detailing_adjustment_14_2_14(calculated_bolt_count: int, connection_detail: str) -> dict[str, Any]:
    """
    Summary:
        Increase the calculated bolt count for specified connection details.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.14
        Annex: None
        Equation/Table: Clause 14.2.14
        Audit ID: SP16-PROC-14.2.14-BOLT-COUNT-INCREASE
        Normative status: normative

    Mathematical form:
        n_adj=ceil(1.10n) for packings or one-sided cover plates; n_adj=ceil(1.50n) for the named short-piece detail.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.2.14-BOLT-COUNT-INCREASE

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    n=_count(calculated_bolt_count,"calculated_bolt_count"); detail=_choice(connection_detail,{"none","packing_or_single_cover_plate","angle_or_channel_short_piece"},"connection_detail")
    if detail == "none":
        factor = 1.0
        adjusted = n
    elif detail == "packing_or_single_cover_plate":
        factor = 1.1
        # Exact integer arithmetic avoids binary-float ceil errors such as
        # ceil(50*1.1)=56 when the mathematical result is exactly 55.
        adjusted = (11 * n + 9) // 10
    else:
        factor = 1.5
        adjusted = (3 * n + 1) // 2
    return {"factor":factor,"adjusted_bolt_count":adjusted}

def table_42_catalog() -> dict[str, Any]:
    """
    Summary:
        Return the audited friction coefficients and reliability factors.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.3
        Annex: None
        Equation/Table: Table 42
        Audit ID: SP16-TBL-42
        Normative status: normative

    Mathematical form:
        Exact mu and gamma_h values for four surface treatments and the printed clearance/load-control routes.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-TBL-42

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return json.loads(json.dumps(_TABLE_42, ensure_ascii=False))

def table_42_friction_parameters(surface_treatment: str, tightening_control: str, load_type: str, hole_bolt_clearance_mm: float) -> dict[str, Any]:
    """
    Summary:
        Look up Table 42 mu and gamma_h for a friction connection.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.3
        Annex: None
        Equation/Table: Table 42
        Audit ID: SP16-TBL-42
        Normative status: normative

    Mathematical form:
        Printed gamma_h route; nut-rotation control multiplies gamma_h by 0.9.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-TBL-42

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    if not isinstance(surface_treatment,str): raise TypeError("surface_treatment must be a string")
    try: row=_TABLE_42["surface_treatments"][surface_treatment]
    except KeyError as exc: raise KeyError(f"Unknown Table 42 surface treatment: {surface_treatment}") from exc
    control=_choice(tightening_control,{"torque","nut_rotation"},"tightening_control"); load=_choice(load_type,{"dynamic","static"},"load_type"); clearance=_real(hole_bolt_clearance_mm,"hole_bolt_clearance_mm")
    if clearance<=0: raise ValueError("hole_bolt_clearance_mm must be positive")
    small=(load=="dynamic" and clearance==1.0) or (load=="static" and 1.0<=clearance<=4.0)
    large=(load=="dynamic" and 3.0<=clearance<=6.0) or (load=="static" and 5.0<=clearance<=6.0)
    if small==large or not (small or large): raise ValueError("Clearance/load combination is not covered by Table 42")
    gamma=float(row["gamma_h_small_clearance" if small else "gamma_h_large_clearance"])
    if control=="nut_rotation": gamma*=0.9
    return {"friction_coefficient":float(row["mu"]),"gamma_h":gamma,"clearance_route":"small" if small else "large","tightening_control":control}

def friction_plane_capacity_eq191(bolt_tension_resistance_n_mm2: float, net_thread_area_mm2: float, friction_coefficient: float, reliability_factor_gamma_h: float) -> float:
    """
    Summary:
        Calculate resistance per friction plane clamped by one pretensioned bolt.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.3
        Annex: None
        Equation/Table: Equation (191)
        Audit ID: SP16-EQ-191
        Normative status: normative

    Mathematical form:
        Q_bh=R_bt*A_bn*mu/gamma_h.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-EQ-191

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    r=_positive(bolt_tension_resistance_n_mm2,"bolt_tension_resistance_n_mm2"); a=_positive(net_thread_area_mm2,"net_thread_area_mm2"); mu=_positive(friction_coefficient,"friction_coefficient"); gh=_positive(reliability_factor_gamma_h,"reliability_factor_gamma_h")
    return r*a*mu/gh

def friction_connection_working_factor_14_3_4(bolt_count: int) -> float:
    """
    Summary:
        Return the friction-connection working-condition factor gamma_b.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.4
        Annex: None
        Equation/Table: Piecewise rule accompanying equation (192)
        Audit ID: SP16-PROC-14.3.4-GAMMA-B
        Normative status: normative

    Mathematical form:
        gamma_b=0.8 for n<5, 0.9 for 5<=n<10, and 1.0 for n>=10.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.3.4-GAMMA-B

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    n=_count(bolt_count,"bolt_count")
    if n<5: return 0.8
    if n<10: return 0.9
    return 1.0

def required_friction_bolt_count_eq192(design_shear_force_n: float, friction_plane_capacity_n: float, friction_planes: int, working_condition_factor: float, *, maximum_search_bolts: int = 10000) -> dict[str, Any]:
    """
    Summary:
        Solve the implicit friction-connection bolt-count requirement.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.4
        Annex: None
        Equation/Table: Equation (192)
        Audit ID: SP16-EQ-192
        Normative status: normative

    Mathematical form:
        n>=N/(Q_bh*k*gamma_b*gamma_c), with gamma_b evaluated from the resulting integer n.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-EQ-192

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    force=_nonnegative(design_shear_force_n,"design_shear_force_n"); q=_positive(friction_plane_capacity_n,"friction_plane_capacity_n"); k=_count(friction_planes,"friction_planes"); gc=_positive(working_condition_factor,"working_condition_factor"); maxn=_count(maximum_search_bolts,"maximum_search_bolts")
    for n in range(1,maxn+1):
        gb=friction_connection_working_factor_14_3_4(n)
        if n>=force/(q*k*gb*gc):
            return {"required_bolts":n,"connection_factor_gamma_b":gb,"continuous_required_bolts_at_governing_factor":force/(q*k*gb*gc),"total_design_capacity_n":n*q*k*gb*gc}
    raise ValueError("No satisfying integer bolt count found within maximum_search_bolts")

def friction_tension_reduction_14_3_6(connection_factor_gamma_b: float, tensile_force_per_bolt_n: float, bolt_tension_resistance_n_mm2: float, net_thread_area_mm2: float) -> dict[str, Any]:
    """
    Summary:
        Reduce gamma_b when a friction bolt is also subjected to tension.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.6
        Annex: None
        Equation/Table: Unnumbered expressions in clause 14.3.6
        Audit ID: SP16-PROC-14.3.6-TENSION-REDUCTION
        Normative status: normative

    Mathematical form:
        gamma_b,adj=gamma_b*(1-N_t/P_b), where P_b=R_bt*A_bn.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.3.6-TENSION-REDUCTION

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    gb=_positive(connection_factor_gamma_b,"connection_factor_gamma_b"); nt=_nonnegative(tensile_force_per_bolt_n,"tensile_force_per_bolt_n"); pb=_positive(bolt_tension_resistance_n_mm2,"bolt_tension_resistance_n_mm2")*_positive(net_thread_area_mm2,"net_thread_area_mm2")
    if nt>=pb: raise ValueError("Tensile force per bolt must be less than bolt pretension P_b")
    reduction=1.0-nt/pb
    return {"bolt_pretension_n":pb,"reduction_factor":reduction,"adjusted_connection_factor_gamma_b":gb*reduction}

def friction_bolt_diameter_check_14_3_7(summed_shifted_thickness_mm: float, bolt_diameter_mm: float) -> dict[str, Any]:
    """
    Summary:
        Check the friction-connection diameter condition against the shifted package thickness.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.7
        Annex: None
        Equation/Table: Clause 14.3.7
        Audit ID: SP16-PROC-14.3.7-DIAMETER-CHECK
        Normative status: normative

    Mathematical form:
        sum(t)<=4d_b.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.3.7-DIAMETER-CHECK

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    t=_positive(summed_shifted_thickness_mm,"summed_shifted_thickness_mm"); d=_positive(bolt_diameter_mm,"bolt_diameter_mm"); limit=4.0*d
    return {"summed_thickness_mm":t,"maximum_summed_thickness_mm":limit,"utilization":t/limit,"pass":t<=limit}

def friction_connection_washer_requirement_14_3_10(hole_bolt_clearance_mm: float, steel_ultimate_resistance_n_mm2: float, *, enlarged_head_and_nut: bool) -> dict[str, Any]:
    """
    Summary:
        Determine whether one washer under the nut is the specified arrangement.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.10
        Annex: None
        Equation/Table: Clause 14.3.10
        Audit ID: SP16-PROC-14.3.10-WASHER
        Normative status: normative

    Mathematical form:
        One washer is specified for enlarged heads/nuts with clearance <=3 mm, or <=4 mm when R_un>=440 N/mm2.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.3.10-WASHER

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    clearance=_nonnegative(hole_bolt_clearance_mm,"hole_bolt_clearance_mm"); run=_positive(steel_ultimate_resistance_n_mm2,"steel_ultimate_resistance_n_mm2")
    qualifies=enlarged_head_and_nut and (clearance<=3.0 or (run>=440.0 and clearance<=4.0))
    return {"one_washer_under_nut_permitted":qualifies,"required_arrangement":"one_washer_under_nut" if qualifies else "external_detailing_route"}

def friction_connection_effective_area_14_3_11(gross_area_mm2: float, net_area_mm2: float, load_type: str) -> dict[str, Any]:
    """
    Summary:
        Select the area for a member weakened by holes in a friction connection.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.3.11
        Annex: None
        Equation/Table: Clause 14.3.11
        Audit ID: SP16-PROC-14.3.11-EFFECTIVE-AREA
        Normative status: normative

    Mathematical form:
        Dynamic: A_n; static: A when A_n>=0.85A, otherwise A_ef=1.18A_n.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Calculated scalar or structured diagnostic result.

    Assumptions:
        - Inputs represent the governing connection geometry and load combination.

    Sign convention:
        - Force magnitudes are non-negative unless vector components are explicitly signed.

    Unit convention:
        - Forces use N, lengths use mm, areas use mm2, and stresses use N/mm2.

    Applicability:
        - Clauses 14.2-14.3 of the supplied standard.

    Limitations:
        - No CAD recognition, bolt-standard lookup, or global structural analysis is performed.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.3.11-EFFECTIVE-AREA

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    a=_positive(gross_area_mm2,"gross_area_mm2"); an=_positive(net_area_mm2,"net_area_mm2"); load=_choice(load_type,{"dynamic","static"},"load_type")
    if an>a: raise ValueError("net_area_mm2 must not exceed gross_area_mm2")
    if load=="dynamic": return {"selected_area_mm2":an,"area_type":"net","net_to_gross_ratio":an/a}
    if an>=0.85*a: return {"selected_area_mm2":a,"area_type":"gross","net_to_gross_ratio":an/a}
    return {"selected_area_mm2":1.18*an,"area_type":"effective_1_18_net","net_to_gross_ratio":an/a}

def bolted_and_friction_external_requirements() -> dict[str, Any]:
    """
    Summary:
        Return the documented external-reference and project-evidence boundaries.

    Standard reference:
        Standard: СП 16.13330.2017 «Стальные конструкции»
        Version: Supplied consolidated text with corrections through 2024 and Amendments No. 1-5
        Clause: 14.2.1, 14.2.6, 14.2.15, 14.3.8-14.3.9
        Annex: None
        Equation/Table: Documentary requirements
        Audit ID: SP16-PROC-14.3.8-14.3.9-DOCUMENTATION-ACCESS
        Normative status: normative

    Mathematical form:
        No numerical equation; returns explicit external evidence routes.

    Parameters:
        Explicit numeric and categorical inputs described by the function signature.

    Returns:
        Type: float | dict[str, Any]
        Unit: explicitly named in the result or dimensionless
        Meaning: Required external references and project-documentation fields.

    Assumptions:
        - The caller will obtain authoritative product and installation data.

    Sign convention:
        - Not applicable.

    Unit convention:
        - Not applicable.

    Applicability:
        - Documentation and external-boundary control for clauses 14.2-14.3.

    Limitations:
        - The function cannot verify certificates, installation quality, or external standards.

    Raises:
        ValueError: TypeError or ValueError for invalid types, ranges, or unsupported normative routes.

    Examples:
        >>> # See the packaged JSON example and unit tests.

    Tests:
        Unit tests:
            - tests/test_bolted_and_friction_connections.py
        Validation cases:
            - V16-SP16-PROC-14.3.8-14.3.9-DOCUMENTATION-ACCESS

    Implementation notes:
        - No unstated interpolation or national choice is applied.
        - Defaults must be explicit in the input configuration.
    """
    return {"bolt_product_standards":"Tables G.3-G.7 and G.9 are external data dependencies","washers_and_installation":"SP 70.13330","anchor_bolts":"SP 43.13330","anti_loosening":"Project drawings must specify the adopted measure","friction_project_data":["bolt, nut, and washer grades and mechanical properties","surface treatment","bolt pretension P_b"],"access_requirement":"Free access for installation, package clamping, and controlled tightening is required"}
