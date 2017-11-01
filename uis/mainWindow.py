from utils import getResourcePath
from PyQt5.uic import loadUiType
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDataWidgetMapper, QFileDialog
from PyQt5.QtCore import QTimer, QItemSelectionModel, QItemSelection
from keyValueModel import KeyValueModel
from schemaDelegate import SchemaDelegate
import sys

MainWindowUI, MainWindowBase = loadUiType(getResourcePath('ui/mainWindow.ui'))


class MainWindow(MainWindowBase, MainWindowUI):
    def __init__(self, backend, parent=None):
        MainWindowBase.__init__(self, parent)
        self.setupUi(self)

        self.backend = backend
        self.instrumentWindowTypes = {}
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(self.timerTimeout)
        self.actionOpenConfig.triggered.connect(lambda: self.openConfig())
        self.runButton.clicked[bool].connect(self.runButtonClicked)
        self.recordButton.clicked[bool].connect(self.recordButtonClicked)
        self.recordDuration.valueChanged.connect(self.recordDurationChanged)
        self.addSample.clicked.connect(self.addSampleClicked)
        self.removeSample.clicked.connect(self.removeSampleClicked)
        self.moveUp.clicked.connect(self.moveUpClicked)
        self.moveDown.clicked.connect(self.moveDownClicked)
        self.samplesList.clicked.connect(self.updateSampleButtons)

        self.running = False

        if(len(sys.argv) > 1):
            self.openConfig(sys.argv[1])

    def openConfig(self, cfgfile=None):
        if cfgfile is None:
            cfgfile, _ = QFileDialog.getOpenFileName(self, "Select File", filter="Configuration files (*.json)")
        try:
            self.backend.load_configfile(cfgfile)
            self.enableConfigWidgets()
            self.linkConfigWidgets(self.backend.config)
        except (FileNotFoundError, ValueError) as err:
            msg = QtWidgets.QErrorMessage()
            msg.setWindowTitle("Config File Error")
            msg.showMessage(str(err))
            msg.exec_()

    def registerInsturmentType(self, name, wnd):
        self.instrumentWindowTypes[name] = wnd

    def enableConfigWidgets(self):
        self.runButton.setEnabled(True)
        self.samplesList.setEnabled(True)
        self.addSample.setEnabled(True)

    def linkConfigWidgets(self, config):
        self.configModel = KeyValueModel(config)
        parent = self.configModel.indexOf(config.samples, 0)
        self.samplesList.setModel(self.configModel)
        self.sampleListDelegate = SchemaDelegate()
        self.samplesList.setItemDelegate(self.sampleListDelegate)
        self.samplesList.setRootIndex(parent)
        self.samplesList.setModelColumn(1)

    def timerTimeout(self):
        updatefns = {}
        for n in range(self.instrumentTabs.count()):
            updatefns[self.instrumentTabs.tabText(n)] = self.instrumentTabs.widget(n).addSample
        if not self.backend.process_samples(updatefns):
            self.recordButton.setChecked(False)
            self.incrementSample()

        for n in range(self.instrumentTabs.count()):
            self.instrumentTabs.widget(n).refresh()

    def runButtonClicked(self, running):
        if running:
            self.running = True
            self.backend.start()
            for name, cfg in self.backend.config.instruments.items():
                instrument = self.backend.instruments[name]
                widget = self.instrumentWindowTypes[cfg.type_](instrument)
                self.instrumentTabs.addTab(widget, name)
            self.updateTimer.start(500)
            self.updateSampleButtons(self.samplesList.currentIndex())
        else:
            self.running = False
            self.backend.stop()
            self.updateTimer.stop()
            self.recordButton.setEnabled(False)
            self.instrumentTabs.clear()
            self.updateSampleButtons(self.samplesList.currentIndex())

    def recordButtonClicked(self, recording):
        index = self.samplesList.currentIndex()
        if recording:
            text = self.configModel.valueOf(index)
            self.backend.start_logging(text)
        else:
            self.backend.stop_logging()
            self.incrementSample()

    def recordDurationChanged(self, val):
        self.backend.config.record_duration = val

    def addSampleClicked(self):
        samples = self.backend.config.samples
        self.backend.config.samples.append("New sample")
        self.samplesList.setFocus()
        index = self.configModel.indexOf(samples[len(samples)-1], 1)
        self.setSampleIndex(index)

    def removeSampleClicked(self):
        samples = self.backend.config.samples
        index = self.samplesList.currentIndex()
        if index.isValid():
            row = index.row()
            samples.removeChildren(row, 1)

            self.samplesList.setFocus()

            if row >= len(samples):
                row = len(samples)-1
            if row < 0:
                self.updateSampleButtons(index)
                return

            index = self.configModel.indexOf(samples[row], 1)
            self.setSampleIndex(index)

    def moveUpClicked(self):
        samples = self.backend.config.samples
        index = self.samplesList.currentIndex()
        if index.isValid():
            row = index.row()
            if row == 0 or row >= len(samples):
                return
            samples.moveChildren(row, 1, row-1)

            self.samplesList.setFocus()
            index = self.configModel.indexOf(samples[row-1], 1)
            self.setSampleIndex(index)

    def moveDownClicked(self):
        samples = self.backend.config.samples
        index = self.samplesList.currentIndex()
        if index.isValid():
            row = index.row()
            if row+1 >= len(samples):
                return
            samples.moveChildren(row, 1, row+2)

            self.samplesList.setFocus()
            index = self.configModel.indexOf(samples[row+1], 1)
            self.setSampleIndex(index)

    def setSampleIndex(self, index):
        self.samplesList.setCurrentIndex(index)
        self.updateSampleButtons(index)

    def updateSampleButtons(self, index):
        samples = self.backend.config.samples
        row = index.row()
        valid = index.isValid() and row >= 0 and row < len(samples)
        self.recordButton.setEnabled(valid and self.running)
        self.removeSample.setEnabled(valid)
        self.moveUp.setEnabled(valid and row > 0)
        self.moveDown.setEnabled(valid and row < len(samples)-1)

    def incrementSample(self):
        if self.autoIncrementSample.isChecked():
            samples = self.backend.config.samples
            row = self.samplesList.currentIndex().row()
            row += 1
            if row >= len(samples):
                row = 0
            index = self.configModel.indexOf(samples[row], 1)
            self.setSampleIndex(index)

    def closeEvent(self, event):
        self.backend.stop()
        self.updateTimer.stop()
