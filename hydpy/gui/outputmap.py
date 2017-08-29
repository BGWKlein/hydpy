
# import...
# ...from standard library
from __future__ import division, print_function
import os
import tkinter
import runpy
# ...from site-packages
import numpy
# ...from HydPy
from hydpy import pub
from hydpy.gui import shapetools
from . import selector
from . import colorbar
from . import outputmapdate
from hydpy.gui import selectionbox

hydpy = None


class OutputMap(tkinter.Tk):
    """Visualisation of model parameters and time series in (multiple) maps."""

    def __init__(self, hydpy, width, height):
        tkinter.Tk.__init__(self)
        self.hydpy = hydpy
        self.menu = Menu(self)
        self.menu.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.map = Map(self, width=width, height=height)
        self.map.pack(side=tkinter.TOP)
        tkinter.mainloop()


class Menu(tkinter.Frame):
    """The single menu of :class:`OutputMap`."""

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        self.arrangement = Arrangement(self)
        self.arrangement.pack(side=tkinter.LEFT)
        self.date = outputmapdate.Date(self, self.master.hydpy)
        self.date.pack(side=tkinter.LEFT)


class Arrangement(tkinter.Frame):
    """Defines the number of :class:`Submap` instances."""

    def __init__(self, master):
        tkinter.Frame.__init__(self, master)
        # Define command and selection buttons.
        self.button = tkinter.Button(self, text='rearrange')
        self.button.grid(row=0, columnspan=4, sticky=tkinter.EW)
        self.button.bind('<Double-Button-1>', self.rearrange)
        # Define entry boxes for the number of rows and columns.
        label = tkinter.Label(self, text='rows:')
        label.grid(row=1, column=0, sticky=tkinter.E)
        self.rowsentry = IntEntry(self, width=1)
        self.rowsentry.grid(row=1, column=1)
        label = tkinter.Label(self, text='columns:')
        label.grid(row=2, column=0, sticky=tkinter.E)
        self.columnsentry = IntEntry(self, width=1)
        self.columnsentry.grid(row=2, column=1)
        # Define entry boxes for the width and height of each submap.
        label = tkinter.Label(self, text='width:')
        label.grid(row=1, column=2, sticky=tkinter.E)
        self.widthentry = IntEntry(self, width=4)
        self.widthentry.grid(row=1, column=3)
        label = tkinter.Label(self, text='height:')
        label.grid(row=2, column=2, sticky=tkinter.E)
        self.heightentry = IntEntry(self, width=4)
        self.heightentry.grid(row=2, column=3)

    def rearrange(self, event):
        self.master.master.map.resize(rows=self.rowsentry.getint(),
                                      columns=self.columnsentry.getint(),
                                      width=self.widthentry.getint(),
                                      height=self.heightentry.getint())


class IntEntry(tkinter.Entry):
    """Defines the number of :class:`Submap` instances in one dimension."""

    def getint(self):
        try:
            return int(self.get())
        except ValueError:
            return 1


class Map(tkinter.Frame):
    """The actual frame for the (muliple) maps of :class:`OutputMap`."""

    def __init__(self, master, width, height):
        tkinter.Frame.__init__(self, master)
        self.shape = (1, 1)
        self.submaps = None
        self.frames = None
        self.drawsubmaps(width=width, height=height)

    def drawsubmaps(self, width, height):
        self.submaps = numpy.empty(self.shape, dtype=object)
        self.frames = []
        for idx in range(self.shape[0]):
            frame = tkinter.Frame(self)
            frame.pack(side=tkinter.TOP)
            self.frames.append(frame)
            for jdx in range(self.shape[1]):
                submap = Submap(frame, width=width, height=height)
                submap.pack(side=tkinter.LEFT)
                self.submaps[idx, jdx] = submap

    def resize(self, rows, columns, width, height):
        for frame in self.frames:
            frame.destroy()
        self.shape = (rows, columns)
        self.drawsubmaps(width=width, height=height)

    def recolor(self):
        for mapsinrow in self.submaps:
            for submap in mapsinrow:
                submap.recolor()


class Submap(tkinter.Frame):
    """One single map contained in :class:`Map`."""

    def __init__(self, master, width, height):
        tkinter.Frame.__init__(self, master, bd=0)
        self.width = width
        self.height = height
        self.update_selection(pub.selections.complete)

    def recolor(self):
        self.infoarea.recolor()
        self.geoarea.recolor()

    def update_selection(self, selection):
        self.selection = selection
        if hasattr(self, 'geoarea'):
            self.geoarea.destroy()
            self.infoarea.destroy()
        self.geoarea = GeoArea(self, width=self.width, height=self.height)
        self.geoarea.pack(side=tkinter.LEFT)
        self.infoarea = InfoArea(self, width=60, height=self.height)
        self.infoarea.pack(side=tkinter.RIGHT)


class GeoArea(tkinter.Canvas):
    """The plotting area for geo objects within a :class:`SubMap`."""

    def __init__(self, master, width, height):
        tkinter.Canvas.__init__(self, master, width=width, height=height)
        for layer in range(1, 4):
            for device in self.master.selection.devices:
                shape = device.shape
                points = shape.vertices_norm.copy()
                points[:, 0] = points[:, 0]*(width-10)+5
                points[:, 1] = points[:, 1]*(height-10)+5
                points = list(points.flatten())
                if shape.layer != layer:
                    continue
                elif isinstance(shape, shapetools.Plane):
                    device.polygon = self.create_polygon(
                            points,  outline='black', width=1, fill='white')
                elif isinstance(shape, shapetools.Line):
                    device.polygon = self.create_line(
                            points, width=1, fill='blue')
                elif isinstance(shape, shapetools.Point):
                    x1, y1 = points
                    x2, y2 = x1+5., y1+5.
                    device.polygon = self.create_oval(x1, y1, x2, y2,
                                                      width=1, fill='red')

    def recolor(self):
        for (name, element) in self.hydpy.elements:
            self.itemconfig(element.temp['polygon'], fill='blue')


class InfoArea(tkinter.Frame):
    """Area reserved for additional information within a :class:`SubMap`."""

    def __init__(self, master, width, height):
        tkinter.Frame.__init__(self, master, width=width, height=height)
        self.description = Description(self)
        self.description.pack(side=tkinter.TOP)
        self.colorbar = colorbar.Colorbar(self, width=width, height=height-70,
                                          selections=self.master.selections)
        self.colorbar.pack(side=tkinter.BOTTOM)
        self.selectionbox = selectionbox.SelectionBox(self)
        self.selectionbox.pack(side=tkinter.BOTTOM)

    def recolor(self):
        self.colorbar.recolor()


class Description(tkinter.Label):
    """Description for a single :class:`SubMap`."""

    def __init__(self, master):
        tkinter.Label.__init__(self, master, text='None')
        self.master.master.selections = []
        self.bind('<Double-Button-1>', self.select)

    def select(self, event):
        sel = selector.Selector(self.master.master.selections,
                                self.master.master.master.master.master.hydpy)
        self.wait_window(sel)
        varnames = []
        for selection in self.master.master.selections:
            if selection.variablestr not in varnames:
                varnames.append(selection.variablestr)
        if varnames:
            self.configure(text='\n'.join(varnames))
        else:
            self.configure(text='None')
        self.master.colorbar.newselections(self.master.master.selections)
