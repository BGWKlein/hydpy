# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
# pylint: enable=missing-docstring

# import...
# ...from standard library
from __future__ import division, print_function
# ...HydPy specific
from hydpy.core import sequencetools


class Q(sequencetools.LinkSequence):
    """Discharge [m³/s]."""
    NDIM, NUMERIC = 0, False


class D(sequencetools.LinkSequence):
    """Water demand [m³/s]."""
    NDIM, NUMERIC = 0, False


class S(sequencetools.LinkSequence):
    """Water supply [m³/s]."""
    NDIM, NUMERIC = 0, False


class R(sequencetools.LinkSequence):
    """Water relief [m³/s]."""
    NDIM, NUMERIC = 0, False


class SenderSequences(sequencetools.LinkSequences):
    """Information link sequences of the dam model."""
    _SEQCLASSES = (Q,
                   D,
                   S,
                   R)
