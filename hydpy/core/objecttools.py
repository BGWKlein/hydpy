# -*- coding: utf-8 -*-
"""This module implements tools to help to standardize the functionality
of the different objects defined by the HydPy framework.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import inspect
import sys
import textwrap
import numbers
# ...from site-packages
import numpy
# ...from HydPy
from hydpy.cythons import pointerutils
from hydpy.core import autodoctools
# from hydpy.pub import ... (actual import commands moved to
# different functions below to avoid circular dependencies)

_INT_NAN = -999999
"""Surrogate for `nan`, which is available for floating point values
but not for integer values."""


def dir_(self):
    """The prefered way for HydPy objects to respond to :func:`dir`.

    Note thedepencence on the `pub.options.dirverbose`.  If this option is
    set `True`, all attributes and methods of the given instance and its
    class (including those inherited from the parent classes) are returned:

    >>> from hydpy.pub import options
    >>> options.dirverbose = True
    >>> from hydpy.core.objecttools import dir_
    >>> class Test(object):
    ...     only_public_attribute =  None
    >>> print(len(dir_(Test())) > 1) # Long list, try it yourself...
    True

    If the option is set to `False`, only the `public` attributes and methods
    (which do need begin with `_`) are returned:

    >>> options.dirverbose = False
    >>> print(dir_(Test())) # Short list with one single entry...
    ['only_public_attribute']
    """
    from hydpy.pub import options
    names = set()
    for thing in list(inspect.getmro(type(self))) + [self]:
        for name in vars(thing).keys():
            if options.dirverbose or not name.startswith('_'):
                names.add(name)
    if names:
        names = list(names)
    else:
        names = [' ']
    return names


def classname(self):
    """Return the class name of the given instance object or class.

    >>> from hydpy.core.objecttools import classname
    >>> from hydpy.pub import options
    >>> print(classname(float))
    float
    >>> print(classname(options))
    Options
    """
    if not inspect.isclass(self):
        self = type(self)
    return str(self).split("'")[1].split('.')[-1]


def instancename(self):
    """Return the class name of the given instance object or class in lower
    case letters.

    >>> from hydpy.core.objecttools import instancename
    >>> from hydpy.pub import options
    >>> print(instancename(options))
    options
    """
    return classname(self).lower()


def name(self):
    """Name of the class of the given instance in lower case letters.

    This function is thought to be implemented as a property.  Otherwise
    it would violate the principle not to access or manipulate private
    attributes ("_name"):

    >>> from hydpy.core.objecttools import name
    >>> class Test(object):
    ...     name = property(name)
    >>> test1 = Test()
    >>> test1.name
    'test'
    >>> test1._name
    'test'

    The private attribute is added for performance reasons only.  Note that
    it is a class attribute:

    >>> test2 = Test()
    >>> test2._name
    'test'
    """
    try:
        return type(self).__dict__['_name']
    except KeyError:
        type(self)._name = instancename(self)
        return type(self).__dict__['_name']


def modulename(self):
    """Return the module name of the given instance object.

    >>> from hydpy.core.objecttools import modulename
    >>> from hydpy.pub import options
    >>> print(modulename(options))
    objecttools
    """
    return self.__module__.split('.')[-1]


def devicename(self):
    """Try to return the name of the (indirect) master
    :class:`~hydpy.core.devicetools.Node` or
    :class:`~hydpy.core.devicetools.Element` instance,
    otherwise return `?`.
    """
    while True:
        device = getattr(self, 'element', getattr(self, 'node', None))
        if device is not None:
            return device.name
        for test in ('model', 'seqs', 'subseqs', 'pars', 'subpars'):
            master = getattr(self, test, None)
            if master is not None:
                self = master
                break
        else:
            return '?'


def augmentexcmessage(prefix=None, suffix=None):
    """Augment an exception message with additional information while keeping
    the original traceback.

    You can prefix and/or suffix text.  If you prefix something (which happens
    much more often in the HydPy framework), the sub-clause ', the following
    error occured:' is automatically included:

    >>> from hydpy.core import objecttools
    >>> import textwrap
    >>> try:
    ...     1 + '1'
    ... except TypeError:
    ...     try:
    ...         prefix = 'While showing how prefixing works'
    ...         suffix = '(This is a final remark.)'
    ...         objecttools.augmentexcmessage(prefix, suffix)
    ...     except TypeError as exc:
    ...         for line in textwrap.wrap(exc.args[0], width=76):
    ...             print(line)
    While showing how prefixing works, the following error occured: unsupported
    operand type(s) for +: 'int' and 'str' (This is a final remark.)

    Note that the ancillary purpose of function :func:`augmentexcmessage` is
    to make re-raising exceptions compatible with both Python 2 and 3.
    """
    from hydpy.pub import pyversion
    exception, message, traceback_ = sys.exc_info()
    if prefix is not None:
        message = ('%s, the following error occured: %s'
                   % (prefix, message))
    if suffix is not None:
        message = ' '.join((message, suffix))
    if pyversion < 3:
        exec('raise exception, message, traceback_')
    else:
        raise exception(message).with_traceback(traceback_)


class _PreserveStrings(object):
    """Helper class for :class:`_Repr_`."""

    def __init__(self, preserve_strings):
        self.new_value = preserve_strings
        self.old_value = repr_._preserve_strings

    def __enter__(self):
        repr_._preserve_strings = self.new_value
        return None

    def __exit__(self, type_, value, traceback):
        repr_._preserve_strings = self.old_value


class _Decimals(object):
    """Helper class for :class:`_Repr_`."""
    def __init__(self, decimals):
        self.new_value = decimals
        self.old_value = repr_._decimals

    def __enter__(self):
        repr_._decimals = self.new_value
        return None

    def __exit__(self, type_, value, traceback):
        repr_._decimals = self.old_value


class _Repr_(object):
    """Singleton class, see the documentation on :func:`repr_`."""

    def __init__(self):
        self._decimals = None
        self._preserve_strings = False

    def __call__(self, value):
        from hydpy.pub import options
        if self._decimals is None:
            decimals = options.reprdigits
        else:
            decimals = self._decimals
        if isinstance(value, str):
            if self._preserve_strings:
                return '"%s"' % value
            else:
                return value
        if isinstance(value, (pointerutils.Double, pointerutils.PDouble)):
            value = float(value)
        if ((decimals is not None) and
                isinstance(value, numbers.Real) and
                (not isinstance(value, numbers.Integral))):
            string = '{0:.{1}f}'.format(value, decimals)
            string = string.rstrip('0')
            if string.endswith('.'):
                string += '0'
            return string
        else:
            return repr(value)

    def preserve_strings(self, preserve_strings):
        """Change the `preserve_string` option inside a with block."""
        return _PreserveStrings(preserve_strings)

    def decimals(self, decimals):
        """Change the `decimals` option inside a with block."""
        return _Decimals(decimals)


repr_ = _Repr_()
"""Modifies :func:`repr` for strings and floats, mainly for supporting
clean float representations that are compatible with :mod:`doctest`.

When value is a string, it is returned without any modification:

>>> from hydpy.core.objecttools import repr_
>>> print('test')
test
>>> print(repr('test'))
'test'
>>> print(repr_('test'))
test

You can change this behaviour of function object :func:`repr_`, when necessary:

>>> with repr_.preserve_strings(True):
...     print(repr_('test'))
"test"

Behind the with block, :func:`repr_` works as before
(even in case of an error):

>>> print(repr_('test'))
test

When value is a float, the result depends on how the option
:attr:`~Options.reprdigits` is set. If it is :class:`None`, :func:`repr`
defines the number of digits in the usual, system dependend manner:

>>> from hydpy.pub import options
>>> options.reprdigits = None
>>> repr(1./3.) == repr_(1./3.)
True

Through setting :attr:`~Options.reprdigits` to a positive integer value,
one defines the maximum number of decimal places, which allows for
doctesting across different systems and Python versions:

>>> options.reprdigits = 6
>>> repr_(1./3.)
'0.333333'
>>> repr_(2./3.)
'0.666667'
>>> repr_(1./2.)
'0.5'

Changing the number of decimal places can be done via a with block:

>>> with repr_.decimals(3):
...     print(repr_(1./3.))
0.333

Such a change is only temporary (even in case of an error):
>>> repr_(1./3.)
'0.333333'

:func:`repr_` can also be applied on numpy's float types:

>>> import numpy
>>> repr_(numpy.float(1./3.))
'0.333333'
>>> repr_(numpy.float64(1./3.))
'0.333333'
>>> repr_(numpy.float32(1./3.))
'0.333333'
>>> repr_(numpy.float16(1./3.))
'0.333252'

Note that the deviation from the `true` result in the last example is due
to the low precision of :class:`~numpy.float16`.

On all types not mentioned above, the usual :func:`repr` function is
applied, e.g.:

>>> repr([1, 2, 3])
'[1, 2, 3]'
>>> repr_([1, 2, 3])
'[1, 2, 3]'
"""


def repr_values(values):
    """Return comma seperated representations of the given values using
    function :func:`repr_`.

    >>> from hydpy.core.objecttools import repr_values
    >>> repr_values([1./1., 1./2., 1./3.])
    '1.0, 0.5, 0.333333'

    Note that the returned string is not wrapped.
    """
    return '%s' % ', '.join(repr_(value) for value in values)


def repr_tuple(values):
    """Return a tuple representation of the given values using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import repr_tuple
    >>> repr_tuple([1./1., 1./2., 1./3.])
    '(1.0, 0.5, 0.333333)'

    Note that the returned string is not wrapped.

    In the special case of an iterable with only one entry, the returned
    string is still a valid tuple:

    >>> repr_tuple([1.])
    '(1.0,)'
    """
    if len(values) == 1:
        return '(%s,)' % repr_values(values)
    else:
        return '(%s)' % repr_values(values)


def repr_list(values):
    """Return a list representation of the given values using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import repr_list
    >>> repr_list([1./1., 1./2., 1./3.])
    '[1.0, 0.5, 0.333333]'

    Note that the returned string is not wrapped.
    """
    return '[%s]' % repr_values(values)


def assignrepr_value(value, prefix, width=None):
    """Return a prefixed string representation of the given value using
    function :func:`repr_`.

    Note that the argument has no effect. It is thought for increasing
    usage compatibility with functions like :func:`assignrepr_list` only.

    >>> from hydpy.core.objecttools import assignrepr_value
    >>> print(assignrepr_value(1./3., 'test = '))
    test = 0.333333
    """
    return prefix + repr_(value)


def assignrepr_values(values, prefix, width=None, _fakeend=0):
    """Return a prefixed, wrapped and properly aligned string representation
    of the given values using function :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_values
    >>> print(assignrepr_values(range(1, 13), 'test(', 20) + ')')
    test(1, 2, 3, 4, 5,
         6, 7, 8, 9, 10,
         11, 12)

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_values(range(1, 13), 'test(') + ')')
    test(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
    """
    blanks = ' '*len(prefix)
    string = repr_values(values)
    if width is None:
        wrapped = [string]
        _fakeend = 0
    else:
        width -= len(prefix)
        wrapped = textwrap.wrap(string+'_'*_fakeend, width)
    if not wrapped:
        wrapped = ['']
    lines = []
    for (idx, line) in enumerate(wrapped):
        if idx == 0:
            lines.append('%s%s' % (prefix, line))
        else:
            lines.append('%s%s' % (blanks, line))
    string = '\n'.join(lines)
    return string[:len(string)-_fakeend]


class _AlwaysBracketed(object):
    """Helper class for :class:`_AssignReprBracketed`."""

    def __init__(self, value):
        self.new_value = value
        self.old_value = _AssignReprBracketed._always_bracketed

    def __enter__(self):
        _AssignReprBracketed._always_bracketed = self.new_value

    def __exit__(self, type_, value, traceback):
        _AssignReprBracketed._always_bracketed = self.old_value


class _AssignReprBracketed(object):
    """"Double Singleton class", see the documentation on
    :func:`assignrepr_tuple` and :func:`assignrepr_list`."""

    _always_bracketed = True

    def __init__(self, brackets):
        self._brackets = brackets

    def __call__(self, values, prefix, width=None):
        if (len(values) == 1) and not self._always_bracketed:
            return assignrepr_value(values[0], prefix)
        elif len(values):
            string = assignrepr_values(
                values, prefix+self._brackets[0], width, 1) + self._brackets[1]
            if (len(values) == 1) and (self._brackets[1] == ')'):
                return string[:-1] + ',)'
            else:
                return string
        else:
            return prefix + self._brackets

    def always_bracketed(self, always_bracketed):
        """Change the `always_bracketed` option inside a with block."""
        return _AlwaysBracketed(always_bracketed)


assignrepr_tuple = _AssignReprBracketed('()')
"""Return a prefixed, wrapped and properly aligned tuple string
representation of the given values using function :func:`repr_`.

>>> from hydpy.core.objecttools import assignrepr_tuple
>>> print(assignrepr_tuple(range(10), 'test = ', 22))
test = (0, 1, 2, 3, 4,
        5, 6, 7, 8, 9)

If no width is given, no wrapping is performed:

>>> print(assignrepr_tuple(range(10), 'test = '))
test = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

Functions :func:`assignrepr_tuple` works also on empty iterables and
those which possess only one entry:

>>> print(assignrepr_tuple([], 'test = '))
test = ()
>>> print(assignrepr_tuple([10], 'test = '))
test = (10,)

Optionally, bracketing single values can be prevented:

>>> with assignrepr_tuple.always_bracketed(False):
...     print(assignrepr_tuple([], 'test = '))
...     print(assignrepr_tuple([10], 'test = '))
...     print(assignrepr_tuple([10, 10], 'test = '))
test = ()
test = 10
test = (10, 10)

Behind the with block, :func:`assignrepr_tuple` works as before
(even in case of an error):

>>> print(assignrepr_tuple([10], 'test = '))
test = (10,)
"""


assignrepr_list = _AssignReprBracketed('[]')
"""Return a prefixed, wrapped and properly aligned list string
representation of the given values using function :func:`repr_`.

>>> from hydpy.core.objecttools import assignrepr_list
>>> print(assignrepr_list(range(10), 'test = ', 22))
test = [0, 1, 2, 3, 4,
        5, 6, 7, 8, 9]

If no width is given, no wrapping is performed:

>>> print(assignrepr_list(range(10), 'test = '))
test = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

Functions :func:`assignrepr_list` works also on empty iterables:

>>> print(assignrepr_list((), 'test = '))
test = []

Optionally, bracketing single values can be prevented:

>>> with assignrepr_list.always_bracketed(False):
...     print(assignrepr_list([], 'test = '))
...     print(assignrepr_list([10], 'test = '))
...     print(assignrepr_list([10, 10], 'test = '))
test = []
test = 10
test = [10, 10]

Behind the with block, :func:`assignrepr_list` works as before
(even in case of an error):

>>> print(assignrepr_list([10], 'test = '))
test = [10,]
"""


def assignrepr_values2(values, prefix):
    """Return a prefixed and properly aligned string representation
    of the given 2-dimensional value matrix using function :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_values2
    >>> import numpy
    >>> print(assignrepr_values2(numpy.eye(3), 'test(') + ')')
    test(1.0, 0.0, 0.0,
         0.0, 1.0, 0.0,
         0.0, 0.0, 1.0)

    Functions :func:`assignrepr_values2` works also on empty iterables:

    >>> print(assignrepr_values2([[]], 'test(') + ')')
    test()
    """
    lines = []
    blanks = ' '*len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append('%s%s,' % (prefix, repr_values(subvalues)))
        else:
            lines.append('%s%s,' % (blanks, repr_values(subvalues)))
    lines[-1] = lines[-1][:-1]
    return '\n'.join(lines)


def _assignrepr_bracketed2(assignrepr_bracketed1, values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned bracketed string
    representation of the given 2-dimensional value matrix using function
    :func:`repr_`."""
    prefix += assignrepr_bracketed1._brackets[0]
    lines = []
    blanks = ' '*len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append(assignrepr_bracketed1(subvalues, prefix, width))
        else:
            lines.append(assignrepr_bracketed1(subvalues, blanks, width))
        if (len(subvalues) == 1) and (lines[-1] == ')'):
            lines[-1] = lines[-1].replace(')', ',)')
        lines[-1] += ','
    lines[-1] = lines[-1][:-1] + assignrepr_bracketed1._brackets[1]
    return '\n'.join(lines)


def assignrepr_tuple2(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned tuple string
    representation of the given 2-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_tuple2
    >>> import numpy
    >>> print(assignrepr_tuple2(numpy.eye(3), 'test = ', 18))
    test = ((1.0, 0.0,
             0.0),
            (0.0, 1.0,
             0.0),
            (0.0, 0.0,
             1.0))

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_tuple2(numpy.eye(3), 'test = '))
    test = ((1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0))

    Functions :func:`assignrepr_tuple2` works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_tuple2([[]], 'test = '))
    test = (())
    >>> print(assignrepr_tuple2([[], [1]], 'test = '))
    test = ((),
            (1,))
    """
    return _assignrepr_bracketed2(assignrepr_tuple, values, prefix, width)


def assignrepr_list2(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned list string
    representation of the given 2-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_list2
    >>> import numpy
    >>> print(assignrepr_list2(numpy.eye(3), 'test = ', 18))
    test = [[1.0, 0.0,
             0.0],
            [0.0, 1.0,
             0.0],
            [0.0, 0.0,
             1.0]]

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_list2(numpy.eye(3), 'test = '))
    test = [[1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]]

    Functions :func:`assignrepr_list2` works also on empty iterables:

    >>> print(assignrepr_list2([[]], 'test = '))
    test = [[]]
    >>> print(assignrepr_list2([[], [1]], 'test = '))
    test = [[],
            [1]]
    """
    return _assignrepr_bracketed2(assignrepr_list, values, prefix, width)


def _assignrepr_bracketed3(assignrepr_bracketed1, values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned bracketed string
    representation of the given 3-dimensional value matrix using function
    :func:`repr_`."""
    prefix += assignrepr_bracketed1._brackets[0]
    lines = []
    blanks = ' '*len(prefix)
    for (idx, subvalues) in enumerate(values):
        if idx == 0:
            lines.append(_assignrepr_bracketed2(
                            assignrepr_bracketed1, subvalues, prefix, width))
        else:
            lines.append(_assignrepr_bracketed2(
                            assignrepr_bracketed1, subvalues, blanks, width))
        if (len(subvalues) <= 1) and (lines[-1][-1] == ')'):
            lines[-1] = lines[-1][:-1] + ',)'
        lines[-1] += ','
    lines[-1] = lines[-1][:-1] + assignrepr_bracketed1._brackets[1]
    if (len(values) <= 1) and (lines[-1][-1] == ')'):
        lines[-1] = lines[-1][:-1] + ',)'
    return '\n'.join(lines)


def assignrepr_tuple3(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned tuple string
    representation of the given 3-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_tuple3
    >>> import numpy
    >>> values = [numpy.eye(3), numpy.ones((3, 3))]
    >>> print(assignrepr_tuple3(values, 'test = ', 18))
    test = (((1.0,
              0.0,
              0.0),
             (0.0,
              1.0,
              0.0),
             (0.0,
              0.0,
              1.0)),
            ((1.0,
              1.0,
              1.0),
             (1.0,
              1.0,
              1.0),
             (1.0,
              1.0,
              1.0)))

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_tuple3(values, 'test = '))
    test = (((1.0, 0.0, 0.0),
             (0.0, 1.0, 0.0),
             (0.0, 0.0, 1.0)),
            ((1.0, 1.0, 1.0),
             (1.0, 1.0, 1.0),
             (1.0, 1.0, 1.0)))

    Functions :func:`assignrepr_tuple3` works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_tuple3([[[]]], 'test = '))
    test = (((),),)
    >>> print(assignrepr_tuple3([[[], [1]]], 'test = '))
    test = (((),
             (1,)),)
    """
    return _assignrepr_bracketed3(assignrepr_tuple, values, prefix, width)


def assignrepr_list3(values, prefix, width=None):
    """Return a prefixed, wrapped and properly aligned list string
    representation of the given 3-dimensional value matrix using function
    :func:`repr_`.

    >>> from hydpy.core.objecttools import assignrepr_list3
    >>> import numpy
    >>> values = [numpy.eye(3), numpy.ones((3, 3))]
    >>> print(assignrepr_list3(values, 'test = ', 18))
    test = [[[1.0,
              0.0,
              0.0],
             [0.0,
              1.0,
              0.0],
             [0.0,
              0.0,
              1.0]],
            [[1.0,
              1.0,
              1.0],
             [1.0,
              1.0,
              1.0],
             [1.0,
              1.0,
              1.0]]]

    If no width is given, no wrapping is performed:

    >>> print(assignrepr_list3(values, 'test = '))
    test = [[[1.0, 0.0, 0.0],
             [0.0, 1.0, 0.0],
             [0.0, 0.0, 1.0]],
            [[1.0, 1.0, 1.0],
             [1.0, 1.0, 1.0],
             [1.0, 1.0, 1.0]]]

    Functions :func:`assignrepr_list3` works also on empty iterables and
    those which possess only one entry:

    >>> print(assignrepr_list3([[[]]], 'test = '))
    test = [[[]]]
    >>> print(assignrepr_list3([[[], [1]]], 'test = '))
    test = [[[],
             [1]]]
    """
    return _assignrepr_bracketed3(assignrepr_list, values, prefix, width)


def round_(values, decimals=None, width=0,
           lfill=None, rfill=None, **kwargs):
    """Prints values with a maximum number of digits in doctests.

    See the documentation on function :func:`repr_` for more details.  And
    note thate the option keyword arguments are passed to the print function.

    Usually one would apply function :func:`round_` on a single or a vector
    of numbers:

    >>> from hydpy.core.objecttools import round_
    >>> round_(1./3., decimals=6)
    0.333333
    >>> round_((1./2., 1./3., 1./4.), decimals=4)
    0.5, 0.3333, 0.25

    Additionally, one can supply a `width` and a `rfill` argument:
    >>> round_(1.0, width=6, rfill='0')
    1.0000

    Alternatively, one can use the `lfill` arguments, which
    might e.g. be usefull for aligning different strings:

    >>> round_('test', width=6, lfill='_')
    __test

    Using both the `lfill` and the `rfill` argument raises an error:

    >>> round_(1.0, lfill='_', rfill='0')
    Traceback (most recent call last):
    ...
    ValueError: For function `round_` values are passed for both arguments `lfill` and `rfill`.  This is not allowed.
    """
    with repr_.decimals(decimals):
        if hasattr(values, '__iter__') and (not isinstance(values, str)):
            string = repr_values(values)
        else:
            string = repr_(values)
        if (lfill is not None) and (rfill is not None):
            raise ValueError(
                'For function `round_` values are passed for both arguments '
                '`lfill` and `rfill`.  This is not allowed.')
        if (lfill is not None) or (rfill is not None):
            width = max(width, len(string))
            if lfill is not None:
                string = string.rjust(width, lfill)
            else:
                string = string.ljust(width, rfill)
        print(string, **kwargs)


def extract(values, types, skip=False):
    """Return a generator that extracts certain objects from `values`.

    This function is thought for supporting the definition of functios
    with arguments, that can be objects of of contain types or that can
    be iterables containing these objects.

    The following examples show that function :func:`extract`
    basically implements a type specific flattening mechanism:

    >>> from hydpy.core.objecttools import extract
    >>> tuple(extract('str1', (str, int)))
    ('str1',)
    >>> tuple(extract(['str1', 'str2'], (str, int)))
    ('str1', 'str2')
    >>> tuple(extract((['str1', 'str2'], [1,]), (str, int)))
    ('str1', 'str2', 1)

    If an object is neither iterable nor of the required type, the
    following exception is raised:

    >>> tuple(extract((['str1', 'str2'], [None, 1]), (str, int)))
    Traceback (most recent call last):
    ...
    TypeError: The given value `None` is neither iterable nor an instance of the following classes: str, int.

    Optionally, :class:`None` values can be skipped:
    >>> tuple(extract(None, (str, int), True))
    ()
    >>> tuple(extract((['str1', 'str2'], [None, 1]), (str, int), True))
    ('str1', 'str2', 1)
    """
    if isinstance(values, types):
        yield values
    elif skip and (values is None):
        return
    else:
        try:
            for value in values:
                for subvalue in extract(value, types, skip):
                    yield subvalue
        except TypeError as exc:
            if exc.args[0].startswith('The given value'):
                raise exc
            else:
                raise TypeError(
                    'The given value `%s` is neither iterable nor an '
                    'instance of the following classes: %s.'
                    % (values,
                       ', '.join(instancename(type_) for type_ in types)))


class Options(object):
    """Singleton class for `global` options."""

    def __init__(self):
        self._printprogress = True
        self._printincolor = True
        self._verbosedir = False
        self._reprcomments = True
        self._usecython = True
        self._fastcython = True
        self._skipdoctests = False
        self._refreshmodels = False
        self._reprdigits = None
        self._warntrim = True
        self._warnsimulationstep = True
        self._checkseries = True
        self._warnmissingcontrolfile = False
        self._warnmissingobsfile = True
        self._warnmissingsimfile = True
        self._usedefaultvalues = False

    def _getprintprogress(self):
        """True/False flag indicating whether information about the progress
        of certain processes shall be printed to the standard output or not.
        The default is `True`.
        """
        return self._printprogress

    def _setprintprogress(self, value):
        self._printprogress = bool(value)

    printprogress = property(_getprintprogress, _setprintprogress)

    def _getprintincolor(self):
        """True/False flag indicating whether information shall be printed
        in color eventually or not. The default is `True`.
        """
        return self._printincolor

    def _setprintincolor(self, value):
        self._printincolor = bool(value)

    printincolor = property(_getprintincolor, _setprintincolor)

    def _getdirverbose(self):
        """True/False flag indicationg whether the listboxes for the member
        selection of the classes of the HydPy framework should be complete
        (True) or restrictive (False).  The latter is more viewable and hence
        the default.
        """
        return self._verbosedir

    def _setdirverbose(self, value):
        self._verbosedir = bool(value)

    dirverbose = property(_getdirverbose, _setdirverbose)

    def _getreprcomments(self):
        """True/False flag indicationg whether comments shall be included
        in string representations of some classes of the HydPy framework or
        not.  The default is `True`.
        """
        return self._reprcomments

    def _setreprcomments(self, value):
        self._reprcomments = bool(value)

    reprcomments = property(_getreprcomments, _setreprcomments)

    def _getusecython(self):
        """True/False flag indicating whether Cython models (True) or pure
        Python models (False) shall be applied if possible.  Using Cython
        models is more time efficient and thus the default.
        """
        return self._usecython

    def _setusecython(self, value):
        self._usecython = bool(value)

    usecython = property(_getusecython, _setusecython)

    def _getfastcython(self):
        """True/False flag indicating whether Cythonization shall be
        configured in a fast but unsafe (True) or in a slow but safe (False)
        mode.  The fast mode is the default.  Setting this flag to False
        can be helpful when the implementation of new models or other
        Cython related features introduces errors that do not result in
        informative error messages.
        """
        return self._fastcython

    def _setfastcython(self, value):
        self._fastcython = bool(value)

    fastcython = property(_getfastcython, _setfastcython)

    def _getskipdoctests(self):
        """True/False flag indicating whether documetation tests shall be
        performed under certain situations.  Applying tests increases
        reliabilty and is thus the default.
        """
        return self._skipdoctests

    def _setskipdoctests(self, value):
        self._skipdoctests = bool(value)

    skipdoctests = property(_getskipdoctests, _setskipdoctests)

    def _getreprdigits(self):
        """Required precision of string representations of floating point
        numbers, defined as the minimum number of digits to be reproduced
        by the string representation (see function :func:`repr_`).
        """
        return self._reprdigits

    def _setreprdigits(self, value):
        if value is None:
            self._reprdigits = value
        else:
            self._reprdigits = int(value)

    reprdigits = property(_getreprdigits, _setreprdigits)

    def _getwarntrim(self):
        """True/False flag indicating whether a warning shall be raised
        whenever certain values needed to be trimmed due to violating
        certain boundaries. Such warnings increase savety and are thus
        the default is `True`.  However, to cope with the limited precision
        of floating point numbers only those violations beyond a small
        tolerance value are reported (see :class:`Trimmer`).  Warnings
        with identical information are reported only once.
        """
        return self._warntrim

    def _setwarntrim(self, value):
        self._warntrim = bool(value)

    warntrim = property(_getwarntrim, _setwarntrim)

    def _getwarnsimulationstep(self):
        """True/False flag indicating whether a warning shall be raised
        when function :func:`~hydpy.core.magictools.simulationstep` is
        called for the first time.
        """
        return self._warnsimulationstep

    def _setwarnsimulationstep(self, value):
        self._warnsimulationstep = bool(value)

    warnsimulationstep = property(_getwarnsimulationstep,
                                  _setwarnsimulationstep)

    def _getcheckseries(self):
        """True/False flag indicating whether an error shall be raised
        when e.g. an incomplete input time series, not spanning the whole
        initialization time period, is loaded.
        """
        return self._checkseries

    def _setcheckseries(self, value):
        self._checkseries = bool(value)

    checkseries = property(_getcheckseries, _setcheckseries)

    def _getwarnmissingcontrolfile(self):
        """True/False flag indicating whether only a warning shall be raised
        when a required control file is missing, or an exception.
        """
        return self._warnmissingcontrolfile

    def _setwarnmissingcontrolfile(self, value):
        self._warnmissingcontrolfile = bool(value)

    warnmissingcontrolfile = property(_getwarnmissingcontrolfile,
                                      _setwarnmissingcontrolfile)

    def _getwarnmissingobsfile(self):
        """True/False flag indicating whether a warning shall be raised when a
        requested observation sequence demanded by a node instance is missing.
        """
        return self._warnmissingobsfile

    def _setwarnmissingobsfile(self, value):
        self._warnmissingobsfile = bool(value)

    warnmissingobsfile = property(_getwarnmissingobsfile,
                                  _setwarnmissingobsfile)

    def _getwarnmissingsimfile(self):
        """True/False flag indicating whether a warning shall be raised when a
        requested simulation sequence demanded a node instance is missing.
        """
        return self._warnmissingsimfile

    def _setwarnmissingsimfile(self, value):
        self._warnmissingsimfile = bool(value)

    warnmissingsimfile = property(_getwarnmissingsimfile,
                                  _setwarnmissingsimfile)

    def _getusedefaultvalues(self):
        """True/False flag indicating whether parameters values shall be
        initialized with standard values or not.
        """
        return self._usedefaultvalues

    def _setusedefaultvalues(self, value):
        self._usedefaultvalues = bool(value)

    usedefaultvalues = property(_getusedefaultvalues,
                                _setusedefaultvalues)

    __dir__ = dir_


def trim(self, lower=None, upper=None):
    """Trim the value(s) of  a :class:`ValueMath` instance.

    One can pass the lower and/or the upper boundary as a function argument.
    Otherwise, boundary values are taken from the class attribute `SPAN`
    of the given :class:`ValueMath` instance, if available.

    Note that method :func:`trim` works differently on :class:`ValueMath`
    instances handling values of different types.  For floating point values,
    an actual trimming is performed.  Additionally, a warning message is
    raised if the trimming results in a change in value exceeding the
    threshold value defined by function :func:`_tolerance`.  (This warning
    message can be suppressed by setting the related option flag to False.)
    For integer values, instead of a warning an exception is raised.
    """
    span = getattr(self, 'SPAN', (None, None))
    if lower is None:
        lower = span[0]
    if upper is None:
        upper = span[1]
    type_ = getattr(self, 'TYPE', float)
    if type_ is float:
        if self.NDIM == 0:
            _trim_float_0d(self, lower, upper)
        else:
            _trim_float_nd(self, lower, upper)
    elif type_ in (int, bool):
        if self.NDIM == 0:
            _trim_int_0d(self, lower, upper)
        else:
            _trim_int_nd(self, lower, upper)
    else:
        raise NotImplementedError(
            'Method `trim` can only be applied on parameters handling '
            'integer or floating point values, but value type of parameter '
            '`%s` is `%s`.' % (self.name, classname(self.TYPE)))


def _trim_float_0d(self, lower, upper):
    from hydpy.pub import options
    if numpy.isnan(self.value):
        return
    if (lower is None) or numpy.isnan(lower):
        lower = -numpy.inf
    if (upper is None) or numpy.isnan(upper):
        upper = numpy.inf
    if self < lower:
        if (self+_tolerance(self)) < (lower-_tolerance(lower)):
            if options.warntrim:
                self.warntrim()
        self.value = lower
    elif self > upper:
        if (self-_tolerance(self)) > (upper+_tolerance(upper)):
            if options.warntrim:
                self.warntrim()
        self.value = upper


def _trim_float_nd(self, lower, upper):
    from hydpy.pub import options
    if lower is None:
        lower = -numpy.inf
    lower = numpy.full(self.shape, lower, dtype=float)
    lower[numpy.where(numpy.isnan(lower))] = -numpy.inf
    if upper is None:
        upper = numpy.inf
    upper = numpy.full(self.shape, upper, dtype=float)
    upper[numpy.where(numpy.isnan(upper))] = numpy.inf
    idxs = numpy.where(numpy.isnan(self.values))
    self[idxs] = lower[idxs]
    if numpy.any(self < lower) or numpy.any(self > upper):
        if (numpy.any((self+_tolerance(self)) <
                      (lower-_tolerance(lower))) or
                numpy.any((self-_tolerance(self)) >
                          (upper+_tolerance(upper)))):
            if options.warntrim:
                self.warntrim()
        self.values = numpy.clip(self.values, lower, upper)
    self[idxs] = numpy.nan


def _trim_int_0d(self, lower, upper):
    if lower is None:
        lower = _INT_NAN
    if upper is None:
        upper = -_INT_NAN
    if (self != _INT_NAN) and ((self < lower) or (self > upper)):
        raise ValueError(
            'The value `%d` of parameter `%s` of element `%s` is not valid.  '
            % (self.value, self.name, devicename(self)))


def _trim_int_nd(self, lower, upper):
    if lower is None:
        lower = _INT_NAN
    lower = numpy.full(self.shape, lower, dtype=int)
    if upper is None:
        upper = -_INT_NAN
    upper = numpy.full(self.shape, upper, dtype=int)
    idxs = numpy.where(self == _INT_NAN)
    self[idxs] = lower[idxs]
    if numpy.any(self < lower) or numpy.any(self > upper):
        raise ValueError(
            'At least one value of parameter `%s` of element `%s` is not '
            'valid.' % (self.name, devicename(self)))
    self[idxs] = _INT_NAN


def _tolerance(values):
    """Returns some sort of "numerical accuracy" to be expected for the
    given floating point value, see method :func:`trim`."""
    return abs(values*1e-15)


class ValueMath(object):
    """Base class for :class:`~hydpy.core.parametertools.Parameter` and
    :class:`~hydpy.core.sequencetools.Sequence`.  Implements special
    methods for arithmetic calculations, comparisons and type conversions.

    The subclasses are required to provide the members `NDIM` (usually a
    class attribute) and `value` (usually a property).  But for testing
    purposes, one can simply add them as instance attributes.

    A few examples for 0-dimensional objects:

    >>> from hydpy.core.objecttools import ValueMath
    >>> vm0 = ValueMath()
    >>> vm0.NDIM = 0
    >>> vm0.shape = ()
    >>> vm0.value = 2.
    >>> print(vm0 + vm0)
    4.0
    >>> print(3. - vm0)
    1.0
    >>> vm0 /= 2.
    >>> print(vm0.value)
    1.0
    >>> print(vm0 > vm0)
    False
    >>> print(vm0 != 1.5)
    True
    >>> vm0.length
    1

    Similar examples for 1-dimensional objects:

    >>> import numpy
    >>> vm1 = ValueMath()
    >>> vm1.NDIM = 1
    >>> vm1.shape = (5,)
    >>> vm1.value = numpy.array([1.,2.,3.])
    >>> print(vm1 + vm1)
    [ 2.  4.  6.]
    >>> print(3. - vm1)
    [ 2.  1.  0.]
    >>> vm1 /= 2.
    >>> print(vm1.value)
    [ 0.5  1.   1.5]
    >>> print(vm1 > vm1)
    [False False False]
    >>> print(vm1 != 1.5)
    [ True  True False]
    >>>
    >>> vm1.length
    5
    """
    # Subclasses need to define...
    NDIM = None    # ... e.g. as class attribute (int)
    name = None    # ... e.g. as property (str)
    value = None   # ... e.g. as property (float or ndarray of dtype float)
    shape = None   # ... e.gl as property (tuple of values of type int)
    # ...and optionally...
    INIT = None

    @staticmethod
    def _arithmetic_conversion(other):
        try:
            return other.value
        except AttributeError:
            return other

    def _arithmetic_exception(self, verb, other):
        augmentexcmessage('While trying to %s %s instance `%s` and %s `%s`'
                          % (verb, classname(self), self.name,
                             classname(other), other))

    @property
    def length(self):
        length = 1
        for idx in range(self.NDIM):
            length *= self.shape[idx]
        return length

    def __add__(self, other):
        try:
            return self.value + self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('add', other)

    def __radd__(self, other):
        return self.__add__(other)

    def __iadd__(self, other):
        self.value = self.__add__(other)
        return self

    def __sub__(self, other):
        try:
            return self.value - self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('subtract', other)

    def __rsub__(self, other):
        try:
            return self._arithmetic_conversion(other) - self.value
        except BaseException:
            self._arithmetic_exception('subtract', other)

    def __isub__(self, other):
        self.value = self.__sub__(other)
        return self

    def __mul__(self, other):
        try:
            return self.value * self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('multiply', other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __imul__(self, other):
        self.value = self.__mul__(other)
        return self

    def __truediv__(self, other):
        try:
            return self.value / self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('divide', other)

    def __rtruediv__(self, other):
        try:
            return self._arithmetic_conversion(other) / self.value
        except BaseException:
            self._arithmetic_exception('divide', other)

    def __itruediv__(self, other):
        self.value = self.__truediv__(other)
        return self

    def __floordiv__(self, other):
        try:
            return self.value // self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('floor divide', other)

    def __rfloordiv__(self, other):
        try:
            return self._arithmetic_conversion(other) // self.value
        except BaseException:
            self._arithmetic_exception('floor divide', other)

    def __ifloordiv__(self, other):
        self.value = self.__floordiv__(other)
        return self

    def __mod__(self, other):
        try:
            return self.value % self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('mod divide', other)

    def __rmod__(self, other):
        try:
            return self._arithmetic_conversion(other) % self.value
        except BaseException:
            self._arithmetic_exception('mod divide', other)

    def __imod__(self, other):
        self.value = self.__mod__(other)
        return self

    def __pow__(self, other):
        try:
            return self.value**self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('exponentiate', other)

    def __rpow__(self, other):
        try:
            return self._arithmetic_conversion(other)**self.value
        except BaseException:
            self._arithmetic_exception('exponentiate', other)

    def __ipow__(self, other):
        self.value = self.__pow__(other)
        return self

    def __neg__(self):
        return -self.value

    def __pos__(self):
        return +self.value

    def __abs__(self):
        return abs(self.value)

    def __invert__(self):
        return 1./self.value

    def __floor__(self):
        return self.value // 1.

    def __ceil__(self):
        return numpy.ceil(self.value)

    def __trunc__(self):
        return numpy.trunc(self.value)

    def __divmod__(self, other):
        return numpy.divmod(self.value, other)

    def __rdivmod__(self, other):
        return numpy.divmod(other, self.value)

    def __lt__(self, other):
        try:
            return self.value < self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (<)', other)

    def __le__(self, other):
        try:
            return self.value <= self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (<=)', other)

    def __eq__(self, other):
        try:
            return self.value == self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (==)', other)

    def __ne__(self, other):
        try:
            return self.value != self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (!=)', other)

    def __ge__(self, other):
        try:
            return self.value >= self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (>=)', other)

    def __gt__(self, other):
        try:
            return self.value > self._arithmetic_conversion(other)
        except BaseException:
            self._arithmetic_exception('compare (>)', other)

    def _typeconversion(self, type_):
        if not self.NDIM:
            if isinstance(type_, type):
                return type_(self.value)
            else:
                attr = getattr(self.value, type_)
                try:
                    return attr()
                except TypeError:
                    return attr
        else:
            raise TypeError('The %s instance `%s` is %d-dimensional and thus '
                            'cannot be converted to a scalar %s value.'
                            % (classname(self), self.name, self.NDIM,
                               classname(type_)))

    def __bool__(self):
        return self._typeconversion(bool)

    def __float__(self):
        return self._typeconversion(float)

    def __int__(self):
        return self._typeconversion(int)

    @property
    def real(self):
        return self._typeconversion('real')

    @property
    def imag(self):
        return self._typeconversion('imag')

    def conjugate(self):
        return self._typeconversion('conjugate')

    def __complex__(self):
        return numpy.complex(self.value)

    def __round__(self, ndigits=0):
        return numpy.round(self.value, ndigits)

    def commentrepr(self):
        """Returns a list with comments, e.g. for making string representations
        more informative.  When :attr:`pub.options.reprcomments` is set to
        `False`, an empty list is returned.
        """
        from hydpy import pub
        if pub.options.reprcomments:
            return ['# %s' % line for line in
                    textwrap.wrap(autodoctools.description(self), 78)]
        else:
            return []

    def _repr(self, values, islong):
        prefix = '%s(' % self.name
        if self.NDIM == 0:
            string = '%s(%s)' % (self.name, repr_(values))
        elif self.NDIM == 1:
            if islong:
                string = assignrepr_list(values, prefix, 75) + ')'
            else:
                string = assignrepr_values(values, prefix, 75) + ')'
        elif self.NDIM == 2:
            if islong:
                string = assignrepr_list2(values, prefix, 75) + ')'
            else:
                string = assignrepr_values2(values, prefix) + ')'
        else:
            raise NotImplementedError(
                '`repr` does not yet support parameters or sequences like `%s`'
                'of element `%s` which handle %d-dimensional matrices.'
                % self.NDIM)
        return '\n'.join(self.commentrepr() + [string])


class FastAccess(object):
    """Used as a surrogate for typed Cython classes when working in
    pure Python mode."""


class HydPyDeprecationWarning(DeprecationWarning):
    pass


autodoctools.autodoc_module()
