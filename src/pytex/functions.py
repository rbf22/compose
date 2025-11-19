"""Python port of KaTeX's functions.js - function registry and imports."""

from __future__ import annotations

from .define_function import _functions

# Export the functions registry
functions = _functions

# Import all function implementations (these will register themselves)
from . import functions as _  # noqa: F401

from .functions import accent  # noqa: F401
from .functions import accentunder  # noqa: F401
from .functions import arrow  # noqa: F401
from .functions import char  # noqa: F401
from .functions import color  # noqa: F401
from .functions import cr  # noqa: F401
from .functions import def_  # noqa: F401
from .functions import delimsizing  # noqa: F401
from .functions import enclose  # noqa: F401
from .functions import environment  # noqa: F401
from .functions import font  # noqa: F401
from .functions import genfrac  # noqa: F401
from .functions import hbox  # noqa: F401
from .functions import horizBrace  # noqa: F401
from .functions import href  # noqa: F401
from .functions import html  # noqa: F401
from .functions import htmlmathml  # noqa: F401
from .functions import includegraphics  # noqa: F401
from .functions import kern  # noqa: F401
from .functions import lap  # noqa: F401
from .functions import math  # noqa: F401
from .functions import mathchoice  # noqa: F401
from .functions import mclass  # noqa: F401
from .functions import op  # noqa: F401
from .functions import operatorname  # noqa: F401
from .functions import ordgroup  # noqa: F401
from .functions import overline  # noqa: F401
from .functions import phantom  # noqa: F401
from .functions import pmb  # noqa: F401
from .functions import raisebox  # noqa: F401
from .functions import relax  # noqa: F401
from .functions import rule  # noqa: F401
from .functions import sizing  # noqa: F401
from .functions import smash  # noqa: F401
from .functions import sqrt  # noqa: F401
from .functions import styling  # noqa: F401
from .functions import supsub  # noqa: F401
from .functions import symbolsOp  # noqa: F401
from .functions import symbolsOrd  # noqa: F401
from .functions import symbolsSpacing  # noqa: F401
from .functions import tag  # noqa: F401
from .functions import text  # noqa: F401
from .functions import underline  # noqa: F401
from .functions import vcenter  # noqa: F401
from .functions import verb  # noqa: F401

__all__ = ["functions"]
