from PyQt4 import QtGui, QtCore

from collections import deque
import pyqtgraph as pg
import numpy as np
from instrument import DataWindow, ConfigWindow

class DCWidget(QtGui.QWidget, DataWindow):
    def __init__(self):
        super().__init__()
        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        pass

    def _layout_controls(self):
        pass

    def configure(self, config):
        pass

    def add_sample(self, time, sample):
        pass

    def refresh(self):
        pass

class DCConfig(QtGui.QWidget, ConfigWindow):
    def __init__(self):
        super().__init__()
        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        pass

    def _layout_controls(self):
        pass
