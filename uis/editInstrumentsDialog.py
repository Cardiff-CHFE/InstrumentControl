from utils import getResourcePath
from PyQt5.uic import loadUiType
from PyQt5.QtCore import QAbstractProxyModel, Qt
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QFileDialog
import os

from patch import useNativeDialog

EditInstrumentsDialogUI, EditInstrumentsDialogBase = loadUiType(getResourcePath('ui/editInstrumentsDialog.ui'))


class EditInstrumentsDialog(EditInstrumentsDialogBase, EditInstrumentsDialogUI):
    def __init__(self, instrumentConfig, instrumentInfo, configPath, parent=None):
        EditInstrumentsDialogBase.__init__(self, parent)
        self.setupUi(self)

        self.config = instrumentConfig.clone()
        self.instrumentInfo = instrumentInfo
        self.configPath = configPath

        self.loadInstrumentIcons()

        self.instrumentType.addItems(list(value.name for value in self.instrumentInfo.values()))
    
        self.instrumentList.itemDoubleClicked.connect(self.instrumentListDoubleClicked)
        self.datadir.editingFinished.connect(self.datadirEditingFinished)
        self.browseButton.clicked.connect(self.browseButtonClicked)
        self.periodicFlush.stateChanged.connect(self.periodicFlushStateChanged)
        self.addInstrument.clicked.connect(self.addInstrumentClicked)
        self.removeInstrument.clicked.connect(self.removeInstrumentClicked)

        self.datadir.setText(self.config.datadir)
        self.periodicFlush.setChecked(bool(self.config.flush_datafiles))

    def loadInstrumentIcons(self):
        self.instrumentList.clear()
        for key, value in self.config.instruments.items():
            item = QListWidgetItem(key)
            item.setIcon(self.instrumentInfo[type(value)].icon)
            self.instrumentList.addItem(item)

    def instrumentListDoubleClicked(self, item):
        instrumentName = item.text()
        instrumentConfig = self.config.instruments[instrumentName]
        wnd = self.instrumentInfo[type(instrumentConfig)].configWindow(instrumentConfig)
        if wnd.exec_() == QDialog.Accepted:
            self.config.instruments[instrumentName] = wnd.config

    def datadirEditingFinished(self):
        self.config.datadir = self.datadir.text()

    def browseButtonClicked(self):
        dialog = QFileDialog(self, "Data save directory", self.configPath)
        dialog.setFileMode(QFileDialog.DirectoryOnly)
        dialog.setOption(QFileDialog.ShowDirsOnly)
        if not useNativeDialog:
            dialog.setOption(QFileDialog.DontUseNativeDialog)
        if dialog.exec_():
            relpath = os.path.relpath(dialog.selectedFiles()[0], self.configPath)
            self.datadir.setText(relpath)
            self.config.datadir = relpath

    def addInstrumentClicked(self):
        instrumentType = self.instrumentType.currentText()
        instrumentName = self.instrumentName.text()
        try:
            _ = self.config.instruments[instrumentName]
            #TODO show error that name already exists
            return
        except KeyError:
            pass
        defaultConfig = next(value.defaultConfig for value in self.instrumentInfo.values() if value.name == instrumentType)
        config = defaultConfig.clone()
        self.config.instruments[instrumentName] = config
        self.loadInstrumentIcons()

    def removeInstrumentClicked(self):
        current = self.instrumentList.currentItem()
        if current is not None:
            del self.config.instruments[current.text()]
            self.loadInstrumentIcons()
        

    def periodicFlushStateChanged(self, value):
        self.config.flush_datafiles = value == Qt.Checked
        