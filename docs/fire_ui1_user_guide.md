# FIRE-UI1 local user guide

## Start on Windows

Double-click:

```text
START_FIRE_UI1.bat
```

or from a terminal in the extracted package:

```text
py -3 fire_ui1_launch.py
```

If the `py` launcher is unavailable:

```text
python fire_ui1_launch.py
```

The application opens a local URL such as:

```text
http://127.0.0.1:8765/
```

No public server is required.

## Guided calculation

1. Answer the current question in the central card.
2. Click **Далее**.
3. The right-hand **Расчётные величины** ledger is updated immediately.
4. For values received from another standard, enter both the value and its
   document / clause provenance.
5. Use **Назад** or a history chip to edit an earlier answer. FIRE-UI replays
   only the valid prefix and deletes obsolete downstream values.
6. The **Trace** tab shows exact node IDs, event order, selected edge and output
   quantities.

## Save and restore

**Сохранить JSON** exports the DAG-locked session snapshot. **Загрузить JSON**
restores it only when graph ID and graph SHA-256 match the running package.

## Current expected stop

FIRE-UI1 does not yet bind all calculation nodes to production functions. On a
route that reaches such a node it must display:

```text
BLOCKED_EXECUTOR_REQUIRED:<node_id>
```

This is correct behavior for UI1. FIRE-UI2 will replace these stops with
explicit production executor bindings, never with frontend formulas.
