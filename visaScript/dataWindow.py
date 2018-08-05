from PyQt5.QtCore import Qt, QVariant, QTime
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.uic import loadUiType
from utils import float_to_si, getResourcePath

DataWindowUi, DataWindowBase = loadUiType(
    getResourcePath('ui/visaScriptDataWindow.ui'))


class DataWindow(
        DataWindowBase, DataWindowUi):
    def __init__(self, instrument, parent=None):
        DataWindowBase.__init__(self, parent)
        self.setupUi(self)

        self.instrument = instrument

    def addSample(self, elapsed, timestamp, sample):
        text = "{}: {}".format(timestamp.isoformat(), sample)
        self.logOutput.appendPlainText(text)

    def refresh(self):
        pass