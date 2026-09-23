"""Traceable implementation of selected СП 16.13330.2017 calculations."""

from .release_metadata import PACKAGE_VERSION, RELEASE_STAGE
from .declarative_runtime_evidence import install as _install_declarative_runtime_evidence
from .declarative_case_evidence import install as _install_declarative_case_evidence

__version__ = PACKAGE_VERSION
__release_stage__ = RELEASE_STAGE

# Audit instrumentation only.  The original declarative executor remains the
# sole engineering calculation path.  The first hook records immutable dataset
# rows selected by successful lookups; the second records which frozen
# expression case/classification rule/check condition the same successful
# execution used.  Neither hook recalculates engineering outputs.
_install_declarative_runtime_evidence()
_install_declarative_case_evidence()

# v0.91 final-SP554 normative remediation.  This is an engineering-runtime
# overlay, not report post-processing: central-compression fire slenderness is
# rebuilt from geometric lambda, Ryn and the normative steel E.  The complete
# published Appendix-B Table B.1 is then installed as one canonical dataset,
# superseding both the locked-draft row and any earlier differential overrides.
# The workflow overlay removes the residual legacy E_norm dependency from §9.2
# only.  Registry scoping is installed last so importing current standard_core
# cannot silently replace executors belonging to older frozen FIRE-UI DAGs.
from .fire_sp554_runtime_v091 import install as _install_fire_sp554_runtime_v091
from .fire_sp554_b1_v091_final import install as _install_fire_sp554_b1_v091_final
from .fire_sp554_runtime_v091_workflow import install as _install_fire_sp554_workflow_v091
from .fire_sp554_v091_registry_scope import install as _install_fire_sp554_registry_scope_v091

_install_fire_sp554_runtime_v091()
_install_fire_sp554_b1_v091_final()
_install_fire_sp554_workflow_v091()
_install_fire_sp554_registry_scope_v091()

# v0.92 P0 route census.  §9.1 is brought onto the same final-publication
# gamma_ct=1.1 contract as §9.2.  Legacy Section 10/11 paths remain deliberately
# fail-closed until their real consumers use the canonical action convention:
# Mz strong-axis bending, My weak-axis bending, Mx torsion only.
from .fire_sp554_runtime_v092 import install as _install_fire_sp554_runtime_v092

_install_fire_sp554_runtime_v092()
