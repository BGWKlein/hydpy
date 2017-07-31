# -*- coding: utf-8 -*-

# import...
# ...from the Python standard library
from __future__ import division, print_function
import os
import sys
import inspect
import warnings
import importlib
import doctest
import types
import collections
# ...from HydPy
from hydpy import pub
from hydpy.core import objecttools
from hydpy.core import timetools
from hydpy.core import filetools
from hydpy.core import parametertools
from hydpy.core import sequencetools
from hydpy.core import devicetools


class Tester(object):

    def __init__(self):
        frame = inspect.currentframe().f_back
        self.filepath = frame.f_code.co_filename
        self.package = frame.f_locals['__package__']
        self.ispackage = os.path.split(self.filepath)[-1] == '__init__.py'

    @property
    def filenames(self):
        if self.ispackage:
            return os.listdir(os.path.dirname(self.filepath))
        else:
            return [self.filepath]

    @property
    def modulenames(self):
        return [os.path.split(fn)[-1].split('.')[0] for fn in self.filenames
                if (fn.endswith('.py') and not fn.startswith('_'))]

    def doit(self):
        usedefaultvalues = pub.options.usedefaultvalues
        pub.options.usedefaultvalues = False
        printprogress = pub.options.printprogress
        pub.options.printprogress = False
        warnsimulationstep = pub.options.warnsimulationstep
        pub.options.warnsimulationstep = False
        timegrids = pub.timegrids
        pub.timegrids = None
        _simulationstep = parametertools.Parameter._simulationstep
        parametertools.Parameter._simulationstep = None
        dirverbose = pub.options.dirverbose
        reprcomments = pub.options.reprcomments
        pub.options.reprcomments = False
        reprdigits = pub.options.reprdigits
        pub.options.reprdigits = 6
        warntrim = pub.options.warntrim
        pub.options.warntrim = False
        nodes = devicetools.Node._registry.copy()
        elements = devicetools.Element._registry.copy()
        devicetools.Node.clearregistry()
        devicetools.Element.clearregistry()
        try:
            color = 34 if pub.options.usecython else 36
            with PrintStyle(color=color, font=4):
                print(
                  'Test %s %s in %sython mode.'
                  % ('package' if self.ispackage else 'module',
                     self.package if self.ispackage else self.modulenames[0],
                     'C' if pub.options.usecython else 'P'))
            with PrintStyle(color=color, font=2):
                for name in self.modulenames:
                    print('    * %s:' % name, )
                    with StdOutErr(indent=8):
                        modulename = '.'.join((self.package, name))
                        module = importlib.import_module(modulename)
                        warnings.filterwarnings('error', module=modulename)
                        warnings.filterwarnings('ignore',
                                                category=ImportWarning)
                        doctest.testmod(module, extraglobs={'testing': True},
                                        optionflags=doctest.ELLIPSIS)
                        warnings.resetwarnings()
        finally:
            pub.options.usedefaultvalues = usedefaultvalues
            pub.options.printprogress = printprogress
            pub.options.warnsimulationstep = warnsimulationstep
            pub.timegrids = timegrids
            parametertools.Parameter._simulationstep = _simulationstep
            pub.options.dirverbose = dirverbose
            pub.options.reprcomments = reprcomments
            pub.options.reprdigits = reprdigits
            pub.options.warntrim = warntrim
            devicetools.Node.clearregistry()
            devicetools.Element.clearregistry()
            devicetools.Node._registry = nodes
            devicetools.Element._registry = elements


class PrintStyle(object):

    def __init__(self, color, font):
        self.color = color
        self.font = font

    def __enter__(self):
        print('\x1B[%d;30;%dm' % (self.font, self.color))

    def __exit__(self, exception, message, traceback_):
        print('\x1B[0m')
        if exception:
            objecttools.augmentexcmessage()


class StdOutErr(object):

    def __init__(self, indent=0):
        self.indent = indent
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.encoding = sys.stdout.encoding
        self.texts = []

    def __enter__(self):
        self.encoding = sys.stdout.encoding
        sys.stdout = self
        sys.stderr = self

    def __exit__(self, exception, message, traceback_):
        if not self.texts:
            self.print_('no failures occurred')
        else:
            for text in self.texts:
                self.print_(text)
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        if exception:
            objecttools.augmentexcmessage()

    def write(self, text):
        self.texts.extend(text.split('\n'))

    def print_(self, text):
        if text.strip():
            self.stdout.write(self.indent*' ' + text + '\n')

    def flush(self):
        pass


def parameterstep(timestep=None):
    """
    Define a parameter time step size within a parameter control file.

    Argument:
      * timestep(:class:`~hydpy.core.timetools.Period`): Time step size.

    Function :func:`parameterstep` should usually be be applied in a line
    immediately behind the model import.  Defining the step size of time
    dependent parameters is a prerequisite to access any model specific
    parameter.

    Note that :func:`parameterstep` implements some namespace magic by
    means of the module :mod:`inspect`.  This makes things a little
    complicated for framework developers, but it eases the definition of
    parameter control files for framework users.
    """
    if timestep is not None:
        parametertools.Parameter._parameterstep = timetools.Period(timestep)
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        model = namespace['Model']()
        namespace['model'] = model
        element = namespace.get('element', None)
        if isinstance(element, devicetools.Element):
            element.model = model
            model.element = element
        if pub.options.usecython and 'cythonizer' in namespace:
            cythonizer = namespace['cythonizer']
            namespace['cythonmodule'] = cythonizer.cymodule
            model.cymodel = cythonizer.cymodule.Model()
            namespace['cymodel'] = model.cymodel
            for (name, func) in cythonizer.pyxwriter.listofmodeluserfunctions:
                setattr(model, name, getattr(model.cymodel, name))
            for func in ('doit', 'new2old', 'openfiles', 'closefiles',
                         'loaddata', 'savedata'):
                if hasattr(model.cymodel, func):
                    setattr(model, func, getattr(model.cymodel, func))
        if 'Parameters' not in namespace:
            namespace['Parameters'] = parametertools.Parameters
        model.parameters = namespace['Parameters'](namespace)
        if 'Sequences' not in namespace:
            namespace['Sequences'] = sequencetools.Sequences
        model.sequences = namespace['Sequences'](namespace)
        namespace['parameters'] = model.parameters
        for (name, pars) in model.parameters:
            namespace[name] = pars
        namespace['sequences'] = model.sequences
        for (name, seqs) in model.sequences:
            namespace[name] = seqs
    try:
        namespace.update(namespace['CONSTANTS'])
    except KeyError:
        pass
    focus = namespace.get('focus')
    for (name, par) in model.parameters.control:
        try:
            if (focus is None) or (par is focus):
                namespace[par.name] = par
            else:
                namespace[par.name] = lambda *args, **kwargs: None
        except AttributeError:
            pass


def simulationstep(timestep):
    """
    Define a simulation time step size for testing purposes within a
    parameter control file.

    Argument:
        * timestep(:class:`~hydpy.core.timetools.Period`): Time step size.

    Using :func:`simulationstep` only affects the values of time dependent
    parameters, when `pub.timegrids.stepsize` is not defined.  It thus has
    no influence on usual hydpy simulations at all.  Use it just to check
    your parameter control files.  Write it in a line immediately behind
    the one calling :func:`parameterstep`.
    """
    if pub.options.warnsimulationstep:
        warnings.warn('Note that the applied function `simulationstep` is '
                      'inteded for testing purposes only.  When doing a '
                      'hydpy simulation, parameter values are initialized '
                      'based on the actual simulation time step as defined '
                      'under `pub.timegrids.stepsize` and the value given '
                      'to `simulationstep` is ignored.')
    parametertools.Parameter._simulationstep = timetools.Period(timestep)


def controlcheck(controldir='default', projectdir=None, controlfile=None):
    namespace = inspect.currentframe().f_back.f_locals
    model = namespace.get('model')
    if model is None:
        if projectdir is None:
            projectdir = os.path.dirname(os.path.abspath(os.curdir))
            projectdir = os.path.split(projectdir)[-1]
        os.chdir(os.path.join('..', '..', '..'))
        controlpath = os.path.abspath(os.path.join('control',
                                                   projectdir,
                                                   controldir))
        initfile = os.path.split(namespace['__file__'])[-1]
        if controlfile is None:
            controlfile = initfile
        filepath = os.path.join(controlpath, controlfile)
        if not os.path.exists(filepath):
            raise IOError('The check of consistency between the control '
                          'parameter file %s and the initial condition file '
                          '%s failed.  The control parameter file does not '
                          'exist in directory %s.'
                          % (controlfile, initfile, controlpath))
        controlmanager = filetools.ControlManager()
        controlmanager.projectdirectory = projectdir
        controlmanager.selecteddirectory = controldir
        model = controlmanager.loadfile(controlfile)['model']
        model.parameters.update()
        namespace['model'] = model
        for name1 in ('states', 'logs'):
            subseqs = getattr(model.sequences, name1, None)
            if subseqs is not None:
                for (name2, seq) in subseqs:
                    namespace[name2] = seq


_PAR_SPEC2CAPT = collections.OrderedDict((('parameters', 'Parameter tools'),
                                          ('constants', 'Constants'),
                                          ('control', 'Control parameters'),
                                          ('derived', 'Derived parameters')))

_SEQ_SPEC2CAPT = collections.OrderedDict((('sequences', 'Sequence tools'),
                                          ('inputs', 'Input sequences'),
                                          ('fluxes', 'Flux sequences'),
                                          ('states', 'State sequences'),
                                          ('logs', 'Log sequences'),
                                          ('inlets', 'Inlet sequences'),
                                          ('outlets', 'Outlet sequences'),
                                          ('receivers', 'Receiver sequences'),
                                          ('senders', 'Sender sequences'),
                                          ('aides', 'Aide sequences')))

_all_spec2capt = _PAR_SPEC2CAPT.copy()
_all_spec2capt.update(_SEQ_SPEC2CAPT)


def _add_title(title, marker):
    """Return a title for a basemodels docstring."""
    return ['', title, marker*len(title)]


def _add_lines(specification, module):
    """Return autodoc commands for a basemodels docstring.

    Note that `collection classes` (e.g. `Model`, `ControlParameters`,
    `InputSequences` are placed on top of the respective section and the
    `contained classes` (e.g. model methods, `ControlParameter` instances,
    `InputSequence` instances at the bottom.  This differs from the order
    of their definition in the respective modules, but results in a better
    documentation structure.
    """
    caption = _all_spec2capt.get(specification, 'dummy')
    if caption.split()[-1] in ('parameters', 'sequences'):
        exists_collectionclass = True
        name_collectionclass = caption.title().replace(' ', '')
    else:
        exists_collectionclass = False
    lines = []
    if specification == 'model':
        lines += ['',
                  '.. autoclass:: ' + module.__name__ + '.Model',
                  '    :members:',
                  '    :show-inheritance:']
    elif exists_collectionclass:
        lines += ['',
                  '.. autoclass:: %s.%s' % (module.__name__,
                                            name_collectionclass),
                  '    :members:',
                  '    :show-inheritance:']
    lines += ['',
              '.. automodule:: ' + module.__name__,
              '    :members:',
              '    :show-inheritance:']
    if specification == 'model':
        lines += ['    :exclude-members: Model']
    elif exists_collectionclass:
        lines += ['    :exclude-members: ' + name_collectionclass]
    return lines


def autodoc_basemodel():
    """Add an exhaustive docstring to the `__init__` module of a basemodel.

    One just has to write `autodoc_basemodel()` at the bottom of an `__init__`
    module of a basemodel, and all model, parameter and sequence information
    are appended to the modules docstring.  The resulting docstring is suitable
    automatic documentation generation via `Sphinx` and `autodoc`.  Hence
    it helps in constructing HydPy's online documentation and supports the
    embeded help feature of `Spyder` (to see the result, import the package
    of an arbitrary basemodel, e.g. `from hydpy.models import lland` and
    press `cntr+i` with the cursor placed on `lland` written in the IPython
    console afterwards).

    Note that the resulting documentation will be complete only when the
    modules of the basemodel are named in the standard way, e.g. `lland_model`,
    `lland_control`, `lland_inputs`.
    """
    namespace = inspect.currentframe().f_back.f_locals
    doc = namespace.get('__doc__')
    if doc is None:
        doc = ''
    basemodulename = namespace['__name__'].split('.')[-1]
    modules = {key: value for key, value in namespace.items()
               if (isinstance(value, types.ModuleType) and
                   key.startswith(basemodulename+'_'))}
    lines = []
    specification = 'model'
    modulename = basemodulename+'_'+specification
    if modulename in modules:
        module = modules[modulename]
        lines += _add_title('Model features', '-')
        lines += _add_lines(specification, module)
    for (spec2capt, title) in zip((_PAR_SPEC2CAPT, _SEQ_SPEC2CAPT),
                                  ('Parameter features', 'Sequence features')):
        new_lines = _add_title(title, '-')
        found_module = False
        for (specification, caption) in spec2capt.items():
            modulename = basemodulename+'_'+specification
            module = modules.get(modulename)
            if module:
                found_module = True
                new_lines += _add_title(caption, '.')
                new_lines += _add_lines(specification, module)
        if found_module:
            lines += new_lines
    doc += '\n'.join(lines)
    namespace['__doc__'] = doc
