from PyQt5 import QtWidgets, QtCore

from collections import deque
import pyqtgraph as pg
import numpy as np
from instrument import DataWindow, ConfigWindow

class DCWidget(QtWidgets.QWidget, DataWindow):
    def __init__(self, inst):
        super().__init__()
        self.instrument = inst
        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        self.trigger_btn = QtWidgets.QPushButton("Trigger")
        self.trigger_btn.clicked.connect(self.trigger_btn_clicked)
        self.record_trigger = QtWidgets.QCheckBox("Trigger on record")
        self.record_trigger.stateChanged.connect(self.record_trigger_changed)

    def _layout_controls(self):
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.trigger_btn)
        vbox.addWidget(self.record_trigger)
        vbox.addStretch()
        self.setLayout(vbox)

    def start(self):
        self.record_trigger.setChecked(self.instrument.cfg.record_trigger)

    def add_sample(self, time, sample):
        pass

    def refresh(self):
        pass

    def trigger_btn_clicked(self):
        self.instrument.trigger()

    def record_trigger_changed(self, state):
        self.instrument.cfg.record_trigger = state

class DCConfigWindow(QtWidgets.QWidget, ConfigWindow):
    def __init__(self):
        super().__init__()
        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        pass

    def _layout_controls(self):
        pass

    def load_config(self, config):
        pass

    def get_config(self):
        pass
