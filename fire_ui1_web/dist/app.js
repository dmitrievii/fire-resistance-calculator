"use strict";
const $ = (id) => {
    const node = document.getElementById(id);
    if (!node)
        throw new Error(`Missing UI element: ${id}`);
    return node;
};
const els = {
    question: $("question-card"),
    next: $("next-button"),
    back: $("back-button"),
    cancelEdit: $("cancel-edit"),
    editIndicator: $("edit-indicator"),
    history: $("history-bar"),
    status: $("status-pill"),
    step: $("step-label"),
    graph: $("graph-id"),
    ledger: $("ledger-view"),
    trace: $("trace-view"),
    ledgerToolbar: $("ledger-toolbar"),
    ledgerSearch: $("ledger-search"),
    ledgerFilter: $("ledger-filter"),
    message: $("message-area"),
    footer: $("normative-footer"),
    newSession: $("new-session"),
    saveSession: $("save-session"),
    loadSession: $("load-session"),
};
let contract = null;
let envelope = null;
let draftPayload = undefined;
let draftProvenance = null;
let submitInFlight = false;
let historyCursor = null;
let catalogFamilies = null;
let materialStrengthCatalogCache = null;
let activeTab = "ledger";
function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
function formatNumber(value) {
    if (!Number.isFinite(value))
        return String(value);
    const abs = Math.abs(value);
    if ((abs !== 0 && abs < 1e-4) || abs >= 1e7)
        return value.toExponential(5);
    return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 6 }).format(value);
}
function displayValue(value) {
    if (typeof value === "boolean")
        return value ? "Да" : "Нет";
    if (typeof value === "number")
        return formatNumber(value);
    if (Array.isArray(value))
        return value.join(", ");
    if (value && typeof value === "object")
        return JSON.stringify(value);
    return String(value ?? "—");
}
function cardByNodeId(nodeId) {
    if (!contract)
        return null;
    return contract.node_cards.find((c) => c.node_id === nodeId) ?? null;
}
function currentRenderCard() {
    if (!envelope)
        return null;
    if (historyCursor !== null) {
        const row = (envelope.state.interaction_history ?? [])[historyCursor];
        return row ? cardByNodeId(row.node_id) : envelope.current_card;
    }
    return envelope.current_card;
}
function currentHistoryRow() {
    if (!envelope || historyCursor === null)
        return null;
    return (envelope.state.interaction_history ?? [])[historyCursor] ?? null;
}
function setMessage(message = "") {
    els.message.innerHTML = message ? `<div class="error-message">${escapeHtml(message)}</div>` : "";
}
async function api(path, init) {
    const response = await fetch(path, {
        ...init,
        headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
    const data = await response.json();
    if (!response.ok)
        throw new Error(data.error || `HTTP ${response.status}`);
    return data;
}
function statusClass(status) {
    const s = status.toLowerCase();
    if (s.startsWith("blocked"))
        return "blocked";
    if (s === "result")
        return "result";
    if (s === "complete")
        return "complete";
    if (s.includes("awaiting"))
        return "awaiting";
    return "";
}
function statusLabel(status) {
    if (status === "AWAITING_INPUT")
        return "Ожидается ответ";
    if (status === "RESULT")
        return "Результат маршрута";
    if (status === "COMPLETE")
        return "Расчёт завершён";
    if (status.startsWith("BLOCKED_EXECUTOR_REQUIRED"))
        return "Ожидается producer binding (UI2)";
    if (status.startsWith("BLOCKED_MISSING_INPUTS"))
        return "Не хватает исходных данных";
    if (status.startsWith("BLOCKED"))
        return "Маршрут остановлен fail-closed";
    return status;
}
function refsHtml(refs = []) {
    if (!refs.length)
        return "";
    const chips = refs.map((r) => {
        const std = r.standard_id || "Норма";
        const parts = [r.section ? `разд. ${r.section}` : "", r.clause ? `п. ${r.clause}` : "", r.formula_ref ? `формула ${r.formula_ref}` : "", r.table_ref ? `табл. ${r.table_ref}` : ""].filter(Boolean);
        return `<span class="normative-ref">${escapeHtml(std)}${parts.length ? ` · ${escapeHtml(parts.join(" · "))}` : ""}</span>`;
    });
    return `<div class="normative-ref-list">${chips.join("")}</div>`;
}
function renderFooter(card) {
    const refs = card?.normative_refs ?? [];
    if (!refs.length) {
        els.footer.textContent = "Для текущего состояния нет отдельной нормативной ссылки.";
        return;
    }
    const text = refs.map((r) => {
        const parts = [r.standard_id, r.clause ? `п. ${r.clause}` : null, r.formula_ref ? `формула ${r.formula_ref}` : null, r.table_ref ? `табл. ${r.table_ref}` : null].filter(Boolean);
        return parts.join(" · ");
    }).join("  |  ");
    els.footer.textContent = text;
}
function optionSource(card, field) {
    // FIRE-UI2.1: boolean must never be shadowed by an empty enum_values array.
    // The backend now also materializes these choices in the UI contract, but
    // the frontend keeps an independent fallback for saved/older contracts.
    if (field.data_type === "boolean")
        return [{ value: true, label: "Да" }, { value: false, label: "Нет" }];
    if (Array.isArray(card.options) && card.options.length)
        return card.options;
    if (Array.isArray(field.enum_values) && field.enum_values.length)
        return field.enum_values;
    return [];
}
function selectedValueForReview() {
    const row = currentHistoryRow();
    return row ? { payload: row.payload, provenance: row.provenance ?? null } : null;
}
function stableJson(value) {
    return JSON.stringify(value ?? null);
}
function reviewChanged() {
    const original = selectedValueForReview();
    if (!original)
        return false;
    return stableJson(original.payload) !== stableJson(draftPayload) || stableJson(original.provenance) !== stableJson(draftProvenance);
}
function renderField(card, field, currentValue) {
    const unit = field.canonical_unit ? `<div class="unit-box">${escapeHtml(field.canonical_unit)}</div>` : "";
    if (field.data_type === "number") {
        return `<div class="field-block">
      <label class="field-label" for="field-${escapeHtml(field.quantity_id)}">${escapeHtml(field.label)}</label>
      <div class="field-row"><input class="number-input" id="field-${escapeHtml(field.quantity_id)}" data-field="${escapeHtml(field.quantity_id)}" type="number" step="any" value="${currentValue ?? ""}">${unit}</div>
      <div class="field-meta">${escapeHtml(field.symbol ? `${field.symbol} · ` : "")}${escapeHtml(field.quantity_id)}</div>
    </div>`;
    }
    if (field.data_type === "enum" || field.data_type === "boolean") {
        const options = optionSource(card, field);
        return `<div class="field-block">
      <label class="field-label" for="field-${escapeHtml(field.quantity_id)}">${escapeHtml(field.label)}</label>
      <select class="select-input" id="field-${escapeHtml(field.quantity_id)}" data-field="${escapeHtml(field.quantity_id)}">
        <option value="">— выберите —</option>
        ${options.map((o) => `<option value="${escapeHtml(String(o.value))}" ${currentValue === o.value ? "selected" : ""}>${escapeHtml(o.label ?? o.value)}</option>`).join("")}
      </select>
      <div class="field-meta">${escapeHtml(field.quantity_id)}</div>
    </div>`;
    }
    return `<div class="field-block">
    <label class="field-label" for="field-${escapeHtml(field.quantity_id)}">${escapeHtml(field.label)}</label>
    <input class="text-input" id="field-${escapeHtml(field.quantity_id)}" data-field="${escapeHtml(field.quantity_id)}" type="text" value="${escapeHtml(currentValue ?? "")}">
    <div class="field-meta">${escapeHtml(field.quantity_id)}</div>
  </div>`;
}
function sectionFamilyFromShapeGroup(shapeGroup) {
    const map = {
        I_ROLLED_DSYMM: "i_section", CHANNEL: "channel", ANGLE: "angle", TEE: "tee",
        RHS_SHS: "rhs_shs", CHS: "chs", C_LIPPED_SECTION: "other", Z_SECTION: "other",
    };
    return map[shapeGroup] ?? "other";
}
function sectionShapeSvg(shapeGroup) {
    const common = `viewBox="0 0 120 120" class="section-svg" aria-label="${escapeHtml(shapeGroup)}"`;
    if (shapeGroup === "I_ROLLED_DSYMM")
        return `<svg ${common}><path d="M20 18 H100 V30 H67 V90 H100 V102 H20 V90 H53 V30 H20 Z" fill="none" stroke="currentColor" stroke-width="6"/></svg>`;
    if (shapeGroup === "RHS_SHS")
        return `<svg ${common}><rect x="20" y="20" width="80" height="80" rx="7" fill="none" stroke="currentColor" stroke-width="7"/><rect x="36" y="36" width="48" height="48" rx="3" fill="none" stroke="currentColor" stroke-width="5"/></svg>`;
    if (shapeGroup === "CHS")
        return `<svg ${common}><circle cx="60" cy="60" r="42" fill="none" stroke="currentColor" stroke-width="7"/><circle cx="60" cy="60" r="27" fill="none" stroke="currentColor" stroke-width="5"/></svg>`;
    if (shapeGroup === "CHANNEL")
        return `<svg ${common}><path d="M92 20 H30 V100 H92 M30 20 H92 M30 100 H92" fill="none" stroke="currentColor" stroke-width="8" stroke-linejoin="round"/></svg>`;
    if (shapeGroup === "ANGLE")
        return `<svg ${common}><path d="M30 20 V92 H100" fill="none" stroke="currentColor" stroke-width="12" stroke-linejoin="miter"/></svg>`;
    if (shapeGroup === "TEE")
        return `<svg ${common}><path d="M20 25 H100 M60 25 V100" fill="none" stroke="currentColor" stroke-width="10"/></svg>`;
    if (shapeGroup === "Z_SECTION")
        return `<svg ${common}><path d="M18 24 H96 L24 96 H102" fill="none" stroke="currentColor" stroke-width="8" stroke-linejoin="round"/></svg>`;
    if (shapeGroup === "C_LIPPED_SECTION")
        return `<svg ${common}><path d="M92 22 H34 V98 H92 M92 22 V40 M92 98 V80" fill="none" stroke="currentColor" stroke-width="7"/></svg>`;
    return `<svg ${common}><path d="M28 25 H92 V95 H28 Z" fill="none" stroke="currentColor" stroke-width="6" stroke-dasharray="8 5"/></svg>`;
}
function renderSectionEditorEntry(card, edit) {
    draftPayload = edit?.payload;
    draftProvenance = null;
    const current = draftPayload;
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">Сечение</span><span>Section Editor</span></div>
    <h1>Основные характеристики сечения</h1>
    <p class="question-subtitle">Выберите способ задания сечения. Геометрические свойства будут материализованы автоматически либо введены вручную для произвольного сечения.</p>
    <div class="section-composition-grid">
      <div class="section-composition active"><strong>Одноветвевое</strong><span>Профиль из сортамента или параметрический шаблон.</span>
        <div class="option-grid compact">
          <button class="option-card ${current === "catalog_section" ? "selected" : ""}" data-geometry-mode="catalog_section"><span class="option-title">Из сортамента</span><span class="option-description">Семейство ГОСТ → профиль → свойства автоматически</span></button>
          <button class="option-card ${current === "parametric_section" ? "selected" : ""}" data-geometry-mode="parametric_section"><span class="option-title">Параметрическое</span><span class="option-description">Поля зависят от выбранной формы</span></button>
        </div>
      </div>
      <div class="section-composition active"><strong>Двухветвевое</strong><span>Две одинаковые ветви из сортамента; решётка/планки задаются далее по СП16.</span>
        <button class="option-card ${current === "double_branch_section" ? "selected" : ""}" data-geometry-mode="double_branch_section"><span class="option-title">Задать две ветви</span></button>
      </div>
      <div class="section-composition active"><strong>Произвольное</strong><span>Ручной ввод готовых характеристик. 2D-контур не используется.</span>
        <button class="option-card ${current === "arbitrary_section" ? "selected" : ""}" data-geometry-mode="arbitrary_section"><span class="option-title">Ввести характеристики</span></button>
      </div>
    </div>
    ${refsHtml(card.normative_refs)}`;
    els.question.querySelectorAll("[data-geometry-mode]").forEach((button) => {
        button.addEventListener("click", () => {
            draftPayload = button.dataset.geometryMode;
            els.question.querySelectorAll("[data-geometry-mode]").forEach((x) => x.classList.remove("selected"));
            button.classList.add("selected");
            updateNextState();
        });
    });
}
function profilePreviewHtml(resolved) {
    const d = resolved.dimensions ?? {}, p = resolved.catalog_properties_interim ?? {}, der = resolved.derived_properties ?? {};
    const rows = [
        ["h", d.h_mm, "mm"], ["b", d.b_mm, "mm"], ["tw", d.tw_mm, "mm"], ["tf", d.tf_mm, "mm"], ["r", d.r_mm, "mm"],
        ["A", p.A_mm2, "mm²"], ["Ix", p.Ix_mm4, "mm⁴"], ["Iy", p.Iy_mm4, "mm⁴"], ["Wx", p.Wx1_mm3, "mm³"], ["Wy", p.Wy1_mm3, "mm³"],
        ["ix", der.radius_x_mm, "mm"], ["iy", der.radius_y_mm, "mm"], ["m", der.mass_kg_m_at_7850, "kg/m"],
    ];
    const shape = String(resolved.shape_group ?? "OTHER");
    return `<div class="profile-preview"><div class="section-sketch">${sectionShapeSvg(shape)}<div class="axis-label axis-x">x</div><div class="axis-label axis-y">y</div></div><div class="profile-metrics">${rows.map(r => `<div><span>${escapeHtml(r[0])}</span><b>${r[1] == null ? "—" : escapeHtml(formatNumber(Number(r[1])))} ${r[2]}</b></div>`).join("")}</div></div>
    <div class="catalog-note">Тип: ${escapeHtml(shape)} · источник: ${escapeHtml(resolved.family?.caption ?? "catalog")} · строка ${escapeHtml(resolved.profile_ref?.source_row_id ?? "—")}. Каталог остаётся interim до original-GOST audit.</div>`;
}
async function renderProfileCatalogSelector(card, edit) {
    draftPayload = edit?.payload;
    draftProvenance = null;
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">Сечение</span><span>Сортамент</span></div>
    <h1>Выбор профиля из сортамента</h1>
    <p class="question-subtitle">Выберите семейство и профиль. После выбора production profile resolver автоматически передаст свойства в расчёт.</p>
    <div class="field-block"><label class="field-label">Сортамент / семейство</label><select id="catalog-family" class="select-input"><option>Загрузка…</option></select></div>
    <div class="field-block"><label class="field-label">Профиль</label><select id="catalog-profile" class="select-input" disabled><option>— сначала выберите семейство —</option></select></div>
    <div id="catalog-preview" class="catalog-preview"></div>${refsHtml(card.normative_refs)}`;
    if (!catalogFamilies) {
        const payload = await api("/api/profile-catalog/families");
        catalogFamilies = payload.families ?? [];
    }
    const familySelect = $("catalog-family"), profileSelect = $("catalog-profile");
    familySelect.innerHTML = `<option value="">— выберите семейство —</option>` + (catalogFamilies ?? []).map((f) => {
        const cold = ["C_LIPPED_SECTION", "Z_SECTION"].includes(f.shape_group);
        return `<option value="${escapeHtml(String(f.family_id))}" ${cold ? "disabled" : ""}>${escapeHtml(f.caption)}${cold ? " — вне текущей области СП554" : ""}</option>`;
    }).join("");
    const oldFamily = Number(edit?.payload?.section_catalog_family_id ?? 0);
    if (oldFamily)
        familySelect.value = String(oldFamily);
    const loadProfiles = async (familyId, selectOld = false) => {
        profileSelect.disabled = true;
        profileSelect.innerHTML = `<option>Загрузка…</option>`;
        const data = await api(`/api/profile-catalog/families/${familyId}/profiles`);
        profileSelect.innerHTML = `<option value="">— выберите профиль —</option>` + (data.profiles ?? []).map((p) => `<option value="${escapeHtml(`${p.designation}::${p.source_row_id}`)}">${escapeHtml(p.designation)}</option>`).join("");
        profileSelect.disabled = false;
        if (selectOld && edit?.payload?.section_designation) {
            const row = Number(edit.payload.section_catalog_source_row_id ?? 0);
            profileSelect.value = `${edit.payload.section_designation}::${row}`;
            if (profileSelect.value)
                await resolveSelection();
        }
    };
    const resolveSelection = async () => {
        const familyId = Number(familySelect.value), selected = profileSelect.value;
        if (!familyId || !selected) {
            draftPayload = undefined;
            updateNextState();
            return;
        }
        const [designation, rowText] = selected.split("::"), row = Number(rowText);
        const resolved = await api(`/api/profile-catalog/resolve?family_id=${familyId}&designation=${encodeURIComponent(designation)}&source_row_id=${row}`);
        const shape = resolved.shape_group;
        draftPayload = { section_catalog_standard: resolved.source?.product_standard_label_unverified ?? resolved.family?.caption ?? "catalog", section_designation: designation,
            section_family: sectionFamilyFromShapeGroup(shape), sp16_i_symmetry_class: shape === "I_ROLLED_DSYMM" ? "double_symmetric" : "not_i",
            section_catalog_family_id: familyId, section_catalog_source_row_id: row };
        $("catalog-preview").innerHTML = profilePreviewHtml(resolved);
        updateNextState();
    };
    familySelect.addEventListener("change", () => { draftPayload = undefined; $("catalog-preview").innerHTML = ""; if (familySelect.value)
        void loadProfiles(Number(familySelect.value));
    else {
        profileSelect.disabled = true;
        profileSelect.innerHTML = `<option>— сначала выберите семейство —</option>`;
    } updateNextState(); });
    profileSelect.addEventListener("change", () => void resolveSelection());
    if (oldFamily)
        await loadProfiles(oldFamily, true);
    updateNextState();
}
function renderParametricSectionEditor(card, edit) {
    const old = edit?.payload ?? {};
    draftPayload = edit?.payload;
    draftProvenance = null;
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">Сечение</span><span>Параметрическое</span></div><h1>Параметрическая геометрия</h1>
    <p class="question-subtitle">После выбора формы показываются только физически относящиеся к ней размеры.</p>
    <div class="field-block"><label class="field-label">Тип сечения</label><select id="param-family" class="select-input">
      <option value="">— выберите —</option><option value="i_section">Двутавр</option><option value="channel">Швеллер</option><option value="angle">Уголок</option><option value="tee">Тавр</option><option value="rhs_shs">Замкнутый прямоугольный/квадратный профиль</option><option value="chs">Круглая труба</option></select></div>
    <div id="param-fields"></div>${refsHtml(card.normative_refs)}`;
    const sel = $("param-family");
    sel.value = old.section_family ?? "";
    const box = $("param-fields");
    const config = {
        i_section: [["sec_h", "h, мм"], ["sec_b", "b, мм"], ["t_w", "tw, мм"], ["t_f", "tf, мм"], ["r_root", "r, мм (необязательно)"]],
        channel: [["sec_h", "h, мм"], ["sec_b", "b, мм"], ["t_w", "tw, мм"], ["t_f", "tf, мм"], ["r_root", "r, мм (необязательно)"]],
        tee: [["sec_h", "h, мм"], ["sec_b", "b, мм"], ["t_w", "tw, мм"], ["t_f", "tf, мм"], ["r_root", "r, мм (необязательно)"]],
        angle: [["sec_h", "полка 1, мм"], ["sec_b", "полка 2, мм"], ["t_w", "t, мм"], ["r_root", "r, мм (необязательно)"]],
        rhs_shs: [["sec_h", "h, мм"], ["sec_b", "b, мм"], ["t_w", "t, мм"]],
        chs: [["sec_h", "D, мм"], ["t_w", "t, мм"]],
    };
    const draw = () => {
        const fam = sel.value, fields = config[fam] ?? [];
        box.innerHTML = fields.map((r) => `<div class="field-block"><label class="field-label">${escapeHtml(r[1])}</label><input class="number-input" data-param="${r[0]}" type="number" step="any" value="${escapeHtml(old[r[0]] ?? "")}"></div>`).join("");
        const sync = () => { if (!fam) {
            draftPayload = undefined;
            updateNextState();
            return;
        } const obj = { section_family: fam }; let ready = true; box.querySelectorAll("[data-param]").forEach(inp => { if (inp.value !== "")
            obj[inp.dataset.param] = Number(inp.value);
        else if (inp.dataset.param !== "r_root")
            ready = false; }); if (fam === "i_section")
            obj.sp16_i_symmetry_class = "double_symmetric"; draftPayload = ready ? obj : undefined; updateNextState(); };
        box.querySelectorAll("input").forEach(x => x.addEventListener("input", sync));
        sync();
    };
    sel.addEventListener("change", () => { draftPayload = undefined; draw(); });
    draw();
}
function renderManualSectionPropertiesEditor(card, edit) {
    const old = edit?.payload?.section_geometry_2d ?? {};
    draftPayload = edit?.payload;
    draftProvenance = null;
    const required = ["A_gross", "J_x", "J_y", "W_el_x_pos", "W_el_x_neg", "W_el_y_pos", "W_el_y_neg", "W_pl_x", "W_pl_y"];
    const optional = ["I_shear_gross", "S_shear_gross", "I_omega_gross", "W_omega_gross", "P_heated_m"];
    const labels = { A_gross: "A, мм²", J_x: "Jx, мм⁴", J_y: "Jy, мм⁴", W_el_x_pos: "Wx,+, мм³", W_el_x_neg: "Wx,−, мм³", W_el_y_pos: "Wy,+, мм³", W_el_y_neg: "Wy,−, мм³", W_pl_x: "Wpl,x, мм³", W_pl_y: "Wpl,y, мм³", I_shear_gross: "I для среза, мм⁴", S_shear_gross: "S для среза, мм³", I_omega_gross: "Iω, мм⁶", W_omega_gross: "Wω, мм⁴", P_heated_m: "Нагреваемый периметр Π, м" };
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">Сечение</span><span>Произвольное</span></div><h1>Готовые характеристики сечения</h1><p class="question-subtitle">Введите известные свойства. Контур 2D не требуется.</p>
    <div class="weakening-grid">${required.map(k => `<label>${labels[k]}<input class="number-input" data-manual="${k}" type="number" step="any" value="${escapeHtml(old[k] ?? "")}"></label>`).join("")}</div>
    <details><summary>Дополнительные характеристики</summary><div class="weakening-grid">${optional.map(k => `<label>${labels[k]}<input class="number-input" data-manual="${k}" type="number" step="any" value="${escapeHtml(old[k] ?? "")}"></label>`).join("")}</div></details>
    <div class="weakening-grid"><label>Классификация<select id="manual-family" class="select-input"><option value="other">Другое</option><option value="i_section">Двутавр</option><option value="channel">Швеллер</option><option value="rhs_shs">Коробчатое</option><option value="chs">Круглая труба</option></select></label></div>${refsHtml(card.normative_refs)}`;
    const fam = $("manual-family");
    fam.value = old.section_family ?? "other";
    const sync = () => { const obj = { section_family: fam.value, section_is_box: fam.value === "rhs_shs", section_is_channel: fam.value === "channel", section_is_pipe: fam.value === "chs", sp16_i_symmetry_class: fam.value === "i_section" ? "double_symmetric" : "not_i" }; let ready = true; els.question.querySelectorAll("[data-manual]").forEach(inp => { if (inp.value !== "")
        obj[inp.dataset.manual] = Number(inp.value);
    else if (required.includes(inp.dataset.manual))
        ready = false; }); draftPayload = ready ? { section_geometry_2d: obj } : undefined; updateNextState(); };
    els.question.querySelectorAll("input").forEach(x => x.addEventListener("input", sync));
    fam.addEventListener("change", sync);
    sync();
}
async function renderDoubleBranchSectionEditor(card, edit) {
    const old = edit?.payload ?? {};
    draftPayload = edit?.payload;
    draftProvenance = null;
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">Сечение</span><span>Двухветвевое</span></div><h1>Двухветвевое сечение</h1><p class="question-subtitle">Две одинаковые ветви с параллельными локальными осями. Решётка/планки задаются далее.</p>
    <div class="field-block"><label class="field-label">Ось симметрии</label><select id="db-axis" class="select-input"><option value="y">Y — ветви разнесены по X</option><option value="x">X — ветви разнесены по Y</option></select></div>
    <div class="field-block"><label class="field-label">Расстояние между центрами ветвей, мм</label><input id="db-spacing" class="number-input" type="number" step="any" value="${escapeHtml(old.double_branch_spacing_mm ?? "")}"></div>
    <div class="field-block"><label class="field-label">Сортамент ветви</label><select id="db-family" class="select-input"><option>Загрузка…</option></select></div>
    <div class="field-block"><label class="field-label">Профиль ветви</label><select id="db-profile" class="select-input" disabled><option>— сначала семейство —</option></select></div><div id="db-preview"></div>${refsHtml(card.normative_refs)}`;
    if (!catalogFamilies) {
        const payload = await api("/api/profile-catalog/families");
        catalogFamilies = payload.families ?? [];
    }
    const axis = $("db-axis"), spacing = $("db-spacing"), fs = $("db-family"), ps = $("db-profile");
    axis.value = old.double_branch_symmetry_axis ?? "y";
    fs.innerHTML = `<option value="">— выберите —</option>` + (catalogFamilies ?? []).filter((f) => !["C_LIPPED_SECTION", "Z_SECTION"].includes(f.shape_group)).map((f) => `<option value="${f.family_id}">${escapeHtml(f.caption)}</option>`).join("");
    let selected = null;
    const sync = () => { const sp = Number(spacing.value); draftPayload = (selected && sp > 0) ? { double_branch_symmetry_axis: axis.value, double_branch_spacing_mm: sp, double_branch_family_id: Number(fs.value), double_branch_designation: selected.designation, double_branch_source_row_id: selected.source_row_id } : undefined; updateNextState(); };
    const load = async (fid, restore = false) => { ps.disabled = true; const data = await api(`/api/profile-catalog/families/${fid}/profiles`); ps.innerHTML = `<option value="">— выберите профиль —</option>` + (data.profiles ?? []).map((p) => `<option value="${escapeHtml(`${p.designation}::${p.source_row_id}`)}">${escapeHtml(p.designation)}</option>`).join(""); ps.disabled = false; if (restore && old.double_branch_designation) {
        ps.value = `${old.double_branch_designation}::${old.double_branch_source_row_id}`;
        if (ps.value)
            await resolve();
    } };
    const resolve = async () => { if (!fs.value || !ps.value) {
        selected = null;
        sync();
        return;
    } const [designation, rowText] = ps.value.split("::"); const row = Number(rowText); const r = await api(`/api/profile-catalog/resolve?family_id=${fs.value}&designation=${encodeURIComponent(designation)}&source_row_id=${row}`); selected = { designation, source_row_id: row }; $("db-preview").innerHTML = profilePreviewHtml(r); sync(); };
    fs.addEventListener("change", () => { selected = null; $("db-preview").innerHTML = ""; if (fs.value)
        void load(Number(fs.value)); sync(); });
    ps.addEventListener("change", () => void resolve());
    axis.addEventListener("change", sync);
    spacing.addEventListener("input", sync);
    if (old.double_branch_family_id) {
        fs.value = String(old.double_branch_family_id);
        await load(Number(fs.value), true);
    }
    sync();
}
async function renderMaterialStrengthEditor(card, edit) {
    const old = edit?.payload ?? {};
    draftPayload = edit?.payload;
    draftProvenance = null;
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">Материал</span><span>СП16 · приложение В</span></div>
    <h1>Сталь и нормативные сопротивления</h1>
    <p class="question-subtitle">Вид проката определяет таблицу В.3/В.4/В.5. Марка и диапазон толщины выбираются только из материализованных строк СП16 — без ручного ввода нормативного документа поставки.</p>
    <div class="material-editor-grid">
      <div class="field-block"><label class="field-label">Вид проката / изделия</label><select id="mat-product" class="select-input"></select><div id="mat-product-hint" class="field-meta"></div></div>
      <div class="field-block"><label class="field-label">Марка стали</label><select id="mat-grade" class="select-input" disabled><option value="">— сначала выберите вид проката —</option></select></div>
      <div class="field-block"><label class="field-label">Толщина для выбора Ryn</label><select id="mat-interval" class="select-input" disabled><option value="">— сначала выберите марку —</option></select><div id="mat-thickness-hint" class="field-meta"></div></div>
    </div>
    <div id="mat-preview" class="material-resistance-preview"></div>
    ${refsHtml(card.normative_refs)}`;
    if (!materialStrengthCatalogCache)
        materialStrengthCatalogCache = await api("/api/material-strength/catalog");
    const context = envelope ? await api(`/api/sessions/${encodeURIComponent(envelope.session_id)}/material-strength-context`) : {};
    const products = materialStrengthCatalogCache?.products ?? [];
    const product = $("mat-product");
    const grade = $("mat-grade");
    const interval = $("mat-interval");
    const preview = $("mat-preview");
    const productHint = $("mat-product-hint");
    const thicknessHint = $("mat-thickness-hint");
    product.innerHTML = `<option value="">— выберите —</option>` + products.map((p) => `<option value="${escapeHtml(p.value)}">${escapeHtml(p.label)} · СП16 ${escapeHtml(p.source_table)}</option>`).join("");
    const initialProduct = old.steel_product_form ?? context.suggested_product_form ?? "";
    if (initialProduct)
        product.value = initialProduct;
    const exactThickness = Number(context.exact_governing_thickness_mm);
    const hasExactThickness = Number.isFinite(exactThickness) && exactThickness > 0;
    productHint.textContent = context.suggestion_reason ? `Предложено по выбранному сечению: ${context.suggestion_reason}.` : "";
    thicknessHint.textContent = hasExactThickness ? `Из геометрии сечения известна фактическая определяющая толщина: ${formatNumber(exactThickness)} мм.` : "Выберите нормативный диапазон толщины.";
    const selectedProduct = () => products.find((p) => p.value === product.value) ?? null;
    const selectedGrade = () => selectedProduct()?.grades?.find((g) => g.steel_grade === grade.value) ?? null;
    const selectedInterval = () => selectedGrade()?.intervals?.find((i) => i.interval_key === interval.value) ?? null;
    const contains = (row, t) => {
        const x = row.thickness_interval ?? {};
        if (x.min_mm != null && (t < Number(x.min_mm) || (t === Number(x.min_mm) && !x.min_inclusive)))
            return false;
        if (x.max_mm != null && (t > Number(x.max_mm) || (t === Number(x.max_mm) && !x.max_inclusive)))
            return false;
        return true;
    };
    const renderPreview = () => {
        const p = selectedProduct(), r = selectedInterval();
        if (!p || !r) {
            preview.innerHTML = "";
            draftPayload = undefined;
            updateNextState();
            return;
        }
        const rs = r.Rs_from_tabulated_Ry_MPa;
        preview.innerHTML = `<div class="material-source-row"><strong>СП16, таблица ${escapeHtml(p.source_table)}</strong><span>${escapeHtml(grade.value)} · ${escapeHtml(r.interval_label)}</span></div>
      <div class="resistance-grid">
        <div><span>Ryn</span><b>${r.Ryn_MPa == null ? "—" : escapeHtml(formatNumber(Number(r.Ryn_MPa)))} MPa</b></div>
        <div><span>Run</span><b>${r.Run_MPa == null ? "—" : escapeHtml(formatNumber(Number(r.Run_MPa)))} MPa</b></div>
        <div><span>Ry</span><b>${r.Ry_MPa == null ? "—" : escapeHtml(formatNumber(Number(r.Ry_MPa)))} MPa</b></div>
        <div><span>Ru</span><b>${r.Ru_MPa == null ? "—" : escapeHtml(formatNumber(Number(r.Ru_MPa)))} MPa</b></div>
        <div><span>Rs*</span><b>${rs == null ? "—" : escapeHtml(formatNumber(Number(rs)))} MPa</b></div>
      </div>
      <div class="catalog-note">* Rs здесь показан только как справочный preview 0,58·Ry(tabulated). Production Rs по таблице 2 материализуется после явного выбора γm.</div>`;
        const obj = { steel_product_form: product.value, steel_grade: grade.value, steel_strength_interval_key: interval.value };
        if (hasExactThickness && context.suggested_product_form === product.value && contains(r, exactThickness))
            obj.governing_product_thickness_mm = exactThickness;
        draftPayload = obj;
        updateNextState();
    };
    const fillIntervals = (preserve = "") => {
        const g = selectedGrade();
        if (!g) {
            interval.disabled = true;
            interval.innerHTML = `<option value="">— сначала выберите марку —</option>`;
            preview.innerHTML = "";
            draftPayload = undefined;
            updateNextState();
            return;
        }
        interval.disabled = false;
        interval.innerHTML = `<option value="">— выберите диапазон —</option>` + (g.intervals ?? []).map((r) => `<option value="${escapeHtml(r.interval_key)}">${escapeHtml(r.interval_label)}</option>`).join("");
        if (preserve && (g.intervals ?? []).some((r) => r.interval_key === preserve))
            interval.value = preserve;
        else if (hasExactThickness && context.suggested_product_form === product.value) {
            const match = (g.intervals ?? []).find((r) => contains(r, exactThickness));
            if (match)
                interval.value = match.interval_key;
        }
        renderPreview();
    };
    const fillGrades = (preserveGrade = "", preserveInterval = "") => {
        const p = selectedProduct();
        if (!p) {
            grade.disabled = true;
            grade.innerHTML = `<option value="">— сначала выберите вид проката —</option>`;
            fillIntervals();
            return;
        }
        grade.disabled = false;
        grade.innerHTML = `<option value="">— выберите марку стали —</option>` + (p.grades ?? []).map((g) => `<option value="${escapeHtml(g.steel_grade)}">${escapeHtml(g.steel_grade)}</option>`).join("");
        if (preserveGrade && (p.grades ?? []).some((g) => g.steel_grade === preserveGrade))
            grade.value = preserveGrade;
        fillIntervals(preserveInterval);
    };
    product.addEventListener("change", () => { fillGrades(); productHint.textContent = ""; });
    grade.addEventListener("change", () => fillIntervals());
    interval.addEventListener("change", renderPreview);
    fillGrades(old.steel_grade ?? "", old.steel_strength_interval_key ?? "");
}
function renderSectionWeakeningEditor(card, edit) {
    const old = edit?.payload ?? { holes_present: false };
    draftProvenance = null;
    const has = Boolean(old?.holes_present);
    const initialD = old?.hole_diameter_mm ?? 20;
    const initialS = old?.hole_pitch_mm ?? 80;
    const initialT = old?.local_thickness_mm ?? "";
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">Сечение</span><span>Ослабления</span></div>
    <h1>Круглые болтовые отверстия</h1>
    <p class="question-subtitle">Пока поддерживается универсальная упрощённая модель круглого сквозного отверстия. Площадь нетто рассчитывается как <strong>Aₙ = A − d·tₕ</strong>. Изменение I/W выбирается отдельным следующим шагом.</p>
    <div class="option-grid compact">
      <button class="option-card ${!has ? "selected" : ""}" data-weak="none"><span class="option-title">Отверстий нет</span></button>
      <button class="option-card ${has ? "selected" : ""}" data-weak="holes"><span class="option-title">Есть болтовые отверстия</span></button>
    </div>
    <div id="weakening-details"></div>
    ${refsHtml(card.normative_refs)}`;
    const details = $("weakening-details");
    const renderDetails = (enabled) => {
        if (!enabled) {
            details.innerHTML = "";
            draftPayload = { schema: "section_weakening_model_v0.49", holes_present: false, model: "none" };
            updateNextState();
            return;
        }
        details.innerHTML = `<div class="weakening-grid">
      <label>Диаметр отверстия d, мм<input id="weak-d" class="number-input" type="number" min="0" step="any" value="${escapeHtml(initialD)}"></label>
      <label>Шаг s, мм<input id="weak-pitch" class="number-input" type="number" min="0" step="any" value="${escapeHtml(initialS)}"></label>
      <label>Локальная толщина tₕ, мм <span class="field-hint">(необязательно)</span><input id="weak-thickness" class="number-input" type="number" min="0" step="any" value="${escapeHtml(initialT)}" placeholder="автоматически из сечения"></label>
    </div>
    <p class="question-subtitle">Если толщина стенки/элемента известна из выбранного профиля, tₕ определяется автоматически. Для формулы (45) СП16 параметр <strong>s</strong> сохраняет нормативный смысл шага отверстий в одном вертикальном ряду; требуется s &gt; d.</p>
    <div id="weak-validation" class="field-hint"></div>`;
        const sync = () => {
            const d = Number(document.getElementById("weak-d").value);
            const pitch = Number(document.getElementById("weak-pitch").value);
            const tRaw = document.getElementById("weak-thickness").value;
            const t = tRaw === "" ? undefined : Number(tRaw);
            const hint = document.getElementById("weak-validation");
            if (!Number.isFinite(d) || d <= 0) {
                hint.textContent = "Диаметр d должен быть больше 0.";
                draftPayload = undefined;
            }
            else if (!Number.isFinite(pitch) || pitch <= d) {
                hint.textContent = "Для формулы (45) требуется s > d.";
                draftPayload = undefined;
            }
            else if (t !== undefined && (!Number.isFinite(t) || t <= 0)) {
                hint.textContent = "Если tₕ задана вручную, она должна быть больше 0.";
                draftPayload = undefined;
            }
            else {
                hint.textContent = "";
                draftPayload = { schema: "section_weakening_model_v0.49", holes_present: true, model: "round_bolt_hole_universal_v1", hole_diameter_mm: d, hole_pitch_mm: pitch };
                if (t !== undefined)
                    draftPayload.local_thickness_mm = t;
            }
            updateNextState();
        };
        details.querySelectorAll("input").forEach(x => x.addEventListener("input", sync));
        sync();
    };
    els.question.querySelectorAll("[data-weak]").forEach(b => b.addEventListener("click", () => {
        els.question.querySelectorAll("[data-weak]").forEach(x => x.classList.remove("selected"));
        b.classList.add("selected");
        renderDetails(b.dataset.weak === "holes");
    }));
    renderDetails(has);
}
function renderCanonicalLoadMenu(card, edit, kind) {
    draftProvenance = null;
    const old = edit?.payload ?? {};
    const kN = (v) => Number(v ?? 0) / 1000;
    const kNm = (v) => Number(v ?? 0) / 1e6;
    const first = (...vals) => vals.find(v => v !== undefined && v !== null) ?? 0;
    const isAmbient = kind === "ambient";
    const q = isAmbient ? {
        N: "ambient_N_force", Mx: "ambient_M_x", My: "ambient_M_y", Qx: "ambient_Q_x", Qy: "ambient_Q_y", T: "ambient_T_torsion", combo: "ambient_load_combination"
    } : {
        N: "N_force", Mx: "M_x", My: "M_y", Qx: "Q_x", Qy: "Q_y", T: "T_torsion", combo: "special_load_combination"
    };
    const oldMx = first(old[q.Mx], old.M_x, old.load_My_local);
    const oldMy = first(old[q.My], old.M_y, old.load_Mz_local);
    const oldQx = first(old[q.Qx], old.Q_x, old.load_Qz_local);
    const oldQy = first(old[q.Qy], old.Q_y, old.load_Qy_local);
    const oldN = first(old[q.N], old.N_force);
    const oldT = first(old[q.T], old.T_torsion);
    const badge = isAmbient ? "AMBIENT_LOAD_CASE" : "FIRE_LOAD_CASE";
    const subtitle = isAmbient
        ? "Обычная проектная ситуация при нормальной температуре. Этот набор используется для будущего полного SP16 mechanical gate."
        : "Пожарная ситуация. Этот набор может отличаться от ambient case и используется downstream-ветвями СП554.";
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">${badge}</span><span>канонические оси СП16</span></div>
    <h1>${isAmbient ? "Расчётные усилия при нормальной температуре" : "Расчётные усилия пожарной ситуации"}</h1>
    <p class="question-subtitle">${subtitle} <strong>x-x</strong> и <strong>y-y</strong> — главные оси поперечного сечения; <strong>s</strong> — продольная ось. N &gt; 0 — растяжение, N &lt; 0 — сжатие.</p>
    <div class="weakening-grid load-grid">
      <label>N, кН<input id="load-N" class="number-input" type="number" step="any" value="${escapeHtml(kN(oldN))}"></label>
      <label>Mx, кН·м<input id="load-Mx" class="number-input" type="number" step="any" value="${escapeHtml(kNm(oldMx))}"></label>
      <label>My, кН·м<input id="load-My" class="number-input" type="number" step="any" value="${escapeHtml(kNm(oldMy))}"></label>
      <label>Qx, кН<input id="load-Qx" class="number-input" type="number" step="any" value="${escapeHtml(kN(oldQx))}"></label>
      <label>Qy, кН<input id="load-Qy" class="number-input" type="number" step="any" value="${escapeHtml(kN(oldQy))}"><span class="locked-field-note">Допускается ввод для census; при Qy≠0 расчёт остановится fail-closed до SP16-MECH3.</span></label>
      <label>T, кН·м<input id="load-T" class="number-input" type="number" step="any" value="${escapeHtml(kNm(oldT))}"><span class="locked-field-note">Допускается ввод для census; при T≠0 расчёт остановится fail-closed до SP16-MECH4.</span></label>
    </div>
    <div id="load-live-summary" class="callout"></div>
    ${isAmbient ? `<div class="callout"><strong>Важно:</strong> FIRE_LOAD_CASE будет задан отдельным следующим шагом: либо явное копирование этого состояния, либо отдельное пожарное сочетание.</div>` : `<div class="callout"><strong>Это отдельный fire case.</strong> Значения не меняют и не перезаписывают AMBIENT_LOAD_CASE.</div>`}
    ${refsHtml(card.normative_refs)}`;
    const sync = () => {
        const read = (id) => Number(document.getElementById(id).value || 0);
        const N = read("load-N"), Mx = read("load-Mx"), My = read("load-My"), Qx = read("load-Qx"), Qy = read("load-Qy"), T = read("load-T");
        const vals = [N, Mx, My, Qx, Qy, T];
        if (vals.some(v => !Number.isFinite(v))) {
            draftPayload = undefined;
            updateNextState();
            return;
        }
        const combo = {
            schema: isAmbient ? "sp16_mech2_ambient_combination_v1" : "sp16_mech2_fire_special_combination_v1",
            kind: isAmbient ? "ambient" : "fire",
            convention: "N>0 tension; N<0 compression; s member axis; x-x/y-y SP16 principal section axes",
            display_units: { force: "kN", moment: "kNm" },
            N_kN: N, Mx_kNm: Mx, My_kNm: My, Qx_kN: Qx, Qy_kN: Qy, T_kNm: T
        };
        draftPayload = {
            [q.combo]: combo,
            [q.N]: N * 1000, [q.Mx]: Mx * 1e6, [q.My]: My * 1e6, [q.Qx]: Qx * 1000, [q.Qy]: Qy * 1000, [q.T]: T * 1e6,
        };
        const axial = N > 0 ? "растяжение" : N < 0 ? "сжатие" : "без N";
        const active = [axial, Mx !== 0 ? "Mx" : "", My !== 0 ? "My" : "", Qx !== 0 ? "Qx" : "", Qy !== 0 ? "Qy" : "", T !== 0 ? "T" : ""].filter(Boolean);
        document.getElementById("load-live-summary").innerHTML = `<strong>Активно:</strong> ${active.join(" · ") || "нулевые усилия"}${Qy !== 0 || T !== 0 ? " · есть fail-closed component" : ""}`;
        updateNextState();
    };
    els.question.querySelectorAll("input").forEach(x => x.addEventListener("input", sync));
    sync();
}
function renderAmbientSignedLoadMenu(card, edit) {
    renderCanonicalLoadMenu(card, edit, "ambient");
}
function renderFireSignedLoadMenu(card, edit) {
    renderCanonicalLoadMenu(card, edit, "fire");
}
function renderBimomentDirectInput(card, edit) {
    draftProvenance = null;
    const currentCanonical = Number(edit?.payload ?? 0);
    const currentDisplay = Number.isFinite(currentCanonical) ? currentCanonical / 1e9 : 0;
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">СП16</span><span>SP16-MECH1</span></div>
    <h1>Прямой ввод бимомента B</h1>
    <p class="question-subtitle">Введите <strong>signed B</strong> для того же расчетного сечения и сочетания. В этом релизе B не вычисляется из T или условий депланации.</p>
    <div class="field-block"><label class="field-label">B, кН·м²</label><input id="bimoment-B" class="number-input" type="number" step="any" value="${escapeHtml(currentDisplay)}"></div>
    <div class="callout">1 кН·м² = 10⁹ Н·мм². Знак B сохраняется end-to-end.</div>
    ${refsHtml(card.normative_refs)}`;
    const input = document.getElementById("bimoment-B");
    const sync = () => { const b = Number(input.value); draftPayload = Number.isFinite(b) ? b * 1e9 : undefined; updateNextState(); };
    input.addEventListener("input", sync);
    sync();
}
function renderVerificationPlanSummary(card) {
    const plan = envelope?.state?.values?.verification_plan?.value ?? {};
    const branches = plan.branches ?? [];
    draftPayload = true;
    draftProvenance = null;
    const stateLabels = { central_tension: "центральное растяжение", central_compression: "центральное сжатие", bending: "изгиб", compression_plus_bending: "сжатие + изгиб", tension_plus_bending: "растяжение + изгиб" };
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">Verification Plan</span><span>автоматически</span></div>
    <h1>План нормативных проверок</h1>
    <p class="question-subtitle">Основная ветвь: <strong>${escapeHtml(stateLabels[plan.stress_state] ?? plan.stress_state ?? "—")}</strong>. План получен из знаков и ненулевых компонентов усилий; вручную выбирать НДС больше не нужно.</p>
    <div class="plan-list">${branches.map((b) => `<div class="result-card"><strong>${escapeHtml(b.label ?? b.id)}</strong><div class="field-hint">${b.status === "deferred" ? "DEFERRED — ветвь будет отмечена явно и не остановит остальные проверки." : "Будет проверяться."}${b.note ? ` ${escapeHtml(b.note)}` : ""}</div></div>`).join("")}</div>
    ${plan.deferred_branch_ids?.length ? `<div class="callout"><strong>Частично неподдержанные компоненты:</strong> ${escapeHtml(plan.deferred_branch_ids.join(", "))}. Они не будут молча отброшены.</div>` : ""}
    ${refsHtml(card.normative_refs)}`;
    updateNextState();
}
function renderApplicabilityCensusSummary(card) {
    const census = envelope?.state?.values?.sp16_applicability_census?.value ?? {};
    const active = census.active_checks ?? [];
    const contextual = census.context_driven_checks ?? [];
    draftPayload = true;
    draftProvenance = null;
    const statusLabel = (row) => {
        const st = String(row.runtime_status ?? "");
        if (st.startsWith("deferred_"))
            return "DEFERRED / FAIL-CLOSED";
        if (st === "direct_input_partial_runtime")
            return "PARTIAL — B задан напрямую";
        return "APPLICABLE";
    };
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">SP16 Applicability Census</span><span>AMBIENT_LOAD_CASE</span></div>
    <h1>Какие проверки СП16 обязательны для этого состояния</h1>
    <p class="question-subtitle">Состав получен автоматически из signed усилий. Пользователь не исключает обязательные ветви вручную. Это <strong>census</strong>, а не окончательный SP16 PASS gate.</p>
    <div class="plan-list">${active.map((r) => `<div class="result-card"><strong>${escapeHtml(r.label ?? r.id)}</strong><div class="field-hint">${escapeHtml(statusLabel(r))} · ${escapeHtml(r.reason ?? "")}${r.normative_scope?.length ? ` · ${escapeHtml(r.normative_scope.join(", "))}` : ""}</div></div>`).join("") || `<div class="result-card"><strong>Нет action-driven проверок</strong><div class="field-hint">Нулевое силовое состояние.</div></div>`}</div>
    ${contextual.length ? `<div class="callout"><strong>Контекстные проверки, которые нельзя решить только по N/M/Q/T:</strong><br>${contextual.map((r) => `${escapeHtml(r.label ?? r.id)} — ${escapeHtml(r.trigger ?? "")}`).join("<br>")}</div>` : ""}
    ${census.deferred_active_check_ids?.length ? `<div class="callout"><strong>Fail-closed:</strong> ${escapeHtml(census.deferred_active_check_ids.join(", "))}. Переход к СП554 будет остановлен до реализации соответствующей SP16 mechanics stage.</div>` : ""}
    <div class="field-hint">Full ambient SP16 gate: ${census.full_ambient_gate_closed ? "CLOSED" : "ещё не закрыт; запланирован после mechanics stages Qy/T и aggregator."}</div>
    ${refsHtml(card.normative_refs)}`;
    updateNextState();
}
function renderRequiredRSelector(card, edit) {
    const current = edit?.payload;
    draftPayload = current;
    draftProvenance = null;
    const values = [15, 30, 45, 60, 90, 120, 150, 180];
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">Результат</span></div><h1>Требуемый предел огнестойкости</h1>
    <p class="question-subtitle">Этот вопрос появляется только после получения собственной огнестойкости Rfact. Для обычного расчёта достаточно выбрать требуемое R.</p>
    <div class="option-grid compact">${values.map(v => `<button class="option-card ${current === v ? "selected" : ""}" data-r="${v}"><span class="option-title">R${v}</span></button>`).join("")}</div>
    <div class="field-block"><label class="field-label">Другое значение, мин</label><input id="r-custom" class="number-input" type="number" step="any" value="${values.includes(current) ? "" : escapeHtml(current ?? "")}"></div>${refsHtml(card.normative_refs)}`;
    els.question.querySelectorAll("[data-r]").forEach(b => b.addEventListener("click", () => { draftPayload = Number(b.dataset.r); els.question.querySelectorAll("[data-r]").forEach(x => x.classList.remove("selected")); b.classList.add("selected"); document.getElementById("r-custom").value = ""; updateNextState(); }));
    const custom = document.getElementById("r-custom");
    custom.addEventListener("input", () => { draftPayload = custom.value === "" ? undefined : Number(custom.value); els.question.querySelectorAll("[data-r]").forEach(x => x.classList.remove("selected")); updateNextState(); });
}
function renderTable30SchemeSelector(card, edit) {
    const current = edit?.payload;
    draftPayload = current;
    draftProvenance = null;
    const rows = [
        { value: "S1", label: "Шарнир — шарнир", mu: "1,00", icon: "○│○", note: "Обычная классическая схема." },
        { value: "S2", label: "Защемление — шарнир", mu: "0,70", icon: "▰│○", note: "Один конец жёстко закреплён, второй шарнирный." },
        { value: "S3", label: "Защемление — защемление", mu: "0,50", icon: "▰│▰", note: "Оба конца жёстко закреплены." },
        { value: "S4", label: "Консоль", mu: "2,00", icon: "▰│·", note: "Один конец защемлён, второй свободен." },
        { value: "S5", label: "Схема 5 таблицы 30", mu: "1,00", icon: "S5", note: "Выбор зависит также от нормативной схемы нагрузки; не определяется только двумя опорами." },
        { value: "S6", label: "Схема 6 таблицы 30", mu: "2,00", icon: "S6", note: "Выбор зависит также от нормативной схемы нагрузки; не определяется только двумя опорами." },
        { value: "S7", label: "Схема 7 таблицы 30", mu: "0,725", icon: "S7", note: "Выбор зависит также от нормативной схемы нагрузки; не определяется только двумя опорами." },
        { value: "S8", label: "Схема 8 таблицы 30", mu: "1,12", icon: "S8", note: "Выбор зависит также от нормативной схемы нагрузки; не определяется только двумя опорами." }
    ];
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">СП 16 · табл. 30</span><span>расчётная длина</span></div>
    <h1>${escapeHtml(card.prompt || card.title || "Схема закрепления")}</h1>
    <p class="question-subtitle">СП 16, п. 10.3.3: коэффициент μ зависит от закрепления концов <strong>и вида нагрузки</strong>. Для четырёх обычных случаев можно выбрать именованную карточку. Схемы 5–8 не угадываются только по двум опорам.</p>
    <div class="field-block"><div class="field-label">Быстрый выбор по концам элемента</div><div class="weakening-grid">
      <label>Левый / нижний конец<select id="mu-left" class="select-input"><option value="">—</option><option value="hinged">Шарнир</option><option value="fixed">Защемление</option><option value="free">Свободный</option></select></label>
      <label>Правый / верхний конец<select id="mu-right" class="select-input"><option value="">—</option><option value="hinged">Шарнир</option><option value="fixed">Защемление</option><option value="free">Свободный</option></select></label>
    </div><div id="mu-shortcut-note" class="field-hint">Выбор концов автоматически выделит только однозначную классическую схему S1–S4.</div></div>
    <div class="option-grid">${rows.map(r => `<button type="button" class="option-card ${current === r.value ? "selected" : ""}" data-table30="${r.value}"><span class="option-title">${escapeHtml(r.label)}</span><span style="font-size:1.5rem;font-family:monospace">${escapeHtml(r.icon)}</span><span class="option-description">μ = ${escapeHtml(r.mu)} · ${escapeHtml(r.note)}</span></button>`).join("")}</div>
    <div class="callout"><strong>Важно.</strong> Схемы S5–S8 оставлены как нормативные идентификаторы: их рисунок нагрузки необходимо сопоставлять с таблицей 30. UI не подменяет вид нагрузки эвристикой.</div>${refsHtml(card.normative_refs)}`;
    const selectValue = (v) => { draftPayload = v; els.question.querySelectorAll("[data-table30]").forEach(x => x.classList.toggle("selected", x.dataset.table30 === v)); updateNextState(); };
    els.question.querySelectorAll("[data-table30]").forEach(b => b.addEventListener("click", () => selectValue(b.dataset.table30)));
    const left = document.getElementById("mu-left");
    const right = document.getElementById("mu-right");
    const note = document.getElementById("mu-shortcut-note");
    const sync = () => {
        const a = left.value, b = right.value;
        let v = "";
        if (a === "hinged" && b === "hinged")
            v = "S1";
        else if ((a === "fixed" && b === "hinged") || (a === "hinged" && b === "fixed"))
            v = "S2";
        else if (a === "fixed" && b === "fixed")
            v = "S3";
        else if ((a === "fixed" && b === "free") || (a === "free" && b === "fixed"))
            v = "S4";
        if (v) {
            const row = rows.find(x => x.value === v);
            note.textContent = `Распознано: ${row.label}; μ = ${row.mu}.`;
            selectValue(v);
        }
        else if (a && b) {
            note.textContent = "Эта пара концов не даёт однозначной классической схемы S1–S4. Выберите нормативную карточку вручную.";
        }
    };
    left.addEventListener("change", sync);
    right.addEventListener("change", sync);
    updateNextState();
}
function renderTable7CurveSelector(card, edit) {
    const current = edit?.payload;
    draftPayload = current;
    draftProvenance = null;
    const rows = [
        { value: "a", alpha: "0,03", beta: "0,06", svg: `<svg viewBox="0 0 120 70" width="120" height="70" aria-label="тип a"><rect x="28" y="15" width="64" height="40" fill="none" stroke="currentColor" stroke-width="5"/><line x1="60" y1="5" x2="60" y2="65" stroke="currentColor" stroke-dasharray="4 4"/></svg>`, note: "Применимость определяется формой сечения и расчётной плоскостью; для прокатного двутавра h > 500 мм в плоскости стенки СП16 отдельно предписывает тип a." },
        { value: "b", alpha: "0,04", beta: "0,09", svg: `<svg viewBox="0 0 120 70" width="120" height="70" aria-label="тип b"><line x1="25" y1="14" x2="95" y2="14" stroke="currentColor" stroke-width="7"/><line x1="60" y1="14" x2="60" y2="56" stroke="currentColor" stroke-width="6"/><line x1="25" y1="56" x2="95" y2="56" stroke="currentColor" stroke-width="7"/><line x1="10" y1="35" x2="110" y2="35" stroke="currentColor" stroke-dasharray="4 4"/></svg>`, note: "Одна из нормативных кривых для сплошных сечений; сверяйте форму и ось на таблице 7." },
        { value: "c", alpha: "0,04", beta: "0,14", svg: `<svg viewBox="0 0 120 70" width="120" height="70" aria-label="тип c"><line x1="25" y1="14" x2="95" y2="14" stroke="currentColor" stroke-width="7"/><line x1="60" y1="14" x2="60" y2="58" stroke="currentColor" stroke-width="6"/><line x1="60" y1="5" x2="60" y2="65" stroke="currentColor" stroke-dasharray="4 4"/></svg>`, note: "Менее благоприятная нормативная кривая; выбор зависит от фактической формы и направления потери устойчивости." }
    ];
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">СП 16 · табл. 7</span><span>a / b / c</span></div>
    <h1>${escapeHtml(card.prompt || card.title || "Тип кривой устойчивости")}</h1>
    <p class="question-subtitle">Схемы ниже — собственная схематическая перерисовка для удобства выбора. Нормативные коэффициенты: a → α=0,03 β=0,06; b → α=0,04 β=0,09; c → α=0,04 β=0,14. Оси x-x/y-y в таблице 7 задают расчётную плоскость.</p>
    <div class="option-grid">${rows.map(r => `<button class="option-card ${current === r.value ? "selected" : ""}" type="button" data-table7="${r.value}"><span class="option-title">Тип ${r.value}</span>${r.svg}<span class="option-description">α = ${r.alpha}; β = ${r.beta}. ${escapeHtml(r.note)}</span></button>`).join("")}</div>
    <div class="callout"><strong>Примечание СП16.</strong> Для прокатных двутавров высотой свыше 500 мм при расчёте устойчивости в плоскости стенки применяется тип a. Для других случаев используйте форму и расчётную плоскость таблицы 7.</div>${refsHtml(card.normative_refs)}`;
    els.question.querySelectorAll("[data-table7]").forEach(b => b.addEventListener("click", () => { draftPayload = b.dataset.table7; els.question.querySelectorAll("[data-table7]").forEach(x => x.classList.toggle("selected", x.dataset.table7 === draftPayload)); updateNextState(); }));
    updateNextState();
}
function renderTable21TypeSelector(card, edit) {
    const current = edit?.payload;
    draftPayload = current;
    draftProvenance = null;
    const options = card.options ?? [];
    const extra = {
        "1": "Сопоставьте фактическую форму сечения, ось изгиба и направление эксцентриситета с первой графической строкой таблицы 21.",
        "2": "Сопоставьте фактическую форму сечения, ось изгиба и направление эксцентриситета со второй графической строкой таблицы 21.",
        "3": "Сопоставьте фактическую форму сечения, ось изгиба и направление эксцентриситета с третьей графической строкой таблицы 21.",
        "4": "Для типа 4 downstream-формулы используют I₂/I₁: моменты инерции меньшей и большей полок относительно оси y–y по обозначениям таблицы 21."
    };
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">СП 16 · табл. 21</span><span>9.2.5</span></div>
    <h1>Тип сечения и направление эксцентриситета</h1>
    <p class="question-subtitle">Выберите строку <strong>по графической схеме таблицы 21</strong>, а не по номеру как самостоятельному признаку. Учитываются форма сечения, оси и направление эксцентриситета.</p>
    <div class="option-grid">${options.map((o) => `<button type="button" class="option-card ${current === o.value ? "selected" : ""}" data-table21="${escapeHtml(String(o.value))}">
      <span class="option-title">${escapeHtml(o.label ?? `Тип ${o.value}`)}</span>
      <span style="font-size:1.55rem;font-weight:700;letter-spacing:.04em">схема ${escapeHtml(String(o.value))} · e →</span>
      <span class="option-description">${escapeHtml(extra[String(o.value)] ?? o.description ?? "")}</span>
    </button>`).join("")}</div>
    <div class="callout"><strong>Важно.</strong> Карточки дают пояснение к выбору, но не заменяют графическую строку нормативной таблицы. Если соответствие сечения схеме неоднозначно, тип нельзя угадывать.</div>
    ${refsHtml(card.normative_refs)}`;
    els.question.querySelectorAll("[data-table21]").forEach(b => b.addEventListener("click", () => {
        draftPayload = b.dataset.table21;
        els.question.querySelectorAll("[data-table21]").forEach(x => x.classList.toggle("selected", x.dataset.table21 === draftPayload));
        updateNextState();
    }));
    updateNextState();
}
function renderHeatedSidesSelector(card, edit) {
    const current = edit?.payload;
    draftPayload = current;
    draftProvenance = null;
    const options = [
        { value: "four_sides", title: "Обогрев с 4 сторон", note: "Открыт весь расчетный периметр сечения.", icon: "↙ ↓ ↘\n→  I  ←\n↖ ↑ ↗" },
        { value: "three_sides", title: "Обогрев с 3 сторон", note: "Верхняя сторона экранирована; остальные стороны подвергаются огневому воздействию.", icon: "──────\n→  I  ←\n↖ ↑ ↗" },
    ];
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">СП 554 · табл. 1</span><span>теплотехника</span></div>
    <h1>Количество обогреваемых сторон</h1>
    <p class="question-subtitle">Здесь задаётся только <strong>3- или 4-сторонний обогрев</strong>. Для незащищённой конструкции P рассчитывается автоматически по контуру стали. Если далее потребуется огнезащита, программа отдельно спросит: <strong>по контуру</strong> или <strong>в виде короба</strong>.</p>
    <div class="option-grid">${options.map(o => `<button type="button" class="option-card ${current === o.value ? "selected" : ""}" data-heated-sides="${o.value}"><span class="option-title">${escapeHtml(o.title)}</span><pre style="margin:.4rem 0;font-size:1.05rem;line-height:1.1">${escapeHtml(o.icon)}</pre><span class="option-description">${escapeHtml(o.note)}</span></button>`).join("")}</div>
    <div class="callout"><strong>Важно.</strong> «По контуру» и «короб» — это не число сторон и не тип стального профиля. Это отдельная геометрия огнезащиты, выбираемая только в protected-route.</div>${refsHtml(card.normative_refs)}`;
    els.question.querySelectorAll("[data-heated-sides]").forEach(b => b.addEventListener("click", () => {
        draftPayload = b.dataset.heatedSides;
        els.question.querySelectorAll("[data-heated-sides]").forEach(x => x.classList.toggle("selected", x.dataset.heatedSides === draftPayload));
        updateNextState();
    }));
    updateNextState();
}
function renderProtectionPerimeterModeSelector(card, edit) {
    const current = edit?.payload;
    draftPayload = current;
    draftProvenance = null;
    const options = [
        { value: "contour", title: "Огнезащита по контуру", svg: `<svg viewBox="0 0 150 90" width="150" height="90" aria-label="огнезащита по контуру"><path d="M25 16 H125 V28 H82 V62 H125 V74 H25 V62 H68 V28 H25 Z" fill="none" stroke="currentColor" stroke-width="5"/><path d="M17 8 H133 V36 H90 V54 H133 V82 H17 V54 H60 V36 H17 Z" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5 4"/></svg>`, note: "Огнезащитный слой повторяет контур профиля. Для двутавра Table 1: P₄ = 4B + 2D − 2t; P₃ = 3B + 2D − 2t." },
        { value: "box", title: "Огнезащита в виде короба", svg: `<svg viewBox="0 0 150 90" width="150" height="90" aria-label="огнезащита в виде короба"><path d="M45 20 H105 M75 20 V70 M45 70 H105" fill="none" stroke="currentColor" stroke-width="7"/><rect x="20" y="8" width="110" height="74" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="5 4"/></svg>`, note: "Огнезащита образует внешний короб. Для двутавра Table 1: P₄ = 2B + 2D; P₃ = B + 2D." },
    ];
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">СП 554 · табл. 1</span><span>огнезащита</span></div>
    <h1>Схема выполнения огнезащиты</h1>
    <p class="question-subtitle">Выбор влияет на обогреваемый периметр P и, следовательно, на приведённую толщину <strong>δпр = A/P</strong>. Количество обогреваемых сторон уже известно из предыдущего теплотехнического шага.</p>
    <div class="option-grid">${options.map(o => `<button type="button" class="option-card ${current === o.value ? "selected" : ""}" data-prot-perimeter="${o.value}"><span class="option-title">${escapeHtml(o.title)}</span>${o.svg}<span class="option-description">${escapeHtml(o.note)}</span></button>`).join("")}</div>
    <div class="callout"><strong>Не путать:</strong> «огнезащита в виде короба» не означает коробчатое стальное сечение. Стальной элемент может оставаться двутавром, швеллером и т. п.</div>${refsHtml(card.normative_refs)}`;
    els.question.querySelectorAll("[data-prot-perimeter]").forEach(b => b.addEventListener("click", () => {
        draftPayload = b.dataset.protPerimeter;
        els.question.querySelectorAll("[data-prot-perimeter]").forEach(x => x.classList.toggle("selected", x.dataset.protPerimeter === draftPayload));
        updateNextState();
    }));
    updateNextState();
}
function renderDocumentedPerformanceMatrixEditor(card, edit) {
    const ledgerValue = (qid) => (envelope?.state?.ledger ?? []).find((x) => x.quantity_id === qid)?.value;
    const current = (edit?.payload && typeof edit.payload === "object" && !Array.isArray(edit.payload)) ? edit.payload : {};
    const axisText = (v) => Array.isArray(v) ? v.join(", ") : "";
    const matrixText = (v) => Array.isArray(v) ? v.map((r) => Array.isArray(r) ? r.join(", ") : "").join("\n") : "";
    const currentTcr = ledgerValue("critical_temperature_c");
    const productId = current.product_id ?? ledgerValue("protection_product_id") ?? "";
    const steelGroup = current.steel_group ?? ledgerValue("steel_strength_group") ?? "ordinary";
    const fireRegime = current.fire_regime ?? ledgerValue("fire_temperature_regime") ?? "standard";
    els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">СП 554 · 12.7–12.10</span><span>конкретный продукт</span></div>
    <h1>Номограмма / матрица огнезащитной эффективности</h1>
    <p class="question-subtitle">Введите данные <strong>только из технической документации выбранного средства огнезащиты</strong>. Это структурированный редактор; внутренний JSON вручную писать не нужно.</p>
    <div class="callout"><strong>Текущая расчётная критическая температура:</strong> ${currentTcr === undefined ? "—" : escapeHtml(String(currentTcr)) + " °C"}. Матрица СП 554 12.8/12.9 должна относиться к точному документированному уровню Tcr; программа не будет придумывать интерполяцию между температурными уровнями.</div>
    <div class="field-grid">
      <label>Марка продукта<input id="perf-product" class="text-input" type="text" value="${escapeHtml(String(productId))}" readonly></label>
      <label>Критическая температура матрицы, °C<input id="perf-tcr" class="text-input" type="number" step="any" value="${escapeHtml(String(current.critical_temperature_c ?? ""))}" placeholder="например 500"></label>
      <label style="grid-column:1/-1">Ось приведённой толщины δпр, мм<input id="perf-delta-axis" class="text-input" type="text" value="${escapeHtml(axisText(current.reduced_thickness_axis_mm))}" placeholder="например 3, 5, 7, 10, 15, 20"></label>
      <label style="grid-column:1/-1">Ось толщины огнезащиты δf, мм<input id="perf-prot-axis" class="text-input" type="text" value="${escapeHtml(axisText(current.protection_thickness_axis_mm))}" placeholder="например 10, 20, 30, 40"></label>
      <label style="grid-column:1/-1">Матрица времени, мин — одна строка на каждое δпр<textarea id="perf-matrix" class="text-input" rows="7" placeholder="25, 45, 65, 90&#10;30, 50, 72, 98&#10;...">${escapeHtml(matrixText(current.time_matrix_min))}</textarea></label>
    </div>
    <label class="checkbox-row"><input id="perf-doc-confirm" type="checkbox" ${current.technical_documentation_12_7_9_confirmed === true ? "checked" : ""}> Подтверждаю, что оси и матрица взяты из технической документации именно выбранного средства огнезащиты.</label>
    <label class="checkbox-row"><input id="perf-upper-carry" type="checkbox" ${current.allow_greater_delta_carry_forward === true ? "checked" : ""}> Документация явно разрешает перенос результата на большую δпр за верхней границей таблицы.</label>
    <div id="perf-editor-status" class="callout" style="display:none"></div>
    ${refsHtml(card.normative_refs)}`;
    const parseVector = (text) => {
        const parts = text.trim().split(/[;,\s]+/).filter(Boolean);
        if (parts.length < 2)
            return null;
        const nums = parts.map(Number);
        return nums.every(Number.isFinite) ? nums : null;
    };
    const parseMatrix = (text) => {
        const rows = text.trim().split(/\n+/).map(x => x.trim()).filter(Boolean);
        if (rows.length < 2)
            return null;
        const parsed = rows.map(r => r.split(/[;,\s]+/).filter(Boolean).map(Number));
        return parsed.every(r => r.length > 0 && r.every(Number.isFinite)) ? parsed : null;
    };
    const sync = () => {
        const tcr = Number(document.getElementById("perf-tcr").value);
        const da = parseVector(document.getElementById("perf-delta-axis").value);
        const pa = parseVector(document.getElementById("perf-prot-axis").value);
        const mx = parseMatrix(document.getElementById("perf-matrix").value);
        const confirmed = document.getElementById("perf-doc-confirm").checked;
        const carry = document.getElementById("perf-upper-carry").checked;
        const status = document.getElementById("perf-editor-status");
        const dimensionsOk = !!(da && pa && mx && mx.length === da.length && mx.every(r => r.length === pa.length));
        const ok = Number.isFinite(tcr) && !!productId && !!da && !!pa && !!mx && dimensionsOk && confirmed;
        if (ok) {
            draftPayload = {
                product_id: String(productId), source_kind: "technical_documentation_12_7_9",
                critical_temperature_c: tcr, steel_group: String(steelGroup), fire_regime: String(fireRegime),
                technical_documentation_12_7_9_confirmed: true,
                reduced_thickness_axis_mm: da, protection_thickness_axis_mm: pa, time_matrix_min: mx,
                allow_greater_delta_carry_forward: carry,
            };
            status.style.display = "none";
        }
        else {
            draftPayload = undefined;
            status.style.display = "block";
            status.textContent = !confirmed ? "Подтвердите источник технической документации." : !dimensionsOk ? "Размер матрицы должен быть: число строк = числу δпр, число значений в каждой строке = числу толщин δf." : "Заполните все поля корректными числовыми данными.";
        }
        draftProvenance = null;
        updateNextState();
    };
    ["perf-tcr", "perf-delta-axis", "perf-prot-axis", "perf-matrix", "perf-doc-confirm", "perf-upper-carry"].forEach(id => {
        const el = document.getElementById(id);
        el.addEventListener("input", sync);
        el.addEventListener("change", sync);
    });
    sync();
}
function renderInteractiveCard(card) {
    const edit = historyCursor !== null ? selectedValueForReview() : null;
    const component = card.presentation?.component;
    if (component === "section_editor_entry") {
        renderSectionEditorEntry(card, edit);
        updateNextState();
        return;
    }
    if (component === "profile_catalog_selector") {
        void renderProfileCatalogSelector(card, edit);
        return;
    }
    if (component === "parametric_section_editor") {
        renderParametricSectionEditor(card, edit);
        return;
    }
    if (component === "manual_section_properties_editor") {
        renderManualSectionPropertiesEditor(card, edit);
        return;
    }
    if (component === "double_branch_section_editor") {
        void renderDoubleBranchSectionEditor(card, edit);
        return;
    }
    if (component === "material_strength_editor") {
        void renderMaterialStrengthEditor(card, edit);
        return;
    }
    if (component === "section_weakening_editor") {
        renderSectionWeakeningEditor(card, edit);
        updateNextState();
        return;
    }
    if (component === "ambient_signed_load_menu") {
        renderAmbientSignedLoadMenu(card, edit);
        updateNextState();
        return;
    }
    if (component === "fire_signed_load_menu") {
        renderFireSignedLoadMenu(card, edit);
        updateNextState();
        return;
    }
    if (component === "bimoment_direct_input") {
        renderBimomentDirectInput(card, edit);
        updateNextState();
        return;
    }
    if (component === "verification_plan_summary") {
        renderVerificationPlanSummary(card);
        return;
    }
    if (component === "applicability_census_summary") {
        renderApplicabilityCensusSummary(card);
        return;
    }
    if (component === "table30_scheme_selector") {
        renderTable30SchemeSelector(card, edit);
        return;
    }
    if (component === "table7_curve_selector") {
        renderTable7CurveSelector(card, edit);
        return;
    }
    if (component === "table21_type_selector") {
        renderTable21TypeSelector(card, edit);
        return;
    }
    if (component === "required_r_selector") {
        renderRequiredRSelector(card, edit);
        updateNextState();
        return;
    }
    if (component === "heated_sides_selector") {
        renderHeatedSidesSelector(card, edit);
        return;
    }
    if (component === "protection_perimeter_mode_selector") {
        renderProtectionPerimeterModeSelector(card, edit);
        return;
    }
    if (component === "documented_performance_matrix_editor") {
        renderDocumentedPerformanceMatrixEditor(card, edit);
        return;
    }
    const notes = card.notes ?? {};
    const fields = card.fields ?? [];
    const scalarCurrent = edit?.payload;
    const firstField = fields[0];
    const options = firstField ? optionSource(card, firstField) : [];
    const useCards = card.node_type === "decision" && options.length > 0;
    let controls = "";
    if (useCards) {
        controls = `<div class="option-grid">${options.map((o) => {
            const selected = scalarCurrent === o.value;
            return `<button class="option-card ${selected ? "selected" : ""}" type="button" data-option-json='${escapeHtml(JSON.stringify(o.value))}'>
        <span class="option-title">${escapeHtml(o.label ?? o.value)}</span>
        ${o.description ? `<span class="option-description">${escapeHtml(o.description)}</span>` : ""}
      </button>`;
        }).join("")}</div>`;
    }
    else {
        controls = fields.map((field) => {
            const value = card.submit_shape === "scalar" ? scalarCurrent : (scalarCurrent?.[field.quantity_id]);
            return renderField(card, field, value);
        }).join("");
    }
    let handoff = "";
    if (card.external_handoff) {
        const p = edit?.provenance ?? {};
        handoff = `<div class="handoff-box">
      <div class="handoff-title">Внешний нормативный результат${card.target_standard_id ? ` · ${escapeHtml(card.target_standard_id)}` : ""}</div>
      <div class="handoff-text">${escapeHtml(card.handoff_reason || "Значение должно иметь проверяемый внешний нормативный источник.")}</div>
      <div class="provenance-grid">
        <label>Документ-источник<input id="prov-document" class="text-input" type="text" value="${escapeHtml(p.source_document ?? "")}" placeholder="Например: СП 2.13130…"></label>
        <label>Ссылка / пункт<input id="prov-reference" class="text-input" type="text" value="${escapeHtml(p.source_reference ?? "")}" placeholder="Например: табл. 21, R45"></label>
      </div>
    </div>`;
    }
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">${escapeHtml(card.owner_standard_id || "DAG")}</span>${card.presentation?.stage ? `<span>${escapeHtml(card.presentation.stage)}</span>` : ""}</div>
    <h1>${escapeHtml(card.prompt || card.title || card.node_id)}</h1>
    ${card.title && card.title !== card.prompt ? `<p class="question-subtitle">${escapeHtml(card.title)}</p>` : ""}
    ${notes.normative_warning ? `<div class="callout"><strong>Нормативное предупреждение.</strong> ${escapeHtml(notes.normative_warning)}</div>` : ""}
    ${handoff}
    ${controls}
    ${refsHtml(card.normative_refs)}
  `;
    draftPayload = edit?.payload;
    draftProvenance = edit?.provenance ?? null;
    if (useCards) {
        els.question.querySelectorAll(".option-card").forEach((button) => {
            button.addEventListener("click", () => {
                draftPayload = JSON.parse(button.dataset.optionJson || "null");
                els.question.querySelectorAll(".option-card").forEach((x) => x.classList.remove("selected"));
                button.classList.add("selected");
                updateNextState();
            });
        });
    }
    else {
        els.question.querySelectorAll("[data-field]").forEach((input) => {
            const sync = () => {
                const qid = input.dataset.field;
                const field = fields.find((f) => f.quantity_id === qid);
                let val = input.value;
                if (field.data_type === "number")
                    val = input.value === "" ? undefined : Number(input.value);
                if (field.data_type === "boolean")
                    val = input.value === "true" ? true : input.value === "false" ? false : undefined;
                if (card.submit_shape === "scalar")
                    draftPayload = val;
                else {
                    const obj = (draftPayload && typeof draftPayload === "object" && !Array.isArray(draftPayload)) ? { ...draftPayload } : {};
                    if (val === undefined || val === "")
                        delete obj[qid];
                    else
                        obj[qid] = val;
                    draftPayload = obj;
                }
                updateNextState();
            };
            input.addEventListener("input", sync);
            input.addEventListener("change", sync);
        });
    }
    if (card.external_handoff) {
        const doc = $("prov-document");
        const ref = $("prov-reference");
        const syncProv = () => {
            draftProvenance = { source_document: doc.value.trim(), source_reference: ref.value.trim() };
            updateNextState();
        };
        doc.addEventListener("input", syncProv);
        ref.addEventListener("input", syncProv);
        syncProv();
    }
}
function renderNonInteractiveCard(card) {
    const status = envelope?.state?.status ?? "";
    const ledgerValue = (qid) => (envelope?.state?.ledger ?? []).find((x) => x.quantity_id === qid)?.value;
    if (status.startsWith("BLOCKED")) {
        els.question.innerHTML = `
      <div class="card-kicker"><span class="standard-badge">DAG FAIL-CLOSED</span><span>${escapeHtml(card?.node_id || envelope?.state?.current_node_id || "")}</span></div>
      <h1>Расчётная ветвь остановлена fail-closed</h1>
      <p class="question-subtitle">Ветка не имеет достаточного подтверждённого production-пути для продолжения. Значение не подменяется приближением и не экстраполируется.</p>
      <div class="blocked-card"><strong>Текущее состояние:</strong><div class="blocked-code">${escapeHtml(status)}</div></div>
      ${refsHtml(card?.normative_refs ?? [])}`;
        return;
    }
    if (card?.node_id === "SP554_R_UI16_DEFERRED_BRANCHES") {
        const plan = ledgerValue("verification_plan") ?? {};
        const branches = plan.branches ?? [];
        const deferred = branches.filter((b) => b.status === "deferred");
        const qy = Number(ledgerValue("Q_y") ?? 0) / 1000;
        const torsion = Number(ledgerValue("T_torsion") ?? 0) / 1e6;
        const loadRows = [
            Math.abs(qy) > 0 ? `<div class="result-card"><strong>Qy = ${escapeHtml(displayValue(qy))} кН</strong><div class="field-hint">Поперечная сила Qy по канонической главной оси: axis-specific shear runtime пока не закрыт; Qy не подменяется Qx.</div></div>` : "",
            Math.abs(torsion) > 0 ? `<div class="result-card"><strong>T = ${escapeHtml(displayValue(torsion))} кН·м</strong><div class="field-hint">Кручение: torsion runtime пока не закрыт; T не подменяется бимоментом B.</div></div>` : ""
        ].filter(Boolean).join("");
        const done = branches.filter((b) => b.status !== "deferred");
        els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">Mechanical gate</span><span>fail-closed</span></div>
      <h1>Механическая проверка не завершена</h1>
      <p class="question-subtitle">Поддерживаемые ветви рассчитаны/запланированы, но активное сочетание содержит воздействия без подтверждённого production-runtime. Переход к теплотехнической стадии заблокирован.</p>
      ${loadRows}
      ${deferred.length ? `<div class="callout"><strong>Незавершённые ветви:</strong> ${deferred.map((b) => escapeHtml(`${b.label ?? b.id}${b.note ? ` — ${b.note}` : ""}`)).join("<br>")}</div>` : ""}
      ${done.length ? `<div class="field-hint"><strong>Остальные ветви плана:</strong> ${done.map((b) => escapeHtml(b.label ?? b.id)).join(" · ")}</div>` : ""}
      ${refsHtml(card.normative_refs ?? [])}`;
        return;
    }
    if (card?.node_id === "SP16_R_AMBIENT_UNSUPPORTED_ACTIONS") {
        const census = ledgerValue("sp16_applicability_census") ?? {};
        const deferred = census.deferred_active_check_ids ?? [];
        els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">SP16 · ambient</span><span>FAIL-CLOSED</span></div>
      <h1>Ambient mechanical verification пока не может быть завершена</h1>
      <p class="question-subtitle">В обычном расчетном состоянии активна механическая компонента, для которой production-runtime ещё не закрыт. Переход к FIRE_LOAD_CASE и СП554 остановлен.</p>
      <div class="callout"><strong>Незакрытые активные ветви:</strong> ${escapeHtml(deferred.join(", ") || "—")}</div>
      ${refsHtml(card.normative_refs ?? [])}`;
        return;
    }
    if (card?.node_id === "SP554_FIRE_D2_R_CRITICAL_TEMPERATURE") {
        const cstatus = ledgerValue("fire_d2_critical_temperature_status");
        const t = ledgerValue("fire_d2_critical_temperature_c");
        const lower = ledgerValue("fire_d2_critical_temperature_lower_bound_c");
        const kind = ledgerValue("fire_d2_critical_temperature_controlling_kind");
        const strength = ledgerValue("fire_d2_strength_inversion_result");
        const modulus = ledgerValue("fire_d2_modulus_inversion_result");
        let headline = "Критическая температура стали";
        let resultText = t !== undefined && t !== null ? `tcr = ${displayValue(t)} °C` : (lower !== undefined && lower !== null ? `tcr > ${displayValue(lower)} °C` : "точная температура не определена");
        if (cstatus === "AMBIENT_CAPACITY_EXCEEDED") {
            headline = "Несущая способность не обеспечена при нормальной температуре";
            resultText = "Определяющая ветвь требует коэффициент > 1; tcr ≤ 20 °C.";
        }
        const kindLabel = kind === "gamma_T" ? "прочность γT" : kind === "gamma_E" ? "модуль упругости γe" : kind === "bounded" ? "обе ветви выше опубликованного диапазона" : kind;
        const branch = (name, row) => row ? `<div class="result-card"><strong>${name}</strong><div class="field-hint">${escapeHtml(row.status ?? "")} · ${row.temperature_c !== null && row.temperature_c !== undefined ? `t = ${escapeHtml(displayValue(row.temperature_c))} °C` : row.temperature_lower_bound_c !== undefined ? `t > ${escapeHtml(displayValue(row.temperature_lower_bound_c))} °C` : "без точной температуры"}</div></div>` : "";
        els.question.innerHTML = `<div class="card-kicker"><span class="standard-badge">SP554 · приложение Б</span><span>${escapeHtml(cstatus ?? "RESULT")}</span></div>
      <h1>${escapeHtml(headline)}</h1><p class="question-subtitle">${escapeHtml(resultText)}</p>
      <div class="callout"><strong>Определяющая ветвь:</strong> ${escapeHtml(kindLabel ?? "—")}. γT и γe инвертируются независимо; численный min(γT,γe) не используется как общая обратная кривая.</div>
      ${branch("Ветка прочности γT", strength)}${branch("Ветка модуля упругости γe", modulus)}${refsHtml(card.normative_refs ?? [])}`;
        return;
    }
    els.question.innerHTML = `
    <div class="card-kicker"><span class="standard-badge">${escapeHtml(card?.owner_standard_id || "DAG")}</span><span>${escapeHtml(card?.node_type || status)}</span></div>
    <h1>${escapeHtml(card?.title || "Маршрут завершён")}</h1>
    <p class="question-subtitle">${status === "RESULT" ? "Получен результат текущей нормативной ветви." : "Текущая guided-сессия завершена."}</p>
    <div class="result-card"><strong>${escapeHtml(statusLabel(status))}</strong></div>
    ${refsHtml(card?.normative_refs ?? [])}`;
}
function payloadIsReady(card) {
    if (!card?.interactive)
        return false;
    const fields = card.fields ?? [];
    if (draftPayload === undefined || draftPayload === null || draftPayload === "")
        return false;
    if (card.submit_shape === "object") {
        const req = fields.filter((f) => f.required !== false).map((f) => f.quantity_id);
        if (!draftPayload || typeof draftPayload !== "object")
            return false;
        if (req.some((qid) => draftPayload[qid] === undefined || draftPayload[qid] === ""))
            return false;
    }
    if (card.external_handoff) {
        if (!draftProvenance?.source_document || !draftProvenance?.source_reference)
            return false;
    }
    return true;
}
function updateNextState() {
    const card = currentRenderCard();
    els.next.disabled = !payloadIsReady(card);
    if (historyCursor !== null) {
        const hist = envelope?.state?.interaction_history ?? [];
        els.next.textContent = reviewChanged() ? "Применить изменение" : (historyCursor < hist.length - 1 ? "Далее →" : "К текущему шагу →");
    }
    else {
        els.next.textContent = "Далее";
    }
}
function renderHistory() {
    const history = envelope?.state?.interaction_history ?? [];
    if (!history.length) {
        els.history.innerHTML = `<span class="history-chip">Начало расчёта</span>`;
        return;
    }
    els.history.innerHTML = history.map((row, idx) => {
        const card = cardByNodeId(row.node_id);
        const label = card?.title || row.node_id;
        return `<button class="history-chip ${historyCursor === idx ? "active-edit" : ""}" type="button" data-history-index="${idx}" title="Перейти к этому шагу">${idx + 1}. ${escapeHtml(label)}</button>`;
    }).join("");
    els.history.querySelectorAll("[data-history-index]").forEach((button) => {
        button.addEventListener("click", () => enterReview(Number(button.dataset.historyIndex)));
    });
    if (historyCursor === null)
        els.history.scrollLeft = els.history.scrollWidth;
}
function renderLedger() {
    const rows = envelope?.state?.ledger ?? [];
    const search = els.ledgerSearch.value.trim().toLowerCase();
    const filter = els.ledgerFilter.value;
    const visible = rows.filter((row) => {
        if (filter !== "all" && row.source_kind !== filter)
            return false;
        if (!search)
            return true;
        return `${row.name_ru ?? ""} ${row.symbol ?? ""} ${row.quantity_id ?? ""}`.toLowerCase().includes(search);
    });
    if (!visible.length) {
        els.ledger.innerHTML = `<div class="ledger-empty">${rows.length ? "Нет величин по выбранному фильтру." : "Величины появятся после первого ответа."}</div>`;
        return;
    }
    els.ledger.innerHTML = visible.map((row) => `
    <div class="ledger-row ${row.source_kind === "CALCULATED" ? "calculated" : ""}" title="${escapeHtml(row.quantity_id)}">
      <div class="ledger-top">
        <div class="ledger-name">${escapeHtml(row.name_ru || row.quantity_id)}${row.symbol ? `<span class="ledger-symbol">${escapeHtml(row.symbol)}</span>` : ""}</div>
        <div class="ledger-value">${escapeHtml(displayValue(row.value))}${row.unit ? `<span class="ledger-unit">${escapeHtml(row.unit)}</span>` : ""}</div>
      </div>
      <div class="ledger-bottom">
        <span class="source-chip ${escapeHtml(row.source_kind)}">${escapeHtml(row.source_kind)}</span>
        <span class="producer-label">${escapeHtml(row.producer_node_id)}</span>
      </div>
    </div>`).join("");
}
function renderTrace() {
    const trace = envelope?.state?.trace ?? [];
    if (!trace.length) {
        els.trace.innerHTML = `<div class="ledger-empty">Execution trace пока пуст.</div>`;
        return;
    }
    els.trace.innerHTML = trace.map((row) => {
        const outputs = Object.entries(row.outputs ?? {}).map(([k, v]) => `${k} = ${displayValue(v)}`).join("; ");
        return `<div class="trace-record">
      <div class="trace-head"><span class="trace-seq">${escapeHtml(row.sequence)}</span><span class="trace-node">${escapeHtml(row.node_id)}</span><span class="trace-event">${escapeHtml(row.event_kind)}</span></div>
      <div class="trace-output">${escapeHtml(outputs || row.status)}${row.selected_edge_id ? `<br>edge: ${escapeHtml(row.selected_edge_id)}` : ""}</div>
    </div>`;
    }).join("");
}
function renderTabs() {
    document.querySelectorAll(".panel-tab").forEach((button) => {
        const tab = button.dataset.tab;
        button.classList.toggle("active", tab === activeTab);
        button.setAttribute("aria-selected", String(tab === activeTab));
    });
    const ledgerActive = activeTab === "ledger";
    els.ledger.hidden = !ledgerActive;
    els.ledgerToolbar.hidden = !ledgerActive;
    els.trace.hidden = ledgerActive;
}
function render() {
    if (!envelope)
        return;
    const state = envelope.state;
    const card = currentRenderCard();
    const status = state.status || "";
    els.status.textContent = statusLabel(status);
    els.status.className = `status-pill ${statusClass(status)}`;
    const answered = (state.interaction_history ?? []).length;
    els.step.textContent = historyCursor !== null ? `Просмотр шага ${historyCursor + 1} из ${answered}` : `Шаг ${answered + (card?.interactive ? 1 : 0)} · ответов: ${answered}`;
    els.graph.textContent = state.graph_id || contract?.graph_id || "DAG";
    renderHistory();
    renderLedger();
    renderTrace();
    renderTabs();
    renderFooter(card);
    setMessage();
    els.back.disabled = answered === 0 || historyCursor === 0;
    els.cancelEdit.hidden = historyCursor === null;
    els.cancelEdit.textContent = "К текущему шагу";
    els.editIndicator.hidden = historyCursor === null;
    if (card?.interactive)
        renderInteractiveCard(card);
    else
        renderNonInteractiveCard(card);
    updateNextState();
}
function enterReview(index) {
    if (!envelope)
        return;
    const history = envelope.state.interaction_history ?? [];
    if (index < 0 || index >= history.length)
        return;
    historyCursor = index;
    draftPayload = undefined;
    draftProvenance = null;
    render();
}
function leaveReview() {
    historyCursor = null;
    draftPayload = undefined;
    draftProvenance = null;
    render();
}
async function submitCurrent() {
    if (!envelope || submitInFlight)
        return;
    const card = currentRenderCard();
    if (!payloadIsReady(card))
        return;
    setMessage();
    submitInFlight = true;
    els.next.disabled = true;
    try {
        const body = JSON.stringify({ payload: draftPayload, provenance: draftProvenance });
        if (historyCursor !== null) {
            const history = envelope.state.interaction_history ?? [];
            const row = history[historyCursor];
            if (!reviewChanged()) {
                if (historyCursor < history.length - 1) {
                    historyCursor += 1;
                    draftPayload = undefined;
                    draftProvenance = null;
                    render();
                    return;
                }
                historyCursor = null;
                draftPayload = undefined;
                draftProvenance = null;
                render();
                return;
            }
            envelope = await api(`/api/sessions/${encodeURIComponent(envelope.session_id)}/answers/${encodeURIComponent(row.node_id)}`, { method: "PUT", body });
            historyCursor = null;
        }
        else {
            envelope = await api(`/api/sessions/${encodeURIComponent(envelope.session_id)}/answer`, { method: "POST", body });
        }
        draftPayload = undefined;
        draftProvenance = null;
        render();
    }
    catch (error) {
        setMessage(error instanceof Error ? error.message : String(error));
    }
    finally {
        submitInFlight = false;
        updateNextState();
    }
}
async function newSession() {
    setMessage();
    try {
        envelope = await api("/api/sessions", { method: "POST", body: "{}" });
        historyCursor = null;
        draftPayload = undefined;
        draftProvenance = null;
        render();
    }
    catch (error) {
        setMessage(error instanceof Error ? error.message : String(error));
    }
}
function saveSession() {
    if (!envelope)
        return;
    const data = JSON.stringify(envelope.state, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fire_calculation_${envelope.session_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
}
async function loadSession(file) {
    setMessage();
    try {
        const text = await file.text();
        const snapshot = JSON.parse(text);
        envelope = await api("/api/sessions/restore", { method: "POST", body: JSON.stringify({ snapshot }) });
        historyCursor = null;
        draftPayload = undefined;
        draftProvenance = null;
        render();
    }
    catch (error) {
        setMessage(`Не удалось восстановить сессию: ${error instanceof Error ? error.message : String(error)}`);
    }
    finally {
        els.loadSession.value = "";
    }
}
async function boot() {
    try {
        contract = await api("/api/ui-contract");
        await newSession();
    }
    catch (error) {
        setMessage(`FIRE-UI1 не запущен: ${error instanceof Error ? error.message : String(error)}`);
    }
}
els.next.addEventListener("click", submitCurrent);
els.back.addEventListener("click", () => {
    const history = envelope?.state?.interaction_history ?? [];
    if (!history.length)
        return;
    if (historyCursor === null)
        enterReview(history.length - 1);
    else if (historyCursor > 0)
        enterReview(historyCursor - 1);
});
els.cancelEdit.addEventListener("click", leaveReview);
els.newSession.addEventListener("click", newSession);
els.saveSession.addEventListener("click", saveSession);
els.loadSession.addEventListener("change", () => {
    const file = els.loadSession.files?.[0];
    if (file)
        void loadSession(file);
});
els.ledgerSearch.addEventListener("input", renderLedger);
els.ledgerFilter.addEventListener("change", renderLedger);
document.querySelectorAll(".panel-tab").forEach((button) => {
    button.addEventListener("click", () => {
        activeTab = button.dataset.tab;
        renderTabs();
    });
});
document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveSession();
    }
    if (event.key === "Enter" && !event.shiftKey && !els.next.disabled && document.activeElement?.tagName !== "TEXTAREA") {
        event.preventDefault();
        void submitCurrent();
    }
});
void boot();
