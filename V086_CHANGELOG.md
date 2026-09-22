# v0.86 — protected FVM UX and fast bounded search

- Protected FVM plots now include explicit legends.
- Thickness profiles identify every sampled absolute time; the dashed last segment still connects the last protection node to the separate lumped steel node.
- Protected time-history plot identifies ISO/GOST fire, exposed protection surface, protection midpoint, last protection node, and steel with distinct styles.
- Protected time-history x-axis is expanded to the next 5 min and uses 5 min ticks.
- The production UI no longer renders the final-step dT/dx debug chart.
- Interactive SP554 12.5 uses one qualified automatic mesh (`n>=12`, `dx<=1.5 mm`, `Fo<=0.25`). The n→2n utility remains available for validation/debug but is no longer mandatory on every direct/inverse calculation.
- Minimum-thickness search no longer records visualization state at every trial thickness. It scouts the full authorized range, takes the first infeasible→feasible crossing, locally refines it, conservatively rounds upward to 0.01 mm, and builds visualization only for the selected thickness.
- Search does not fail solely because of small global non-monotonic numerical noise; it remains bounded and never extrapolates beyond the user-specified range.
- Failure diagnostics now report the best completed scout result when no feasible thickness is found.

Regression control: real STO ARSS mineral-wool R60 case over 5…40 mm selects approximately 22.05 mm with R≈60.017 min on the single production mesh.
