"""Traceable implementation of selected СП 16.13330.2017 calculations."""

from .release_metadata import PACKAGE_VERSION, RELEASE_STAGE
from .declarative_runtime_evidence import install as _install_declarative_runtime_evidence

__version__ = PACKAGE_VERSION
__release_stage__ = RELEASE_STAGE

# Audit instrumentation only: this preserves the existing declarative executor
# as the sole engineering calculation path and records dataset-row evidence for
# REPORT-IR after successful lookups.
_install_declarative_runtime_evidence()
