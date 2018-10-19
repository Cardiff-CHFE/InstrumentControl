from PyQt5.QtCore import Qt, QVariant, QTime
from PyQt5.uic import loadUiType
import pyqtgraph as pg
import numpy as np
import array
from utils import float_to_si, getResourcePath

DataWindowUi, DataWindowBase = loadUiType(
    getResourcePath('ui/dataloggerDataWindow.ui'))


class DataWindow(
        DataWindowBase, DataWindowUi):
    def __init__(self, instrument, parent=None):
        DataWindowBase.__init__(self, parent)
        self.setupUi(self)

        self.instrument = instrument

    def addSample(self, elapsed, timestamp, sample):
        ch0 = sample[0]
        ch1 = sample[1]
        if self.instrument.config.model == '1316':
            self.raw0.setText("Tempearture 1: {:4.1f} Celcius".format(ch0))
            self.raw1.setText("Tempearture 2: {:4.1f} Celcius".format(ch1))
        else:
            self.raw0.setText("Tempearture: {:4.1f} Celcius".format(ch0))
            self.raw1.setText("Relative humidity: {:4.1f}%".format(ch1))

    def refresh(self):
        pass