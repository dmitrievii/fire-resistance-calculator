"""v0.92 trace-bound canonical z/y stability report overlay.

The retained v0.89 narrative printed a generic §3.1 stability formula before the
corresponding MECH7 runtime node had necessarily executed. The active v0.92
report is progressive: no z/y formula is shown until completed
``sp16_effective_length_zy_trace`` evidence exists.

After execution this module formats, but never evaluates, the values captured by
the qualified MECH7 runtime and its validated full-phi evidence producer:

    l_eff -> lambda -> lambda_bar -> Table-7 alpha/beta -> delta -> phi

The canonical property contract is explicit: z is the strong principal axis
(Iz/Wz/iz), y is the weak principal axis (Iy/Wy/iy). No legacy principal-x
bending semantics are accepted or displayed.
"""
from __future__ import annotations

import math
import re
from typing import Any, Mapping

import streamlit_expertise_report_v089 as _v089
from standard_core.sp16_mech7_v092_effective_length import EVIDENCE_QID
from standard_core.sp16_mech7_v092_phi_evidence import PHI_TRACE_SCHEMA
from streamlit_expertise_report_v092 import compact_engineering_markdown
from streamlit_expertise_report_v092_actions import (
    render_expertise_narrative_markdown_v092_actions,
)

_TRACE_SCHEMA = "sp16_v092_effective_length_zy_trace_v1"
_SECTION_RE = re.compile(
    r"(?ms)^### 3\.1 Расч[ёе]тные длины и гибкости\s*\n.*?(?=^### 3\.2\s|^## 4\.\s|\Z)"
)
_AXIS_META = {
    "z": {"role": "сильная главная ось", "inertia": "I_z", "section_modulus": "W_z", "radius": "i_z"},
    "y": {"role": "слабая главная ось", "inertia": "I_y", "section_modulus": "W_y", "radius": "i_y"},
}


def _fmt(value: Any, *, digits: int = 6) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"numeric trace value expected, got {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("non-finite trace value is not reportable")
    return format(number, f".{digits}g")


def _raw_qid(report: Mapping[str, Any], qid: str) -> Any:
    hit = _v089._find_row(report, qids=(qid,))
    return _v089._row_raw(hit) if hit else None


def _numeric_qid(report: Mapping[str, Any], qid: str) -> float | None:
    value = _raw_qid(report, qid)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _trace(report: Mapping[str, Any]) -> Mapping[str, Any] | None:
    value = _raw_qid(report, EVIDENCE_QID)
    if not isinstance(value, Mapping):
        return None
    if value.get("schema") != _TRACE_SCHEMA:
        raise ValueError("v0.92 z/y report: effective-length trace schema mismatch")
    convention = value.get("axis_convention")
    if not isinstance(convention, Mapping):
        raise ValueError("v0.92 z/y report: canonical axis convention is absent")
    if convention.get("z") != "strong principal axis" or convention.get("y") != "weak principal axis":
        raise ValueError("v0.92 z/y report: non-canonical principal-axis evidence")
    return value


def _route_line(axis: str, state: Mapping[str, Any]) -> str:
    route = state.get("route")
    route = route if isinstance(route, Mapping) else {}
    leff = _fmt(state.get("effective_length_mm"))
    mu = route.get("mu")
    length = route.get("member_length_mm")
    if isinstance(mu, (int, float)) and not isinstance(mu, bool) and isinstance(length, (int, float)) and not isinstance(length, bool):
        return rf"$$l_{{ef,{axis}}}=\mu_{{{axis}}}L={_fmt(mu)}\cdot {_fmt(length)}={leff}\;\mathrm{{mm}}$$"
    route_name = str(route.get("route_kind") or route.get("method") or "SP16 §10").strip()
    return rf"Расчётная длина по выполненному нормативному маршруту `{route_name}`: $l_{{ef,{axis}}}=\mathbf{{{leff}\;mm}}$."


def _phi_lines(axis: str, state: Mapping[str, Any]) -> list[str]:
    evidence = state.get("phi_evidence")
    if not isinstance(evidence, Mapping) or evidence.get("schema") != PHI_TRACE_SCHEMA:
        raise ValueError(f"v0.92 z/y report: full phi evidence for axis {axis} is absent")
    if evidence.get("validated_against_runtime") is not True:
        raise ValueError(f"v0.92 z/y report: phi evidence for axis {axis} is not runtime-validated")
    curve = str(evidence.get("curve") or "")
    lambda_bar = _fmt(evidence.get("lambda_bar")); alpha = _fmt(evidence.get("alpha")); beta = _fmt(evidence.get("beta"))
    final_phi = _fmt(evidence.get("final_phi")); state_phi = _fmt(state.get("phi"))
    if curve != str(state.get("curve") or "") or lambda_bar != _fmt(state.get("lambda_bar")):
        raise ValueError(f"v0.92 z/y report: phi evidence operands mismatch for axis {axis}")
    if final_phi != state_phi:
        raise ValueError(f"v0.92 z/y report: phi evidence result mismatch for axis {axis}")
    lines = [rf"По таблице 7 для оси {axis}: $\alpha={alpha}$, $\beta={beta}$, тип кривой **{curve}**.", ""]
    branch = evidence.get("branch")
    if branch == "low_slenderness_direct_phi_1":
        lines.extend([rf"При $\bar{{\lambda}}_{{{axis}}}={lambda_bar}<0.6$ для кривой {curve} применяется прямое правило п. 7.1.3:", "", rf"$$\varphi_{{{axis}}}=1.0={final_phi}$$", ""])
        return lines
    if branch != "eq8_eq9_with_table7":
        raise ValueError(f"v0.92 z/y report: unknown phi-evidence branch for axis {axis}")
    delta = _fmt(evidence.get("delta")); radicand = _fmt(evidence.get("eq8_radicand")); phi_eq8 = _fmt(evidence.get("phi_eq8"))
    lines.extend([
        rf"$$\delta_{{{axis}}}=9.87\left(1-\alpha+\beta\bar{{\lambda}}_{{{axis}}}\right)+\bar{{\lambda}}_{{{axis}}}^2=9.87\left(1-{alpha}+{beta}\cdot {lambda_bar}\right)+{lambda_bar}^2={delta}$$", "",
        rf"$$\varphi_{{8,{axis}}}=\frac{{19.74}}{{\delta_{{{axis}}}+\sqrt{{\delta_{{{axis}}}^2-39.48\bar{{\lambda}}_{{{axis}}}^2}}}}=\frac{{19.74}}{{{delta}+\sqrt{{{radicand}}}}}={phi_eq8}$$", ""])
    if evidence.get("cap_applied") is True:
        cap = _fmt(evidence.get("cap_candidate")); threshold = _fmt(evidence.get("cap_threshold_lambda_bar"))
        lines.extend([rf"Так как $\bar{{\lambda}}_{{{axis}}}={lambda_bar}\ge {threshold}$, runtime применил предельное правило:", "", rf"$$\varphi_{{cap,{axis}}}=\frac{{7.6}}{{\bar{{\lambda}}_{{{axis}}}^2}}={cap}$$", "", rf"$$\varphi_{{{axis}}}=\min({phi_eq8},\;{cap})={final_phi}$$", ""])
    else:
        lines.extend([rf"$$\varphi_{{{axis}}}=\varphi_{{8,{axis}}}={final_phi}$$", ""])
    return lines


def _axis_block(axis: str, state: Mapping[str, Any], ry: float | None, elastic: float | None) -> list[str]:
    meta = _AXIS_META[axis]; radius = _fmt(state.get("radius_mm")); leff = _fmt(state.get("effective_length_mm")); lam = _fmt(state.get("lambda")); lam_bar = _fmt(state.get("lambda_bar"))
    lines = [f"#### Ось {axis} — {meta['role']}", "", "Привязка свойств сечения: " + f"${meta['inertia']}$, ${meta['section_modulus']}$, ${meta['radius']}$; " + rf"в runtime использован ${meta['radius']}={radius}\;mm$.", "", _route_line(axis, state), "", rf"$$\lambda_{{{axis}}}=\frac{{l_{{ef,{axis}}}}}{{i_{{{axis}}}}}=\frac{{{leff}}}{{{radius}}}={lam}$$", ""]
    if ry is not None and elastic is not None:
        lines.extend([rf"$$\bar{{\lambda}}_{{{axis}}}=\lambda_{{{axis}}}\sqrt{{\frac{{R_y}}{{E}}}}={lam}\sqrt{{\frac{{{_fmt(ry)}}}{{{_fmt(elastic)}}}}}={lam_bar}$$", ""])
    else:
        lines.extend([rf"$\bar{{\lambda}}_{{{axis}}}=\mathbf{{{lam_bar}}}$ — значение зафиксировано runtime; числовая подстановка $R_y/E$ не выводится, поскольку один из этих операндов отсутствует в REPORT-IR.", ""])
    lines.extend(_phi_lines(axis, state)); return lines


def zy_stability_section(report: Mapping[str, Any]) -> str:
    trace = _trace(report)
    if trace is None: return ""
    z = trace.get("z"); y = trace.get("y")
    if not isinstance(z, Mapping) or not isinstance(y, Mapping): raise ValueError("v0.92 z/y report: both axis states are required")
    ry = _numeric_qid(report, "Ry_formula"); elastic = _numeric_qid(report, "E_norm"); governing = trace.get("governing_axis_by_phi")
    if governing not in {"z", "y"}: raise ValueError("v0.92 z/y report: governing phi axis is absent")
    lines = ["### 3.1 Расчётные длины, гибкости и коэффициенты устойчивости", "", "Численные значения ниже являются проекцией выполненного MECH7 runtime trace; presentation-слой их не пересчитывает.", ""]
    lines.extend(_axis_block("z", z, ry, elastic)); lines.extend(_axis_block("y", y, ry, elastic))
    role = _AXIS_META[str(governing)]["role"]
    lines.extend([rf"**Определяющая по $\varphi$ ось:** **{governing} ({role})** — это значение зафиксировано runtime trace.", "", f"*Нормативное основание: {trace.get('normative_basis') or 'СП 16.13330.2017, раздел 10'}; полный расчёт φ — п. 7.1.3, формулы (8)–(9), таблица 7.*", ""])
    return "\n".join(lines)


def replace_zy_stability_section(markdown: str, report: Mapping[str, Any]) -> str:
    text = str(markdown or ""); section = zy_stability_section(report); match = _SECTION_RE.search(text)
    if match: text = _SECTION_RE.sub(section + ("\n" if section else ""), text, count=1)
    elif section:
        anchor = re.search(r"(?m)^### 3\.2\s", text) or re.search(r"(?m)^## 4\.\s", text)
        if anchor: text = text[:anchor.start()] + section + "\n" + text[anchor.start():]
        else: text = text.rstrip() + "\n\n" + section
    return compact_engineering_markdown(text) + "\n"


def render_expertise_narrative_markdown_v092_zy(report: Mapping[str, Any]) -> str:
    return replace_zy_stability_section(render_expertise_narrative_markdown_v092_actions(report), report)


__all__ = ["replace_zy_stability_section", "render_expertise_narrative_markdown_v092_zy", "zy_stability_section"]
