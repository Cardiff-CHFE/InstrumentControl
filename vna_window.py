from PyQt4 import QtGui, QtCore

from collections import deque
import pyqtgraph as pg
import numpy as np
from vna import lorentz_fn
from instrument import DataWindow, ConfigWindow

class VNAWidget(QtGui.QWidget, DataWindow):
    def __init__(self):
        super().__init__()
        self._create_controls()
        self._layout_controls()

        self.freq_plotdata = []
        self.qfac_plotdata = []

        #Create queues
        self.sample_count = 40
        self.freq_queue = None
        self.qfac_queue = None
        self.last_freq = None
        self.last_qfac = None
        self.f_offset = None
        self.q_offset = None
        self.sample_queue = None
        self.colours = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        self.sample_roll = 0;
        self.sample_n = 0;

    def _create_controls(self):
        self.graph = pg.GraphicsLayoutWidget()
        self.freq_plot = pg.PlotItem(title="Frequency")
        self.freq_plot.setLabel("left", "change in Frequency", "Hz")
        self.freq_plot.setLabel("bottom", "Sample", "")

        self.qfac_plot = pg.PlotItem(title="Q factor")
        self.qfac_plot.setLabel("left", "change in Q factor")
        self.qfac_plot.setLabel("bottom", "Sample", "")

        # self.track_plot = pg.PlotItem(title="Tracking")
        # self.track_plot.setLabel("left", "Amplitude", "dB")
        # self.track_plot.setLabel("bottom", "Frequency", "Hz")
        # self.track_plotdata = self.track_plot.plot(pen="m")
        # self.track_plotdata_calc = self.track_plot.plot(pen="c")

        self.zero_btn = QtGui.QPushButton("Zero offset")
        self.zero_btn.clicked.connect(self.zero_btn_clicked)
        
        self.bw_override = QtGui.QCheckBox("Bandwidth factor override")
        self.bw_override.stateChanged.connect(self.bw_override_changed)
        
        self.bw_factor = QtGui.QDoubleSpinBox()
        self.bw_factor.setRange(1.5, 1000)
        self.bw_factor.valueChanged.connect(self.bw_factor_changed)
        
        self.track_enable = QtGui.QCheckBox("Enable Tracking")
        self.track_enable.setChecked(True)
        self.track_enable.stateChanged.connect(self.track_enable_changed)
        
        self.reset_tracking = QtGui.QPushButton("Reset Tracking")
        self.reset_tracking.clicked.connect(self.reset_tracking_pressed)

        self.segment_list = QtGui.QTableWidget()
        self.segment_list.itemClicked.connect(self.segment_list_clicked)

    def _layout_controls(self):
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.graph, 8)
        self.graph.addItem(self.freq_plot, 0,0)
        self.graph.addItem(self.qfac_plot, 1,0)
        # self.graph.addItem(self.track_plot, 0,1,2,1)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.zero_btn)
        vbox.addWidget(self.bw_override)
        vbox.addWidget(self.bw_factor)
        vbox.addWidget(self.track_enable)
        vbox.addWidget(self.reset_tracking)
        vbox.addWidget(self.segment_list)
        vbox.addStretch()
        hbox.addLayout(vbox, 2)
        self.setLayout(hbox)

    def zero_btn_clicked(self):
        if self.last_sample:
            self.f_offset = np.array(self.last_sample.f0, dtype=np.float)
            self.q_offset = np.array(self.last_sample.q, dtype=np.float)

    def set_channel_count(self, count):
        #for pdata in self.freq_plotdata:
        self.freq_plot.clear()
        #for pdata in self.qfac_plotdata:
        self.qfac_plot.clear()

        self.freq_plotdata = [self.freq_plot.plot(pen=self.colours[n]) for n in range(count)]
        self.qfac_plotdata = [self.qfac_plot.plot(pen=self.colours[n]) for n in range(count)]
        self.freq_queue = np.zeros((count, self.sample_count))
        self.qfac_queue = np.zeros((count, self.sample_count))
        self.sample_queue = np.zeros(self.sample_count)
        self.f_offset = np.zeros(count)
        self.q_offset = np.zeros(count)
        self.last_sample = None
        self.sample_roll = 0;
        self.sample_n = 0;

    def configure(self, config):
        self.set_channel_count(len(config["segments"]))
        self.segment_list.clear()
        
        # Create list of segments sorted by frequency. This is to match
        # the ordering in the recorded samples.
        segments = []
        for n, s in config["segments"].items():
            segments.append((n, s["f0"]))
        segments.sort(key=lambda seg: seg[1])
        
        seg_headings = [s[0] for s in segments]
        self.segment_list.setRowCount(len(seg_headings))
        self.segment_list.setColumnCount(4)        
        self.segment_list.setVerticalHeaderLabels(seg_headings)
        self.segment_list.setHorizontalHeaderLabels(["Enabled", "F0 (GHz)", "Q factor", "Insertion loss (dB)"])
        for row, item in enumerate(seg_headings):
            checkbox = QtGui.QTableWidgetItem()
            checkbox.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            checkbox.setCheckState(QtCore.Qt.Checked)
            self.segment_list.setItem(row, 0, checkbox)
            for col in range(3):
                self.segment_list.setItem(row, col+1, QtGui.QTableWidgetItem("0.0"))
        self.segment_list.resizeColumnsToContents()
        self.segment_list.resizeRowsToContents()

    def add_sample(self, time, sample):
        freq = np.array(sample.f0, dtype=np.float)
        qfac = np.array(sample.q, dtype=np.float)
        self.raw_ampl = sample.ampl
        self.raw_freq = sample.freq
        
        self.freq_queue[:,self.sample_roll] = freq
        self.qfac_queue[:,self.sample_roll] = qfac

        self.sample_queue[self.sample_roll] = self.sample_n
        self.sample_n += 1
        self.sample_roll += 1
        if self.sample_roll == self.sample_count:
            self.sample_roll = 0
        self.last_sample = sample

    def refresh(self):
        freq_queue = np.roll(self.freq_queue, -self.sample_roll, axis=1)
        qfac_queue = np.roll(self.qfac_queue, -self.sample_roll, axis=1)
        sample_queue = np.roll(self.sample_queue, -self.sample_roll)

        for i in range(self.f_offset.size):
            self.freq_plotdata[i].setData(sample_queue, freq_queue[i]-self.f_offset[i])
            self.qfac_plotdata[i].setData(sample_queue, qfac_queue[i]-self.q_offset[i])
                

        if self.last_sample:
            for row, f in enumerate(self.last_sample.f0):
                if f is not None:
                    self.segment_list.item(row, 1).setText("{:g}".format(f/1e9))
            for row, q in enumerate(self.last_sample.q):
                if q is not None:
                    self.segment_list.item(row, 2).setText("{:g}".format(q))
            for row, il in enumerate(self.last_sample.il):
                if il is not None:
                    self.segment_list.item(row, 3).setText("{:g}".format(il))

            # self.track_plotdata.setData(self.raw_freq[0],20*np.log10(self.raw_ampl[0]))
            # q = self.last_sample.q[0]
            # f0 = self.last_sample.f0[0]
            # il = self.last_sample.il[0]
            # minf = self.raw_freq[0][0]
            # maxf = self.raw_freq[0][-1]
            # span = np.linspace(minf,maxf,100)
            # ampl = 20*np.log10(lorentz_fn(span,f0,f0/q,10**(il/20)))
            # self.track_plotdata_calc.setData(span,ampl)
            
    def bw_override_changed(self, state):
        if state == QtCore.Qt.Checked:
            self.instrument.set_bw_factor_override(self.bw_factor.value())
        else:
            self.instrument.set_bw_factor_override(None)
            
    def bw_factor_changed(self, val):
        if self.bw_override.checkState() == QtCore.Qt.Checked:
            self.instrument.set_bw_factor_override(val)
            
    def track_enable_changed(self, state):
        self.instrument.set_tracking_override(state == QtCore.Qt.Checked)
        self.bw_override.setEnabled(state == QtCore.Qt.Checked)
            
    def segment_list_clicked(self, tableItem):
        if self.segment_list.column(tableItem) == 0:
            row = self.segment_list.row(tableItem)
            checked = tableItem.checkState() == QtCore.Qt.Checked
            print("row {} is {}".format(row, "checked" if checked else "unchecked"))
            self.instrument.set_segment_enabled(row, checked)
            
    def reset_tracking_pressed(self):
        self.instrument.reset_tracking()

class VNAConfig(QtGui.QTabWidget, ConfigWindow):
    def __init__(self):
        super().__init__()
        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        self.general_tab = QtGui.QWidget()
        self.modes_tab = VNAModesWidget()
        self.calculations_tab = QtGui.QWidget()

    def _layout_controls(self):
        self.addTab(self.general_tab, "General")
        self.addTab(self.modes_tab, "Modes")
        self.addTab(self.calculations_tab, "Calculations")
        
    def load_config(self, config):
        self.config = config
        self.modes_tab.load_modes(self.config["segments"])
        
    def get_config(self):
        return self.config
        
class VNAModesWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()
        self._create_controls()
        self._layout_controls()

    def _create_controls(self):
        self.mode_list = QtGui.QListWidget()
        self.mode_list.currentItemChanged.connect(self.list_item_changed)
        self.add_mode_btn = QtGui.QPushButton("Add")
        self.add_mode_btn.clicked.connect(self.add_mode_btn_clicked)
        self.remove_mode_btn = QtGui.QPushButton("Remove")
        self.remove_mode_btn.clicked.connect(self.remove_mode_btn_clicked)
        self.load_mode_btn = QtGui.QPushButton("Load")
        self.load_mode_btn.clicked.connect(self.load_mode_btn_clicked)
        self.mode_name_txt = QtGui.QLineEdit()
        self.mode_name_txt.editingFinished.connect(self.mode_name_txt_finish)
        self.f0_spinbox = QtGui.QDoubleSpinBox()
        self.f0_spinbox.setRange(0.0, 99.0)
        self.f0_spinbox.setDecimals(5)
        self.f0_spinbox.valueChanged.connect(self.f0_spinbox_changed)
        self.span_spinbox = QtGui.QDoubleSpinBox()
        self.span_spinbox.setRange(0.0, 100000.0)
        self.span_spinbox.setDecimals(3)
        self.span_spinbox.valueChanged.connect(self.span_spinbox_changed)
        
    def _layout_controls(self):
        hbox = QtGui.QHBoxLayout()
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mode_list)
        ihbox = QtGui.QHBoxLayout()
        ihbox.addWidget(self.add_mode_btn)
        ihbox.addWidget(self.remove_mode_btn)
        ihbox.addWidget(self.load_mode_btn)
        vbox.addLayout(ihbox)        
        hbox.addLayout(vbox)
        
        groupBox = QtGui.QGroupBox("Mode settings")
        ivbox = QtGui.QVBoxLayout()
        ivbox.addWidget(QtGui.QLabel("Mode name"))
        ivbox.addWidget(self.mode_name_txt)
        ivbox.addWidget(QtGui.QLabel("Frequency (GHz)"))
        ivbox.addWidget(self.f0_spinbox)
        ivbox.addWidget(QtGui.QLabel("Span (KHz)"))
        ivbox.addWidget(self.span_spinbox)  
        ivbox.addStretch(1.0)
        
        groupBox.setLayout(ivbox)
        hbox.addWidget(groupBox)
        
        self.setLayout(hbox)
        
    def load_modes(self, modes):
        self.modes = modes
        self.mode_list.clear()
        self.mode_list.addItems(list(modes.keys()))
        self.mode_name_txt.setEnabled(False)
        self.f0_spinbox.setEnabled(False)
        self.span_spinbox.setEnabled(False)
        
        
    def list_item_changed(self, current, previous):
        if current:
            self.mode_name_txt.setEnabled(True)
            self.f0_spinbox.setEnabled(True)
            self.span_spinbox.setEnabled(True)
            
            text = current.text()
            self.mode_name_txt.setText(text)
            self.f0_spinbox.setValue(self.modes[text]["f0"]/1e9)
            self.span_spinbox.setValue(self.modes[text]["span"]/1e3)
            
        else:
            self.mode_name_txt.setEnabled(False)
            self.f0_spinbox.setEnabled(False)
            self.v.setEnabled(False)
            
        
    def add_mode_btn_clicked(self):
        i = 1
        while "Mode {}".format(i) in self.modes.keys():
            i+=1
        modename = "Mode {}".format(i)
        self.modes[modename] = {
            "f0": 2.5E+09,
            "span": 50E+06,
            "points": 101,
            "ifbw": 10e3,
            "power": 0.0,
            "gnmp": 0.0
        }
        self.mode_list.addItem(modename)
        
        
    def remove_mode_btn_clicked(self):
        pass
        
    def load_mode_btn_clicked(self):
        pass
        
    def mode_name_txt_finish(self):
        newtxt = self.mode_name_txt.text()
        if not newtxt in self.modes.keys():
            self.modes[newtxt] = self.modes.pop(self.mode_list.currentItem().text())
            self.mode_list.currentItem().setText(newtxt)
        elif self.mode_list.currentItem().text() != newtxt:
            existsErr = QtGui.QErrorMessage()
            existsErr.showMessage("Mode with the same name already exists")
            self.mode_name_txt.setText(self.mode_list.currentItem().text())
            
    def f0_spinbox_changed(self, val):
        self.modes[self.mode_list.currentItem().text()]["f0"] = val*1e9
        
    def span_spinbox_changed(self, val):
        self.modes[self.mode_list.currentItem().text()]["span"] = val*1e3
