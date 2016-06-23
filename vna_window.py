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

        #Create deques
        self.freq_queue = []
        self.qfac_queue = []
        self.last_freq = None
        self.last_qfac = None
        self.f_offset = []
        self.q_offset = []
        self.time_queue = deque()
        self.timespan = 10.0
        self.colours = ['r', 'g', 'b', 'c', 'm', 'y', 'w']

    def _create_controls(self):
        self.graph = pg.GraphicsLayoutWidget()
        self.freq_plot = pg.PlotItem(title="Frequency")
        self.freq_plot.setLabel("left", "change in Frequency", "Hz")
        self.freq_plot.setLabel("bottom", "Time", "s")

        self.qfac_plot = pg.PlotItem(title="Q factor")
        self.qfac_plot.setLabel("left", "change in Q factor")
        self.qfac_plot.setLabel("bottom", "Time", "s")

        # self.track_plot = pg.PlotItem(title="Tracking")
        # self.track_plot.setLabel("left", "Amplitude", "dB")
        # self.track_plot.setLabel("bottom", "Frequency", "Hz")
        # self.track_plotdata = self.track_plot.plot(pen="m")
        # self.track_plotdata_calc = self.track_plot.plot(pen="c")

        self.zero_btn = QtGui.QPushButton("Zero offset")
        self.zero_btn.clicked.connect(self.zero_btn_clicked)

        self.segment_list = QtGui.QTableWidget()


    def _layout_controls(self):
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.graph, 8)
        self.graph.addItem(self.freq_plot, 0,0)
        self.graph.addItem(self.qfac_plot, 1,0)
        # self.graph.addItem(self.track_plot, 0,1,2,1)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.zero_btn)
        vbox.addWidget(self.segment_list)
        vbox.addStretch()
        hbox.addLayout(vbox, 2)
        self.setLayout(hbox)

    def zero_btn_clicked(self):
        if self.last_sample:
            self.f_offset = self.last_sample.f0
            self.q_offset = self.last_sample.q

    def set_channel_count(self, count):
        #for pdata in self.freq_plotdata:
        self.freq_plot.clear()
        #for pdata in self.qfac_plotdata:
        self.qfac_plot.clear()


        self.freq_plotdata = [self.freq_plot.plot(pen=self.colours[n]) for n in range(count)]
        self.qfac_plotdata = [self.qfac_plot.plot(pen=self.colours[n]) for n in range(count)]
        self.freq_queue = [deque() for n in range(count)]
        self.qfac_queue = [deque() for n in range(count)]
        self.time_queue.clear()
        self.f_offset = [0.0 for n in range(count)]
        self.q_offset = [0.0 for n in range(count)]
        self.last_sample = None

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
        self.segment_list.setColumnCount(3)        
        self.segment_list.setVerticalHeaderLabels(seg_headings)
        self.segment_list.setHorizontalHeaderLabels(["F0 (GHz)", "Q factor", "Insertion loss (dB)"])
        for row, item in enumerate(seg_headings):
            for col in range(3):
                self.segment_list.setItem(row, col, QtGui.QTableWidgetItem("0.0"))
        self.segment_list.resizeColumnsToContents()
        self.segment_list.resizeRowsToContents()

    def add_sample(self, time, sample):
        freq = sample.f0
        qfac = sample.q
        self.raw_ampl = sample.ampl
        self.raw_freq = sample.freq
        for f, queue, offset in zip(freq, self.freq_queue, self.f_offset):
            queue.append(f-offset)
        for q, queue, offset in zip(qfac, self.qfac_queue, self.q_offset):
            queue.append(q-offset)
        self.time_queue.append(time)
        self.last_sample = sample

        while self.time_queue[-1]-self.time_queue[0] > self.timespan:
            self.time_queue.popleft()
            for queue in self.freq_queue:
                queue.popleft()
            for queue in self.qfac_queue:
                queue.popleft()

    def refresh(self):
        for pdata, queue in zip(self.freq_plotdata, self.freq_queue):
            pdata.setData(self.time_queue, queue)
        for pdata, queue in zip(self.qfac_plotdata, self.qfac_queue):
            pdata.setData(self.time_queue, queue)

        if self.last_sample:
            for row, f in enumerate(self.last_sample.f0):
                self.segment_list.item(row, 0).setText("{:g}".format(f/1e9))
            for row, q in enumerate(self.last_sample.q):
                self.segment_list.item(row, 1).setText("{:g}".format(q))
            for row, il in enumerate(self.last_sample.il):
                self.segment_list.item(row, 2).setText("{:g}".format(il))
                #self.segment_list.item(row, 0).setText(str())
        #    for i, f in enumerate(self.last_sample.f0):
        #        self.freq_list.item(i).setText(self.seg_headings[i] + ": {:5g}".format(f))
        #    for i, q in enumerate(self.last_sample.q):
        #        self.qfac_list.item(i).setText(self.seg_headings[i] + ": {:5g}".format(q))

            # self.track_plotdata.setData(self.raw_freq[0],20*np.log10(self.raw_ampl[0]))
            # q = self.last_sample.q[0]
            # f0 = self.last_sample.f0[0]
            # il = self.last_sample.il[0]
            # minf = self.raw_freq[0][0]
            # maxf = self.raw_freq[0][-1]
            # span = np.linspace(minf,maxf,100)
            # ampl = 20*np.log10(lorentz_fn(span,f0,f0/q,10**(il/20)))
            # self.track_plotdata_calc.setData(span,ampl)

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
