from PyQt4 import QtGui, QtCore

from collections import deque
import pyqtgraph as pg
import numpy as np

class DCWidget(QtGui.QWidget):
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
