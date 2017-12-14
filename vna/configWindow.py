from utils import getResourcePath
from PyQt5.QtCore import Qt, QAbstractProxyModel, QModelIndex
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.uic import loadUiType
from .config import Segment

ConfigWindowUi, ConfigWindowBase = loadUiType(getResourcePath('ui/vnaConfigWindow.ui'))


class ConfigWindow(
        ConfigWindowBase, ConfigWindowUi):
    def __init__(self, vnaConfig, parent=None):
        ConfigWindowBase.__init__(self, parent)
        self.setupUi(self)

        self._selectedSegment = None
        self.config = vnaConfig.clone()
        self.segments.addItems(self.config.segments.keys())
        for i in range(self.segments.count()):
            self.segments.item(i).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)

        self.segments.currentRowChanged.connect(self.segmentsRowChanged)
        self.segments.itemChanged.connect(self.segmentsItemChanged)
        self.addSegment.clicked.connect(self.addSegmentClicked)
        self.removeSegment.clicked.connect(self.removeSegmentClicked)
        if len(self.config.segments):
            self.segments.setCurrentRow(0)
            self.segmentsRowChanged(0)

        self.f0.editingFinished.connect(self.f0EditingFinished)
        self.span.editingFinished.connect(self.spanEditingFinished)
        self.points.editingFinished.connect(self.pointsEditingFinished)
        self.ifbw.editingFinished.connect(self.ifbwEditingFinished)
        self.power.editingFinished.connect(self.powerEditingFinished)
        self.sampleInterval.editingFinished.connect(self.sampleIntervalEditingFinished)
        self.bandwidthFactor.editingFinished.connect(self.bandwidthFactorEditingFinished)
        self.trackFrequency.stateChanged.connect(self.trackFrequencyStateChanged)
        self.trackSpan.stateChanged.connect(self.trackSpanStateChanged)
        self.vnaModel.currentIndexChanged[str].connect(self.vnaModelCurrentIndexChanged)

        self.sampleInterval.setValue(self.config.sample_interval)
        self.bandwidthFactor.setValue(self.config.bandwidth_factor)
        self.trackFrequency.setChecked(bool(self.config.track_frequency))
        self.trackSpan.setChecked(bool(self.config.track_span))
        self.vnaModel.setCurrentText(str(self.config.model))

    def keyPressEvent(self, event):
        event.ignore()

    def segmentsRowChanged(self, row):
        try:
            self.selectedSegment = self.config.segments.child(row)
        except IndexError:
            self.selectedSegment = None

    def segmentsItemChanged(self, item):
        widget = item.listWidget()
        row = widget.row(item)
        segments = self.config.segments
        if segments.childKey(row) != item.text():
            segments.setChildKey(row, item.text())

    def addSegmentClicked(self):
        keyfmt = 'Mode {}'
        idx = 0
        while True:
            key = keyfmt.format(idx)
            if key not in self.config.segments:
                break
            idx += 1
        
        self.config.segments[key] = {
            'f0': 2.500E+09,
            'span': 20E+06,
            'points': 201,
            'ifbw': 10e3,
            'power': 0.0
        }
        item = QListWidgetItem(key)
        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled)
        self.segments.addItem(item)
        row = len(self.config.segments)-1
        self.segments.setCurrentRow(row)
        self.segmentsRowChanged(row)


    def removeSegmentClicked(self):
        row = self.segments.currentRow()
        self.config.segments.removeChild(row)
        self.segments.takeItem(row)
        if row >= len(self.config.segments):
            row = len(self.config.segments)-1

        if row >= 0:
            self.segments.setFocus()
            self.segments.setCurrentRow(row)
            self.segmentsRowChanged(row)
        else:
            self.selectedSegment = None

    def f0EditingFinished(self):
        self.selectedSegment.f0 = self.f0.value()

    def spanEditingFinished(self):
        self.selectedSegment.span = self.span.value()

    def pointsEditingFinished(self):
        self.selectedSegment.points = self.points.value()

    def ifbwEditingFinished(self):
        self.selectedSegment.ifbw = self.ifbw.value()

    def powerEditingFinished(self):
        self.selectedSegment.power = self.power.value()

    def sampleIntervalEditingFinished(self):
        value = self.sampleInterval.value()
        self.config.sample_interval = value

    def bandwidthFactorEditingFinished(self):
        value = self.bandwidthFactor.value()
        self.config.bandwidth_factor = value

    def trackFrequencyStateChanged(self, value):
        self.config.track_frequency = value

    def trackSpanStateChanged(self, value):
        self.config.track_span = value

    def vnaModelCurrentIndexChanged(self, value):
        self.config.model = value

    def updateSegmentWidgets(self):
        segment = self.selectedSegment
        if segment is not None:
            self.removeSegment.setEnabled(True)
            self.f0.setValue(segment.f0)
            self.span.setValue(segment.span)
            self.points.setValue(segment.points)
            self.ifbw.setValue(segment.ifbw)
            self.power.setValue(segment.power)
        else:
            self.removeSegment.setEnabled(False)

    def enableSegmentWidgets(self, enabled):
        self.f0.setEnabled(enabled)
        self.span.setEnabled(enabled)
        self.points.setEnabled(enabled)
        self.ifbw.setEnabled(enabled)
        self.power.setEnabled(enabled)

    @property
    def selectedSegment(self):
        return self._selectedSegment

    @selectedSegment.setter
    def selectedSegment(self, value):
        self._selectedSegment = value
        self.enableSegmentWidgets(value is not None)
        self.updateSegmentWidgets()
