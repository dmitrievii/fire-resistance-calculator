"""v0.86 installer: protected-FVM legends, five-minute time axis and faster search."""
from __future__ import annotations

import html
import math
from typing import Any, Mapping, Sequence

import streamlit_guided_ux_v084 as _v084
import streamlit_guided_ux_v085 as _v085

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech7_v086_fvm_overlay import GRAPH_SUFFIX, build_model
from standard_core.sp16_mech7_v086_fvm_runtime import install_registry_remediation

_INSTALLED = "_fire_v086_fvm_fast_search_legends_installed"

_PROTECTED_TIME_STYLES = {
    "ISO 834 / ГОСТ 30247.0": {"stroke": "#111111", "width": 2.3, "dash": "8 5"},
    "Поверхность огнезащиты": {"stroke": "#e67e22", "width": 2.0, "dash": ""},
    "Середина огнезащиты": {"stroke": "#9467bd", "width": 2.0, "dash": ""},
    "Последний узел огнезащиты": {"stroke": "#1f77b4", "width": 2.0, "dash": ""},
    "Сталь": {"stroke": "#d62728", "width": 2.8, "dash": ""},
}

_PROFILE_STYLES = ["#a8a8a8", "#909090", "#737373", "#555555", "#2f2f2f", "#d62728"]


def _temperature_bounds(rows: Sequence[Mapping[str, Any]], y_key: str, guide_y: float | None = None) -> tuple[float, float]:
    return _v085._temperature_bounds(rows, y_key, guide_y)


def _polyline(points, sx, sy) -> str:
    return " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in points)


def _series_style(name: str, *, actual_group: str | None, fire_group: str | None, style_map: Mapping[str, Mapping[str, Any]] | None) -> tuple[str, float, str]:
    if style_map and name in style_map:
        spec = style_map[name]
        return str(spec.get("stroke") or "#777"), float(spec.get("width") or 1.8), str(spec.get("dash") or "")
    if name == actual_group:
        return "#d62728", 3.0, ""
    if name == fire_group:
        return "#111111", 2.3, "8 5"
    return "#9a9a9a", 1.5, ""


def _legend_svg(groups: Sequence[str], *, x: float, y: float, width: float, style_map: Mapping[str, Mapping[str, Any]] | None, actual_group: str | None, fire_group: str | None) -> tuple[list[str], float]:
    """Return a compact two-column SVG legend and the vertical space it consumes."""
    if not groups:
        return [], 0.0
    col_count = 2 if len(groups) > 3 else 1
    rows = math.ceil(len(groups) / col_count)
    row_h = 18.0
    col_w = width / col_count
    parts: list[str] = []
    for i, name in enumerate(groups):
        row = i % rows
        col = i // rows
        xx = x + col * col_w
        yy = y + row * row_h
        stroke, sw, dash = _series_style(name, actual_group=actual_group, fire_group=fire_group, style_map=style_map)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<line x1="{xx:.1f}" y1="{yy:.1f}" x2="{xx+26:.1f}" y2="{yy:.1f}" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>')
        parts.append(f'<text x="{xx+33:.1f}" y="{yy+4:.1f}" font-size="10.5" fill="#333">{html.escape(name)}</text>')
    return parts, rows * row_h + 8.0


def _svg_chart(
    series: Sequence[Mapping[str, Any]], *, x_key: str, y_key: str, group_key: str,
    width: int = 780, height: int = 440, x_label: str = "t, мин", y_label: str = "T, °C",
    actual_group: str | None = None, fire_group: str | None = None,
    guide_x: float | None = None, guide_y: float | None = None,
    x_tick_step: float | None = None,
    style_map: Mapping[str, Mapping[str, Any]] | None = None,
    legend: bool = True,
) -> str:
    rows = [r for r in series if isinstance(r.get(x_key), (int, float)) and isinstance(r.get(y_key), (int, float))]
    if not rows:
        return ""
    groups: dict[str, list[tuple[float, float]]] = {}
    for r in rows:
        groups.setdefault(str(r[group_key]), []).append((float(r[x_key]), float(r[y_key])))
    group_order = list(groups)

    ml, mr, mb = 62, 18, 48
    legend_parts: list[str] = []
    legend_h = 0.0
    if legend:
        legend_parts, legend_h = _legend_svg(
            group_order, x=ml, y=18.0, width=width-ml-mr,
            style_map=style_map, actual_group=actual_group, fire_group=fire_group,
        )
    mt = 18 + int(legend_h)

    xmin_data = min(float(r[x_key]) for r in rows)
    xmax_data = max(float(r[x_key]) for r in rows)
    if x_tick_step is not None:
        step = float(x_tick_step)
        if step <= 0:
            raise ValueError("x_tick_step must be > 0")
        xmin = math.floor(xmin_data / step) * step
        xmax = math.ceil(xmax_data / step) * step
        if xmax <= xmin:
            xmax = xmin + step
        ticks = []
        tick = xmin
        while tick <= xmax + 1e-9:
            ticks.append(tick)
            tick += step
    else:
        xmin, xmax = xmin_data, xmax_data
        if xmax <= xmin:
            xmax = xmin + 1.0
        ticks = [xmin + (xmax-xmin)*i/5 for i in range(6)]

    ymin, ymax = _temperature_bounds(rows, y_key, guide_y)
    sx = lambda x: ml + (float(x)-xmin)/(xmax-xmin)*(width-ml-mr)
    sy = lambda y: mt + (ymax-float(y))/(ymax-ymin)*(height-mt-mb)
    out = [f'<svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#fff;border:1px solid rgba(49,51,63,.18);border-radius:12px">']
    out.extend(legend_parts)
    for x in ticks:
        X = sx(x)
        out.append(f'<line x1="{X:.1f}" y1="{mt}" x2="{X:.1f}" y2="{height-mb}" stroke="#ececec"/>')
        label = f"{x:.0f}" if x_tick_step is not None else f"{x:g}"
        out.append(f'<text x="{X:.1f}" y="{height-mb+20}" text-anchor="middle" font-size="11" fill="#555">{label}</text>')
    for y in range(0, int(ymax)+1, 100):
        Y = sy(float(y))
        out.append(f'<line x1="{ml}" y1="{Y:.1f}" x2="{width-mr}" y2="{Y:.1f}" stroke="#ececec"/>')
        out.append(f'<text x="{ml-8}" y="{Y+4:.1f}" text-anchor="end" font-size="11" fill="#555">{y}</text>')
    for name, pts in groups.items():
        pts = sorted(pts)
        stroke, sw, dash = _series_style(name, actual_group=actual_group, fire_group=fire_group, style_map=style_map)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        out.append(f'<polyline points="{_polyline(pts, sx, sy)}" fill="none" stroke="{stroke}" stroke-width="{sw}"{dash_attr}/>')
    if guide_x is not None and guide_y is not None:
        X, Y = sx(guide_x), sy(guide_y)
        out.append(f'<line x1="{ml}" y1="{Y:.1f}" x2="{X:.1f}" y2="{Y:.1f}" stroke="#d62728" stroke-width="1.6" stroke-dasharray="4 4"/>')
        out.append(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{X:.1f}" y2="{height-mb}" stroke="#d62728" stroke-width="1.6" stroke-dasharray="4 4"/>')
        out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="4" fill="#d62728"/>')
        out.append(f'<text x="{X+7:.1f}" y="{Y-8:.1f}" font-size="11" fill="#d62728">Tcr={guide_y:.1f} °C; t={guide_x:.2f} мин</text>')
    out.append(f'<text x="{(ml+width-mr)/2:.1f}" y="{height-8}" text-anchor="middle" font-size="12" fill="#333">{html.escape(x_label)}</text>')
    out.append(f'<text x="16" y="{height/2:.1f}" text-anchor="middle" transform="rotate(-90 16 {height/2:.1f})" font-size="12" fill="#333">{html.escape(y_label)}</text>')
    out.append('</svg>')
    return ''.join(out)


def _fvm_model_svg(vis: Mapping[str, Any]) -> str:
    """Compact final-step FVM field; no separate dT/dx debug diagram in production UI."""
    final = vis.get("final_state")
    if not isinstance(final, Mapping):
        return ""
    temps = [float(x) for x in final.get("protection_temperatures_c") or []]
    if not temps:
        return ""
    n = len(temps)
    th = float(vis.get("protection_thickness_mm") or 0.0)
    dx = float(vis.get("dx_mm") or 0.0)
    steel = float(final.get("steel_temperature_c"))
    ymax = max(100.0, math.ceil(max([steel, *temps])/100.0)*100.0)
    w, h, x0, x1 = 840, 245, 105, 715
    cell = (x1-x0)/n
    parts = [
        f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;background:#fff;border:1px solid #ddd;border-radius:12px">',
        '<text x="22" y="112" font-size="13">Пожар</text>', '<text x="765" y="112" font-size="13">Сталь</text>',
        f'<text x="105" y="28" font-size="12" fill="#333">Температурное поле на последнем расчётном шаге · t={float(final["time_min"]):.2f} мин</text>',
    ]
    label_stride = max(1, math.ceil(n/10))
    for i, t in enumerate(temps):
        x = x0 + i*cell
        parts.append(f'<rect x="{x:.1f}" y="65" width="{cell:.1f}" height="82" fill="{_v085._temp_fill(t, ymax)}" stroke="#666" stroke-width="0.7"/>')
        if i % label_stride == 0 or i == n-1:
            parts.append(f'<text x="{x+cell/2:.1f}" y="57" text-anchor="middle" font-size="9" fill="#333">{t:.0f}°</text>')
    steel_x = x1 + 10
    parts.append(f'<rect x="{steel_x}" y="55" width="38" height="102" fill="{_v085._temp_fill(steel, ymax)}" stroke="#444"/>')
    parts.append(f'<text x="{steel_x+19}" y="49" text-anchor="middle" font-size="10">{steel:.0f}°</text>')

    graph_top, graph_bottom = 72, 140
    sy = lambda t: graph_bottom - (float(t)/ymax)*(graph_bottom-graph_top)
    points = [(x0+i*cell, sy(t)) for i, t in enumerate(temps)]
    parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in points)}" fill="none" stroke="#111" stroke-width="1.6"/>')
    for x, y in points:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.1" fill="#111"/>')
    parts.append(f'<line x1="{points[-1][0]:.1f}" y1="{points[-1][1]:.1f}" x2="{steel_x+19:.1f}" y2="{sy(steel):.1f}" stroke="#111" stroke-width="1.5" stroke-dasharray="4 3"/>')
    parts.append(f'<circle cx="{steel_x+19:.1f}" cy="{sy(steel):.1f}" r="2.4" fill="#111"/>')

    policy = vis.get("mesh_policy") if isinstance(vis.get("mesh_policy"), Mapping) else {}
    fo, dt = policy.get("fourier_number_max"), policy.get("time_step_min")
    parts.append(f'<text x="{(x0+x1)/2:.1f}" y="181" text-anchor="middle" font-size="12">δзащ={th:g} мм · рабочая сетка n={n} · Δx={dx:.3g} мм</text>')
    if isinstance(dt, (int, float)) and isinstance(fo, (int, float)):
        parts.append(f'<text x="{(x0+x1)/2:.1f}" y="201" text-anchor="middle" font-size="11" fill="#555">Δt={float(dt):.6g} мин · Fo(max)={float(fo):.3f}</text>')
    parts.append('<text x="410" y="225" text-anchor="middle" font-size="10.5" fill="#666">Один квалифицированный рабочий mesh; n→2n используется только в validation/debug, не в обычном расчёте.</text>')
    parts.append('</svg>')
    return ''.join(parts)


def _profile_chart(vis: Mapping[str, Any]) -> str:
    profiles = [r for r in vis.get("profile_samples") or [] if isinstance(r, Mapping)]
    if not profiles:
        return ""
    th = float(vis.get("protection_thickness_mm") or 0.0)
    values: list[float] = []
    for r in profiles:
        values.extend(float(v) for v in r.get("protection_temperatures_c") or [])
        if isinstance(r.get("steel_temperature_c"), (int, float)):
            values.append(float(r["steel_temperature_c"]))
    ymax = max(100.0, math.ceil(max(values or [100.0])/100.0)*100.0)
    width, height, ml, mr, mb = 800, 470, 64, 25, 55
    legend_h = 62
    mt = 25 + legend_h
    sx = lambda x: ml + float(x)/max(th, 1e-9)*(width-ml-mr)
    sy = lambda y: mt + (ymax-float(y))/ymax*(height-mt-mb)
    out = [f'<svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#fff;border:1px solid rgba(49,51,63,.18);border-radius:12px">']

    legend_names = [f"t = {float(r['time_min']):.2f} мин" for r in profiles]
    for idx, name in enumerate(legend_names):
        col, row = idx // 3, idx % 3
        xx, yy = ml + col*330, 23 + row*18
        stroke = _PROFILE_STYLES[min(idx, len(_PROFILE_STYLES)-1)] if idx < len(profiles)-1 else "#d62728"
        sw = 2.8 if idx == len(profiles)-1 else 1.5
        out.append(f'<line x1="{xx}" y1="{yy}" x2="{xx+26}" y2="{yy}" stroke="{stroke}" stroke-width="{sw}"/>')
        out.append(f'<text x="{xx+33}" y="{yy+4}" font-size="10.5" fill="#333">{html.escape(name)}</text>')

    for y in range(0, int(ymax)+1, 100):
        Y = sy(y)
        out.append(f'<line x1="{ml}" y1="{Y:.1f}" x2="{width-mr}" y2="{Y:.1f}" stroke="#ececec"/><text x="{ml-8}" y="{Y+4:.1f}" text-anchor="end" font-size="11" fill="#555">{y}</text>')
    for i in range(6):
        x = th*i/5
        X = sx(x)
        out.append(f'<line x1="{X:.1f}" y1="{mt}" x2="{X:.1f}" y2="{height-mb}" stroke="#f0f0f0"/><text x="{X:.1f}" y="{height-mb+20}" text-anchor="middle" font-size="11" fill="#555">{x:g}</text>')
    for idx, r in enumerate(profiles):
        xs = [float(x) for x in r.get("protection_node_positions_mm") or []]
        ts = [float(t) for t in r.get("protection_temperatures_c") or []]
        if len(xs) != len(ts) or not xs:
            continue
        is_final = idx == len(profiles)-1
        stroke = "#d62728" if is_final else _PROFILE_STYLES[min(idx, len(_PROFILE_STYLES)-2)]
        sw = 2.8 if is_final else 1.5
        out.append(f'<polyline points="{_polyline(list(zip(xs,ts)), sx, sy)}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>')
        steel = float(r["steel_temperature_c"])
        out.append(f'<line x1="{sx(xs[-1]):.1f}" y1="{sy(ts[-1]):.1f}" x2="{sx(th):.1f}" y2="{sy(steel):.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-dasharray="4 3"/>')
        out.append(f'<circle cx="{sx(th):.1f}" cy="{sy(steel):.1f}" r="{4 if is_final else 2.5}" fill="{stroke}"/>')
    out.append(f'<text x="{(ml+width-mr)/2:.1f}" y="{height-10}" text-anchor="middle" font-size="12">x по толщине огнезащиты, мм</text>')
    out.append(f'<text x="17" y="{height/2:.1f}" text-anchor="middle" transform="rotate(-90 17 {height/2:.1f})" font-size="12">T, °C</text>')
    out.append('</svg>')
    return ''.join(out)


def _render_fdm_visualizations(core: Any, env: Mapping[str, Any]) -> None:
    st = core.st
    trace = _v084._fdm_trace_from_env(core, env)
    if not trace:
        return
    vis = trace.get("visualization")
    if not isinstance(vis, Mapping) or vis.get("schema") != "sp554_v085_fvm_visualization_v2":
        return
    st.markdown("### Прогрев защищённого элемента · FVM / СП 554 12.5")
    t1, t2, t3 = st.tabs(["FVM-модель", "Температура по толщине", "Температура по времени"])
    with t1:
        svg = _fvm_model_svg(vis)
        if svg:
            st.markdown(svg, unsafe_allow_html=True)
        st.caption(
            "Рабочая сетка выбирается автоматически: не менее 12 интервалов, Δx ≤ 1,5 мм и устойчивый шаг времени Fo≤0,25. "
            "Обычный интерактивный расчёт выполняется один раз. Проверка n→2n остаётся validation/debug-проверкой и не замедляет каждый пользовательский расчёт."
        )
    with t2:
        svg = _profile_chart(vis)
        if svg:
            st.markdown(svg, unsafe_allow_html=True)
        st.caption(
            "Каждая сплошная линия — распределение температуры по расчётным узлам огнезащиты в момент времени, указанный в легенде. "
            "Пунктирный последний отрезок соединяет последний узел огнезащиты с отдельным сосредоточенным узлом стали на x=δзащ."
        )
    with t3:
        rows = []
        mapping = [
            ("fire_temperature_c", "ISO 834 / ГОСТ 30247.0"),
            ("surface_temperature_c", "Поверхность огнезащиты"),
            ("mid_protection_temperature_c", "Середина огнезащиты"),
            ("interface_protection_temperature_c", "Последний узел огнезащиты"),
            ("steel_temperature_c", "Сталь"),
        ]
        for r in vis.get("time_series") or []:
            for key, name in mapping:
                if isinstance(r.get(key), (int, float)):
                    rows.append({"x": float(r["time_min"]), "y": float(r[key]), "series": name})
        if rows:
            st.markdown(
                _svg_chart(
                    rows, x_key="x", y_key="y", group_key="series", x_label="t, мин", y_label="T, °C",
                    actual_group="Сталь", fire_group="ISO 834 / ГОСТ 30247.0", x_tick_step=5.0,
                    style_map=_PROTECTED_TIME_STYLES, legend=True,
                ),
                unsafe_allow_html=True,
            )
        st.caption(
            "Кривые: пожарная температура ISO 834 / ГОСТ 30247.0; поверхность огнезащиты со стороны пожара; "
            "середина слоя; последний FVM-узел огнезащиты перед сталью; отдельная температура стального элемента."
        )


def _semantic_replay(source: Any, model: Any, registry: Any):
    return _v085._semantic_replay(source, model, registry)


def install(core: Any) -> None:
    _v085.install(core)
    if getattr(core, _INSTALLED, False):
        return

    _v084._svg_chart = _svg_chart
    _v084._render_fdm_visualizations = _render_fdm_visualizations
    _v085._svg_chart = _svg_chart
    _v085._render_fdm_visualizations = _render_fdm_visualizations

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _invalidate():
        try:
            core.st.session_state.pop("_fire_contract", None)
            core.st.session_state.pop("_fire_contract_map", None)
        except Exception:
            pass

    def _upgrade(app):
        registry = app.service.registry
        install_registry_remediation(registry)
        if GRAPH_SUFFIX not in str(app.model.graph.get("graph_id") or ""):
            old_sessions = dict(app.service.sessions)
            new_model = build_model(app.model)
            new_service = GuidedCalculationService(new_model, registry=registry)
            for sid, old_session in old_sessions.items():
                new_service.sessions[sid] = _semantic_replay(old_session, new_model, registry)
            app.model = new_model
            app.service = new_service
            _invalidate()
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_svg_chart", "_profile_chart", "_fvm_model_svg", "_render_fdm_visualizations"]
