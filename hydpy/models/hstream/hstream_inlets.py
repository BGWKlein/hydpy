# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Q(sequencetools.InletSequence):
    """Runoff [m³/s]."""
    NDIM, NUMERIC = 1, False


class InletSequences(sequencetools.InletSequences):
    """Upstream link sequences of the hstream model."""
    CLASSES = (Q,)
