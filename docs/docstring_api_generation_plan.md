# Docstring API generation plan

The v0.9 public API is statically audited by `tests/test_docstrings.py` and `standard_core.final_audit.audit_public_docstrings`.

Every public function must contain the required sections:

`Summary`, `Standard reference`, `Parameters`, `Returns`, `Assumptions`, `Sign convention`, `Unit convention`, `Applicability`, `Limitations`, `Raises`, `Examples`, `Tests`, and `Implementation notes`.

Future generated API documentation should preserve audit IDs, exact standard references, unit-explicit argument names, sign conventions, applicability gates, external dependencies, and test/validation links. Generated documentation must never convert an implementation status into a compliance or certification claim.
