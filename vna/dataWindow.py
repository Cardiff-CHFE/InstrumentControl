from PyQt5.QtCore import Qt, QVariant, QTime
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.uic import loadUiType
import pyqtgraph as pg
import numpy as np
import array
from utils import float_to_si, getResourcePath

DataWindowUi, DataWindowBase = loadUiType(
    getResourcePath('ui/vnaDataWindow.ui'))


class DataWindow(
        DataWindowBase, DataWindowUi):
    def __init__(self, instrument, parent=None):
        DataWindowBase.__init__(self, parent)
        self.setupUi(self)

        self.instrument = instrument

        # Create plots
        self.frequencyPlot = pg.PlotItem(title="Frequency")
        self.frequencyPlot.setLabel("left", "change in Frequency", "Hz")
        self.frequencyPlot.setLabel("bottom", "Time (s)", "")

        self.qFactorPlot = pg.PlotItem(title="Q factor")
        self.qFactorPlot.setLabel("left", "change in Q factor")
        self.qFactorPlot.setLabel("bottom", "Time (s)", "")

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
        self.historicalDuration.timeChanged.connect(self.historicalDurationChanged)

        self.lastSample = None
        self.maxSamples = 100
        self.historicalSeconds = 0
        self.historicalDurationChanged(self.historicalDuration.time())
        self.frequencyBuffers = [array.array('f') for n in range(segmentCount)]
        self.qFactorBuffers = [array.array('f') for n in range(segmentCount)]
        self.timeBuffer = array.array('f')
        self.frequencyOffset = np.zeros(segmentCount)
        self.qFactorOffset = np.zeros(segmentCount)

    def zeroOffsetClicked(self):
        if self.lastSample:
            self.frequencyOffset = np.array(self.lastSample.f0, dtype=np.float)
            self.qFactorOffset = np.array(self.lastSample.q, dtype=np.float)

    def bwOverrideChanged(self, state):
        if state == Qt.Checked:
            self.instrument.set_bw_factor_override(self.bw_factor.value())
        else:
            self.instrument.set_bw_factor_override(None)

    def bwFactorChanged(self, val):
        if self.bwOverride.checkState() == Qt.Checked:
            self.instrument.set_bw_factor_override(val)

    def trackEnableChanged(self, state):
        self.instrument.set_tracking_override(state == Qt.Checked)
        self.bwOverride.setEnabled(state == Qt.Checked)

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

    def historicalDurationChanged(self, time):
        self.historicalSeconds = QTime(0,0).secsTo(time)

    def addSample(self, time, sample):
        for freq, frequencyBuffer in zip(sample.f0, self.frequencyBuffers):
            frequencyBuffer.append(freq)

        for qfac, qFactorBuffer in zip(sample.q, self.qFactorBuffers):
            qFactorBuffer.append(qfac)

        self.timeBuffer.append(time)

        self.lastSample = sample

    def refresh(self):
        interval = self.instrument.cfg.sample_interval
        bufferlen = len(self.timeBuffer)
        if not bufferlen:
            return
        start = max(bufferlen-int(self.historicalSeconds/interval), 0)
        sample_skip = max((bufferlen-start)//self.maxSamples, 1)
        times = self.timeBuffer[start::sample_skip]

        for i in range(self.frequencyOffset.size):
            if self.enabledSegments[i]:
                freqs = np.array(self.frequencyBuffers[i][start::sample_skip])
                qfacs = np.array(self.qFactorBuffers[i][start::sample_skip])
                self.frequencyPlotData[i].setData(times, freqs-self.frequencyOffset[i])
                self.qFactorPlotData[i].setData(times, qfacs-self.qFactorOffset[i])
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
