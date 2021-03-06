# -*- coding: utf-8 -*-
"""This module provides features for applying and implementing
hydrological models.

.. _`thorough description`: http://www.hydrology.ruhr-uni-bochum.de/\
hydrolgy/mam/download/schriftenreihe_29.pdf

.. _`Clark and Kavetski`: \
https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2009WR008894
"""
# import...
# ...from standard library
import abc
import importlib
import inspect
import itertools
import os
import types
from typing import *
# ...from site-packages
from typing import Dict, Set

import numpy
# ...from HydPy
from hydpy import conf
from hydpy.core import objecttools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import typingtools
from hydpy.cythons import modelutils
if TYPE_CHECKING:
    from hydpy.core import devicetools
    from hydpy.core import masktools


class Method:
    """Base class for defining (hydrological) calculation methods."""
    CONTROLPARAMETERS: Tuple[Type[typingtools.VariableProtocol], ...] = ()
    DERIVEDPARAMETERS: Tuple[Type[typingtools.VariableProtocol], ...] = ()
    REQUIREDSEQUENCES: Tuple[Type[typingtools.VariableProtocol], ...] = ()
    UPDATEDSEQUENCES: Tuple[Type[typingtools.VariableProtocol], ...] = ()
    RESULTSEQUENCES: Tuple[Type[typingtools.VariableProtocol], ...] = ()

    @staticmethod
    @abc.abstractmethod
    def __call__(model: 'Model') -> None:
        """The actual calculaton function."""

    __name__ = property(objecttools.get_name)


class Model:
    """Base class for all hydrological models.

    Class |Model| provides everything to create a usable application
    model, except method |Model.simulate|.  See class |AdHocModel| and
    |ELSModel|, which implement this method.
    """

    element: Optional['devicetools.Element']
    cymodel: Optional[typingtools.CyModelProtocol]
    _name: ClassVar[Optional[str]] = None

    INLET_METHODS: ClassVar[Tuple[Callable, ...]]
    OUTLET_METHODS: ClassVar[Tuple[Callable, ...]]
    RECEIVER_METHODS: ClassVar[Tuple[Callable, ...]]
    SENDER_METHODS: ClassVar[Tuple[Callable, ...]]
    METHOD_GROUPS: ClassVar[Tuple[str, ...]]

    SOLVERPARAMETERS: Tuple[Type[typingtools.VariableProtocol], ...] = ()

    def __init__(self) -> None:
        self.cymodel = None
        self.element = None
        self._init_methods()

    def _init_methods(self) -> None:
        """Convert all pure Python calculation functions of the model class to
        methods and assign them to the model instance.
        """
        for name_group in self.METHOD_GROUPS:
            functions = getattr(self, name_group, ())
            shortname2method: Dict[str, types.MethodType] = {}
            shortnames: Set[str] = set()
            for func in functions:
                method = types.MethodType(func.__call__, self)
                name_func = func.__name__.lower()
                setattr(self, name_func, method)
                shortname = '_'.join(name_func.split('_')[:-1])
                if shortname not in shortnames:
                    shortname2method[shortname] = method
                    shortnames.add(shortname)
                else:
                    shortname2method.pop(shortname, None)
            for (shortname, method) in shortname2method.items():
                if method is not None:
                    setattr(self, shortname, method)

    def connect(self) -> None:
        """Connect all |LinkSequence| objects of the actual model to
        the corresponding |NodeSequence| objects.

        You cannot connect the link sequences until the |Model| object
        itself is connected to an |Element| object referencing the
        required |Node| objects:

        >>> from hydpy import prepare_model
        >>> prepare_model('hstream_v1').connect()
        Traceback (most recent call last):
        ...
        AttributeError: While trying to build the node connection of the \
`inlet` sequences of the model handled by element `?`, the following \
error occurred: 'NoneType' object has no attribute 'inlets'

        The application model |hstream_v1| can receive inflow from an
        arbitrary number of upstream nodes and passes its outflow to
        a single downstream node (note that property |Element.model| of
        class |Element| calls method |Model.connect| automatically):

        >>> from hydpy import Element, Node
        >>> in1 = Node('in1', variable='Q')
        >>> in2 = Node('in2', variable='Q')
        >>> out1 = Node('out1', variable='Q')

        >>> element1 = Element(
        ...     'element1', inlets=(in1, in2), outlets=out1)
        >>> element1.model = prepare_model('hstream_v1')

        Now all connections work as expected:

        >>> in1.sequences.sim = 1.0
        >>> in2.sequences.sim = 2.0
        >>> out1.sequences.sim = 3.0
        >>> element1.model.sequences.inlets.q
        q(1.0, 2.0)
        >>> element1.model.sequences.outlets.q
        q(3.0)
        >>> element1.model.sequences.inlets.q *= 2.0
        >>> element1.model.sequences.outlets.q *= 2.0
        >>> in1.sequences.sim
        sim(2.0)
        >>> in2.sequences.sim
        sim(4.0)
        >>> out1.sequences.sim
        sim(6.0)

        To show some possible errors and related error messages, we
        define three additional nodes of, two handling variables
        different from discharge (`Q`):

        >>> in3 = Node('in3', variable='X')
        >>> out2 = Node('out2', variable='Q')
        >>> out3 = Node('out3', variable='X')

        Link sequence names must match the `variable` a node is handling:

        >>> element2 = Element(
        ...     'element2', inlets=(in1, in2), outlets=out3)
        >>> element2.model = prepare_model('hstream_v1')
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the \
`outlet` sequences of the model handled by element `element2`, the \
following error occurred: Sequence `q` of element `element2` cannot be \
connected due to no available node handling variable `Q`.

        One can connect a 0-dimensional link sequence to a single node
        sequence only:

        >>> element3 = Element(
        ...     'element3', inlets=(in1, in2), outlets=(out1, out2))
        >>> element3.model = prepare_model('hstream_v1')
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the \
`outlet` sequences of the model handled by element `element3`, the following \
error occurred: Sequence `q` cannot be connected as it is 0-dimensional \
but multiple nodes are available which are handling variable `Q`.

        Method |Model.connect| generally reports about unusable node
        sequences:

        >>> element4 = Element(
        ...     'element4', inlets=(in1, in2), outlets=(out1, out3))
        >>> element4.model = prepare_model('hstream_v1')
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the \
`outlet` sequences of the model handled by element `element4`, the \
following error occurred: The following nodes have not been connected \
to any sequences: out3.

        >>> element5 = Element(
        ...     'element5', inlets=(in1, in2, in3), outlets=out1)
        >>> element5.model = prepare_model('hstream_v1')
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the \
`inlet` sequences of the model handled by element `element5`, the \
following error occurred: The following nodes have not been connected \
to any sequences: in3.

        >>> element6 = Element(
        ...     'element6', inlets=in1, outlets=out1, receivers=in2)
        >>> element6.model = prepare_model('hstream_v1')
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the \
`receiver` sequences of the model handled by element `element6`, the \
following error occurred: The following nodes have not been connected \
to any sequences: in2.

        >>> element7 = Element(
        ...     'element7', inlets=in1, outlets=out1, senders=in2)
        >>> element7.model = prepare_model('hstream_v1')
        Traceback (most recent call last):
        ...
        RuntimeError: While trying to build the node connection of the \
`sender` sequences of the model handled by element `element7`, the \
following error occurred: The following nodes have not been connected \
to any sequences: in2.
        """
        try:
            for group in ('inlets', 'receivers', 'outlets', 'senders'):
                self._connect_subgroup(group)
        except BaseException:
            objecttools.augment_excmessage(
                f'While trying to build the node connection of '
                f'the `{group[:-1]}` sequences of the model handled '
                f'by element `{objecttools.devicename(self)}`')

    def _connect_subgroup(self, group: str) -> None:
        available_nodes = getattr(self.element, group)
        links = getattr(self.sequences, group, ())
        applied_nodes = []
        for seq in links:
            selected_nodes = tuple(node for node in available_nodes
                                   if node.variable.lower() == seq.name)
            if seq.NDIM == 0:
                if not selected_nodes:
                    raise RuntimeError(
                        f'Sequence {objecttools.elementphrase(seq)} '
                        f'cannot be connected due to no available node '
                        f'handling variable `{seq.name.upper()}`.')
                if len(selected_nodes) > 1:
                    raise RuntimeError(
                        f'Sequence `{seq.name}` cannot be connected as '
                        f'it is 0-dimensional but multiple nodes are '
                        f'available which are handling variable '
                        f'`{seq.name.upper()}`.')
                applied_nodes.append(selected_nodes[0])
                seq.set_pointer(selected_nodes[0].get_double(group))
            elif seq.NDIM == 1:
                seq.shape = len(selected_nodes)
                for idx, node in enumerate(selected_nodes):
                    applied_nodes.append(node)
                    seq.set_pointer(node.get_double(group), idx)
        if len(applied_nodes) < len(available_nodes):
            remaining_nodes = [node.name for node in available_nodes
                               if node not in applied_nodes]
            raise RuntimeError(
                f'The following nodes have not been connected to any '
                f'sequences: {objecttools.enumeration(remaining_nodes)}.')

    @property
    def name(self) -> str:
        """Name of the model type.

        For base models, |Model.name| corresponds to the package name:

        >>> from hydpy import prepare_model
        >>> hland = prepare_model('hland')
        >>> hland.name
        'hland'

        For application models, |Model.name| corresponds the module name:

        >>> hland_v1 = prepare_model('hland_v1')
        >>> hland_v1.name
        'hland_v1'

        This last example has only technical reasons:

        >>> hland.name
        'hland'
        """
        name = self._name
        if name is None:
            substrings = self.__module__.split('.')
            name = substrings[1] if len(substrings) == 2 else substrings[2]
            type(self)._name = name
        return name

    @property
    def parameters(self) -> parametertools.Parameters:
        """All parameters of the actual model.

        >>> from hydpy import prepare_model
        >>> model = prepare_model('hland_v1')
        >>> hasattr(model, 'parameters')
        True

        When using the standard model import mechanism (see functions
        |parameterstep| and |prepare_model|) and not demolishing a
        correctly prepared model, you should never encounter a
        situation where the following error occurs:

        >>> del vars(model)['parameters']
        >>> model.parameters
        Traceback (most recent call last):
        ...
        AttributeError: Model `hland_v1` of element `?` does not handle \
any parameters so far.
        """
        parameters = vars(self).get('parameters')
        if parameters is None:
            raise AttributeError(
                f'Model {objecttools.elementphrase(self)} '
                f'does not handle any parameters so far.')
        return parameters

    @parameters.setter
    def parameters(self, parameters: parametertools.Parameters) -> None:
        vars(self)['parameters'] = parameters

    @property
    def sequences(self) -> 'sequencetools.Sequences':
        """All sequences of the actual model.

        >>> from hydpy import prepare_model
        >>> model = prepare_model('hland_v1')
        >>> hasattr(model, 'sequences')
        True

        When using the standard model import mechanism (see functions
        |parameterstep| and |prepare_model|) and not demolishing a
        correctly prepared model, you should never encounter a
        situation where the following error occurs:

        >>> del vars(model)['sequences']
        >>> model.sequences
        Traceback (most recent call last):
        ...
        AttributeError: Model `hland_v1` of element `?` does not handle \
any sequences so far.
        """
        sequences = vars(self).get('sequences')
        if sequences is None:
            raise AttributeError(
                f'Model {objecttools.elementphrase(self)} '
                f'does not handle any sequences so far.')
        return sequences

    @sequences.setter
    def sequences(self, sequences: 'sequencetools.Sequences') -> None:
        vars(self)['sequences'] = sequences

    @property
    def idx_sim(self) -> int:
        """The index of the current simulation time step.

        Some methods require to know the index of the current simulation
        step (with respect to the initialisation period),  which one
        usually updates by passing it to method  |Model.simulate|.
        However, you are allowed to change it manually, which is often
        beneficial when testing some methods:

        >>> from hydpy import prepare_model
        >>> model = prepare_model('hland_v1')
        >>> model.idx_sim
        0
        >>> model.idx_sim = 1
        >>> model.idx_sim
        1
        """
        if self.cymodel:
            return self.cymodel.idx_sim
        return vars(self).get('idx_sim', 0)

    @idx_sim.setter
    def idx_sim(self, value: int) -> None:
        if self.cymodel:
            self.cymodel.idx_sim = value
        else:
            vars(self)['idx_sim'] = int(value)

    @abc.abstractmethod
    def simulate(self, idx: int) -> None:
        """Perform a simulation run over a single simulation time step."""

    def load_data(self) -> None:
        """Call method |Sequences.load_data| of attribute `sequences`.

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        if self.sequences:
            self.sequences.load_data(self.idx_sim)

    def save_data(self, idx: int) -> None:
        """Call method |Sequences.save_data| of attribute `sequences`.

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        if self.sequences:
            self.sequences.save_data(idx)

    def update_inlets(self) -> None:
        """Call all methods defined as "INLET_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(2)
        >>> class Test(AdHocModel):
        ...     INLET_METHODS = print_1, print_2
        >>> Test().update_inlets()
        1
        2

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        for method in self.INLET_METHODS:
            method.__call__(self)

    def update_outlets(self) -> None:
        """Call all methods defined as "OUTLET_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(2)
        >>> class Test(AdHocModel):
        ...     OUTLET_METHODS = print_1, print_2
        >>> Test().update_outlets()
        1
        2

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        for method in self.OUTLET_METHODS:
            method.__call__(self)

    def update_receivers(self, idx: int) -> None:
        """Call all methods defined as "RECEIVER_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...        print(test.idx_sim+1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(test.idx_sim+2)
        >>> class Test(AdHocModel):
        ...     RECEIVER_METHODS = print_1, print_2
        >>> test = Test()
        >>> test.update_receivers(1)
        2
        3

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        for method in self.RECEIVER_METHODS:
            method.__call__(self)

    def update_senders(self, idx: int) -> None:
        """Call all methods defined as "SENDER_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...        print(test.idx_sim+1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(test.idx_sim+2)
        >>> class Test(AdHocModel):
        ...     SENDER_METHODS = print_1, print_2
        >>> test = Test()
        >>> test.update_senders(1)
        2
        3

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        for method in self.SENDER_METHODS:
            method.__call__(self)

    def new2old(self) -> None:
        """Call method |StateSequences.new2old| of subattribute
        `sequences.states`.

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        if self.sequences:
            self.sequences.states.new2old()

    @property
    def masks(self) -> 'masktools.Masks':
        """All predefined masks of the actual model type contained in a
        |Masks| objects.

        To give an example, we show the masks implemented by the
        |hland_v1| application model:

        >>> from hydpy.models.hland_v1 import *
        >>> parameterstep('1d')
        >>> model.masks
        complete of module hydpy.models.hland.hland_masks
        land of module hydpy.models.hland.hland_masks
        noglacier of module hydpy.models.hland.hland_masks
        soil of module hydpy.models.hland.hland_masks
        field of module hydpy.models.hland.hland_masks
        forest of module hydpy.models.hland.hland_masks
        ilake of module hydpy.models.hland.hland_masks
        glacier of module hydpy.models.hland.hland_masks

        You can use them, for example, to average the zone-specific
        precipitation values handled by sequence |hland_fluxes.PC|.
        When passing no argument, method |Variable.average_values|
        applies the `complete` mask.  Pass mask `land` to average the
        values of all zones except those of type |hland_constants.ILAKE|:

        >>> nmbzones(4)
        >>> zonetype(FIELD, FOREST, GLACIER, ILAKE)
        >>> zonearea(1.0)
        >>> fluxes.pc = 1.0, 3.0, 5.0, 7.0
        >>> fluxes.pc.average_values()
        4.0
        >>> fluxes.pc.average_values(model.masks.land)
        3.0

        To try to query the masks of a model not implementing any masks
        results in the following error:

        >>> from hydpy import prepare_model
        >>> prepare_model('test_v1').masks
        Traceback (most recent call last):
        ...
        AttributeError: Model `test_v1` does not handle a group of masks.
        """
        masks = vars(self).get('masks')
        if masks is None:
            raise AttributeError(
                f'Model `{self.name}` does not handle a group of masks.')
        return masks

    @masks.setter
    def masks(self, masks: 'masktools.Masks') -> None:
        vars(self)['masks'] = masks

    @classmethod
    def get_methods(cls) -> Iterator[Method]:
        """Convenience method for iterating through all methods selected by
        a |Model| subclass.

        >>> from hydpy.models import hland_v1
        >>> for method in hland_v1.Model.get_methods():
        ...     print(method.__name__)   # doctest: +ELLIPSIS
        Calc_TC_V1
        Calc_TMean_V1
        ...
        Calc_QT_V1
        Pass_Q_v1

        Note that function |Model.get_methods| returns the "raw" |Method|
        objects instead of the modified Python or Cython functions used
        for performing calculations.
        """
        for name_group in getattr(cls, 'METHOD_GROUPS', ()):
            for method in getattr(cls, name_group, ()):
                yield method

    def __str__(self) -> str:
        return self.name

    def __init_subclass__(cls):
        modulename = cls.__module__
        if modulename.count('.') > 2:
            modulename = modulename.rpartition('.')[0]
        module = importlib.import_module(modulename)
        modelname = modulename.split('.')[-1]

        allsequences = set()
        st = sequencetools
        infos = (
            (st.InletSequences, st.InletSequence, set()),
            (st.ReceiverSequences, st.ReceiverSequence, set()),
            (st.InputSequences, st.InputSequence, set()),
            (st.FluxSequences, st.FluxSequence, set()),
            (st.StateSequences, st.StateSequence, set()),
            (st.LogSequences, st.LogSequence, set()),
            (st.AideSequences, st.AideSequence, set()),
            (st.OutletSequences, st.OutletSequence, set()),
            (st.SenderSequences, st.SenderSequence, set()),
        )
        for method in cls.get_methods():
            for sequence in itertools.chain(
                    method.REQUIREDSEQUENCES,
                    method.UPDATEDSEQUENCES,
                    method.RESULTSEQUENCES):
                for _, typesequence, sequences in infos:
                    if issubclass(sequence, typesequence):
                        sequences.add(sequence)
        for typesequences, _, sequences in infos:
            allsequences.update(sequences)
            classname = objecttools.classname(typesequences)
            if not hasattr(module, classname):
                members = {
                    'CLASSES': cls._sort_variables(sequences),
                    '__doc__': f'{classname[:-9]} sequences '
                               f'of model {modelname}.',
                    '__module__': modulename,
                }
                typesequence = type(classname, (typesequences,), members)
                setattr(module, classname, typesequence)

        controlparameters = set()
        derivedparameters = set()
        for host in itertools.chain(cls.get_methods(), allsequences):
            controlparameters.update(
                getattr(host, 'CONTROLPARAMETERS', ()))
            derivedparameters.update(
                getattr(host, 'DERIVEDPARAMETERS', ()))
        for par in itertools.chain(derivedparameters, cls.SOLVERPARAMETERS):
            controlparameters.update(getattr(par, 'CONTROLPARAMETERS', ()))
            derivedparameters.update(getattr(par, 'DERIVEDPARAMETERS', ()))
        if controlparameters and not hasattr(module, 'ControlParameters'):
            module.ControlParameters = type(
                'ControlParameters',
                (parametertools.SubParameters,),
                {'CLASSES': cls._sort_variables(controlparameters),
                 '__doc__': f'Control parameters of model {modelname}.',
                 '__module__': modulename},
            )
        if derivedparameters and not hasattr(module, 'DerivedParameters'):
            module.DerivedParameters = type(
                'DerivedParameters',
                (parametertools.SubParameters,),
                {'CLASSES': cls._sort_variables(derivedparameters),
                 '__doc__': f'Derived parameters of model {modelname}.',
                 '__module__': modulename},
            )
        if cls.SOLVERPARAMETERS and not hasattr(module, 'SolverParameters'):
            module.SolverParameters = type(
                'SolverParameters',
                (parametertools.SubParameters,),
                {'CLASSES': cls._sort_variables(cls.SOLVERPARAMETERS),
                 '__doc__': f'Solver parameters of model {modelname}.',
                 '__module__': modulename},
            )

    @staticmethod
    def _sort_variables(variables: Iterable[Type[typingtools.VariableProtocol]]
                        ) -> Tuple[Type[typingtools.VariableProtocol], ...]:
        return tuple(var_ for (idx, var_) in sorted(
            (inspect.getsourcelines(var_)[1], var_) for var_ in variables
        ))

    # sorting with dependencies, or is the definition order always okay?
    #
    # @classmethod
    # def _sort_derivedparameters(
    #         cls,
    #         parameters: Iterable[Type[parametertools.Parameter]]
    # ) -> Tuple[Type[parametertools.Parameter], ...]:
    #     dps = []
    #     for newpar in parameters:
    #         for idx, oldpar in enumerate(dps):
    #             print(newpar, oldpar, idx)
    #             if newpar in getattr(oldpar, 'DERIVEDPARAMETERS', ()):
    #                 dps.insert(idx, newpar)
    #                 print('done')
    #                 break
    #         else:
    #             dps.append(newpar)
    #     return tuple(dps)


class AdHocModel(Model):
    """Base class for models solving the underlying differential equations
    in an "ad hoc manner".

    "Ad hoc" stands for the classical approaches in hydrology, to calculate
    individual fluxes separately (often sequentially) and without error
    control (see `Clark and Kavetski`_).
    """

    RUN_METHODS: ClassVar[Tuple[Callable, ...]]
    ADD_METHODS: ClassVar[Tuple[Callable, ...]]
    METHOD_GROUPS = (
        'RUN_METHODS', 'ADD_METHODS',
        'INLET_METHODS', 'OUTLET_METHODS',
        'RECEIVER_METHODS', 'SENDER_METHODS')

    def simulate(self, idx: int) -> None:
        """Perform a simulation run over a single simulation time step.

        The required argument `idx` corresponds to property |Model.idx_sim|.

        You can integrate method |Model.simulate| into your workflows for
        tailor-made simulation runs.  Method |Model.simulate| is complete
        enough to allow for consecutive calls.  However, note that it
        does neither call |Model.save_data|, |Model.update_receivers|,
        nor |Model.update_senders|.  Also, one would have to reset the
        related node sequences, as done in the following example:

        >>> from hydpy.examples import prepare_full_example_2
        >>> hp, pub, TestIO = prepare_full_example_2()
        >>> model = hp.elements.land_dill.model
        >>> for idx in range(4):
        ...     model.simulate(idx)
        ...     print(hp.nodes.dill.sequences.sim)
        ...     hp.nodes.dill.sequences.sim = 0.0
        sim(11.658511)
        sim(8.842278)
        sim(7.103614)
        sim(6.00763)
        >>> hp.nodes.dill.sequences.sim.series
        InfoArray([ nan,  nan,  nan,  nan])

        The results above are identical to those of method |HydPy.simulate|
        of class |HydPy|, which is the standard method to perform simulation
        runs (except that method |HydPy.simulate| of class |HydPy| also
        performs the steps neglected by method |Model.simulate| of class
        |Model| mentioned above):

        >>> from hydpy import round_
        >>> hp.reset_conditions()
        >>> hp.simulate()
        >>> round_(hp.nodes.dill.sequences.sim.series)
        11.658511, 8.842278, 7.103614, 6.00763

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        self.load_data()
        self.update_inlets()
        self.run()
        self.new2old()
        self.update_outlets()

    def run(self) -> None:
        """Call all methods defined as "RUN_METHODS" in the defined order.

        >>> from hydpy.core.modeltools import AdHocModel, Method
        >>> class print_1(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(1)
        >>> class print_2(Method):
        ...     @staticmethod
        ...     def __call__(self):
        ...         print(2)
        >>> class Test(AdHocModel):
        ...     RUN_METHODS = print_1, print_2
        >>> Test().run()
        1
        2

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        for method in self.RUN_METHODS:
            method.__call__(self)


class SolverModel(Model):
    """Base class for hydrological models which solve ordinary differential
    equations with numerical integration algorithms."""

    PART_ODE_METHODS: ClassVar[Tuple[Callable, ...]]
    FULL_ODE_METHODS: ClassVar[Tuple[Callable, ...]]

    @abc.abstractmethod
    def solve(self) -> None:
        """Solve all `FULL_ODE_METHODS` in parallel."""


class NumConstsELS:
    """Configuration options for using the "Explicit Lobatto Sequence"
    implemented by class |ELSModel|.

    You can change the following solver options at your own risk.

    >>> from hydpy.core.modeltools import NumConstsELS
    >>> consts = NumConstsELS()

    The maximum number of Runge Kutta submethods to be applied (the
    higher, the better the theoretical accuracy, but also the worse
    the time spent unsuccessful when the theory does not apply):

    >>> consts.nmb_methods
    10

    The number of entries to handle the stages of the highest order method
    (must agree with the maximum number of methods):

    >>> consts.nmb_stages
    11

    The maximum increase of the integration step size in case of success:

    >>> consts.dt_increase
    2.0

    The maximum decrease of the integration step size in case of failure:

    >>> consts.dt_decrease
    10.0

    The Runge Kutta coefficients, one matrix for each submethod:

    >>> consts.a_coefs.shape
    (11, 12, 11)
    """

    nmb_methods: int
    nmb_stages: int
    dt_increase: float
    dt_decrease: float
    a_coeffs: numpy.ndarray

    def __init__(self):
        self.nmb_methods = 10
        self.nmb_stages = 11
        self.dt_increase = 2.
        self.dt_decrease = 10.
        path = os.path.join(
            conf.__path__[0], 'a_coefficients_explicit_lobatto_sequence.npy')
        self.a_coefs = numpy.load(path)


class NumVarsELS:
    """Intermediate results of the "Explicit Lobatto Sequence" implemented
    by class |ELSModel|.

    Class |NumVarsELS| should be of relevance for model developers,
    as it helps to evaluate how efficient newly implemented models
    are solved (see the documentation on method |ELSModel.solve| of
    class |ELSModel| as an example).
    """

    nmb_calls: int
    t0: float
    t1: float
    dt_est: float
    dt: float
    idx_method: int
    idx_stage: int
    error: float
    last_error: float
    extrapolated_error: float
    f0_ready: bool

    def __init__(self):
        self.nmb_calls = 0
        self.t0 = 0.
        self.t1 = 0.
        self.dt_est = 1.
        self.dt = 1.
        self.idx_method = 0
        self.idx_stage = 0
        self.error = 0.
        self.last_error = 0.
        self.extrapolated_error = 0.
        self.f0_ready = False


class ELSModel(SolverModel):
    """Base class for hydrological models using the "Explicit Lobatto
    Sequence" for solving ordinary differential equations.

    The "Explicit Lobatto Sequence" is a variable order Runge Kutta
    method combining different Lobatto methods.  Its main idea is to
    first calculate a solution with a lower order method, then to use
    these results to apply the next higher order method, and to compare
    both results.  If they are close enough, the latter results are
    accepted.  If not, the next higher order method is applied (or,
    if no higher-order method is available, the step size is
    decreased, and the algorithm restarts with the method of the
    lowest order).  So far, the `thorough description`_ of the
    algorithm is available in German only.

    Note the strengths and weaknesses of class |ELSModel| discussed
    in the documentation on method |ELSModel.solve|.  Model developers
    should not derive from class |ELSModel| when trying to implement
    models with a high potential for stiff parameterisations.
    Discontinuities should be regularised, for example by the
    "smoothing functions" provided by module |smoothtools|.  Model
    users should be careful not to define two small smoothing factors,
    to avoid needlessly long simulation times.
    """

    PART_ODE_METHODS: ClassVar[Tuple[Callable, ...]]
    FULL_ODE_METHODS: ClassVar[Tuple[Callable, ...]]
    METHOD_GROUPS = (
        'INLET_METHODS', 'OUTLET_METHODS',
        'RECEIVER_METHODS', 'SENDER_METHODS',
        'PART_ODE_METHODS', 'FULL_ODE_METHODS')
    numconsts: NumConstsELS
    numvars: NumVarsELS

    def __init__(self) -> None:
        super().__init__()
        self.numconsts = NumConstsELS()
        self.numvars = NumVarsELS()

    def simulate(self, idx: int) -> None:
        """Similar to method |Model.simulate| of class |AdHocModel| but
        calls method |ELSModel.solve| instead of |AdHocModel.run|.

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        self.idx_sim = idx
        self.load_data()
        self.update_inlets()
        self.solve()
        self.update_outlets()

    def solve(self) -> None:
        """Solve all `FULL_ODE_METHODS` in parallel.

        Implementing numerical integration algorithms that (hopefully)
        always work well in practice is a tricky task.  The following
        exhaustive examples show how well our "Explicit Lobatto
        Sequence" algorithm performs for the numerical test models
        |test_v1| and |test_v2|.  We hope to cover all possible
        corner-cases.  Please tell us if you find one we missed.

        First, we set the value of parameter |test_control.K| to zero,
        resulting in no changes at all, and thus defining the simplest
        test case possible:

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.0)

        Second, we assign values to the solver parameters
        |test_solver.AbsErrorMax| and |test_solver.RelDTMin| to specify
        the required numerical accuracy and the smallest internal
        step size:

        >>> solver.abserrormax = 1e-2
        >>> solver.reldtmin = 1e-4

        Calling method |ELSModel.solve| correctly calculates zero
        discharge (|test_fluxes.Q|) and thus does not change the water
        storage (|test_states.S|):

        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(1.0)
        >>> fluxes.q
        q(0.0)

        The achieve the above result, |ELSModel| requires two function
        calls, one for the initial guess (using the Explicit Euler Method)
        and the other one (extending the Explicit Euler method to the
        Explicit Heun method) to confirm the first guess meets the
        required accuracy:

        >>> model.numvars.idx_method
        2
        >>> model.numvars.dt
        1.0
        >>> model.numvars.nmb_calls
        2

        With moderate changes due to setting the value of parameter
        |test_control.K| to 0.1, two method calls are still sufficient:

        >>> k(0.1)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.905)
        >>> fluxes.q
        q(0.095)
        >>> model.numvars.idx_method
        2
        >>> model.numvars.nmb_calls
        2

        Calculating the analytical solution shows |ELSModel| did not
        exceed the given tolerance value:

        >>> import numpy
        >>> from hydpy import round_
        >>> round_(numpy.exp(-k))
        0.904837

        After decreasing the allowed error by one order of magnitude,
        |ELSModel| requires four method calls (again, one for the
        first order and one for the second order method, and two
        additional calls for the third order method):

        >>> solver.abserrormax = 1e-3
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.904833)
        >>> fluxes.q
        q(0.095167)
        >>> model.numvars.idx_method
        3
        >>> model.numvars.nmb_calls
        4

        After decreasing |test_solver.AbsErrorMax| by a factor of ten
        again, |ELSModel| needs one further higher order method, which
        requires three additional calls, making a sum of seven:

        >>> solver.abserrormax = 1e-4
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.904837)
        >>> fluxes.q
        q(0.095163)
        >>> model.numvars.idx_method
        4
        >>> model.numvars.nmb_calls
        7

        |ELSModel| achieves even a very extreme numerical precision
        (just for testing, way beyond hydrological requirements), in
        one single step, but now requires a total of 29 method calls:

        >>> solver.abserrormax = 1e-12
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.904837)
        >>> fluxes.q
        q(0.095163)
        >>> model.numvars.dt
        1.0
        >>> model.numvars.idx_method
        8
        >>> model.numvars.nmb_calls
        29

        With a more dynamical parameterisation, where the storage decreases
        by about 40% per time step, |ELSModel| needs seven method calls
        to meet a "normal" error tolerance:

        >>> solver.abserrormax = 1e-2
        >>> k(0.5)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.606771)
        >>> fluxes.q
        q(0.393229)
        >>> model.numvars.idx_method
        4
        >>> model.numvars.nmb_calls
        7
        >>> round_(numpy.exp(-k))
        0.606531

        Being an explicit integration method, the "Explicit Lobatto
        Sequence" can be inefficient for solving stiff initial value
        problems.  Setting |test_control.K| to 2.0 forces |ELSModel|
        to solve the problem in two substeps, requiring a total of
        22 method calls:

        >>> k(2.0)
        >>> round_(numpy.exp(-k))
        0.135335
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.134658)
        >>> fluxes.q
        q(0.865342)
        >>> round_(model.numvars.dt)
        0.3
        >>> model.numvars.nmb_calls
        22

        Increasing the stiffness of the initial value problem further
        can increase computation times rapidly:

        >>> k(4.0)
        >>> round_(numpy.exp(-k))
        0.018316
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.019774)
        >>> fluxes.q
        q(0.980226)
        >>> round_(model.numvars.dt)
        0.3
        >>> model.numvars.nmb_calls
        44

        If we prevent |ELSModel| from compensating its problems by
        decreasing the step size, it does not achieve satisfying results:

        >>> solver.reldtmin = 1.0
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.09672)
        >>> fluxes.q
        q(0.90328)
        >>> round_(model.numvars.dt)
        1.0
        >>> model.numvars.nmb_calls
        46

        You can restrict the number of Lobatto methods that are allowed
        to be used.  Using two methods only is an inefficient choice for
        the given initial value problem, but at least solves it with the
        required accuracy:

        >>> solver.reldtmin = 1e-4
        >>> model.numconsts.nmb_methods = 2
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.020284)
        >>> fluxes.q
        q(0.979716)
        >>> round_(model.numvars.dt)
        0.156698
        >>> model.numvars.nmb_calls
        74

        Besides its weaknesses with stiff problems, |ELSModel| cannot
        solve discontinuous problems well.  We use the |test_v1| example
        model to demonstrate how |ELSModel| sbehaves when confronted
        with such a problem.

        >>> from hydpy import reverse_model_wildcard_import
        >>> reverse_model_wildcard_import()
        >>> from hydpy.models.test_v2 import *
        >>> parameterstep()

        Everything works fine, as long as the discontinuity does not
        affect the considered simulation step:

        >>> k(0.5)
        >>> solver.abserrormax = 1e-2
        >>> solver.reldtmin = 1e-4
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(0.5)
        >>> fluxes.q
        q(0.5)
        >>> model.numvars.idx_method
        2
        >>> model.numvars.dt
        1.0
        >>> model.numvars.nmb_calls
        2

        The occurrence of a discontinuity within the simulation step
        often increases computation times more than a stiff parameterisation:

        >>> k(2.0)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(-0.006827)
        >>> fluxes.q
        q(1.006827)
        >>> model.numvars.nmb_calls
        58

        >>> k(2.1)
        >>> states.s(1.0)
        >>> model.numvars.nmb_calls = 0
        >>> model.solve()
        >>> states.s
        s(-0.00072)
        >>> fluxes.q
        q(1.00072)
        >>> model.numvars.nmb_calls
        50

        When working in Cython mode, the standard model import overrides
        this generic Python version with a model-specific Cython version.
        """
        self.numvars.t0, self.numvars.t1 = 0., 1.
        self.numvars.dt_est = 1.
        self.numvars.f0_ready = False
        self.reset_sum_fluxes()
        while self.numvars.t0 < self.numvars.t1-1e-14:
            self.numvars.last_error = 999999.
            self.numvars.dt = min(
                self.numvars.t1-self.numvars.t0,
                max(self.numvars.dt_est, self.parameters.solver.reldtmin))
            if not self.numvars.f0_ready:
                self.calculate_single_terms()
                self.numvars.idx_method = 0
                self.numvars.idx_stage = 0
                self.set_point_fluxes()
                self.set_point_states()
                self.set_result_states()
            for self.numvars.idx_method in range(
                    1, self.numconsts.nmb_methods+1):
                for self.numvars.idx_stage in range(
                        1, self.numvars.idx_method):
                    self.get_point_states()
                    self.calculate_single_terms()
                    self.set_point_fluxes()
                for self.numvars.idx_stage in range(
                        1, self.numvars.idx_method+1):
                    self.integrate_fluxes()
                    self.calculate_full_terms()
                    self.set_point_states()
                self.set_result_fluxes()
                self.set_result_states()
                self.calculate_error()
                self.extrapolate_error()
                if self.numvars.idx_method == 1:
                    continue
                if self.numvars.error <= self.parameters.solver.abserrormax:
                    self.numvars.dt_est = (self.numconsts.dt_increase *
                                           self.numvars.dt)
                    self.numvars.f0_ready = False
                    self.addup_fluxes()
                    self.numvars.t0 = self.numvars.t0+self.numvars.dt
                    self.new2old()
                    break
                if ((self.numvars.extrapolated_error >
                     self.parameters.solver.abserrormax) and
                        (self.numvars.dt > self.parameters.solver.reldtmin)):
                    self.numvars.f0_ready = True
                    self.numvars.dt_est = (self.numvars.dt /
                                           self.numconsts.dt_decrease)
                    break
                self.numvars.last_error = self.numvars.error
                self.numvars.f0_ready = True
            else:
                if self.numvars.dt <= self.parameters.solver.reldtmin:
                    self.numvars.f0_ready = False
                    self.addup_fluxes()
                    self.numvars.t0 = self.numvars.t0+self.numvars.dt
                    self.new2old()
                else:
                    self.numvars.f0_ready = True
                    self.numvars.dt_est = (self.numvars.dt /
                                           self.numconsts.dt_decrease)
        self.get_sum_fluxes()

    def calculate_single_terms(self) -> None:
        """Apply all methods stored in the `PART_ODE_METHODS` tuple.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.25)
        >>> states.s = 1.0
        >>> model.calculate_single_terms()
        >>> fluxes.q
        q(0.25)
        """
        self.numvars.nmb_calls = self.numvars.nmb_calls+1
        for method in self.PART_ODE_METHODS:
            method.__call__(self)

    def calculate_full_terms(self) -> None:
        """Apply all methods stored in the `FULL_ODE_METHODS` tuple.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> k(0.25)
        >>> states.s.old = 1.0
        >>> fluxes.q = 0.25
        >>> model.calculate_full_terms()
        >>> states.s.old
        1.0
        >>> states.s.new
        0.75
        """
        for method in self.FULL_ODE_METHODS:
            method.__call__(self)

    def get_point_states(self) -> None:
        """Load the states corresponding to the actual stage.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 2.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._s_points)
        >>> points[:4] = 0.0, 0.0, 1.0, 0.0
        >>> model.get_point_states()
        >>> states.s.old
        2.0
        >>> states.s.new
        1.0
        """
        self._get_states(self.numvars.idx_stage, 'points')

    def _get_states(self, idx: int, type_: str) -> None:
        states = self.sequences.states
        for state in states:
            temp = getattr(states.fastaccess, f'_{state.name}_{type_}')
            state.new = temp[idx]

    def set_point_states(self) -> None:
        """Save the states corresponding to the actual stage.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(states.fastaccess._s_points)
        >>> points[:] = 0.
        >>> model.set_point_states()
        >>> from hydpy import round_
        >>> round_(points[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_states(self.numvars.idx_stage, 'points')

    def set_result_states(self) -> None:
        """Save the final states of the actual method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> states.s.old = 2.0
        >>> states.s.new = 1.0
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(states.fastaccess._s_results)
        >>> results[:] = 0.0
        >>> model.set_result_states()
        >>> from hydpy import round_
        >>> round_(results[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_states(self.numvars.idx_method, 'results')

    def _set_states(self, idx: int, type_: str) -> None:
        states = self.sequences.states
        for state in states:
            temp = getattr(states.fastaccess, f'_{state.name}_{type_}')
            temp[idx] = state.new

    def get_sum_fluxes(self) -> None:
        """Get the sum of the fluxes calculated so far.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 0.0
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> model.get_sum_fluxes()
        >>> fluxes.q
        q(1.0)
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            flux(getattr(fluxes.fastaccess, f'_{flux.name}_sum'))

    def set_point_fluxes(self) -> None:
        """Save the fluxes corresponding to the actual stage.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 1.
        >>> model.numvars.idx_stage = 2
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:] = 0.
        >>> model.set_point_fluxes()
        >>> from hydpy import round_
        >>> round_(points[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_stage, 'points')

    def set_result_fluxes(self) -> None:
        """Save the final fluxes of the actual method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.q = 1.
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:] = 0.
        >>> model.set_result_fluxes()
        >>> from hydpy import round_
        >>> round_(results[:4])
        0.0, 0.0, 1.0, 0.0
        """
        self._set_fluxes(self.numvars.idx_method, 'results')

    def _set_fluxes(self, idx: int, type_: str) -> None:
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            temp = getattr(fluxes.fastaccess, f'_{flux.name}_{type_}')
            temp[idx] = flux

    def integrate_fluxes(self) -> None:
        """Perform a dot multiplication between the fluxes and the
        A coefficients associated with the different stages of the
        actual method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.idx_method = 2
        >>> model.numvars.idx_stage = 1
        >>> model.numvars.dt = 0.5
        >>> points = numpy.asarray(fluxes.fastaccess._q_points)
        >>> points[:4] = 15., 2., -999., 0.
        >>> model.integrate_fluxes()
        >>> from hydpy import round_
        >>> from hydpy import pub
        >>> round_(numpy.asarray(model.numconsts.a_coefs)[1, 1, :2])
        0.375, 0.125
        >>> fluxes.q
        q(2.9375)
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            points = getattr(fluxes.fastaccess, f'_{flux.name}_points')
            coefs = self.numconsts.a_coefs[self.numvars.idx_method-1,
                                           self.numvars.idx_stage,
                                           :self.numvars.idx_method]
            flux(self.numvars.dt *
                 numpy.dot(coefs, points[:self.numvars.idx_method]))

    def reset_sum_fluxes(self) -> None:
        """Set the sum of the fluxes calculated so far to zero.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 5.
        >>> model.reset_sum_fluxes()
        >>> fluxes.fastaccess._q_sum
        0.0
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            setattr(fluxes.fastaccess, f'_{flux.name}_sum', 0.)

    def addup_fluxes(self) -> None:
        """Add up the sum of the fluxes calculated so far.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> fluxes.fastaccess._q_sum = 1.0
        >>> fluxes.q(2.0)
        >>> model.addup_fluxes()
        >>> fluxes.fastaccess._q_sum
        3.0
        """
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            sum_ = getattr(fluxes.fastaccess, f'_{flux.name}_sum')
            sum_ += flux
            setattr(fluxes.fastaccess, f'_{flux.name}_sum', sum_)

    def calculate_error(self) -> None:
        """Estimate the numerical error based on the fluxes calculated
        by the current and the last method.

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.idx_method = 2
        >>> results = numpy.asarray(fluxes.fastaccess._q_results)
        >>> results[:4] = 0., 3., 4., 0.
        >>> model.calculate_error()
        >>> from hydpy import round_
        >>> round_(model.numvars.error)
        1.0
        """
        self.numvars.error = 0.
        fluxes = self.sequences.fluxes
        for flux in fluxes.numericsequences:
            results = getattr(fluxes.fastaccess, f'_{flux.name}_results')
            diff = (results[self.numvars.idx_method] -
                    results[self.numvars.idx_method-1])
            self.numvars.error = max(self.numvars.error,
                                     numpy.max(numpy.abs(diff)))

    def extrapolate_error(self) -> None:
        """Estimate the numerical error expected when applying all methods
        available based on the results of the current and the last method.

       Note that you cannot apply this extrapolation strategy on the first
       method.   If the current method is the first one, method
       |ELSModel.extrapolate_error| returns `-999.9`:

        >>> from hydpy.models.test_v1 import *
        >>> parameterstep()
        >>> model.numvars.error = 1e-2
        >>> model.numvars.last_error = 1e-1
        >>> model.numvars.idx_method = 10
        >>> model.extrapolate_error()
        >>> from hydpy import round_
        >>> round_(model.numvars.extrapolated_error)
        0.01
        >>> model.numvars.idx_method = 9
        >>> model.extrapolate_error()
        >>> round_(model.numvars.extrapolated_error)
        0.001
        """
        if self.numvars.idx_method > 2:
            self.numvars.extrapolated_error = modelutils.exp(
                modelutils.log(self.numvars.error) +
                (modelutils.log(self.numvars.error) -
                 modelutils.log(self.numvars.last_error)) *
                (self.numconsts.nmb_methods-self.numvars.idx_method))
        else:
            self.numvars.extrapolated_error = -999.9
