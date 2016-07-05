import sys
import traceback
import os
import copy

from PyQt4 import QtGui, QtCore

import vna
import dc_power
from backend import Backend

from vna_window import VNAWidget, VNAConfig
from dc_power_window import DCWidget, DCConfig

class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()
        self.setWindowTitle("Instrument Control")

        self.backend = Backend()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.timer_timeout)

        self._load_instruments()
        self._create_controls()
        self._layout_controls()

    def _load_instruments(self):
        # Instrument drivers only control the instruments (no GUI)
        self.backend.instrument_drivers = {
            "vna": vna.VNA,
            "dc": dc_power.DCPower
        }
        # Instrument widgets provide GUI feedback on the instrument state
        self.inst_widgets = {
            "vna": VNAWidget,
            "dc": DCWidget
        }

        # Instrument configurations are GUIs for changing instrument settings
        self.inst_configs = {
            "vna": VNAConfig,
            "dc": DCConfig
        }

    def _create_controls(self):
        self.instrument_list = QtGui.QListWidget()

        self.add_inst_btn = QtGui.QPushButton("Add")
        self.add_inst_btn.setEnabled(False)
        self.add_inst_btn.clicked.connect(self.add_inst_btn_clicked)
        
        self.cfg_inst_btn = QtGui.QPushButton("Configure")
        self.cfg_inst_btn.setEnabled(False)
        self.cfg_inst_btn.clicked.connect(self.cfg_inst_btn_clicked)  
        
        self.del_inst_btn = QtGui.QPushButton("Delete")
        self.del_inst_btn.setEnabled(False)
        self.del_inst_btn.clicked.connect(self.del_inst_btn_clicked)        

        self.run_btn = QtGui.QPushButton("Run experiment")
        self.run_btn.setCheckable(True)
        self.run_btn.setEnabled(False)
        self.run_btn.clicked[bool].connect(self.run_btn_clicked)        

        self.sample_text = QtGui.QLineEdit()
        self.record_btn = QtGui.QPushButton("Record data")
        self.record_btn.setCheckable(True)
        self.record_btn.setEnabled(False)
        self.record_btn.clicked[bool].connect(self.record_btn_clicked)
        
        self.sample_number = QtGui.QSpinBox()
        self.sample_number.setMinimum(1)
        self.sample_number.setEnabled(False)
        self.sample_number.valueChanged.connect(self.sample_number_changed)
        
        self.edit_samples = QtGui.QPushButton("Edit samples")
        self.edit_samples.setEnabled(False)
        self.edit_samples.clicked.connect(self.edit_samples_btn_clicked)

        self.auto_increment = QtGui.QCheckBox("Auto increment")
        self.auto_increment.setChecked(True)
        
        self.record_duration = QtGui.QDoubleSpinBox()
        self.record_duration.setRange(0, 10000)
        self.record_duration.setEnabled(False)
        self.record_duration.valueChanged.connect(self.record_duration_changed)

        self.tabs = QtGui.QTabWidget()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        openAction = QtGui.QAction('&Open config', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.open_folder)
        saveAction = QtGui.QAction('&Save config', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.save_folder)
        #TODO remove to enable saving
        saveAction.setEnabled(False)        
        closeAction = QtGui.QAction('Close', self)
        closeAction.setShortcut('Ctrl+Q')
        closeAction.triggered.connect(self.close)
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(closeAction)

    def _layout_controls(self):
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(QtGui.QLabel("Instruments"))
        vbox.addWidget(self.instrument_list)
        ihbox = QtGui.QHBoxLayout()
        ihbox.addWidget(self.add_inst_btn)
        ihbox.addWidget(self.cfg_inst_btn)
        ihbox.addWidget(self.del_inst_btn)
        vbox.addLayout(ihbox)
        hline = QtGui.QFrame()
        hline.setFrameShape(QtGui.QFrame.HLine)
        hline.setFrameShadow(QtGui.QFrame.Sunken)
        vbox.addWidget(hline)
        vbox.addWidget(self.run_btn)
        hline = QtGui.QFrame()
        hline.setFrameShape(QtGui.QFrame.HLine)
        hline.setFrameShadow(QtGui.QFrame.Sunken)
        vbox.addWidget(hline)
        vbox.addWidget(QtGui.QLabel("Sample number"))
        ihbox = QtGui.QHBoxLayout()
        ihbox.addWidget(self.sample_number)
        ihbox.addWidget(self.edit_samples)
        vbox.addLayout(ihbox)
        vbox.addWidget(self.auto_increment)
        
        vbox.addWidget(QtGui.QLabel("Record duration in seconds (0=forever):"))
        vbox.addWidget(self.record_duration)
        
        vbox.addWidget(QtGui.QLabel("Sample name"))
        vbox.addWidget(self.sample_text)
        vbox.addWidget(self.record_btn)
        

        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.tabs, 1.0)

        window = QtGui.QWidget()
        window.setLayout(hbox)

        self.setCentralWidget(window)
        self.resize(900,500)
        
    def enable_config_widgets(self):
        self.add_inst_btn.setEnabled(True)
        self.cfg_inst_btn.setEnabled(True)
        self.del_inst_btn.setEnabled(True)
        self.run_btn.setEnabled(True)
        self.edit_samples.setEnabled(True)
        self.record_duration.setEnabled(True)
        

    def open_folder(self):
        cfgfile = str(QtGui.QFileDialog.getOpenFileName(self, "Select File", filter="Configuration files (*.json)"))
        self.backend.load_configfile(cfgfile)
        self.enable_config_widgets()
        self.update_gui()

    def save_folder(self):
        self.backend.save_configfile()

    def add_inst_btn_clicked(self):
        pass

    def cfg_inst_btn_clicked(self):
        item = self.instrument_list.currentItem()
        if item is not None:
            cfg = self.backend.config["instruments"][item.text()]
            cfgwnd = ConfigWindow(cfg, self.inst_configs[cfg["type"]]())
            if cfgwnd.exec_() == QtGui.QDialog.Accepted:
                self.backend.config["instruments"][item.text()] = cfgwnd.get_config()

    def del_inst_btn_clicked(self):
        row = self.instrument_list.currentRow()
        item = self.instrument_list.takeItem(row)
        if item is not None:
            del self.backend.config["instruments"][item.text()]
            self.tabs.removeTab(row)

    def update_gui(self):
        self.instrument_list.clear()
        self.instrument_list.addItems(list(self.backend.config["instruments"].keys()))
        self.tabs.clear()
        for name, inst in self.backend.config["instruments"].items():
            self.tabs.addTab(self.inst_widgets[inst["type"]](), name)
        if "samples" in self.backend.config and len(self.backend.config["samples"]) > 0:
            self.sample_number.setMaximum(len(self.backend.config["samples"]))
            self.sample_number.setEnabled(True)
            self.sample_number.setValue(1)
            #Make sure sample_text is updated even if sample_number doesn't change
            self.sample_number_changed(1)
        else:
            self.sample_number.setEnabled(False)            
        self.record_duration.setValue(self.backend.config["record_duration"])
        
    def increment_sample(self):
        if self.auto_increment.isChecked() and "samples" in self.backend.config:
                if self.sample_number.value() < self.sample_number.maximum():
                    self.sample_number.setValue(self.sample_number.value()+1)
                else:
                    self.sample_number.setValue(1)

    def run_btn_clicked(self, running):
        if running:
            self.backend.load_instruments()
            self.backend.start()
            self.timer.start(500)
            for n in range(self.tabs.count()):
                name = self.tabs.tabText(n)
                self.tabs.widget(n).instrument = self.backend.instruments[name]
                self.tabs.widget(n).configure(self.backend.config["instruments"][name])
            self.record_btn.setEnabled(True)
        else:
            self.backend.stop()
            self.timer.stop()
            self.record_btn.setEnabled(False)

    def sample_number_changed(self, val):
        self.sample_text.setText(self.backend.config["samples"][val-1])
        
    def record_duration_changed(self, val):
        self.backend.config["record_duration"] = val

    def record_btn_clicked(self, checked):
        if checked:
            self.backend.start_logging(self.sample_text.text())
        else:
            self.backend.stop_logging()
            self.increment_sample()
                    
    def edit_samples_btn_clicked(self):
        editWnd = EditSamplesWindow(self.backend.config["samples"])
        if editWnd.exec_() == QtGui.QDialog.Accepted:
            self.backend.config["samples"] = editWnd.get_samples()
            self.update_gui()

    def debug_btn_checked(self, state):
        if(state == QtCore.Qt.Checked):
            self.debug_tab = DebugWidget(self)
            self.tabs.insertTab(0, self.debug_tab, "Debug")
        else:
            self.tabs.removeTab(0)
            self.debug_tab = None

    def timer_timeout(self):
        tabfns = {self.tabs.tabText(n): self.tabs.widget(n).add_sample for n in range(self.tabs.count())}
        if not self.backend.process_samples(tabfns):
            self.record_btn.setChecked(False)
            self.increment_sample()

        for n in range(self.tabs.count()):
            self.tabs.widget(n).refresh()

    def closeEvent(self, event):
        self.backend.stop()
        self.timer.stop()


class DebugWidget(QtGui.QWidget):
    def __init__(self, app_window):
        super(DebugWidget, self).__init__()
        self.app_window = app_window
        self.locals = {}

        vbox = QtGui.QVBoxLayout()

        self.output_txt = QtGui.QTextEdit()
        self.output_txt.setReadOnly(True)
        vbox.addWidget(self.output_txt)

        self.input_cmd = QtGui.QComboBox()
        self.input_cmd.setEditable(True)
        self.input_cmd.lineEdit().returnPressed.connect(self.input_cmd_return)
        vbox.addWidget(self.input_cmd)

        self.setLayout(vbox)

    def run_cmd(self, cmd):
        self.output_txt.append(">>> " + cmd)
        try:
            res = repr(eval(cmd, globals(), self.locals))
            self.output_txt.append(res)
        except SyntaxError:
            try:
                exec(cmd, globals(), self.locals)
            except Exception as ex:
                self.output_txt.append(traceback.format_exc())
        except Exception as ex:
            self.output_txt.append(traceback.format_exc())

    def input_cmd_return(self):
        cmd = self.input_cmd.currentText()
        self.input_cmd.setEditText("")
        self.run_cmd(cmd)

class ConfigWindow(QtGui.QDialog):
    def __init__(self, config, cfgwidget):
        super(ConfigWindow, self).__init__()
        self.setWindowTitle("Instrument Config")
        self.cfgwidget = cfgwidget
        self.cfgwidget.load_config(copy.deepcopy(config))

        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        self.ok = QtGui.QPushButton("Ok")
        self.ok.clicked.connect(self.accept)
        self.cancel = QtGui.QPushButton("Cancel")
        self.cancel.clicked.connect(self.reject)

    def _layout_controls(self):
    
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1.0)
        hbox.addWidget(self.ok)
        hbox.addWidget(self.cancel)
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.cfgwidget, 1.0)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        
    def get_config(self):
        return self.cfgwidget.get_config()
        
class EditSamplesWindow(QtGui.QDialog):
    def __init__(self, samples):
        super(EditSamplesWindow, self).__init__()
        self._create_controls()
        self._layout_controls()
        
        self.sample_list.addItems(samples)
        
    def _create_controls(self):
        self.sample_list = QtGui.QListWidget()
        
        self.ok = QtGui.QPushButton("Ok")
        self.ok.clicked.connect(self.accept)
        self.cancel = QtGui.QPushButton("Cancel")
        self.cancel.clicked.connect(self.reject)
        
        self.add_sample_btn = QtGui.QPushButton("Add Sample")
        self.add_sample_btn.clicked.connect(self.add_sample_btn_clicked)
        self.rename_sample_btn = QtGui.QPushButton("Rename Sample")
        self.rename_sample_btn.clicked.connect(self.rename_sample_btn_clicked)
        self.remove_sample_btn = QtGui.QPushButton("Remove Sample")
        self.remove_sample_btn.clicked.connect(self.remove_sample_btn_clicked)
        
        self.move_up_btn = QtGui.QPushButton("Move sample up")
        self.move_up_btn.clicked.connect(self.move_up_btn_clicked)
        self.move_down_btn = QtGui.QPushButton("Move sample down")
        self.move_down_btn.clicked.connect(self.move_down_btn_clicked)
        
    def _layout_controls(self):                
        vbox = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.sample_list)
        ivbox = QtGui.QVBoxLayout()
        ivbox.addWidget(self.add_sample_btn)
        ivbox.addWidget(self.rename_sample_btn)
        ivbox.addWidget(self.remove_sample_btn)        
        ivbox.addStretch(1.0)
        ivbox.addWidget(self.move_up_btn)
        ivbox.addWidget(self.move_down_btn)
        hbox.addLayout(ivbox)
        vbox.addLayout(hbox)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1.0)
        hbox.addWidget(self.ok)
        hbox.addWidget(self.cancel)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        
    def add_sample_btn_clicked(self):
        text, ok = QtGui.QInputDialog.getText(self, 'Sample name input',  'Sample name:')
        
        if ok:
            self.sample_list.addItem(text)
        
    def rename_sample_btn_clicked(self):
        item = self.sample_list.currentItem()
        if item:
            text, ok = QtGui.QInputDialog.getText(self, 'Rename sample',  'New sample name:')
            if ok:
                item.setText(text)
        
    def remove_sample_btn_clicked(self):
        row = self.sample_list.currentRow()
        if row >= 0:
            item = self.sample_list.takeItem(row)
        
    def move_up_btn_clicked(self):
        row = self.sample_list.currentRow()
        if row > 0:
            item = self.sample_list.takeItem(row)
            self.sample_list.insertItem(row-1, item)
            self.sample_list.setCurrentRow(row-1)
        
    def move_down_btn_clicked(self):
        row = self.sample_list.currentRow()
        if row >= 0 and row < self.sample_list.count()-1:
            item = self.sample_list.takeItem(row)
            self.sample_list.insertItem(row+1, item)
            self.sample_list.setCurrentRow(row+1)
        
    def get_samples(self):
        return [self.sample_list.item(i).text() for i in range(self.sample_list.count())]
    
    
if __name__ == "__main__":
    qApp = QtGui.QApplication(sys.argv)
    wnd = ApplicationWindow()
    wnd.show()
    sys.exit(qApp.exec_())
