"""v0.84 installer: calculated thermal diagrams and thermal UX defaults."""
from __future__ import annotations

import html
import math
from typing import Any, Mapping, Sequence

import streamlit_guided_ux_v083 as _v083

from standard_core.fire_ui0 import GuidedCalculationService, FireUIError
from standard_core.sp16_mech7_v084_thermal_visual_overlay import GRAPH_SUFFIX, build_model
from standard_core.sp16_mech7_v084_thermal_visual_runtime import (
    install_registry_remediation,
    unprotected_heating_diagram,
    protected_fdm_visualization,
)

_INSTALLED = "_fire_v084_thermal_visualization_installed"
_FIRE_REGIME_NODE = "SP554_D_FIRE_REGIME"
_INITIAL_TEMP_NODE = "GOST30247_I_INITIAL_FURNACE_TEMPERATURE"
_JOINTS_NODE = "SP554_D_JOINTS"
_VALIDATION_NODE = "SP554_I_12_6_VALIDATION_EVIDENCE"


def _default_payload_for_node(node_id: str, old_payload: Any) -> Any:
    """Return v0.84 visible defaults without silently submitting them."""
    if old_payload is not None:
        return old_payload
    if node_id == _JOINTS_NODE:
        return False
    if node_id == _INITIAL_TEMP_NODE:
        return 20.0
    if node_id == _VALIDATION_NODE:
        return {
            "protection_12_6_max_deviation_pct": 20.0,
            "protection_12_6_validation_evidence_complete": True,
        }
    return old_payload


def _ledger_values(core: Any, env: Mapping[str, Any]) -> dict[str, Any]:
    return {row.get("quantity_id"): row.get("value") for row in env.get("state", {}).get("ledger", [])}


def _polyline(points: Sequence[tuple[float, float]], sx, sy) -> str:
    return " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in points)


def _svg_chart(
    series: Sequence[Mapping[str, Any]], *, x_key: str, y_key: str, group_key: str,
    width: int = 780, height: int = 410, x_label: str = "t, мин", y_label: str = "T, °C",
    actual_group: str | None = None, fire_group: str | None = None,
    guide_x: float | None = None, guide_y: float | None = None,
) -> str:
    rows = [r for r in series if isinstance(r.get(x_key), (int,float)) and isinstance(r.get(y_key), (int,float))]
    if not rows:
        return ""
    ml, mr, mt, mb = 58, 18, 18, 48
    xmin, xmax = min(float(r[x_key]) for r in rows), max(float(r[x_key]) for r in rows)
    ymin, ymax = min(float(r[y_key]) for r in rows), max(float(r[y_key]) for r in rows)
    if guide_y is not None: ymin, ymax = min(ymin, guide_y), max(ymax, guide_y)
    if xmax <= xmin: xmax = xmin + 1.0
    if ymax <= ymin: ymax = ymin + 1.0
    pad = 0.04*(ymax-ymin); ymin -= pad; ymax += pad
    sx=lambda x: ml+(float(x)-xmin)/(xmax-xmin)*(width-ml-mr)
    sy=lambda y: mt+(ymax-float(y))/(ymax-ymin)*(height-mt-mb)
    groups: dict[str,list[tuple[float,float]]] = {}
    for r in rows: groups.setdefault(str(r[group_key]),[]).append((float(r[x_key]),float(r[y_key])))
    out=[f'<svg viewBox="0 0 {width} {height}" style="width:100%;height:auto;background:#fff;border:1px solid rgba(49,51,63,.18);border-radius:12px">']
    # grid + labels
    for i in range(6):
        x=xmin+(xmax-xmin)*i/5; X=sx(x)
        out.append(f'<line x1="{X:.1f}" y1="{mt}" x2="{X:.1f}" y2="{height-mb}" stroke="#ececec"/>')
        out.append(f'<text x="{X:.1f}" y="{height-mb+20}" text-anchor="middle" font-size="11" fill="#555">{x:g}</text>')
    for i in range(6):
        y=ymin+(ymax-ymin)*i/5; Y=sy(y)
        out.append(f'<line x1="{ml}" y1="{Y:.1f}" x2="{width-mr}" y2="{Y:.1f}" stroke="#ececec"/>')
        out.append(f'<text x="{ml-8}" y="{Y+4:.1f}" text-anchor="end" font-size="11" fill="#555">{y:.0f}</text>')
    # series
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


def _render_unprotected_chart(core: Any, env: Mapping[str, Any], initial: float) -> None:
    st=core.st
    vals=_ledger_values(core,env)
    try:
        data=unprotected_heating_diagram(vals, initial_temperature_c=float(initial))
    except Exception as exc:
        st.info(f"Диаграмма появится после определения δпр и критической температуры: {exc}")
        return
    actual_name=f"Расчётная δпр={data['actual_reduced_thickness_mm']:g} мм"
    combined=[*data['steel_series'],*data['fire_series']]
    svg=_svg_chart(combined,x_key='time_min',y_key='temperature_c',group_key='series',
                   actual_group=actual_name,fire_group='ISO 834 / ГОСТ 30247.0',
                   guide_x=data.get('actual_crossing_time_min'),guide_y=data.get('critical_temperature_c'))
    st.markdown("**Прогрев незащищённого стального элемента — СП 554, 12.1–12.4**")
    st.markdown(svg,unsafe_allow_html=True)
    st.caption("Серые: δпр = 3, 5, 10, 15, 20 мм · красная: фактическая δпр · пунктир: ISO 834 / ГОСТ 30247.0. Время достижения Tcr определяется пересечением красной кривой с горизонталью Tcr.")


def _render_fire_thermal_card(core: Any, env: Mapping[str, Any], card: Mapping[str, Any], old_payload: Any, mode_key: str):
    st=core.st
    values=[o['value'] for o in card.get('options',[])]
    labels={o['value']:o.get('label',o['value']) for o in card.get('options',[])}
    current=old_payload if old_payload in values else 'standard'
    c1,c2=st.columns(2)
    regime=c1.selectbox("Режим пожара",values,index=values.index(current),format_func=lambda x:labels.get(x,str(x)),key=f"fire:v084:{mode_key}:regime")
    temp=float(st.session_state.get("fire:v084:initial_temperature_c",20.0))
    temp=c2.number_input("Начальная температура T₀, °C",min_value=1.0,max_value=40.0,value=temp,step=1.0,key="fire:v084:initial_temperature_c")
    if regime=='standard':
        _render_unprotected_chart(core,env,float(temp))
    else:
        st.info("Расчётная диаграмма 12.1–12.4 на этой вкладке относится к стандартному температурному режиму.")
    return regime,{"v084_initial_temperature_c":float(temp)},True


def _fdm_trace_from_env(core: Any, env: Mapping[str, Any]) -> Mapping[str, Any] | None:
    trace=core._ledger_value(env,"protection_12_5_calculation_trace")
    if not isinstance(trace,Mapping): return None
    if isinstance(trace.get('selected_result'),Mapping): trace=trace['selected_result']
    return trace


def _render_fdm_visualizations(core: Any, env: Mapping[str, Any]) -> None:
    st=core.st; trace=_fdm_trace_from_env(core,env)
    if not trace: return
    vis=trace.get('visualization')
    if not isinstance(vis,Mapping) or vis.get('schema')!='sp554_v084_fdm_visualization_v1':
        try:
            vis=protected_fdm_visualization(_ledger_values(core,env))
        except Exception as exc:
            st.info(f"FVM-графики недоступны для текущего состояния: {exc}")
            return
    st.markdown("### Прогрев защищённого элемента · FVM / СП 554 12.5")
    t1,t2,t3=st.tabs(["FVM-модель","Температура по толщине","Температура во времени"])
    with t1:
        n=int(vis.get('layer_count') or 0); th=float(vis.get('protection_thickness_mm') or 0); dx=float(vis.get('dx_mm') or 0)
        w=760; h=180; x0=120; x1=650; cell=(x1-x0)/max(n,1)
        parts=[f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;background:#fff;border:1px solid #ddd;border-radius:12px">',
               '<text x="25" y="90" font-size="13">Пожар</text>','<text x="675" y="90" font-size="13">Сталь</text>']
        for i in range(n):
            x=x0+i*cell; parts.append(f'<rect x="{x:.1f}" y="55" width="{cell:.1f}" height="60" fill="#f3f3f3" stroke="#777"/><text x="{x+cell/2:.1f}" y="90" text-anchor="middle" font-size="11">{i+1}</text>')
        parts.append(f'<rect x="{x1}" y="45" width="22" height="80" fill="#bbb" stroke="#555"/><text x="{(x0+x1)/2:.1f}" y="145" text-anchor="middle" font-size="12">δзащ={th:g} мм · n={n} · Δx={dx:g} мм</text></svg>')
        st.markdown(''.join(parts),unsafe_allow_html=True)
        st.caption("Одномерная конечно-разностная/контроль-объёмная модель СП 554 12.5; последний полуэлемент защиты связан с сосредоточенной теплоёмкостью стали по (12.7).")
    with t2:
        rows=[]
        for prof in vis.get('profile_samples') or []:
            name=f"t={float(prof['time_min']):g} мин"
            for x,y in zip(prof.get('positions_mm') or [],prof.get('temperatures_c') or []): rows.append({'x':float(x),'y':float(y),'series':name})
        if rows: st.markdown(_svg_chart(rows,x_key='x',y_key='y',group_key='series',x_label='Координата по толщине защиты, мм',y_label='T, °C'),unsafe_allow_html=True)
    with t3:
        rows=[]; mapping=[('fire_temperature_c','ISO 834 / ГОСТ 30247.0'),('surface_temperature_c','Поверхность защиты'),('mid_protection_temperature_c','Середина защиты'),('interface_protection_temperature_c','Граница защита/сталь'),('steel_temperature_c','Сталь')]
        for r in vis.get('time_series') or []:
            for key,name in mapping:
                if isinstance(r.get(key),(int,float)): rows.append({'x':float(r['time_min']),'y':float(r[key]),'series':name})
        if rows: st.markdown(_svg_chart(rows,x_key='x',y_key='y',group_key='series',x_label='t, мин',y_label='T, °C',actual_group='Сталь',fire_group='ISO 834 / ГОСТ 30247.0'),unsafe_allow_html=True)


def _semantic_replay(source: Any, model: Any, registry: Any):
    return _v083._semantic_replay(source,model,registry)


def install(core: Any) -> None:
    _v083.install(core)
    if getattr(core,_INSTALLED,False): return
    # core.st is the actual Streamlit module in production and fake module in tests.
    previous_generic=core._render_generic
    previous_body=core._render_card_body
    previous_submit=core._submit
    previous_noninteractive=core._render_noninteractive

    def _render_generic(card,old_payload,old_provenance,mode_key):
        nid=card.get('node_id')
        old_payload=_default_payload_for_node(str(nid or ''),old_payload)
        payload,prov,ready=previous_generic(card,old_payload,old_provenance,mode_key)
        if nid==_VALIDATION_NODE:
            core.st.caption("Предзаполнено значениями 20 % / Да. Нажатие «Далее» является подтверждением, что фактический набор валидационных случаев 12.6 полон и максимальное отклонение действительно не превышает указанное значение.")
        return payload,prov,ready

    def _render_card_body(app,sid,env,card,old_payload,old_provenance,mode_key):
        if card.get('node_id')==_FIRE_REGIME_NODE:
            return _render_fire_thermal_card(core,env,card,old_payload,mode_key)
        return previous_body(app,sid,env,card,old_payload,old_provenance,mode_key)

    def _submit(app,sid,card,payload,provenance,editing):
        if editing or card.get('node_id')!=_FIRE_REGIME_NODE:
            return previous_submit(app,sid,card,payload,provenance,editing)
        try:
            app.service.submit(sid,payload,provenance=provenance)
            session=app.service.get_session(sid)
            if payload=='standard' and session.current_node_id==_INITIAL_TEMP_NODE:
                temp=float((provenance or {}).get('v084_initial_temperature_c',20.0))
                app.service.submit(sid,temp,provenance={"ui_surface":"v0.84_combined_thermal_card","default_or_user_value":temp})
            core.st.rerun()
        except FireUIError as exc:
            core.st.error(str(exc))

    def _render_noninteractive(env,card):
        previous_noninteractive(env,card)
        _render_fdm_visualizations(core,env)

    core._render_generic=_render_generic
    core._render_card_body=_render_card_body
    core._submit=_submit
    core._render_noninteractive=_render_noninteractive

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

__all__=['install','_default_payload_for_node']
