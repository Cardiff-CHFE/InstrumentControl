from utils import getResourcePath
from PyQt5.QtCore import Qt, QAbstractProxyModel, QModelIndex
# from PyQt5.QtWidgets import
from PyQt5.uic import loadUiType
from keyValueModel import KeyValueModel
from schemaDelegate import SchemaDelegate
from .config import Segment

ConfigWindowUi, ConfigWindowBase = loadUiType(getResourcePath('ui/vnaConfigWindow.ui'))


class ConfigWindow(
        ConfigWindowBase, ConfigWindowUi):
    def __init__(self, vnaConfig, parent=None):
        ConfigWindowBase.__init__(self, parent)
        self.setupUi(self)

        self._selectedSegment = None
        self.config = vnaConfig.clone()
        self.configModel = KeyValueModel(self.config)
        self.segments.setModel(self.configModel)
        self.segments.setRootIndex(self.configModel.indexOf(self.config.segments, 0))
        self.segments.setModelColumn(0)
        self.segmentsDelegate = SchemaDelegate()
        self.segments.setItemDelegate(self.segmentsDelegate)
        self.segments.selectionModel().currentChanged.connect(self.onCurrentChanged)
        self.removeSegment.setEnabled(len(self.config.segments)>0)

        self.configModel.dataChanged.connect(self.onModelDataChanged)
        self.addSegment.clicked.connect(self.onAddSegment)
        self.removeSegment.clicked.connect(self.onRemoveSegment)
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

    def onModelDataChanged(self, topLeft, bottomRight, roles):
        value = self.configModel.valueOf(topLeft)
        parent = value.parent
        if isinstance(parent, Segment):
            if parent == self.selectedSegment:
                self.updateSegmentWidgets()

    def onCurrentChanged(self, current, prev):
        value = current.model().valueOf(current)
        assert(isinstance(value, Segment))
        self.selectedSegment = value

    def onAddSegment(self):
        self.config.segments.addChild({
            'f0': 2.500E+09,
            'span': 20E+06,
            'points': 201,
            'ifbw': 10e3,
            'power': 0.0
        })
        self.removeSegment.setEnabled(True)

    def onRemoveSegment(self):
        value = self.selectedSegment
        if value is not None:
            row = value.row
            self.config.segments.removeChild(row)
            if row > 0:
                value = self.config.segments.child(row-1)
                index = self.configModel.indexOf(value, 1)
                self.segments.setCurrentIndex(index)
                # self.segments.setFocus()
                self.selectedSegment = value
            else:
                self.selectedSegment = None
                self.removeSegment.setEnabled(False)

    def f0EditingFinished(self):
        segment = self.selectedSegment
        if segment is not None:
            segment.f0 = self.f0.value()

    def spanEditingFinished(self):
        segment = self.selectedSegment
        if segment is not None:
            segment.span = self.span.value()

    def pointsEditingFinished(self):
        segment = self.selectedSegment
        if segment is not None:
            segment.points = self.points.value()

    def ifbwEditingFinished(self):
        segment = self.selectedSegment
        if segment is not None:
            segment.ifbw = self.ifbw.value()

    def powerEditingFinished(self):
        segment = self.selectedSegment
        if segment is not None:
            segment.power = self.power.value()

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
            print("Data changed")
            self.f0.setValue(segment.f0)
            self.span.setValue(segment.span)
            self.points.setValue(segment.points)
            self.ifbw.setValue(segment.ifbw)
            self.power.setValue(segment.power)

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
