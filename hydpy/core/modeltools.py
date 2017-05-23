# -*- coding: utf-8 -*-

# import...
# ...from standard library
from __future__ import division, print_function
# ...from HydPy
from hydpy.core import objecttools


class MetaModelType(type):
    def __new__(cls, name, parents, dict_):
        for tuplename in ('_RUNMETHODS', '_ADDMETHODS'):
            methods = dict_.get(tuplename, ())
            uniques = {}
            for method in methods:
                dict_[method.__name__] = method
                shortname = '_'.join(method.__name__.split('_')[:-1])
                if shortname in uniques:
                    uniques[shortname] = None
                else:
                    uniques[shortname] = method
            for (shortname, method) in uniques.items():
                if method is not None:
                    dict_[shortname] = method
        return type.__new__(cls, name, parents, dict_)

MetaModelClass = MetaModelType('MetaModelClass', (), {})


class Model(MetaModelClass):
    """Base class for all hydrological models."""

    _RUNMETHODS = ()
    _ADDMETHODS = ()

    def __init__(self):
        self.element = None
        self.parameters = None
        self.sequences = None
        self.cymodel = type('dummy', (), {})
        self.cymodel.idx_sim = -999

    def connect(self):
        """Connect the link sequences of the actual model."""
        conname_isentry_pairs = (('inlets', True),
                                 ('receivers', True),
                                 ('outlets', False),
                                 ('senders', False))
        for (conname, isentry) in conname_isentry_pairs:
            nodes = getattr(self.element, conname).slaves
            if len(nodes) == 1:
                node = nodes[0]
                links = getattr(self.sequences, conname)
                seq = getattr(links, node.variable.lower(), None)
                if seq is None:
                    RuntimeError('ToDo')
                elif isentry:
                    seq.setpointer(node.getdouble_via_exits())
                else:
                    seq.setpointer(node.getdouble_via_entries())
            else:
                NotImplementedError('ToDo')
#        nodes = self.element.inlets.slaves
#        if len(nodes) == 1:
#            node = nodes[0]
#            seq = getattr(self.sequences.inlets, node.variable.lower(), None)
#            if seq is None:
#                RuntimeError('ToDo')
#            else:
#                seq.setpointer(node.getdouble_via_exits())
#        else:
#            NotImplementedError('ToDo')
#        nodes = self.element.outlets.slaves
#        if not nodes:
#            RuntimeError('ToDo')
#        elif len(nodes) == 1:
#            node = nodes[0]
#            seq = getattr(self.sequences.outlets, node.variable.lower(), None)
#            if seq is None:
#                RuntimeError('ToDo')
#            else:
#                seq.setpointer(node.getdouble_via_entries())
#        else:
#            NotImplementedError('ToDo')

    def doit(self, idx):
        self.idx_sim = idx
        self.loaddata()
        self.update_inlets()
        self.run()
        self.update_outlets()
        self.update_senders()
        self.new2old()
        self.savedata()

    def run(self):
        for method in self._RUNMETHODS:
            if not method.__name__.startswith('update_'):
                method(self)

    def loaddata(self):
        self.sequences.loaddata(self.idx_sim)

    def savedata(self):
        self.sequences.savedata(self.idx_sim)

    def update_inlets(self):
        """Maybe."""
        pass

    def update_outlets(self):
        """In any case."""
        pass

    def update_receivers(self):
        pass

    def update_senders(self):
        pass

    def new2old(self):
        """Assign the new/final state values of the actual time step to the
        new/initial state values of the next time step.  Needs to be
        overwritten in Cython mode.
        """
        try:
            self.sequences.states.new2old()
        except AttributeError:
            pass

    def _getidx_sim(self):
        """Index of the actual simulation time step."""
        return self.cymodel.idx_sim
    def _setidx_sim(self, value):
        self.cymodel.idx_sim = int(value)
    idx_sim = property(_getidx_sim, _setidx_sim)

    def __dir__(self):
        return objecttools.dir_(self)
