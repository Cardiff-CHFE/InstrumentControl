from PyQt5.QtCore import Qt, QVariant, QTime
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.uic import loadUiType
import pyqtgraph as pg
import numpy as np
import array
from utils import float_to_si, getResourcePath
from .driver import lorentz_fn

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

        self.fitPlot = pg.PlotItem(title="Realtime fit")
        self.fitPlot.setLabel("left", "Amplitude")
        self.fitPlot.setLabel("bottom", "Frequency")

        self.measuredPlotData = self.fitPlot.plot(pen='r', connect='finite')
        self.fitPlotData = self.fitPlot.plot(pen='g', connect='finite')

        self.fitGraph.addItem(self.fitPlot, 0, 0)

        segmentCount = len(self.instrument.cfg.segments)
        colours = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        self.frequencyPlotData = []
        self.qFactorPlotData = []
        self.enabledSegments = [True]*segmentCount

        for i in range(segmentCount):
            freq = self.frequencyPlot.plot(pen=colours[i], connect='finite')
            qfac = self.qFactorPlot.plot(pen=colours[i], connect='finite')
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
        self.clearOffset.clicked.connect(self.clearOffsetClicked)
        self.bwOverride.stateChanged.connect(self.bwOverrideChanged)
        self.bwFactor.valueChanged.connect(self.bwFactorChanged)
        self.trackEnable.stateChanged.connect(self.trackEnableChanged)
        self.resetSegments.clicked.connect(self.resetSegmentsPressed)
        self.forceRetrack.clicked.connect(self.forceRetrackPressed)
        self.segmentTable.itemClicked.connect(self.segmentTableClicked)

        if self.instrument.cfg.sample_interval == 0.0:
            self.displayDurationType.setCurrentText('samples')
            self.displayDurationType.setEnabled(False)

        self.lastSample = None
        self.maxSamples = 100
        self.frequencyBuffers = [array.array('f') for n in range(segmentCount)]
        self.qFactorBuffers = [array.array('f') for n in range(segmentCount)]
        self.timeBuffer = array.array('f')
        self.frequencyOffset = np.zeros(segmentCount)
        self.qFactorOffset = np.zeros(segmentCount)

    def zeroOffsetClicked(self):
        if self.lastSample:
            self.frequencyOffset = np.array(self.lastSample.f0, dtype=np.float)
            self.qFactorOffset = np.array(self.lastSample.q, dtype=np.float)

    def clearOffsetClicked(self):
        self.frequencyOffset = np.zeros(len(self.frequencyBuffers), dtype=np.float)
        self.qFactorOffset = np.zeros(len(self.qFactorBuffers), dtype=np.float)

    def bwOverrideChanged(self, state):
        if state == Qt.Checked:
            self.instrument.set_bw_factor_override(self.bwFactor.value())
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
            # if checked:
            #     self.frequencyBuffer[row] = np.nan
            #     self.qFactorBuffer[row] = np.nan
            self.instrument.set_segment_enabled(row, checked)

    def addSample(self, time, sample):
        for freq, frequencyBuffer in zip(sample.f0, self.frequencyBuffers):
            if freq is not None:
                frequencyBuffer.append(freq)
            else:
                frequencyBuffer.append(np.nan)

        for qfac, qFactorBuffer in zip(sample.q, self.qFactorBuffers):
            if qfac is not None:
                qFactorBuffer.append(qfac)
            else:
                qFactorBuffer.append(np.nan)

        self.timeBuffer.append(time)

        self.lastSample = sample

    def refresh(self):
        bufferlen = len(self.timeBuffer)
        if not bufferlen:
            return

        displayDuration = self.displayDuration.value()
        displayType = self.displayDurationType.currentText()
        if displayType == "samples":
            start = max(bufferlen-max(int(displayDuration), 1)-1, 0)
        else:
            if displayType == "minutes":
                displayDuration *= 60.0
            elif displayType == "hours":
                displayDuration *= 60.0*60.0
            interval = self.instrument.cfg.sample_interval
            start = max(bufferlen-int(displayDuration/interval)-1, 0)


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

            freq = self.lastSample.freq[0]
            ampl = self.lastSample.ampl[0]
            f0 = self.lastSample.f0[0]
            bw = self.lastSample.bw[0]
            skew = self.lastSample.skew[0]
            pmax = 10.0**(self.lastSample.il[0]/20.0)

            self.measuredPlotData.setData(freq, 20*np.log10(ampl))
            self.fitPlotData.setData(freq, 20*np.log10(lorentz_fn(freq, f0, bw, pmax, skew)))

