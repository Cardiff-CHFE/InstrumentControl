from resources import getResourcePath
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.uic import loadUiType
import pyqtgraph as pg
import numpy as np
from utils import float_to_si

NetworkAnalyserViewerUi, NetworkAnalyserViewerBase = loadUiType(
    getResourcePath('ui/vnaDataWindow.ui'))


class DataWindow(
        NetworkAnalyserViewerBase, NetworkAnalyserViewerUi):
    def __init__(self, instrument, parent=None):
        NetworkAnalyserViewerBase.__init__(self, parent)
        self.setupUi(self)

        self.instrument = instrument

        # Create plots
        self.frequencyPlot = pg.PlotItem(title="Frequency")
        self.frequencyPlot.setLabel("left", "change in Frequency", "Hz")
        self.frequencyPlot.setLabel("bottom", "Sample", "")

        self.qFactorPlot = pg.PlotItem(title="Q factor")
        self.qFactorPlot.setLabel("left", "change in Q factor")
        self.qFactorPlot.setLabel("bottom", "Sample", "")

        self.graph.addItem(self.frequencyPlot, 0, 0)
        self.graph.addItem(self.qFactorPlot, 1, 0)

        segmentCount = len(self.instrument.cfg.segments)
        colours = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        self.frequencyPlotData = []
        self.qFactorPlotData = []
        self.enabledSegments = [True]*segmentCount

        for i in range(segmentCount):
            freq = self.frequencyPlot.plot(pen=colours[i])
            qfac = self.qFactorPlot.plot(pen=colours[i])
            self.frequencyPlotData.append(freq)
            self.qFactorPlotData.append(qfac)

        self.segmentTable.setRowCount(segmentCount)
        self.segmentTable.setColumnCount(4)
        self.segmentTable.setVerticalHeaderLabels([s.name for s in self.instrument.cfg.segments])
        self.segmentTable.setHorizontalHeaderLabels(["Enabled", "F0 (GHz)", "Q factor", "Insertion loss (dB)"])
        for row in range(segmentCount):
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Checked)
            self.segmentTable.setItem(row, 0, checkbox)
            for col in range(3):
                self.segmentTable.setItem(row, col+1, QTableWidgetItem("0.0"))
            self.segmentTable.resizeColumnsToContents()
            self.segmentTable.resizeRowsToContents()

        # Bind signals
        self.zeroOffset.clicked.connect(self.zeroOffsetClicked)
        self.bwOverride.stateChanged.connect(self.bwOverrideChanged)
        self.bwFactor.valueChanged.connect(self.bwFactorChanged)
        self.trackEnable.stateChanged.connect(self.trackEnableChanged)
        self.resetSegments.clicked.connect(self.resetSegmentsPressed)
        self.forceRetrack.clicked.connect(self.forceRetrackPressed)
        self.segmentTable.itemClicked.connect(self.segmentTableClicked)

        self.lastSample = None
        self.maxSamples = 40
        self.frequencyQueue = np.full((segmentCount, self.maxSamples), np.nan)
        self.qFactorQueue = np.full((segmentCount, self.maxSamples), np.nan)
        self.sampleIndexQueue = np.zeros(self.maxSamples)
        self.frequencyOffset = np.zeros(segmentCount)
        self.qFactorOffset = np.zeros(segmentCount)
        self.sampleQueueRoll = 0
        self.nextSampleIndex = 0

    def zeroOffsetClicked(self):
        if self.lastSample:
            self.frequencyOffset = np.array(self.lastSample.f0, dtype=np.float)
            self.qFactorOffset = np.array(self.lastSample.q, dtype=np.float)

    def bwOverrideChanged(self, state):
        if state == QtCore.Qt.Checked:
            self.instrument.set_bw_factor_override(self.bw_factor.value())
        else:
            self.instrument.set_bw_factor_override(None)

    def bwFactorChanged(self, val):
        if self.bw_override.checkState() == QtCore.Qt.Checked:
            self.instrument.set_bw_factor_override(val)

    def trackEnableChanged(self, state):
        self.instrument.set_tracking_override(state == QtCore.Qt.Checked)
        self.bw_override.setEnabled(state == QtCore.Qt.Checked)

    def resetSegmentsPressed(self):
        self.instrument.reset_segments()

    def forceRetrackPressed(self):
        self.instrument.force_retrack()

    def segmentTableClicked(self, tableItem):
        if self.segmentTable.column(tableItem) == 0:
            row = self.segmentTable.row(tableItem)
            checked = tableItem.checkState() == Qt.Checked
            self.enabledSegments[row] = checked
            if checked:
                self.frequencyQueue[row] = np.nan
                self.qFactorQueue[row] = np.nan
            self.instrument.set_segment_enabled(row, checked)

    def addSample(self, time, sample):
        freq = np.array(sample.f0, dtype=np.float)
        qfac = np.array(sample.q, dtype=np.float)

        self.frequencyQueue[:, self.sampleQueueRoll] = freq
        self.qFactorQueue[:, self.sampleQueueRoll] = qfac
        self.sampleIndexQueue[self.sampleQueueRoll] = self.nextSampleIndex
        self.nextSampleIndex += 1
        self.sampleQueueRoll += 1
        if self.sampleQueueRoll == self.maxSamples:
            self.sampleQueueRoll = 0
        self.lastSample = sample

    def refresh(self):
        freq = np.roll(self.frequencyQueue, -self.sampleQueueRoll, axis=1)
        qfac = np.roll(self.qFactorQueue, -self.sampleQueueRoll, axis=1)
        idxs = np.roll(self.sampleIndexQueue, -self.sampleQueueRoll)

        for i in range(self.frequencyOffset.size):
            if self.enabledSegments[i]:
                self.frequencyPlotData[i].setData(idxs, freq[i]-self.frequencyOffset[i])
                self.qFactorPlotData[i].setData(idxs, qfac[i]-self.qFactorOffset[i])
            else:
                self.frequencyPlotData[i].setData([], [])
                self.qFactorPlotData[i].setData([], [])

        if self.lastSample:
            for row, f in enumerate(self.lastSample.f0):
                if f is not None:
                    self.segmentTable.item(row, 1).setText(float_to_si(f, 6) + "Hz")
            for row, q in enumerate(self.lastSample.q):
                if q is not None:
                    self.segmentTable.item(row, 2).setText(float_to_si(q, 6))
            for row, il in enumerate(self.lastSample.il):
                if il is not None:
                    self.segmentTable.item(row, 3).setText(float_to_si(il, 6) + "dB")
