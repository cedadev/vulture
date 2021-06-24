# -*- coding: utf-8 -*-

"""Top-level package for vulture."""

from .__version__ import __author__, __email__, __version__  # noqa: F401

from .wsgi import application  # noqa: F401


# Test that cfchecker and vulture versions are th same
import cfchecker

cf_checker_version = cfchecker.__version__

if __version__ != cf_checker_version:
    raise Exception(f"Version mismatch between 'vulture' ({__version__}) "
                    f"and 'cfchecker' ({cf_checker_version})")
