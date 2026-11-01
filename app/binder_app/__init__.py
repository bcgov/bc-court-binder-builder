#!/usr/bin/env python
"""
binder_app package
=====================================

Purpose:
    Desktop app for building and checking BC court electronic binders.

Layer: Application
"""

import sys

MIN_PYTHON = (3, 10)

if sys.version_info < MIN_PYTHON:
    raise SystemExit(
        "Court binder builder needs Python {}.{} or newer (you have {}.{}). "
        "See INSTALL.md, Option 4.".format(*MIN_PYTHON, *sys.version_info[:2])
    )
