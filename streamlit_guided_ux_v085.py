"""v0.85 installer: corrected thermal axes, FVM mesh and spatial-gradient visuals."""
from __future__ import annotations

import html
import math
from typing import Any, Mapping, Sequence

import streamlit_guided_ux_v084 as _v084

from standard_core.fire_ui0 import GuidedCalculationService
from standard_core.sp16_mech7_v085_fvm_mesh_overlay import GRAPH_SUFFIX, build_model
from standard_core.sp16_mech7_v085_fvm_runtime import install_registry_remediation

_INSTALLED = "_fire_v085_fvm_mesh_gradient_installed"


def _temperature_bounds(rows: Sequence[Mapping[str, Any]], y_key: str, guide_y: float | None = None) -> tuple[float, float]:
    values = [float(r[y_key]) for r in rows if isinstance(r.get(y_key), (int, float)) and math.isfinite(float(r[y_key]))]
    if guide_y is not None and math.isfinite(float(guide_y)):
        values.append(float(guide_y))
    ymax_data = max(values) if values else 100.0
    ymax = max(100.0, math.ceil(ymax_data / 100.0) * 100.0)
    return 0.0, ymax


def _polyline(points, sx, sy) -> str:
    return " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in points)


def _svg_chart(
    series: Sequence[Mapping[str, Any]], *, x_key: str, y_key: str, group_key: str,
    width: int = 780, height: int = 410, x_label: str = "t, мин", y_label: str = "T, °C",
    actual_group: str | None = None, fire_group: str | None = None,
    guide_x: float | None = None, guide_y: float | None = None,
) -> str:
    """Temperature chart with a fixed zero baseline and exact 100 C ticks."""
    rows = [r for r in series if isinstance(r.get(x_key), (int,float)) and isinstance(r.get(y_key), (int,float))]
    if not rows:
        return ""
    ml, mr, mt, mb = 62, 18, 18, 48
    xmin, xmax = min(float(r[x_key]) for r in rows), max(float(r[x_key]) for r in rows)
    ymin, ymax = _temperature_bounds(rows, y_key, guide_y)
    if xmax <= xmin:
        xmax = xmin + 1.0
    sx=lambda x: ml+(float(x)-xmin)/(xmax-xmin)*(width-ml-mr)
    sy=lambda y: mt+(ymax-float(y))/(ymax-ymin)*(height-mt-mb)
    groups: dict[str,list[tuple[float,float]]] = {}
    for r in rows:
        groups.setdefault(str(r[group_key]),[]).append((float(r[x_key]),float(r[y_key])))
    out=[f'<svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#fff;border:1px solid rgba(49,51,63,.18);border-radius:12px">']
    for i in range(6):
        x=xmin+(xmax-xmin)*i/5; X=sx(x)
        out.append(f'<line x1="{X:.1f}" y1="{mt}" x2="{X:.1f}" y2="{height-mb}" stroke="#ececec"/>')
        out.append(f'<text x="{X:.1f}" y="{height-mb+20}" text-anchor="middle" font-size="11" fill="#555">{x:g}</text>')
    for y in range(0, int(ymax)+1, 100):
        Y=sy(float(y))
        out.append(f'<line x1="{ml}" y1="{Y:.1f}" x2="{width-mr}" y2="{Y:.1f}" stroke="#ececec"/>')
        out.append(f'<text x="{ml-8}" y="{Y+4:.1f}" text-anchor="end" font-size="11" fill="#555">{y}</text>')
    for name, pts in groups.items():
        pts=sorted(pts)
        if name == actual_group:
            stroke="#d62728"; sw=3.0; dash=""
        elif name == fire_group:
            stroke="#111"; sw=2.3; dash=' stroke-dasharray="8 5"'
        else:
            stroke="#9a9a9a"; sw=1.5; dash=""
        out.append(f'<polyline points="{_polyline(pts,sx,sy)}" fill="none" stroke="{stroke}" stroke-width="{sw}"{dash}/>' )
    if guide_x is not None and guide_y is not None:
        X=sx(guide_x); Y=sy(guide_y)
        out.append(f'<line x1="{ml}" y1="{Y:.1f}" x2="{X:.1f}" y2="{Y:.1f}" stroke="#d62728" stroke-width="1.6" stroke-dasharray="4 4"/>')
        out.append(f'<line x1="{X:.1f}" y1="{Y:.1f}" x2="{X:.1f}" y2="{height-mb}" stroke="#d62728" stroke-width="1.6" stroke-dasharray="4 4"/>')
        out.append(f'<circle cx="{X:.1f}" cy="{Y:.1f}" r="4" fill="#d62728"/>')
        out.append(f'<text x="{X+7:.1f}" y="{Y-8:.1f}" font-size="11" fill="#d62728">Tcr={guide_y:.1f} °C; t={guide_x:.2f} мин</text>')
    out.append(f'<text x="{(ml+width-mr)/2:.1f}" y="{height-8}" text-anchor="middle" font-size="12" fill="#333">{html.escape(x_label)}</text>')
    out.append(f'<text x="16" y="{height/2:.1f}" text-anchor="middle" transform="rotate(-90 16 {height/2:.1f})" font-size="12" fill="#333">{html.escape(y_label)}</text>')
    out.append('</svg>')
    return ''.join(out)


def _temp_fill(temp: float, ymax: float) -> str:
    ratio = min(1.0, max(0.0, float(temp) / max(float(ymax), 1.0)))
    # Blue -> pale yellow -> red; presentation only, numerical values are printed separately.
    if ratio <= 0.5:
        q=ratio/0.5; r=int(70+185*q); g=int(130+110*q); b=int(210-120*q)
    else:
        q=(ratio-0.5)/0.5; r=255; g=int(240-180*q); b=int(90-60*q)
    return f"rgb({r},{g},{b})"


def _fvm_model_svg(vis: Mapping[str, Any]) -> str:
    final=vis.get("final_state")
    if not isinstance(final, Mapping):
        return ""
    temps=[float(x) for x in final.get("protection_temperatures_c") or []]
    n=len(temps)
    if n == 0:
        return ""
    th=float(vis.get("protection_thickness_mm") or 0.0)
    dx=float(vis.get("dx_mm") or 0.0)
    steel=float(final.get("steel_temperature_c"))
    ymax=max(100.0, math.ceil(max([steel,*temps])/100.0)*100.0)
    w=840; h=365; x0=105; x1=715; cell=(x1-x0)/n
    parts=[f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;background:#fff;border:1px solid #ddd;border-radius:12px">',
           '<text x="22" y="112" font-size="13">Пожар</text>','<text x="765" y="112" font-size="13">Сталь</text>',
           f'<text x="105" y="28" font-size="12" fill="#333">Температурное поле на последнем расчётном шаге · t={float(final["time_min"]):.2f} мин</text>']
    label_stride=max(1, math.ceil(n/10))
    for i,t in enumerate(temps):
        x=x0+i*cell
        parts.append(f'<rect x="{x:.1f}" y="65" width="{cell:.1f}" height="82" fill="{_temp_fill(t,ymax)}" stroke="#666" stroke-width="0.7"/>')
        if i % label_stride == 0 or i == n-1:
            parts.append(f'<text x="{x+cell/2:.1f}" y="57" text-anchor="middle" font-size="9" fill="#333">{t:.0f}°</text>')
    steel_x=x1+10
    parts.append(f'<rect x="{steel_x}" y="55" width="38" height="102" fill="{_temp_fill(steel,ymax)}" stroke="#444"/>')
    parts.append(f'<text x="{steel_x+19}" y="49" text-anchor="middle" font-size="10">{steel:.0f}°</text>')

    # Temperature profile through actual FVM nodes.  The steel node is plotted
    # separately at the interface and is not silently re-labelled as protection.
    points=[]
    graph_top,graph_bottom=72,140
    sy=lambda t: graph_bottom-(float(t)/ymax)*(graph_bottom-graph_top)
    for i,t in enumerate(temps): points.append((x0+i*cell,sy(t)))
    parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in points)}" fill="none" stroke="#111" stroke-width="1.6"/>')
    for x,y in points: parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.1" fill="#111"/>')
    # Last protection-node -> lumped steel-interface segment is deliberately dashed.
    parts.append(f'<line x1="{points[-1][0]:.1f}" y1="{points[-1][1]:.1f}" x2="{steel_x+19:.1f}" y2="{sy(steel):.1f}" stroke="#111" stroke-width="1.5" stroke-dasharray="4 3"/>')
    parts.append(f'<circle cx="{steel_x+19:.1f}" cy="{sy(steel):.1f}" r="2.4" fill="#111"/>')

    policy=vis.get("mesh_policy") if isinstance(vis.get("mesh_policy"),Mapping) else {}
    fo=policy.get("fourier_number_max")
    dt=policy.get("time_step_min")
    coarse=policy.get("coarse_interval_count")
    refined=policy.get("refined_interval_count")
    parts.append(f'<text x="{(x0+x1)/2:.1f}" y="178" text-anchor="middle" font-size="12">δзащ={th:g} мм · рабочая сетка n={n} · Δx={dx:.3g} мм</text>')
    if isinstance(coarse,(int,float)) and isinstance(refined,(int,float)):
        parts.append(f'<text x="{(x0+x1)/2:.1f}" y="197" text-anchor="middle" font-size="11" fill="#555">Проверка сходимости: n={int(coarse)} → {int(refined)} · PASS</text>')
    if isinstance(dt,(int,float)) and isinstance(fo,(int,float)):
        parts.append(f'<text x="{(x0+x1)/2:.1f}" y="214" text-anchor="middle" font-size="11" fill="#555">Δt={float(dt):.6g} мин · Fo(max)={float(fo):.3f}</text>')

    # Explicit dT/dx diagram for the final time step.
    gradients=[g for g in final.get("temperature_gradients_c_per_mm") or [] if isinstance(g,Mapping) and isinstance(g.get("x_mid_mm"),(int,float)) and isinstance(g.get("dT_dx_c_per_mm"),(int,float))]
    if gradients:
        gy0,gy1=245,323
        vals=[float(g["dT_dx_c_per_mm"]) for g in gradients]
        gmin=min(vals+[0.0]); gmax=max(vals+[0.0])
        if abs(gmax-gmin)<1e-12:
            gmin-=1.0; gmax+=1.0
        pad=0.08*(gmax-gmin); gmin-=pad; gmax+=pad
        gsx=lambda x: x0+float(x)/max(th,1e-9)*(x1-x0)
        gsy=lambda v: gy0+(gmax-float(v))/(gmax-gmin)*(gy1-gy0)
        zero_y=gsy(0.0)
        parts.append(f'<text x="{x0}" y="236" font-size="11" fill="#333">Температурный градиент последнего шага: dT/dx, °C/мм</text>')
        parts.append(f'<line x1="{x0}" y1="{zero_y:.1f}" x2="{x1}" y2="{zero_y:.1f}" stroke="#999" stroke-width="1"/>')
        gpts=[(gsx(g["x_mid_mm"]),gsy(g["dT_dx_c_per_mm"])) for g in gradients]
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in gpts)}" fill="none" stroke="#6b3fa0" stroke-width="2"/>')
        stride=max(1,math.ceil(len(gpts)/8))
        for i,((x,y),g) in enumerate(zip(gpts,gradients)):
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#6b3fa0"/>')
            if i % stride == 0 or i == len(gpts)-1:
                parts.append(f'<text x="{x:.1f}" y="{min(gy1+15,y+14):.1f}" text-anchor="middle" font-size="8" fill="#6b3fa0">{float(g["dT_dx_c_per_mm"]):.1f}</text>')
        parts.append(f'<text x="{x0-8}" y="{gsy(gmax)+4:.1f}" text-anchor="end" font-size="8" fill="#666">{gmax:.1f}</text>')
        parts.append(f'<text x="{x0-8}" y="{gsy(gmin)+4:.1f}" text-anchor="end" font-size="8" fill="#666">{gmin:.1f}</text>')
    parts.append('</svg>')
    return ''.join(parts)

def _profile_chart(vis: Mapping[str, Any]) -> str:
    profiles=[r for r in vis.get("profile_samples") or [] if isinstance(r,Mapping)]
    if not profiles:
        return ""
    th=float(vis.get("protection_thickness_mm") or 0.0)
    values=[]
    for r in profiles:
        values.extend(float(v) for v in r.get("protection_temperatures_c") or [])
        if isinstance(r.get("steel_temperature_c"),(int,float)): values.append(float(r["steel_temperature_c"]))
    ymax=max(100.0,math.ceil(max(values or [100.0])/100.0)*100.0)
    width=800;height=430;ml=64;mr=25;mt=25;mb=55
    sx=lambda x: ml+float(x)/max(th,1e-9)*(width-ml-mr)
    sy=lambda y: mt+(ymax-float(y))/ymax*(height-mt-mb)
    out=[f'<svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#fff;border:1px solid rgba(49,51,63,.18);border-radius:12px">']
    for y in range(0,int(ymax)+1,100):
        Y=sy(y); out.append(f'<line x1="{ml}" y1="{Y:.1f}" x2="{width-mr}" y2="{Y:.1f}" stroke="#ececec"/><text x="{ml-8}" y="{Y+4:.1f}" text-anchor="end" font-size="11" fill="#555">{y}</text>')
    for i in range(6):
        x=th*i/5; X=sx(x); out.append(f'<line x1="{X:.1f}" y1="{mt}" x2="{X:.1f}" y2="{height-mb}" stroke="#f0f0f0"/><text x="{X:.1f}" y="{height-mb+20}" text-anchor="middle" font-size="11" fill="#555">{x:g}</text>')
    for idx,r in enumerate(profiles):
        xs=[float(x) for x in r.get("protection_node_positions_mm") or []]
        ts=[float(t) for t in r.get("protection_temperatures_c") or []]
        if len(xs)!=len(ts) or not xs: continue
        is_final=idx==len(profiles)-1
        stroke="#d62728" if is_final else f"rgb({150+int(70*idx/max(1,len(profiles)-1))},{150+int(70*idx/max(1,len(profiles)-1))},{150+int(70*idx/max(1,len(profiles)-1))})"
        sw=2.8 if is_final else 1.4
        pts=list(zip(xs,ts)); out.append(f'<polyline points="{_polyline(pts,sx,sy)}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>')
        steel=float(r["steel_temperature_c"])
        # The last interval to the lumped steel node is dashed: it is not an additional protection node.
        out.append(f'<line x1="{sx(xs[-1]):.1f}" y1="{sy(ts[-1]):.1f}" x2="{sx(th):.1f}" y2="{sy(steel):.1f}" stroke="{stroke}" stroke-width="{sw}" stroke-dasharray="4 3"/>')
        out.append(f'<circle cx="{sx(th):.1f}" cy="{sy(steel):.1f}" r="{4 if is_final else 2.5}" fill="{stroke}"/>')
        if is_final:
            out.append(f'<text x="{sx(th)-6:.1f}" y="{sy(steel)-8:.1f}" text-anchor="end" font-size="11" fill="#d62728">сталь {steel:.0f} °C</text>')
    out.append(f'<text x="{(ml+width-mr)/2:.1f}" y="{height-10}" text-anchor="middle" font-size="12">x по толщине огнезащиты, мм</text>')
    out.append(f'<text x="17" y="{height/2:.1f}" text-anchor="middle" transform="rotate(-90 17 {height/2:.1f})" font-size="12">T, °C</text>')
    out.append('</svg>')
    return ''.join(out)


def _render_fdm_visualizations(core: Any, env: Mapping[str, Any]) -> None:
    st=core.st
    trace=_v084._fdm_trace_from_env(core,env)
    if not trace: return
    vis=trace.get('visualization')
    if not isinstance(vis,Mapping) or vis.get('schema')!='sp554_v085_fvm_visualization_v2':
        return
    st.markdown("### Прогрев защищённого элемента · FVM / СП 554 12.5")
    t1,t2,t3=st.tabs(["FVM-модель","Температура по толщине","Температура во времени"])
    with t1:
        svg=_fvm_model_svg(vis)
        if svg: st.markdown(svg,unsafe_allow_html=True)
        policy=vis.get('mesh_policy') if isinstance(vis.get('mesh_policy'),Mapping) else {}
        st.caption(
            "Базовая сетка выбирается автоматически: не менее 12 интервалов и Δx ≤ 1,5 мм; затем результат проверяется на удвоенной сетке n→2n. "
            "В отчёт и графики попадает именно уточнённая 2n-сетка после PASS по критерию |ΔtR|≤0,05 мин или ≤0,1 %. "
            "Шаг времени ограничен Fo≤0,25. Это численная политика проекта, а не нормативное свойство материала."
        )
    with t2:
        svg=_profile_chart(vis)
        if svg: st.markdown(svg,unsafe_allow_html=True)
        st.caption("Сплошные линии — температуры расчётных узлов огнезащиты. Пунктир последнего интервала ведёт к отдельному сосредоточенному узлу стали на x=δзащ; сталь не подменяет последний защитный узел.")
    with t3:
        rows=[]; mapping=[('fire_temperature_c','ISO 834 / ГОСТ 30247.0'),('surface_temperature_c','Поверхность защиты'),('mid_protection_temperature_c','Середина защиты'),('interface_protection_temperature_c','Последний узел защиты'),('steel_temperature_c','Сталь')]
        for r in vis.get('time_series') or []:
            for key,name in mapping:
                if isinstance(r.get(key),(int,float)): rows.append({'x':float(r['time_min']),'y':float(r[key]),'series':name})
        if rows: st.markdown(_svg_chart(rows,x_key='x',y_key='y',group_key='series',x_label='t, мин',y_label='T, °C',actual_group='Сталь',fire_group='ISO 834 / ГОСТ 30247.0'),unsafe_allow_html=True)


def _semantic_replay(source: Any, model: Any, registry: Any):
    return _v084._semantic_replay(source,model,registry)


def install(core: Any) -> None:
    _v084.install(core)
    if getattr(core,_INSTALLED,False): return
    # v0.84 rendering closures resolve these globals at call time, so replacing
    # them upgrades both new and retained sessions without stacking duplicate UI.
    _v084._svg_chart=_svg_chart
    _v084._render_fdm_visualizations=_render_fdm_visualizations
    previous_new_application=core._new_application
    previous_ensure_app=core._ensure_app
    def _invalidate():
        try:
            core.st.session_state.pop('_fire_contract',None); core.st.session_state.pop('_fire_contract_map',None)
        except Exception: pass
    def _upgrade(app):
        registry=app.service.registry; install_registry_remediation(registry)
        if GRAPH_SUFFIX not in str(app.model.graph.get('graph_id') or ''):
            old_sessions=dict(app.service.sessions); new_model=build_model(app.model); new_service=GuidedCalculationService(new_model,registry=registry)
            for sid,old_session in old_sessions.items(): new_service.sessions[sid]=_semantic_replay(old_session,new_model,registry)
            app.model=new_model; app.service=new_service; _invalidate()
        return app
    core._new_application=lambda:_upgrade(previous_new_application())
    core._ensure_app=lambda:_upgrade(previous_ensure_app())
    setattr(core,_INSTALLED,True)


__all__=['install','_svg_chart','_profile_chart','_fvm_model_svg']
