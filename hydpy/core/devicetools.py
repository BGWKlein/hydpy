# -*- coding: utf-8 -*-
"""This modules implements tools for handling "eodes" and "elements", which
are the most fundamental means to structure HydPy projects.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import copy
import struct
import weakref
# ...from site-packages
from matplotlib import pyplot
# ...from HydPy
from hydpy import pub
from hydpy.core import connectiontools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import autodoctools
from hydpy.cythons import pointerutils


class Device(object):

    _registry = {}
    _selection = {}

    def _get_name(self):
        """Name of the actual device (node or element)."""
        return self._name

    def _set_name(self, name):
        self._checkname(name)
        _handlers = self._handlers.copy()
        for handler in _handlers:
            handler.remove_device(self)
        try:
            del self._registry[self._name]
        except KeyError:
            pass
        else:
            self._registry[name] = self
        self._name = name
        for handler in _handlers:
            handler.add_device(self)

    name = property(_get_name, _set_name)

    def _checkname(self, name):
        """Raises an :class:`~exceptions.ValueError` if the given name is not
        a valid Python identifier.
        """
        exc = ValueError('For initializing `%s` objects, `value` is a '
                         'necessary function argument.  Principally, any '
                         'object is allowed that supports the Python build-in '
                         'function `str`.  But note that `str(value)` must '
                         'return a valid Python identifier (that does '
                         'not start with a number, that does not contain `-`, '
                         'that is not a Python keyword like `for`...).  The '
                         'given object returned the string `%s`, which is not '
                         'a valid Python identifier.'
                         % (objecttools.classname(self), name))
        try:
            exec('%s = None' % name)
        except SyntaxError:
            raise exc
        if name in dir(__builtins__):
            raise exc

    @classmethod
    def clearregistry(cls):
        cls._selection.clear()
        cls._registry.clear()

    @classmethod
    def registerednames(cls):
        """Get all names of :class:`Device` objects initialized so far."""
        return cls._registry.keys()

    def add_handler(self, handler):
        self._handlers.add(handler)

    def remove_handler(self, handler):
        self._handlers.remove(handler)

    def __iter__(self):
        for (key, value) in vars(self).items():
            if isinstance(value, connectiontools.Connections):
                yield (key, value)

    def __lt__(self, other):
        return self.name < other.name

    def __le__(self, other):
        return self.name <= other.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __ge__(self, other):
        return self.name >= other.name

    def __gt__(self, other):
        return self.name > other.name

    def __hash__(self):
        return id(self)

    def __str__(self):
        return self.name

    def __dir__(self):
        return objecttools.dir_(self)


class Node(Device):
    """
    readobs = False
    readext = False
    passsim = True
    passobs = False
    passext = False
    """
    _registry = {}
    _selection = {}
    _predefinedvariable = 'Q'
    ROUTING_MODES = ('newsim', 'obs', 'oldsim')

    def __new__(cls, value, variable=None):
        """Returns an already existing :class:`Node` instance or, if such
        an instance does not exist yet, a new newly created one.
        """
        name = str(value)
        if name not in cls._registry:
            self = object.__new__(Node)
            self._checkname(name)
            self._name = name
            if variable is None:
                self._variable = self._predefinedvariable
            else:
                self._variable = variable
            self.entries = connectiontools.Connections(self)
            self.exits = connectiontools.Connections(self)
            self.sequences = sequencetools.NodeSequences(self)
            self.routingmode = 'newsim'
            self._blackhole = None
            self._handlers = weakref.WeakSet()
            cls._registry[name] = self
        cls._selection[name] = cls._registry[name]
        return cls._registry[name]

    def __init__(self, name, variable=None, route=None):
        if (variable is not None) and (variable != self.variable):
            raise ValueError('The variable to be represented by a `Node '
                             'instance cannot be changed.  The variable of '
                             'node `%s` is `%s` instead of `%s` or `None`.  '
                             'Keep in mind, that `name` is the unique '
                             'identifier of node objects.'
                             % (self.name, self.variable, variable))

    def _getvariable(self):
        """The variable handled by the respective node instance."""
        return self._variable
    variable = property(_getvariable)

    @classmethod
    def predefinevariable(cls, name):
        cls._predefinedvariable = str(name)

    @classmethod
    def registerednodes(cls):
        """Get all :class:`Node` objects initialized so far."""
        return Nodes(cls._registry.values())

    @classmethod
    def gathernewnodes(cls):
        """Gather all `new` :class:`Node` objects. :class:`Node` objects
        are deemed to be new if their constructor has been called since the
        last usage of this method.
        """
        nodes = Nodes(cls._selection.values())
        cls._selection.clear()
        return nodes

    def _getroutingmode(self):
        return self._routingmode

    def _setroutingmode(self, value):
        if value in self.ROUTING_MODES:
            self._routingmode = value
            if value == 'newsim':
                self.sequences.sim.use_ext = False
            elif value == 'obs':
                self.sequences.sim.use_ext = False
                self.sequences.obs.use_ext = True
            elif value == 'oldsim':
                self.sequences.sim.use_ext = True
                self._blackhole = pointerutils.Double(0.)
        else:
            raise ValueError('When trying to set the routing mode of node %s, '
                             'the value `%s` was given, but only the '
                             'following values are allowed: %s.'
                             % (self.name, value,
                                 ', '.join(self.ROUTING_MODES)))

    routingmode = property(_getroutingmode, _setroutingmode)

    def getdouble_via_exits(self):
        if self.routingmode != 'obs':
            return self.sequences.fastaccess.sim
        else:
            return self.sequences.fastaccess.obs

    def getdouble_via_entries(self):
        if self.routingmode != 'oldsim':
            return self.sequences.fastaccess.sim
        else:
            return self._blackhole

    def reset(self, idx=None):
        self.sequences.fastaccess.sim[0] = 0.

    def _loaddata_sim(self, idx):
        fastaccess = self.sequences.fastaccess
        if fastaccess._sim_ramflag:
            fastaccess.sim[0] = fastaccess._sim_array[idx]
        elif fastaccess._sim_diskflag:
            raw = fastaccess._sim_file.read(8)
            fastaccess.sim[0] = struct.unpack('d', raw)

    def _savedata_sim(self, idx):
        fastaccess = self.sequences.fastaccess
        if fastaccess._sim_ramflag:
            fastaccess._sim_array[idx] = fastaccess.sim[0]
        elif fastaccess._sim_diskflag:
            raw = struct.pack('d', fastaccess.sim[0])
            fastaccess._sim_file.write(raw)

    def _loaddata_obs(self, idx):
        fastaccess = self.sequences.fastaccess
        if fastaccess._obs_ramflag:
            fastaccess.obs[0] = fastaccess._obs_array[idx]
        elif fastaccess._obs_diskflag:
            raw = fastaccess._obs_file.read(8)
            fastaccess.obs[0] = struct.unpack('d', raw)

    def prepare_allseries(self, ramflag=True):
        self.prepare_simseries(ramflag)
        self.prepare_obsseries(ramflag)

    def prepare_simseries(self, ramflag=True):
        self._prepare_nodeseries('sim', ramflag)

    def prepare_obsseries(self, ramflag=True):
        self._prepare_nodeseries('obs', ramflag)

    def _prepare_nodeseries(self, seqname, ramflag):
        seq = getattr(self.sequences, seqname)
        if ramflag:
            seq.activate_ram()
        else:
            seq.activate_disk()

    def comparisonplot(self, **kwargs):
        for (name, seq) in self.sequences:
            if pyplot.isinteractive():
                name = ' '.join((self.name, name))
            pyplot.plot(seq.series, label=name, **kwargs)
        pyplot.legend()
        variable = self.variable
        if variable == 'Q':
            variable = u'Q [m³/s]'
        pyplot.ylabel(variable)
        if not pyplot.isinteractive():
            pyplot.show()

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        lines = ['%sNode("%s", variable="%s",'
                 % (prefix, self.name, self.variable)]
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)


class Element(Device):

    _registry = {}
    _selection = {}

    def __new__(cls, value, inlets=None, outlets=None,
                receivers=None, senders=None):
        """Returns an already existing :class:`Element` instance or, if such
        an instance does not exist yet, a new newly created one.
        """
        name = str(value)
        if name not in cls._registry:
            self = object.__new__(Element)
            self._checkname(name)
            self._name = name
            self.inlets = connectiontools.Connections(self)
            self.outlets = connectiontools.Connections(self)
            self.receivers = connectiontools.Connections(self)
            self.senders = connectiontools. Connections(self)
            self.model = None
            self._handlers = weakref.WeakSet()
            cls._registry[name] = self
        cls._selection[name] = cls._registry[name]
        return cls._registry[name]

    def __init__(self, name, inlets=None, outlets=None,
                 receivers=None, senders=None):
        """Adds the given :class:`~connectiontools.Connections` instances to
        the (old or new) :class:`Element` instance."""
        if inlets is not None:
            for inlet in Nodes(inlets):
                if inlet in self.outlets:
                    raise ValueError('For element `%s`, the given inlet node '
                                     '`%s` is already defined as an outlet '
                                     'node, which is not allowed.'
                                     % (self, inlet))
                self.inlets += inlet
                inlet.exits += self
        if outlets is not None:
            for outlet in Nodes(outlets):
                if outlet in self.inlets:
                    raise ValueError('For element `%s`, the given outlet node '
                                     '`%s` is already defined as an inlet '
                                     'node, which is not allowed.'
                                     % (self, outlet))
                self.outlets += outlet
                outlet.entries += self
        if receivers is not None:
            for receiver in Nodes(receivers):
                if receiver in self.senders:
                    raise ValueError('For element `%s`, the given receiver '
                                     'node `%s` is already defined as an '
                                     'sender node, which is not allowed.'
                                     % (self, receiver))
                self.receivers += receiver
                receiver.exits += self
        if senders is not None:
            for sender in Nodes(senders):
                if sender in self.receivers:
                    raise ValueError('For element `%s`, the given sender node '
                                     '`%s` is already defined as an receiver, '
                                     'node which is not allowed.'
                                     % (self, sender))
                self.senders += sender
                sender.entries += self

    @classmethod
    def registeredelements(cls):
        """Get all :class:`Element` objects initialized so far."""
        return Elements(cls._registry.values())

    @classmethod
    def gathernewelements(cls):
        """Gather all `new` :class:`Element` objects. :class:`Element` objects
        are deemed to be new if their constructor has been called since the
        last usage of this method.
        """
        elements = Elements(cls._selection.values())
        cls._selection.clear()
        return elements

    def _getvariables(self):
        variables = set()
        for (name, connections) in self:
            variables.update(connections.variables)
        return variables
    variables = property(_getvariables)

    def initmodel(self):
        dict_ = pub.controlmanager.loadfile(element=self)
        self.connect(dict_['model'])

    def connect(self, model=None):
        if model is not None:
            self.model = model
            model.element = self
        try:
            self.model.connect()
        except BaseException:
            objecttools.augmentexcmessage(
                'While trying to build the connections of the model handled '
                'by element `%s`' % self.name)

    def prepare_allseries(self, ramflag=True):
        self.prepare_inputseries(ramflag)
        self.prepare_fluxseries(ramflag)
        self.prepare_stateseries(ramflag)

    def prepare_inputseries(self, ramflag=True):
        self._prepare_series('inputs', ramflag)

    def prepare_fluxseries(self, ramflag=True):
        self._prepare_series('fluxes', ramflag)

    def prepare_stateseries(self, ramflag=True):
        self._prepare_series('states', ramflag)

    def _prepare_series(self, name_subseqs, ramflag):
        sequences = self.model.sequences
        subseqs = getattr(sequences, name_subseqs, None)
        if subseqs:
            if ramflag:
                subseqs.activate_ram()
            else:
                subseqs.activate_disk()

    def _plot(self, subseqs, selnames, kwargs):
        for name in selnames:
            seq = getattr(subseqs, name)
            if seq.NDIM == 0:
                label = kwargs.pop('label', ' '.join((self.name, name)))
                pyplot.plot(seq.series, label=label, **kwargs)
                pyplot.legend()
            else:
                color = kwargs.pop('color', kwargs.pop('c', 'red'))
                pyplot.plot(seq.series, color=color, **kwargs)
        if not pyplot.isinteractive():
            pyplot.show()

    def inputplot(self, *args, **kwargs):
        self._plot(self.model.sequences.inputs, args, kwargs)

    def fluxplot(self, *args, **kwargs):
        self._plot(self.model.sequences.fluxes, args, kwargs)

    def stateplot(self, *args, **kwargs):
        self._plot(self.model.sequences.states, args, kwargs)

    def assignrepr(self, prefix):
        """Return a :func:`repr` string with an prefixed assignement.

        Argument:
            * prefix(:class:`str`): Usually something like 'x = '.
        """
        with objecttools.repr_.preserve_strings(True):
            with objecttools.assignrepr_tuple.always_bracketed(False):
                blanks = ' ' * (len(prefix) + 8)
                lines = ['%sElement("%s",' % (prefix, self.name)]
                for conname in ('inlets', 'outlets', 'receivers', 'senders'):
                    connections = getattr(self, conname, None)
                    if connections:
                        subprefix = '%s%s=' % (blanks, conname)
                        nodes = [str(node) for node in connections.slaves]
                        line = objecttools.assignrepr_list(
                                                nodes, subprefix, width=70)
                        lines.append(line + ',')
                lines[-1] = lines[-1][:-1]+')'
                return '\n'.join(lines)

    def __repr__(self):
        return self.assignrepr('')


class Devices(object):

    __slots__ = ('_devices')

    _contentclass = None

    def __init__(self, *values):
        self._devices = {}
        try:
            self._extract_values(values)
        except BaseException:
            objecttools.augmentexcmessage(
                'While trying to initialize a `%s` object'
                % objecttools.classname(self))

    def _extract_values(self, values):
        for value in objecttools.extract(
                        values, types=(self._contentclass, str), skip=True):
            self.add_device(value)

    def add_device(self, device):
        device = self._contentclass(device)
        self._devices[device.name] = device
        device.add_handler(self)

    def remove_device(self, device):
        device = self._contentclass(device)
        try:
            del self._devices[device.name]
        except KeyError:
            raise KeyError(
                'The selected %s object does not handle a %s object named '
                '`%s`, which could be removed.'
                % (objecttools.classname(self),
                   objecttools.classname(self._contentclass), device))
        device.remove_handler(self)

    @property
    def names(self):
        return tuple(device.name for device in self)

    @property
    def devices(self):
        return tuple(device for device in self)

    def copy(self):
        """Return a copy of the actual :class:`Devices` instance."""
        new = copy.copy(self)
        new._devices = copy.copy(self._devices)
        for device in self:
            device.add_handler(new)
        return new

    def __iter__(self):
        for (name, device) in sorted(self._devices.items()):
            yield device

    def __getitem__(self, name):
        try:
            return self._devices[name]
        except KeyError:
            raise KeyError(
                'The selected %s object does not handle a %s object named '
                '`%s`, which could be returned.'
                % (objecttools.classname(self),
                   objecttools.classname(self._contentclass), name))

    def __getattr__(self, name):
        try:
            _devices = super(Devices, self).__getattribute__('_devices')
            return _devices[name]
        except KeyError:
            raise AttributeError(
                'The selected %s object has neither a `%s` attribute nor does '
                'it handle a %s object named `%s`, which could be returned.'
                % (objecttools.classname(self), name,
                   objecttools.classname(self._contentclass), name))

    def __delattr__(self, name):
        deleted_something = False
        if name in vars(self):
            super(Devices, self).__delattr__(name)
            deleted_something = True
        if name in self._devices:
            self.remove_device(name)
            deleted_something = True
        if not deleted_something:
            raise AttributeError(
                'The selected %s object has neither a `%s` attribute nor does '
                'it handle a %s object named `%s`, which could be deleted.'
                % (objecttools.classname(self), name,
                   objecttools.classname(self._contentclass), name))

    def __contains__(self, device):
        device = self._contentclass(device)
        return device.name in self._devices

    def __len__(self):
        return len(self._devices)

    def __add__(self, values):
        new = self.copy()
        for device in self.__class__(values):
            new.add_device(device)
        return new

    def __iadd__(self, values):
        for device in self.__class__(values):
            self.add_device(device)
        return self

    def __sub__(self, values):
        new = self.copy()
        for device in self.__class__(values):
            try:
                new.remove_device(device)
            except KeyError:
                pass
        return new

    def __isub__(self, values):
        for device in self.__class__(values):
            try:
                self.remove_device(device)
            except KeyError:
                pass
        return self

    def __lt__(self, other):
        return set(self._devices.keys()) < set(other._devices.keys())

    def __le__(self, other):
        return set(self._devices.keys()) <= set(other._devices.keys())

    def __eq__(self, other):
        return set(self._devices.keys()) == set(other._devices.keys())

    def __ne__(self, other):
        return set(self._devices.keys()) != set(other._devices.keys())

    def __ge__(self, other):
        return set(self._devices.keys()) >= set(other._devices.keys())

    def __gt__(self, other):
        return set(self._devices.keys()) > set(other._devices.keys())

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        with objecttools.repr_.preserve_strings(True):
            with pub.options.ellipsis(2, optional=True):
                prefix += '%s(' % objecttools.classname(self)
                repr_ = objecttools.assignrepr_values(
                                        self.names, prefix, width=70)
                return repr_ + ')'

    def __dir__(self):
        return objecttools.dir_(self) + list(self.names)


class Nodes(Devices):

    _contentclass = Node

    def prepare_allseries(self, ramflag=True):
        self.prepare_simseries(ramflag)
        self.prepare_obsseries(ramflag)

    def prepare_simseries(self, ramflag=True):
        for node in self:
            node.prepare_simseries(ramflag)

    def prepare_obsseries(self, ramflag=True):
        for node in self:
            node.prepare_obsseries(ramflag)


class Elements(Devices):

    _contentclass = Element

    def prepare_allseries(self, ramflag=True):
        for element in self:
            element.prepare_allseries(ramflag)

    def prepare_inputseries(self, ramflag=True):
        for element in self:
            element.prepare_inputseries(ramflag)

    def prepare_fluxseries(self, ramflag=True):
        for element in self:
            element.prepare_fluxseries(ramflag)

    def prepare_stateseries(self, ramflag=True):
        for element in self:
            element.prepare_stateseries(ramflag)


autodoctools.autodoc_module()
