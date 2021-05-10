# -*- coding: utf-8 -*-

"""Top-level package for vulture."""

from .__version__ import __author__, __email__, __version__  # noqa: F401

from roocs_utils.config import get_config
import vulture

CONFIG = get_config(vulture)

from .wsgi import application  # noqa: F401
