# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class SunshineDuration(sequencetools.InputSequence):
    """Sunshine duration [h]."""

    NDIM, NUMERIC = 0, False
