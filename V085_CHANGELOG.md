# v0.85 — FVM mesh / gradient remediation

Scope implemented from user review:

1. Temperature chart axes
   - y-axis starts at 0 °C;
   - temperature ticks are exact 100 °C increments;
   - applies to unprotected and protected thermal charts through the cumulative v0.84 renderer patch.

2. FVM final-step gradient
   - protected-element FVM model now shows the actual final-step temperature field;
   - explicit dT/dx [°C/mm] curve is rendered for the final step;
   - the final protection node -> lumped steel interface segment is distinguished from protection nodes.

3. Mesh selection
   - removed the production dependence on the legacy fixed n=3 route through the v0.85 registry override;
   - base mesh: n >= 12 and dx <= 1.5 mm;
   - explicit time step: Fo <= 0.25;
   - final reported result is checked on doubled mesh n -> 2n;
   - convergence criterion: |Δt_R| <= 0.05 min OR relative Δt_R <= 0.1 %;
   - refined 2n result is retained after PASS;
   - criterion is explicitly labelled as project numerical control, not an SP554 material requirement.

4. Thickness profile correction
   - protection-node profile uses only real FVM protection nodes;
   - steel remains a separate lumped interface node at x = delta_protection;
   - no fake protection node is created at x = delta_protection by substituting steel temperature.

Control case (20 mm protection):
- base n = 14, dx = 1.428571 mm;
- refined n = 28, dx = 0.714286 mm;
- base fire resistance = 85.522044 min;
- refined fire resistance = 85.523622 min;
- difference = 0.001578 min = 0.001845 % -> PASS.

Focused cumulative regression:
- v0.81 -> v0.85: 23/23 PASS.
- FIRE-UI23 + v0.84 + v0.85 focused set: 20/20 PASS.
