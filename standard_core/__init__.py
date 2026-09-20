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
