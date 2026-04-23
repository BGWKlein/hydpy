# pylint: disable=missing-module-docstring

from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core.typingtools import *
from hydpy.models.snow import snow_parameters


class NLayers(parametertools.NmbParameter):
    """Number of snow layers  [-]."""

    SPAN = (1, None)


class ZLayers(snow_parameters.Parameter1DLayers):
    """Height of each snow layer [m].

    You can use method |snow_model.BaseModel.prepare_layers| to determine the values of
    |ZLayers| based on the catchment's elevation distribution.
    """


class LayerArea(snow_parameters.Parameter1DLayers):
    """Area of snow layer as a percentage of total area [-].

    Calling method |snow_model.BaseModel.prepare_layers| to determine the values of
    parameter |ZLayers| also sets all entries of parameter |LayerArea| to the same
    average value.
    """

    SPAN = (0.0, 1.0)


class GradP(parametertools.Parameter):
    """Altitude gradient of precipitation [1/m]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    INIT = 0.00041


class GradTMean(snow_parameters.Parameter1D366):
    """Altitude gradient of daily mean air temperature for each day of the year
    [°C/100m].

    To apply the values proposed by :cite:t:`ref-Valery` for France, provide the
    keyword argument `option` with the value `"valery"`.

    >>> from hydpy import print_vector
    >>> from hydpy.models.snow import *
    >>> simulationstep("1d")
    >>> parameterstep("1d")
    >>> nlayers(5)
    >>> gradtmean(option="valery")
    >>> gradtmean
    gradtmean(option="valery")
    >>> print_vector(gradtmean.values[90:95])
    0.59, 0.591, 0.591, 0.592, 0.593

    If an invalid option name is passed:

    >>> gradtmean(option="valery2")
    Traceback (most recent call last):
    ...
    ValueError: Parameter `gradtmean` of element `?` supports the options `valery`, \
but `valery2` is given.

    """

    TYPE: Final = float
    SPAN = (0.0, None)
    KEYWORDS = {"option": parametertools.Keyword(name="option")}

    def __call__(self, *args, **kwargs) -> None:
        self._keywordarguments = parametertools.KeywordArguments(False)
        idx = self._find_kwargscombination(args, kwargs, ({"option"},))
        if idx is None:
            super().__call__(*args, **kwargs)
        else:
            self._keywordarguments = parametertools.KeywordArguments(
                option=kwargs["option"]
            )
            self.values = self._get_values_according_to_option()


    def _get_values_according_to_option(self) -> VectorFloat:
        kwargs = self._keywordarguments
        if kwargs["option"] == "valery":
            values = [
            0.434, 0.434, 0.435, 0.436 ,0.437, 0.439, 0.440, 0.441, 0.442, 0.444, 0.445,
            0.446, 0.448, 0.450, 0.451, 0.453, 0.455, 0.456, 0.458, 0.460, 0.462, 0.464,
            0.466, 0.468, 0.470, 0.472, 0.474, 0.476, 0.478, 0.480, 0.483, 0.485, 0.487,
            0.489, 0.492, 0.494, 0.496, 0.498, 0.501, 0.503, 0.505, 0.508, 0.510, 0.512,
            0.515, 0.517, 0.519, 0.522, 0.524, 0.526, 0.528, 0.530, 0.533, 0.535, 0.537,
            0.539, 0.541, 0.543, 0.545, 0.546, 0.547, 0.549, 0.551, 0.553, 0.555, 0.557,
            0.559, 0.560, 0.562, 0.564, 0.566, 0.567, 0.569, 0.570, 0.572, 0.573, 0.575,
            0.576, 0.577, 0.579, 0.580, 0.581, 0.582, 0.583, 0.584, 0.585, 0.586, 0.587,
            0.588, 0.589, 0.590, 0.591, 0.591, 0.592, 0.593, 0.593, 0.594, 0.595, 0.595,
            0.596, 0.596, 0.597, 0.597, 0.597, 0.598, 0.598, 0.598, 0.599, 0.599, 0.599,
            0.599, 0.600, 0.600, 0.600, 0.600, 0.600, 0.601, 0.601, 0.601, 0.601, 0.601,
            0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.602, 0.602,
            0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
            0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
            0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
            0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602, 0.602,
            0.602, 0.601, 0.601, 0.601, 0.601, 0.601, 0.601, 0.600, 0.600, 0.600, 0.600,
            0.599, 0.599, 0.599, 0.598, 0.598, 0.598, 0.597, 0.597, 0.597, 0.596, 0.596,
            0.595, 0.595, 0.594, 0.594, 0.593, 0.593, 0.592, 0.592, 0.591, 0.590, 0.590,
            0.589, 0.588, 0.588, 0.587, 0.586, 0.586, 0.585, 0.584, 0.583, 0.583, 0.582,
            0.581, 0.580, 0.579, 0.578, 0.578, 0.577, 0.576, 0.575, 0.574, 0.573, 0.572,
            0.571, 0.570, 0.569, 0.569, 0.568, 0.567, 0.566, 0.565, 0.564, 0.563, 0.562,
            0.561, 0.560, 0.558, 0.557, 0.556, 0.555, 0.554, 0.553, 0.552, 0.551, 0.550,
            0.549, 0.548, 0.546, 0.545, 0.544, 0.543, 0.542, 0.541, 0.540, 0.538, 0.537,
            0.536, 0.535, 0.533, 0.532, 0.531, 0.530, 0.528, 0.527, 0.526, 0.525, 0.523,
            0.522, 0.521, 0.519, 0.518, 0.517, 0.515, 0.514, 0.512, 0.511, 0.510, 0.508,
            0.507, 0.505, 0.504, 0.502, 0.501, 0.499, 0.498, 0.496, 0.495, 0.493, 0.492,
            0.490, 0.489, 0.487, 0.485, 0.484, 0.482, 0.481, 0.479, 0.478, 0.476, 0.475,
            0.473, 0.471, 0.470, 0.468, 0.467, 0.465, 0.464, 0.462, 0.461, 0.459, 0.458,
            0.456, 0.455, 0.454, 0.452, 0.451, 0.450, 0.448, 0.447, 0.446, 0.445, 0.443,
            0.442, 0.441, 0.440, 0.439, 0.438, 0.437, 0.436, 0.435, 0.434, 0.434, 0.433,
            0.432, 0.431, 0.431, 0.430, 0.430, 0.429, 0.429, 0.429, 0.428, 0.428, 0.428,
            0.428, 0.428, 0.428, 0.428, 0.428, 0.429, 0.429, 0.429, 0.430, 0.430, 0.431,
            0.431, 0.432, 0.433]
        else:
            raise ValueError(
                f"Parameter {objecttools.elementphrase(self)} supports "
                f"the options `valery`, but "
                f"`{kwargs['option']}` is given."
            ) from None
        return values

    def __repr__(self) -> str:
        if self._keywordarguments.valid:
            values = self._get_values_according_to_option()
            if (values == self.values).all():
                strings = []
                for name, value in self._keywordarguments:
                    strings.append(f'{name}="{objecttools.repr_(value)}"')
                return f"{self.name}({', '.join(strings)})"

        return super().__repr__()




class GradTMin(snow_parameters.Parameter1D366):
    """Altitude gradient of daily minimum air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class GradTMax(snow_parameters.Parameter1D366):
    """Altitude gradient of daily maximum air temperature for each day of the year
    [°C/100m]."""

    TYPE: Final = float
    SPAN = (0.0, None)


class MeanAnSolidPrecip(snow_parameters.Parameter1DLayers):
    """Mean annual solid precipitation [mm/a]."""

    SPAN = (0.0, None)


class CN1(parametertools.Parameter):
    """Temporal weighting coefficient for the snow pack's thermal state [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)


class CN2(parametertools.Parameter):
    """Degree-day melt coefficient [mm/°C/T]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    TIME = True
    SPAN = (0.0, None)


class CN3(parametertools.Parameter):
    """Accumulation threshold [mm]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, None)


class CN4(parametertools.Parameter):
    """Fraction of annual snowfall defining the melt threshold [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = float
    SPAN = (0.0, 1.0)
    INIT = 0.9


class Hysteresis(parametertools.Parameter):
    """Flag that indicates whether hysteresis of build-up and melting of the snow cover
    should be considered [-]."""

    NDIM: Final[Literal[0]] = 0
    TYPE: Final = bool
    SPAN = (False, True)
    INIT = False
