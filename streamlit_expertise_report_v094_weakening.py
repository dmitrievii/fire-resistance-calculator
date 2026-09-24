"""v0.94 report remediation for section weakening and gamma_m aliases."""
from __future__ import annotations

import re
from typing import Any, Mapping

import streamlit_expertise_report_v093_progressive_hotfix as _v093


def _rows(report: Mapping[str, Any]):
    for block in report.get("blocks") or []:
        if not isinstance(block, Mapping) or block.get("progress_state") == "PENDING_CURRENT":
            continue
        for field in ("outputs", "inputs"):
            for row in block.get(field) or []:
                if isinstance(row, Mapping):
                    yield row, block


def _hit(report: Mapping[str, Any], *qids: str):
    wanted = {q.lower() for q in qids}
    for row, block in reversed(list(_rows(report))):
        qid = str(row.get("quantity_id") or "")
        if qid.lower() in wanted:
            return row, block
    return None


def _raw(hit):
    return hit[0].get("raw_value") if hit else None


def _fmt(value: Any) -> str:
    return _v093._fmt(value)


def _weakening_section(report: Mapping[str, Any]) -> str:
    model = _hit(report, "section_weakening_model")
    trace = _hit(report, "section_weakening_trace")
    an = _hit(report, "A_net", "An", "A_n")
    ah = _hit(report, "alpha_h")
    if not any((model, trace, an, ah)):
        return ""

    model_value = _raw(model)
    lines = ["### 1.2 Ослабления поперечного сечения", ""]
    if model_value == "no_weakening":
        lines.extend(["Ослабления отсутствуют; расчёт ведётся по характеристикам брутто.", ""])
        return "\n".join(lines)

    trace_value = _raw(trace)
    if isinstance(trace_value, Mapping):
        kind = trace_value.get("kind")
        if kind == "circular_bolt_holes":
            A = trace_value.get("A_gross_mm2")
            d = trace_value.get("hole_diameter_mm")
            tw = trace_value.get("web_thickness_mm")
            count = trace_value.get("holes_count", 1)
            delta = trace_value.get("area_reduction_mm2")
            net = trace_value.get("A_net_mm2")
            if all(v is not None for v in (d, tw, delta)):
                lines.extend([
                    "Для круглых болтовых отверстий потеря площади раскрывается непосредственно из выполненного runtime:", "",
                    "$$ \\Delta A=n_h d t_w $$", "",
                    f"$$ \\Delta A={_fmt(count)}\\cdot{_fmt(d)}\\cdot{_fmt(tw)}={_fmt(delta)}\\;\\mathrm{{mm^2}} $$", "",
                ])
            if all(v is not None for v in (A, delta, net)):
                lines.extend([
                    "Площадь нетто:", "",
                    "$$ A_n=A-\\Delta A $$", "",
                    f"$$ A_n={_fmt(A)}-{_fmt(delta)}={_fmt(net)}\\;\\mathrm{{mm^2}} $$", "",
                ])
        elif kind == "manual_net_properties":
            lines.extend(["Характеристики нетто введены пользователем. Ниже показаны только значения, реально опубликованные выполненным runtime.", ""])
            props = trace_value.get("net_properties") or {}
            for key, value in props.items():
                lines.append(f"- ${key}$: **{_fmt(value)}** (введено пользователем)")
            lines.append("")

    if ah:
        value = _raw(ah)
        row = ah[0]
        # Prefer producer-provided expression/substitution if REPORT-IR exposes it.
        expr = row.get("formula") or row.get("expression")
        subst = row.get("substitution")
        if expr:
            lines.extend(["Коэффициент ослабления $\\alpha_h$:", "", f"$$ {expr} $$", ""])
        if subst:
            lines.extend([f"$$ {subst} $$", ""])
        lines.extend([f"Результат: **$\\alpha_h={_fmt(value)}$**.", ""])

    if an and not (isinstance(trace_value, Mapping) and trace_value.get("A_net_mm2") is not None):
        lines.extend([f"Площадь нетто $A_n$: **{_fmt(_raw(an))} mm²**.", ""])

    lines.append("*Нормативное основание и provenance берутся из выполненного weakening-node; presentation layer не пересчитывает нормативные величины.*")
    return "\n".join(lines)


def _insert_weakening(text: str, report: Mapping[str, Any]) -> str:
    section = _weakening_section(report)
    if not section:
        return text
    # Replace an older weakening subsection if present.
    text = re.sub(r"(?ms)^### 1\.2\s+Ослабления.*?(?=^### 1\.[3-9]\s|^## 2\.\s|\Z)", lambda _m: "", text, count=1)
    anchor = re.search(r"(?m)^## 2\.\s", text)
    if anchor:
        return text[:anchor.start()].rstrip() + "\n\n" + section + "\n\n" + text[anchor.start():]
    return text.rstrip() + "\n\n" + section + "\n"


def _patch_gamma_aliases(report: Mapping[str, Any]) -> Mapping[str, Any]:
    """Expose an already executed gamma_m under the canonical report qid.

    No value is inferred from Ryn/Ry.  Only an existing ledger/report row whose
    qid explicitly denotes gamma_m is aliased for the v0.93 material renderer.
    """
    if _hit(report, "gamma_m", "material_safety_factor"):
        return report
    candidate = None
    for row, block in _rows(report):
        qid = str(row.get("quantity_id") or "").lower().replace("γ", "gamma")
        if "gamma_m" in qid or "gammam" in qid:
            candidate = (row, block)
    if candidate is None:
        return report
    copied = dict(report)
    blocks = [dict(b) if isinstance(b, Mapping) else b for b in report.get("blocks") or []]
    copied["blocks"] = blocks
    source_row, source_block = candidate
    for idx, block in enumerate(blocks):
        if isinstance(block, Mapping) and block.get("owner_node_id") == source_block.get("owner_node_id"):
            outputs = list(block.get("outputs") or [])
            alias = dict(source_row)
            alias["quantity_id"] = "gamma_m"
            outputs.append(alias)
            block["outputs"] = outputs
            blocks[idx] = block
            break
    return copied


def render_expertise_narrative_markdown_v094(report: Mapping[str, Any]) -> str:
    patched = _patch_gamma_aliases(report)
    text = _v093.render_expertise_narrative_markdown_v093_progressive(patched)
    return _insert_weakening(text, patched)


__all__ = ["render_expertise_narrative_markdown_v094"]
