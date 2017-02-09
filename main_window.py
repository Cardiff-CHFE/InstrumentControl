import sys
import traceback
import os
import copy

from PyQt5 import QtWidgets, QtCore

import vna
import dc_power
from backend import Backend

from vna_window import VNAWidget, VNAConfigWindow
from dc_power_window import DCWidget, DCConfigWindow

class ApplicationWindow(QtWidgets.QMainWindow):
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
            "vna": VNAConfigWindow,
            "dc": DCConfigWindow
        }

    def _create_controls(self):
        """Create all the QT controls"""
        self.instrument_list = QtWidgets.QListWidget()

        self.add_inst_btn = QtWidgets.QPushButton("Add")
        self.add_inst_btn.setEnabled(False)
        self.add_inst_btn.clicked.connect(self.add_inst_btn_clicked)

        self.cfg_inst_btn = QtWidgets.QPushButton("Configure")
        self.cfg_inst_btn.setEnabled(False)
        self.cfg_inst_btn.clicked.connect(self.cfg_inst_btn_clicked)

        self.del_inst_btn = QtWidgets.QPushButton("Delete")
        self.del_inst_btn.setEnabled(False)
        self.del_inst_btn.clicked.connect(self.del_inst_btn_clicked)

        self.run_btn = QtWidgets.QPushButton("Run experiment")
        self.run_btn.setCheckable(True)
        self.run_btn.setEnabled(False)
        self.run_btn.clicked[bool].connect(self.run_btn_clicked)

        self.sample_text = QtWidgets.QLineEdit()
        self.record_btn = QtWidgets.QPushButton("Record data")
        self.record_btn.setCheckable(True)
        self.record_btn.setEnabled(False)
        self.record_btn.clicked[bool].connect(self.record_btn_clicked)

        self.sample_number = QtWidgets.QSpinBox()
        self.sample_number.setMinimum(1)
        self.sample_number.setEnabled(False)
        self.sample_number.valueChanged.connect(self.sample_number_changed)

        self.edit_samples = QtWidgets.QPushButton("Edit samples")
        self.edit_samples.setEnabled(False)
        self.edit_samples.clicked.connect(self.edit_samples_btn_clicked)

        self.auto_increment = QtWidgets.QCheckBox("Auto increment")
        self.auto_increment.setChecked(True)

        self.record_duration = QtWidgets.QDoubleSpinBox()
        self.record_duration.setRange(0, 10000)
        self.record_duration.setEnabled(False)
        self.record_duration.valueChanged.connect(self.record_duration_changed)

        self.tabs = QtWidgets.QTabWidget()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        #Open configuration file menu option
        openAction = QtWidgets.QAction('&Open config', self)
        openAction.setShortcut('Ctrl+O')
        openAction.triggered.connect(self.open_config)
        #Save configuration file menu option
        saveAction = QtWidgets.QAction('&Save config', self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.triggered.connect(self.save_config)
        #TODO remove to enable saving
        saveAction.setEnabled(False)
        #Reload configuration file menu option. Disabled at startup
        self.reloadAction = QtWidgets.QAction('&Reload config', self)
        self.reloadAction.setShortcut('Ctrl+R')
        self.reloadAction.triggered.connect(self.reload_config)
        self.reloadAction.setEnabled(False)
        #Close menu option
        closeAction = QtWidgets.QAction('Close', self)
        closeAction.setShortcut('Ctrl+Q')
        closeAction.triggered.connect(self.close)
        #Add all actions to file menu
        fileMenu.addAction(openAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(self.reloadAction)
        fileMenu.addAction(closeAction)

    def _layout_controls(self):
        """Position controls within the window"""
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(QtWidgets.QLabel("Instruments"))
        vbox.addWidget(self.instrument_list)
        ihbox = QtWidgets.QHBoxLayout()
        ihbox.addWidget(self.add_inst_btn)
        ihbox.addWidget(self.cfg_inst_btn)
        ihbox.addWidget(self.del_inst_btn)
        vbox.addLayout(ihbox)
        hline = QtWidgets.QFrame()
        hline.setFrameShape(QtWidgets.QFrame.HLine)
        hline.setFrameShadow(QtWidgets.QFrame.Sunken)
        vbox.addWidget(hline)
        vbox.addWidget(self.run_btn)
        hline = QtWidgets.QFrame()
        hline.setFrameShape(QtWidgets.QFrame.HLine)
        hline.setFrameShadow(QtWidgets.QFrame.Sunken)
        vbox.addWidget(hline)
        vbox.addWidget(QtWidgets.QLabel("Record duration in seconds (0=forever):"))
        vbox.addWidget(self.record_duration)
        hline = QtWidgets.QFrame()
        hline.setFrameShape(QtWidgets.QFrame.HLine)
        hline.setFrameShadow(QtWidgets.QFrame.Sunken)
        vbox.addWidget(hline)
        vbox.addWidget(QtWidgets.QLabel("Sample number"))
        ihbox = QtWidgets.QHBoxLayout()
        ihbox.addWidget(self.sample_number)
        ihbox.addWidget(self.edit_samples)
        vbox.addLayout(ihbox)
        vbox.addWidget(self.auto_increment)
        vbox.addWidget(QtWidgets.QLabel("Sample name"))
        vbox.addWidget(self.sample_text)
        vbox.addWidget(self.record_btn)


        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.tabs, 1.0)

        window = QtWidgets.QWidget()
        window.setLayout(hbox)

        self.setCentralWidget(window)
        self.resize(900,500)

    def enable_config_widgets(self):
        """
        Enable buttons to modify configuration settings.

        This is typically called when a configuration file has been loaded
        """
        self.add_inst_btn.setEnabled(True)
        self.cfg_inst_btn.setEnabled(True)
        self.del_inst_btn.setEnabled(True)
        self.run_btn.setEnabled(True)
        self.edit_samples.setEnabled(True)
        self.record_duration.setEnabled(True)
        self.reloadAction.setEnabled(True)


    def open_config(self):
        cfgfile, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", filter="Configuration files (*.json)")
        try:
            self.backend.load_configfile(cfgfile)
            self.enable_config_widgets()
            self.update_gui()
        except (FileNotFoundError, ValueError) as err:
            msg = QtWidgets.QErrorMessage()
            msg.setWindowTitle("Config File Error")
            msg.showMessage(str(err))
            msg.exec_()


    def save_config(self):
        self.backend.save_configfile()

    def reload_config(self):
        cfgfile = self.backend.configfile
        self.backend.load_configfile(cfgfile)
        self.update_gui()

    def add_inst_btn_clicked(self):
        """Add instrument button click handler"""
        pass

    def cfg_inst_btn_clicked(self):
        """Configure instrument button click handler"""
        item = self.instrument_list.currentItem()
        if item is not None:
            cfg = self.backend.config["instruments"][item.text()]
            cfgwnd = ConfigWindow(cfg, self.inst_configs[cfg["type"]]())
            if cfgwnd.exec_() == QtWidgets.QDialog.Accepted:
                self.backend.config["instruments"][item.text()] = cfgwnd.get_config()

    def del_inst_btn_clicked(self):
        """delete instrument button click handler"""
        row = self.instrument_list.currentRow()
        item = self.instrument_list.takeItem(row)
        if item is not None:
            del self.backend.config["instruments"][item.text()]
            self.tabs.removeTab(row)

    def update_gui(self):
        """Resets the user interface with the new configuration"""
        self.instrument_list.clear()
        self.instrument_list.addItems(list(self.backend.config["instruments"].keys()))
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
        """Auto-increment the sample number if enabled in the gui"""
        if self.auto_increment.isChecked() and "samples" in self.backend.config:
                if self.sample_number.value() < self.sample_number.maximum():
                    self.sample_number.setValue(self.sample_number.value()+1)
                else:
                    self.sample_number.setValue(1)

    def run_btn_clicked(self, running):
        """Start/stop the running of the instruments"""
        if running:
            self.backend.load_instruments()
            self.backend.start()
            for name, icfg in self.backend.config["instruments"].items():
                inst = self.backend.instruments[name]
                widget = self.inst_widgets[icfg["type"]](inst)
                self.tabs.addTab(widget, name)
                widget.start()


            self.timer.start(500)
            self.record_btn.setEnabled(True)
        else:
            self.backend.stop()
            self.timer.stop()
            self.record_btn.setEnabled(False)
            for n in range(self.tabs.count()):
                self.tabs.widget(n).stop()
            self.tabs.clear()

    def sample_number_changed(self, val):
        self.sample_text.setText(self.backend.config["samples"][val-1])

    def record_duration_changed(self, val):
        self.backend.config["record_duration"] = val

    def record_btn_clicked(self, checked):
        """Enable/disable recording of samples to file"""
        if checked:
            self.backend.start_logging(self.sample_text.text())
        else:
            self.backend.stop_logging()
            self.increment_sample()

    def edit_samples_btn_clicked(self):
        """Display window to edit list of samples names"""
        editWnd = EditSamplesWindow(self.backend.config["samples"])
        if editWnd.exec_() == QtWidgets.QDialog.Accepted:
            self.backend.config["samples"] = editWnd.get_samples()
            self.update_gui()

    def debug_btn_checked(self, state):
        """Add debugging tab. Currently not fully implemented"""
        if(state == QtCore.Qt.Checked):
            self.debug_tab = DebugWidget(self)
            self.tabs.insertTab(0, self.debug_tab, "Debug")
        else:
            self.tabs.removeTab(0)
            self.debug_tab = None

    def timer_timeout(self):
        """Update gui with live instrument information"""
        tabfns = {self.tabs.tabText(n): self.tabs.widget(n).add_sample for n in range(self.tabs.count())}
        if not self.backend.process_samples(tabfns):
            self.record_btn.setChecked(False)
            self.increment_sample()

        for n in range(self.tabs.count()):
            self.tabs.widget(n).refresh()

    def closeEvent(self, event):
        self.backend.stop()
        self.timer.stop()


class DebugWidget(QtWidgets.QWidget):
    def __init__(self, app_window):
        super(DebugWidget, self).__init__()
        self.app_window = app_window
        self.locals = {}

        vbox = QtWidgets.QVBoxLayout()

        self.output_txt = QtWidgets.QTextEdit()
        self.output_txt.setReadOnly(True)
        vbox.addWidget(self.output_txt)

        self.input_cmd = QtWidgets.QComboBox()
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

class ConfigWindow(QtWidgets.QDialog):
    """
    Generic configuration window.

    Instruments must provide a widget that also implements the methods of
    ConfigWindow in the instrument module.

    """
    def __init__(self, config, cfgwidget):
        super(ConfigWindow, self).__init__()
        self.setWindowTitle("Instrument Config")
        self.cfgwidget = cfgwidget
        self.cfgwidget.load_config(copy.deepcopy(config))

        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        self.ok = QtWidgets.QPushButton("Ok")
        self.ok.clicked.connect(self.accept)
        self.cancel = QtWidgets.QPushButton("Cancel")
        self.cancel.clicked.connect(self.reject)

    def _layout_controls(self):

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1.0)
        hbox.addWidget(self.ok)
        hbox.addWidget(self.cancel)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.cfgwidget, 1.0)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def get_config(self):
        return self.cfgwidget.get_config()

class EditSamplesWindow(QtWidgets.QDialog):
    def __init__(self, samples):
        super(EditSamplesWindow, self).__init__()
        self._create_controls()
        self._layout_controls()

        self.sample_list.addItems(samples)

    def _create_controls(self):
        self.sample_list = QtWidgets.QListWidget()

        self.ok = QtWidgets.QPushButton("Ok")
        self.ok.clicked.connect(self.accept)
        self.cancel = QtWidgets.QPushButton("Cancel")
        self.cancel.clicked.connect(self.reject)

        self.add_sample_btn = QtWidgets.QPushButton("Add Sample")
        self.add_sample_btn.clicked.connect(self.add_sample_btn_clicked)
        self.rename_sample_btn = QtWidgets.QPushButton("Rename Sample")
        self.rename_sample_btn.clicked.connect(self.rename_sample_btn_clicked)
        self.remove_sample_btn = QtWidgets.QPushButton("Remove Sample")
        self.remove_sample_btn.clicked.connect(self.remove_sample_btn_clicked)

        self.move_up_btn = QtWidgets.QPushButton("Move sample up")
        self.move_up_btn.clicked.connect(self.move_up_btn_clicked)
        self.move_down_btn = QtWidgets.QPushButton("Move sample down")
        self.move_down_btn.clicked.connect(self.move_down_btn_clicked)

    def _layout_controls(self):
        vbox = QtWidgets.QVBoxLayout()

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.sample_list)
        ivbox = QtWidgets.QVBoxLayout()
        ivbox.addWidget(self.add_sample_btn)
        ivbox.addWidget(self.rename_sample_btn)
        ivbox.addWidget(self.remove_sample_btn)
        ivbox.addStretch(1.0)
        ivbox.addWidget(self.move_up_btn)
        ivbox.addWidget(self.move_down_btn)
        hbox.addLayout(ivbox)
        vbox.addLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1.0)
        hbox.addWidget(self.ok)
        hbox.addWidget(self.cancel)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def add_sample_btn_clicked(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'Sample name input',  'Sample name:')

        if ok:
            self.sample_list.addItem(text)

    def rename_sample_btn_clicked(self):
        item = self.sample_list.currentItem()
        if item:
            text, ok = QtWidgets.QInputDialog.getText(self, 'Rename sample',  'New sample name:')
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
    qApp = QtWidgets.QApplication(sys.argv)
    wnd = ApplicationWindow()
    wnd.show()
    sys.exit(qApp.exec_())
