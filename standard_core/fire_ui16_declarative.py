"""Safe declarative execution helpers for FIRE-UI1.6.

The normative DAG already carries many calculation/classification/lookup/check
specifications.  This module executes only those frozen specifications through a
small AST evaluator and deterministic table interpolation.  It intentionally
contains no ad-hoc SP16/SP554 formulas.
"""
from __future__ import annotations

import ast
import copy
import json
import math
from pathlib import Path
from typing import Any, Mapping


class DeclarativeExecutionError(ValueError):
    """
    Summary:
        Signal a fail-closed error while evaluating frozen declarative DAG specifications.

    Standard reference:
        СП 16.13330.2017 / SP554 execution infrastructure only; this exception does not define a normative formula. Audit ID: FIRE-UI16-DECL-001.

    Fields:
        Inherits the standard ``ValueError`` message payload; no additional mutable fields are introduced.

    Validation:
        Exercised by FIRE-UI1.6 declarative-runtime, route-census, and end-to-end qualification tests.

    Used by:
        Safe AST expression evaluation, declarative conditions, table lookup/interpolation, and guided DAG execution.
    """

    pass


def condition_value(condition: Mapping[str, Any] | None, values: Mapping[str, Any]) -> bool | None:
    """
    Summary:
        Evaluate a frozen DAG applicability/route condition against the resolved session quantities.

    Standard reference:
        Generic FIRE-UI1.6 DAG execution contract; normative meaning is carried by the condition stored in the frozen SP16/SP554 graph. Audit ID: FIRE-UI16-DECL-002.

    Parameters:
        condition: Frozen ``comparison``/``all_of``/``any_of``/``not`` condition or ``None``.
        values: Currently resolved quantity values keyed by DAG quantity id.

    Returns:
        ``True`` or ``False`` when resolvable, otherwise ``None`` when required quantities are not yet available.

    Assumptions:
        Condition objects have already passed DAG schema validation and use only the supported declarative operators.

    Sign convention:
        Preserves signed numeric values exactly; comparison semantics come from the frozen condition.

    Unit convention:
        No unit conversion is performed; compared quantities must already use the DAG-declared units.

    Applicability:
        FIRE-UI1.6 route applicability, branch conditions, and dependency-producer filtering.

    Limitations:
        Unknown condition/operator types fail closed rather than being inferred.

    Raises:
        DeclarativeExecutionError for unsupported condition types or comparison operators.

    Examples:
        ``condition_value({"type":"comparison","quantity_id":"has_My","operator":"eq","value":True}, {"has_My":True})`` returns ``True``.

    Tests:
        FIRE-UI1.6 declarative-runtime and signed-load end-to-end qualification tests.

    Implementation notes:
        Three-state evaluation deliberately distinguishes an inapplicable branch from a branch whose predicate is not yet resolvable.
    """
    if condition is None:
        return True
    ctype = condition.get("type")
    if ctype in {"all_of", "any_of"}:
        states = [condition_value(c, values) for c in condition.get("conditions") or []]
        if ctype == "all_of":
            if any(s is False for s in states):
                return False
            if any(s is None for s in states):
                return None
            return True
        if any(s is True for s in states):
            return True
        if any(s is None for s in states):
            return None
        return False
    if ctype == "not":
        state = condition_value(condition.get("condition"), values)
        return None if state is None else not state
    if ctype != "comparison":
        raise DeclarativeExecutionError(f"unsupported condition type: {ctype}")
    qid = condition.get("quantity_id")
    if qid not in values:
        return None
    left = values[qid]
    right = condition.get("value")
    op = condition.get("operator")
    if op == "eq": return left == right
    if op == "neq": return left != right
    if op == "in": return left in right
    if op == "not_in": return left not in right
    if op == "lt": return left < right
    if op == "lte": return left <= right
    if op == "gt": return left > right
    if op == "gte": return left >= right
    raise DeclarativeExecutionError(f"unsupported comparison operator: {op}")


def condition_quantity_ids(condition: Mapping[str, Any] | None) -> set[str]:
    """
    Summary:
        Collect every DAG quantity id referenced by a declarative condition.

    Standard reference:
        Generic FIRE-UI1.6 dependency-resolution infrastructure; normative references remain attached to the owning DAG node/edge. Audit ID: FIRE-UI16-DECL-003.

    Parameters:
        condition: Frozen condition tree or ``None``.

    Returns:
        Set of referenced quantity identifiers.

    Assumptions:
        Nested conditions use the supported ``all_of``, ``any_of``, ``not``, and ``comparison`` shapes.

    Sign convention:
        Not applicable; only identifiers are inspected.

    Unit convention:
        Not applicable.

    Applicability:
        Producer selection and deferred applicability evaluation in the FIRE-UI1.6 scheduler.

    Limitations:
        Unknown condition shapes contribute no identifiers and are rejected later by actual condition execution.

    Raises:
        Does not raise for ``None`` or structurally empty supported conditions.

    Examples:
        A comparison on ``gamma_t`` returns ``{"gamma_t"}``.

    Tests:
        FIRE-UI1.6 dependency call/return and route-census tests.

    Implementation notes:
        Traversal is recursive and deduplicates identifiers by returning a set.
    """
    if not condition:
        return set()
    ctype = condition.get("type")
    if ctype in {"all_of", "any_of"}:
        out: set[str] = set()
        for c in condition.get("conditions") or []:
            out.update(condition_quantity_ids(c))
        return out
    if ctype == "not":
        return condition_quantity_ids(condition.get("condition"))
    if ctype == "comparison" and condition.get("quantity_id"):
        return {str(condition["quantity_id"])}
    return set()


class _ObjView:
    def __init__(self, value: Mapping[str, Any]):
        self._value = value
    def __getattr__(self, name: str) -> Any:
        if name not in self._value:
            raise DeclarativeExecutionError(f"object has no field {name}")
        v = self._value[name]
        return _ObjView(v) if isinstance(v, Mapping) else v


def _wrap(v: Any) -> Any:
    return _ObjView(v) if isinstance(v, Mapping) else v


def _is_finite(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def _max_non_null(*args: Any) -> float:
    vals = [float(v) for v in args if v is not None]
    if not vals:
        raise DeclarativeExecutionError("max_non_null has no values")
    return max(vals)


def _min_non_null(*args: Any) -> float:
    vals = [float(v) for v in args if v is not None]
    if not vals:
        raise DeclarativeExecutionError("min_non_null has no values")
    return min(vals)


def _select_phi_ey_or_phi_y(phi_ey: Any, phi_y: Any) -> float:
    vals = [float(v) for v in (phi_ey, phi_y) if v is not None]
    if not vals:
        raise DeclarativeExecutionError("neither phi_ey nor phi_y is available")
    return min(vals)


def _signed_compression_term(v: Any) -> float:
    # Frozen DAG uses this helper for the worst compressive contribution of a
    # signed moment/bimoment term.  Magnitude is the conservative envelope.
    return abs(float(v))

def _zero_field(points: Any) -> list[float]:
    return [0.0 for _ in _point_rows(points)]

def _local_web_field(points: Any, sigma_loc: Any, *, zero_elsewhere: bool = True, preserve_point_keys: bool = True) -> list[float]:
    points=_unwrap(points)
    raw = points.get("points") if isinstance(points, Mapping) else points
    if not isinstance(raw, list) or not raw:
        raise DeclarativeExecutionError("local_web_field requires section points")
    out=[]
    for p in raw:
        region=str(p.get("region") or "") if isinstance(p, Mapping) else ""
        active = "web" in region.lower()
        out.append(float(sigma_loc) if active else (0.0 if zero_elsewhere else float("nan")))
    return out


def _unwrap(v: Any) -> Any:
    if isinstance(v, _ObjView): return v._value
    return v

def _point_rows(points: Any) -> list[dict[str, float]]:
    points=_unwrap(points)
    if isinstance(points, Mapping):
        points = points.get("points")
    if not isinstance(points, list) or not points:
        raise DeclarativeExecutionError("section_evaluation_points must contain a non-empty points list")
    rows=[]
    for p in points:
        if not isinstance(p, Mapping):
            raise DeclarativeExecutionError("section point must be an object")
        rows.append({k: float(p.get(k) or 0.0) for k in ("x","y","omega")})
    return rows


def _field_over_section_points(points: Any, expression_value: Any = None) -> Any:
    # Direct AST calls with a point-dependent expression are handled specially
    # by _Evaluator.visit_Call; this fallback only supports already materialized fields.
    if isinstance(expression_value, list):
        return expression_value
    raise DeclarativeExecutionError("field_over_section_points requires point-dependent expression")


_SIMPLE_FUNCS = {
    "abs": abs, "sqrt": math.sqrt, "min": min, "max": max, "bool": bool,
    "tuple": tuple, "is_finite": _is_finite, "max_non_null": _max_non_null,
    "min_non_null": _min_non_null, "select_phi_ey_or_phi_y": _select_phi_ey_or_phi_y,
    "signed_compression_term": _signed_compression_term,
    "zero_field": _zero_field, "local_web_field": _local_web_field,
}


class _Evaluator(ast.NodeVisitor):
    def __init__(self, env: Mapping[str, Any], point: Mapping[str, float] | None = None):
        self.env = dict(env)
        self.point = dict(point or {})

    def visit_Expression(self, node): return self.visit(node.body)
    def visit_Constant(self, node): return node.value
    def visit_Name(self, node):
        if node.id in {"true", "True"}: return True
        if node.id in {"false", "False"}: return False
        if node.id in {"null", "None"}: return None
        if node.id == "pi": return math.pi
        if node.id in self.point: return self.point[node.id]
        if node.id in self.env: return self.env[node.id]
        if node.id in _SIMPLE_FUNCS: return _SIMPLE_FUNCS[node.id]
        raise DeclarativeExecutionError(f"unknown expression name: {node.id}")
    def visit_Attribute(self, node):
        base=self.visit(node.value)
        if isinstance(base,_ObjView): return getattr(base,node.attr)
        if isinstance(base,Mapping):
            if node.attr not in base: raise DeclarativeExecutionError(f"object has no field {node.attr}")
            return base[node.attr]
        raise DeclarativeExecutionError("attribute access is allowed only on mapping values")
    def visit_BinOp(self,node):
        a,b=self.visit(node.left),self.visit(node.right)
        if isinstance(node.op,ast.Add): return a+b
        if isinstance(node.op,ast.Sub): return a-b
        if isinstance(node.op,ast.Mult): return a*b
        if isinstance(node.op,ast.Div): return a/b
        if isinstance(node.op,ast.Pow): return a**b
        # The frozen expr_v1 corpus uses ^ with mathematical exponent semantics.
        # Python parses ^ as BitXor, therefore interpret it as power here.
        if isinstance(node.op,ast.BitXor): return a**b
        if isinstance(node.op,ast.Mod): return a%b
        raise DeclarativeExecutionError(f"unsupported binary operator {type(node.op).__name__}")
    def visit_UnaryOp(self,node):
        v=self.visit(node.operand)
        if isinstance(node.op,ast.USub): return -v
        if isinstance(node.op,ast.UAdd): return +v
        if isinstance(node.op,ast.Not): return not v
        raise DeclarativeExecutionError(f"unsupported unary operator {type(node.op).__name__}")
    def visit_Compare(self,node):
        left=self.visit(node.left)
        for op,comp in zip(node.ops,node.comparators):
            right=self.visit(comp)
            ok = (left==right if isinstance(op,ast.Eq) else
                  left!=right if isinstance(op,ast.NotEq) else
                  left<right if isinstance(op,ast.Lt) else
                  left<=right if isinstance(op,ast.LtE) else
                  left>right if isinstance(op,ast.Gt) else
                  left>=right if isinstance(op,ast.GtE) else
                  left in right if isinstance(op,ast.In) else
                  left not in right if isinstance(op,ast.NotIn) else None)
            if ok is None: raise DeclarativeExecutionError(f"unsupported comparison {type(op).__name__}")
            if not ok: return False
            left=right
        return True
    def visit_BoolOp(self,node):
        vals=[self.visit(v) for v in node.values]
        if isinstance(node.op,ast.And): return all(vals)
        if isinstance(node.op,ast.Or): return any(vals)
        raise DeclarativeExecutionError(f"unsupported boolean operator {type(node.op).__name__}")
    def visit_IfExp(self,node): return self.visit(node.body if self.visit(node.test) else node.orelse)
    def visit_Call(self,node):
        if not isinstance(node.func,ast.Name):
            raise DeclarativeExecutionError("only named helper calls are allowed")
        name=node.func.id
        if name == "field_over_section_points":
            points=self.visit(node.args[0]); rows=_point_rows(points)
            if len(node.args)<2: raise DeclarativeExecutionError("field_over_section_points requires point expression")
            expr=node.args[1]
            return [_Evaluator(self.env,p).visit(expr) for p in rows]
        if name == "max_abs_over_section_points":
            points=self.visit(node.args[0]); rows=_point_rows(points)
            if len(node.args)<2: raise DeclarativeExecutionError("max_abs_over_section_points requires point expression")
            expr=node.args[1]; vals=[_Evaluator(self.env,p).visit(expr) for p in rows]
            return max(abs(float(v)) for v in vals)
        if name == "max_abs_field":
            field=self.visit(node.args[0])
            if not isinstance(field,list) or not field: raise DeclarativeExecutionError("max_abs_field requires non-empty field")
            return max(abs(float(v)) for v in field)
        if name == "max_over_common_section_points":
            # Signature used by SP554 10.4: expression, field1, field2, ... .
            # Evaluate the first AST expression index-by-index, binding aliases
            # sigma_x/sigma_y/tau_xy from *_field argument names.
            if len(node.args)<2: raise DeclarativeExecutionError("max_over_common_section_points requires expression and fields")
            expr=node.args[0]
            fields=[]; aliases=[]
            for arg in node.args[1:]:
                vals=self.visit(arg)
                if not isinstance(vals,list) or not vals: raise DeclarativeExecutionError("common-point field must be a non-empty list")
                fields.append(vals)
                if isinstance(arg,ast.Name):
                    alias=arg.id[:-6] if arg.id.endswith("_field") else arg.id
                else: alias=f"field_{len(aliases)}"
                aliases.append(alias)
            n=len(fields[0])
            if any(len(f)!=n for f in fields): raise DeclarativeExecutionError("common-point fields have different lengths")
            vals=[]
            for i in range(n):
                env=dict(self.env)
                for alias,field in zip(aliases,fields): env[alias]=field[i]
                vals.append(_Evaluator(env,self.point).visit(expr))
            return max(float(v) for v in vals)
        if name not in _SIMPLE_FUNCS:
            raise DeclarativeExecutionError(f"unsupported expression helper: {name}")
        fn=_SIMPLE_FUNCS[name]
        return fn(*[self.visit(a) for a in node.args], **{kw.arg:self.visit(kw.value) for kw in node.keywords})
    def generic_visit(self,node):
        raise DeclarativeExecutionError(f"unsupported AST node: {type(node).__name__}")


def eval_expr(expression: str, env: Mapping[str, Any]) -> Any:
    """
    Summary:
        Evaluate one frozen ``expr_v1`` expression with the restricted FIRE-UI1.6 AST interpreter.

    Standard reference:
        Executes expressions transcribed into the frozen SP16/SP554 DAG; no additional normative equation is introduced here. Audit ID: FIRE-UI16-DECL-004.

    Parameters:
        expression: Frozen declarative expression string.
        env: Resolved quantity environment keyed by DAG ids.

    Returns:
        Scalar, boolean, list field, or structured value produced by the supported expression.

    Assumptions:
        Expression provenance and quantity units are already frozen in the DAG.

    Sign convention:
        Signed values are preserved unless the frozen expression explicitly applies ``abs`` or another transformation.

    Unit convention:
        Uses the units of supplied quantities; no implicit conversion is performed.

    Applicability:
        Declarative SP16/SP554 calculation, classification, and check nodes in FIRE-UI1.6.

    Limitations:
        Only whitelisted AST nodes and helper functions are executable; arbitrary Python execution is prohibited.

    Raises:
        DeclarativeExecutionError for unsupported syntax, unknown symbols, invalid helper calls, or malformed fields.

    Examples:
        ``eval_expr("abs(N)/(A_n*Ry)", values)`` evaluates the frozen expression when all quantities are present.

    Tests:
        FIRE-UI1.6 declarative-runtime, formula-pipeline, and end-to-end route tests.

    Implementation notes:
        Mathematical ``^`` tokens are normalized to exponent semantics before Python AST parsing to preserve the frozen corpus notation.
    """
    # expr_v1 uses mathematical caret notation. Replace before Python parsing
    # so exponent precedence is preserved (mapping ast.BitXor afterwards is not).
    expression=expression.replace("^", "**")
    tree=ast.parse(expression,mode="eval")
    wrapped={k:_wrap(v) for k,v in env.items()}
    return _Evaluator(wrapped).visit(tree)


def _dataset(model: Any, dataset_id: str) -> Mapping[str, Any]:
    for ds in model.graph.get("datasets") or []:
        if ds.get("id") == dataset_id:
            return ds
    raise DeclarativeExecutionError(f"unknown dataset {dataset_id}")


def _rows_for_dataset(model: Any, ds: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    storage=ds.get("storage") or {}
    if storage.get("mode") == "inline":
        return list(storage.get("rows") or [])
    if storage.get("mode") == "external":
        if not model.source_path: raise DeclarativeExecutionError("external dataset requires model.source_path")
        p=(Path(model.source_path).parent / str(storage["uri"])).resolve()
        obj=json.loads(p.read_text(encoding="utf-8"))
        if isinstance(obj,list): return obj
        if isinstance(obj,dict) and isinstance(obj.get("rows"),list): return obj["rows"]
        if isinstance(obj,dict) and isinstance(obj.get("profiles"),list): return obj["profiles"]
        raise DeclarativeExecutionError(f"unsupported external dataset shape for {ds['id']}")
    raise DeclarativeExecutionError(f"unsupported dataset storage mode for {ds['id']}")


def _lerp(x,x0,x1,y0,y1):
    if x1==x0: return float(y0)
    return float(y0)+(float(y1)-float(y0))*(float(x)-float(x0))/(float(x1)-float(x0))


def _lookup(model: Any, spec: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    ds=_dataset(model,spec["dataset_id"]); rows=_rows_for_dataset(model,ds)
    selectors={b["dataset_field"]: values[b["quantity_id"]] for b in spec.get("selector_bindings") or [] if b["quantity_id"] in values}
    if len(selectors) != len(spec.get("selector_bindings") or []):
        missing=[b["quantity_id"] for b in spec.get("selector_bindings") or [] if b["quantity_id"] not in values]
        raise DeclarativeExecutionError(f"lookup missing selectors {missing}")
    method=((spec.get("interpolation") or {}).get("method") or "none")
    outputs=spec.get("output_bindings") or []
    if method == "none":
        matches=[r for r in rows if all(r.get(k)==v for k,v in selectors.items())]
        if len(matches)!=1: raise DeclarativeExecutionError(f"exact lookup {ds['id']} expected 1 row, got {len(matches)} for {selectors}")
        return {b["quantity_id"]: matches[0][b["dataset_field"]] for b in outputs}
    axis_text=(spec.get("interpolation") or {}).get("axis") or ""
    axes=[x.strip() for x in axis_text.split(",") if x.strip()]
    if method == "linear":
        if len(axes)!=1: raise DeclarativeExecutionError("linear lookup requires one interpolation axis")
        ax=axes[0]; x=float(selectors[ax]); cats={k:v for k,v in selectors.items() if k!=ax}
        cand=sorted([r for r in rows if all(r.get(k)==v for k,v in cats.items())], key=lambda r: float(r[ax]))
        exact=[r for r in cand if float(r[ax])==x]
        if exact: return {b["quantity_id"]: exact[0][b["dataset_field"]] for b in outputs}
        lo=[r for r in cand if float(r[ax])<x]; hi=[r for r in cand if float(r[ax])>x]
        if not lo or not hi: raise DeclarativeExecutionError(f"linear lookup {ds['id']} extrapolation forbidden at {x}")
        a,b=lo[-1],hi[0]
        return {ob["quantity_id"]:_lerp(x,float(a[ax]),float(b[ax]),a[ob["dataset_field"]],b[ob["dataset_field"]]) for ob in outputs}
    if method == "bilinear":
        if len(axes)!=2: raise DeclarativeExecutionError("bilinear lookup requires two axes")
        ax,ay=axes; x=float(selectors[ax]); y=float(selectors[ay]); cats={k:v for k,v in selectors.items() if k not in axes}
        cand=[r for r in rows if all(r.get(k)==v for k,v in cats.items())]
        xs=sorted({float(r[ax]) for r in cand}); ys=sorted({float(r[ay]) for r in cand})
        def bracket(vals,z):
            if z in vals: return z,z
            lo=[v for v in vals if v<z]; hi=[v for v in vals if v>z]
            if not lo or not hi: raise DeclarativeExecutionError(f"bilinear lookup {ds['id']} extrapolation forbidden")
            return lo[-1],hi[0]
        x0,x1=bracket(xs,x); y0,y1=bracket(ys,y)
        def row_at(xx,yy):
            rr=[r for r in cand if float(r[ax])==xx and float(r[ay])==yy]
            if len(rr)!=1: raise DeclarativeExecutionError(f"bilinear grid point missing {xx},{yy}")
            return rr[0]
        out={}
        for ob in outputs:
            f=ob["dataset_field"]
            q00=float(row_at(x0,y0)[f])
            if x0==x1 and y0==y1: val=q00
            elif x0==x1: val=_lerp(y,y0,y1,q00,float(row_at(x0,y1)[f]))
            elif y0==y1: val=_lerp(x,x0,x1,q00,float(row_at(x1,y0)[f]))
            else:
                q10=float(row_at(x1,y0)[f]); q01=float(row_at(x0,y1)[f]); q11=float(row_at(x1,y1)[f])
                r0=_lerp(x,x0,x1,q00,q10); r1=_lerp(x,x0,x1,q01,q11); val=_lerp(y,y0,y1,r0,r1)
            out[ob["quantity_id"]]=val
        return out
    raise DeclarativeExecutionError(f"unsupported lookup interpolation method {method}")


def can_execute_declarative(node: Mapping[str, Any]) -> bool:
    """
    Summary:
        Report whether a DAG node carries a declarative specification supported by the FIRE-UI1.6 runtime.

    Standard reference:
        Generic execution capability check for frozen SP16/SP554 DAG nodes. Audit ID: FIRE-UI16-DECL-005.

    Parameters:
        node: One frozen normative DAG node.

    Returns:
        ``True`` when the node contains a supported calculation, classification, lookup, or check specification.

    Assumptions:
        Node schema validation has already occurred.

    Sign convention:
        Not applicable.

    Unit convention:
        Not applicable.

    Applicability:
        Guided executor dispatch before falling back to explicitly registered Python executors.

    Limitations:
        Capability does not guarantee that all required inputs are currently resolved.

    Raises:
        Does not intentionally raise for ordinary mapping input.

    Examples:
        A node with ``calculation_spec`` returns ``True``.

    Tests:
        FIRE-UI1.6 declarative dispatch and route-census tests.

    Implementation notes:
        This is a structural capability predicate, not an engineering applicability decision.
    """
    if node.get("classification_rules") and node.get("output_quantity_id"): return True
    if node.get("lookup_spec"): return True
    if node.get("check_condition") and len(node.get("produces") or []) == 1: return True
    spec=node.get("calculation_spec") or node.get("check_spec")
    if spec and spec.get("expression_language") in {"expr_v1","executor_v1"}:
        if spec.get("expression") or spec.get("cases"): return True
    return False


def _neutral_missing(qid: str, values: Mapping[str, Any]) -> Any:
    # Mathematically neutral denominator placeholders are admitted only when the
    # corresponding signed action is exactly zero. They are not materialized in
    # the ledger and therefore cannot masquerade as resolved section properties.
    pairs={
        "W_omega_eff":"B_bimoment", "I_omega_n":"B_bimoment",
        "W_pl_x_eff":"M_x", "I_xn":"M_x",
        "W_pl_y_eff":"M_y", "I_yn":"M_y",
    }
    action=pairs.get(qid)
    if action and action in values and float(values[action])==0.0: return 1.0
    raise KeyError(qid)


def required_missing(node: Mapping[str, Any], values: Mapping[str, Any]) -> list[str]:
    """
    Summary:
        Determine unresolved required inputs for one declaratively executable DAG node.

    Standard reference:
        Generic FIRE-UI1.6 dependency scheduler over frozen SP16/SP554 node requirements. Audit ID: FIRE-UI16-DECL-006.

    Parameters:
        node: Frozen DAG node carrying a declarative execution specification.
        values: Resolved session quantities.

    Returns:
        Ordered list of required quantity ids that are not yet available.

    Assumptions:
        Required inputs are declared by the frozen node specification rather than inferred from engineering heuristics.

    Sign convention:
        Not applicable.

    Unit convention:
        Not applicable.

    Applicability:
        Dependency call/return scheduling and deferred branch execution.

    Limitations:
        Optional quantities do not appear in the returned list unless made conditionally required by the frozen spec.

    Raises:
        DeclarativeExecutionError when the node's declarative specification is malformed.

    Examples:
        A node requiring ``N`` and ``A_n`` returns ``["A_n"]`` when only ``N`` is resolved.

    Tests:
        FIRE-UI1.6 dependency-resolution and parallel-branch tests.

    Implementation notes:
        The result feeds producer resolution; it never fabricates defaults for unresolved engineering inputs.
    """
    missing=[]
    for b in node.get("consumes") or []:
        qid=b["quantity_id"]
        if not b.get("required") or qid in values: continue
        try: _neutral_missing(qid,values)
        except KeyError: missing.append(qid)
    return missing


def execute_declarative(model: Any, node: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
    """
    Summary:
        Execute one supported frozen declarative SP16/SP554 DAG node and return its produced quantities.

    Standard reference:
        Normative formula/table provenance is taken exclusively from the supplied frozen DAG node and referenced datasets. Audit ID: FIRE-UI16-DECL-007.

    Parameters:
        model: Loaded immutable normative DAG model providing referenced datasets.
        node: Frozen calculation/classification/lookup/check DAG node.
        values: Resolved input quantities for the current guided session.

    Returns:
        Mapping from produced quantity ids to calculated, classified, checked, or lookup values.

    Assumptions:
        Required inputs are present, referenced datasets are immutable package resources, and the node passed schema/audit validation.

    Sign convention:
        Preserves signed session loads and applies sign transformations only when explicitly encoded in the frozen specification.

    Unit convention:
        Uses DAG-declared and dataset units without hidden conversion.

    Applicability:
        FIRE-UI1.6 guided execution of supported frozen declarative SP16/SP554 nodes.

    Limitations:
        Unsupported specification shapes, prohibited extrapolation, and ambiguous lookups fail closed.

    Raises:
        DeclarativeExecutionError for missing or invalid inputs, unsupported specifications, invalid table domains, or unsafe expressions.

    Examples:
        The scheduler invokes this function only after ``required_missing`` reports no unresolved mandatory inputs.

    Tests:
        FIRE-UI1.6 signed-load matrix, lookup/interpolation, dependency-resolution, and mechanical-to-thermal boundary tests.

    Implementation notes:
        Execution is deterministic and uses only the restricted AST/table runtime; arbitrary ``eval`` is never used.
    """
    if node.get("classification_rules") and node.get("output_quantity_id"):
        matches=[]; unresolved=False
        for r in node["classification_rules"]:
            st=condition_value(r.get("when"),values)
            if st is True: matches.append(r)
            elif st is None: unresolved=True
        if len(matches)==1: return {node["output_quantity_id"]: copy.deepcopy(matches[0]["output_value"])}
        if len(matches)>1: raise DeclarativeExecutionError(f"classification {node['id']} has multiple matches")
        if unresolved: raise DeclarativeExecutionError(f"classification {node['id']} condition unresolved")
        if node.get("fallback_behavior") == "explicit_value" and "fallback_value" in node:
            return {node["output_quantity_id"]: copy.deepcopy(node["fallback_value"])}
        raise DeclarativeExecutionError(f"classification {node['id']} has no match")
    if node.get("lookup_spec"):
        return _lookup(model,node["lookup_spec"],values)
    if node.get("check_condition"):
        state=condition_value(node["check_condition"],values)
        if state is None: raise DeclarativeExecutionError(f"check {node['id']} condition unresolved")
        produces=node.get("produces") or []
        if len(produces)!=1: raise DeclarativeExecutionError(f"check node {node['id']} must have one output")
        return {produces[0]["quantity_id"]: bool(state)}
    spec=node.get("calculation_spec") or node.get("check_spec")
    if not spec: raise DeclarativeExecutionError(f"node {node['id']} has no declarative spec")
    env={}
    for b in spec.get("bindings") or []:
        qid=b["quantity_id"]
        if qid in values: env[b["variable"]]=values[qid]
        else:
            try: env[b["variable"]]=_neutral_missing(qid,values)
            except KeyError:
                # Optional bindings may legitimately be absent in a non-selected piecewise case.
                required=next((bool(x.get("required")) for x in node.get("consumes") or [] if x.get("quantity_id")==qid),False)
                if required: raise DeclarativeExecutionError(f"node {node['id']} missing binding {qid}")
                env[b["variable"]]=None
    expression=spec.get("expression")
    if not expression and spec.get("cases"):
        matches=[]; unresolved=False
        for case in spec["cases"]:
            state=condition_value(case.get("when"),values)
            if state is True: matches.append(case)
            elif state is None: unresolved=True
        if len(matches)>1: raise DeclarativeExecutionError(f"piecewise node {node['id']} has multiple matching cases")
        if not matches:
            if unresolved: raise DeclarativeExecutionError(f"piecewise node {node['id']} conditions unresolved")
            raise DeclarativeExecutionError(f"piecewise node {node['id']} has no matching case")
        expression=matches[0].get("expression")
    if not expression: raise DeclarativeExecutionError(f"node {node['id']} has no executable expression")
    result=eval_expr(expression,env)
    produces=node.get("produces") or []
    if len(produces)!=1:
        raise DeclarativeExecutionError(f"generic expression node {node['id']} must have exactly one produced quantity")
    return {produces[0]["quantity_id"]: result}
