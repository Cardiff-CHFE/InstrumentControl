from instrument import Instrument, runlater
import math
import random
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import linregress
import time
import copy


class InstrumentError(RuntimeError):
    pass


class E5071X:
    def __init__(self, config):
        global VisaIOError, onoff
        import visa
        from pyvisa.errors import VisaIOError
        import scpi
        from scpi import onoff
        rm = visa.ResourceManager()
        self.res = scpi.Wrapper(rm.open_resource(config.resource))

    def supports_markers(self):
        return True

    def setup(self, use_markers):
        self.res.reset()
        self.res.write(":CALC1:PAR1:DEF {}", "S21")
        self.res.write(":INIT1:CONT {}", onoff(True))

        if not use_markers:
            self.res.write(":TRIG:SOUR BUS")
        self.res.write(":SENS1:SWE:TYPE {}", "SEGM")
        self.res.write(":SENS1:SWE:DELAY {}", 0.001)
        self.res.write(":SENS1:SWE:GEN {}", "STEP")
        if use_markers:
            self.res.write(":CALC1:MARK:BWID {}", onoff(True))
            self.res.write(":CALC1:MARK:FUNC:MULT:TYPE {}", "PEAK")
            self.res.write(":CALC1:MARK:FUNC:EXEC")
            self.res.write(":CALC1:MARK:FUNC:MULT:TRAC {}", onoff(True))

    def set_segments(self, segments):
        enacount = 0
        # [<buf>,<stim>,<ifbw>,<pow>,<del>,<time>,<segm>]
        data = [5, 1, 1, 1, 0, 0, None]
        for s in segments:
            if s.enabled:
                enacount += 1
                data += [s.f0, s.span, s.points, s.ifbw, s.power]
        data[6] = enacount
        self.res.write_ascii_values(":SENS1:SEGM:DATA", data)

    def autoscale(self):
        self.res.write(":DISP:WIND1:TRAC1:Y:AUTO")

    def trigger(self, use_markers, force=False):
        if use_markers and force:
            # Force complete trigger
            self.res.write(":TRIG:SOUR BUS")

        if (not use_markers) or force:
            self.res.write(":TRIG:SING")
            self.res.query("*OPC?")

        if use_markers and force:
            # Reset back to default
            self.res.write(":TRIG:SOUR INT")

    def get_marker_data(self, marker=1, channel=1):
        try:
            return self.res.query_ascii_values(":CALC{}:MARK{}:BWID:DATA?", channel, marker)
        except VisaIOError:
            raise InstrumentError()

    def get_sweep_data(self):
        data = self.res.query_ascii_values(":CALC1:DATA:SDAT?")
        return np.array(data).reshape((-1, 2)).T

    def get_freq_data(self, channel=1):
        return self.res.query_ascii_values(":SENS{}:FREQ:DATA?", channel)

    def cleanup(self):
        self.res.close()


class N5232A:
    def __init__(self, config):
        import visa
        from pyvisa.errors import VisaIOError
        import scpi
        from scpi import onoff
        rm = visa.ResourceManager()
        self.res = scpi.Wrapper(rm.open_resource(config.resource))

    def supports_markers(self):
        return False

    def setup(self, use_markers):
        self.res.reset()
        if use_markers:
            raise ValueError("N5232A currently does not support markers")
        self.res.write(":CALC1:PAR1:DEF {}", "S21")
        self.res.write(":INIT1:CONT {}", onoff(True))
        if not use_markers:
            self.res.write(":TRIG:SOUR MAN")
        self.res.write(":SENS1:SWE:TYPE {}", "SEGM")
        self.res.write(":SENS1:SWE:DELAY {}", 0.001)
        self.res.write(":SENS1:SWE:GEN {}", "STEP")

    def set_segments(self, segments, channel=1):
        enacount = 0
        data = ["SSTOP", None]
        for s in segments:
            if s.enabled:
                enacount += 1
                data += [1, s.points, s.f0, s.span, s.ifbw, 0, s.power]
        data[1] = enacount

        self.res.write(":SENS{}:SEGM:BWID:CONT {}", channel, onoff(True))
        self.res.write(":SENS{}:SEGM:POW:CONT {}", channel, onoff(True))
        self.res.write_ascii_values(":SENS{}:SEGM:LIST", data, channel)

    def autoscale(self):
        self.res.write(":DISP:WIND1:TRAC1:Y:AUTO")

    def trigger(self, use_markers, force=False):
        if use_markers and force:
            # Force complete trigger
            self.res.write(":TRIG:SOUR MAN")

        if (not use_markers) or force:
            self.res.write(":INIT:IMM")
            self.res.query("*OPC?")

        if use_markers and force:
            # Reset back to default
            self.res.write(":TRIG:SOUR INT")

    def get_marker_data(self, marker=1, channel=1):
        raise NotImplementedError()

    def get_sweep_data(self):
        data = self.res.query_ascii_values(":CALC1:DATA? SDAT")
        return np.array(data).reshape((-1, 2)).T

    def get_freq_data(self):
        return self.res.query_ascii_values(":CALC1:X?")

    def cleanup(self):
        self.res.close()


class S2VNA:
    def __init__(self, config):
        import pythoncom, win32com.client
        pythoncom.CoInitialize()
        self.app = win32com.client.Dispatch('S2VNA.application')
        if not self.app.Ready:
            for i in range(1, 21):
                time.sleep(1)
                print("Connection attempt {}".format(i))
                if self.app.Ready:
                    break
        if not self.app.Ready:
            raise RuntimeError("Instrument was not ready in time")

    def supports_markers(self):
        return False

    def setup(self, use_markers):
        self.app.scpi.system.preset()
        self.app.scpi.trigger.sequence.source = "bus"
        self.app.scpi.GetCALCulate(1).GetPARameter(1).define = 'S21'
        self.app.scpi.GetINITiate(1).continuous = True
        self.app.scpi.GetSENSe(1).sweep.type = 'segment'
        self.app.scpi.GetSENSe(1).sweep.point.time = 0.001
        self.app.scpi.display.GetWINDow(1).X.spacing = 'obase'
        # self.res.write(":SENS1:SWE:GEN {}", "STEP") # TODO find me if I exist

    def set_segments(self, segments, channel=1):
        enacount = 0
        # [<buf>,<stim>,<ifbw>,<pow>,<del>,<time>,<segm>]
        data = [5, 1, 1, 1, 0, 0, None]
        for s in segments:
            if s.enabled:
                enacount += 1
                data += [s.f0, s.span, s.points, s.ifbw, s.power]
        data[6] = enacount
        self.app.scpi.GetSENSe(1).segment.data = data

    def autoscale(self):
        pass

    def trigger(self, use_markers, force=False):
        self.app.scpi.trigger.sequence.SINGle()

    def get_marker_data(self, marker=1, channel=1):
        raise NotImplementedError()

    def get_sweep_data(self):
        data = self.app.scpi.GetCALCulate(1).selected.data.sdata
        return np.array(data).reshape((-1, 2)).T

    def get_freq_data(self):
        return self.app.scpi.GetSENSe(1).frequency.data

    def cleanup(self):
        del self.app


class Simulated:
    def __init__(self, config):
        self.segments = []
        self.modes = [
            (2.5e9, 500e3),
            (4.529E+09, 300e3),
        ]

    def supports_markers(self):
        return False

    def setup(self, use_markers):
        pass

    def set_segments(self, segments, channel=1):
        self.segments = [segment.copy() for segment in segments]

    def autoscale(self):
        pass

    def trigger(self, use_markers, force=False):
        time.sleep(0.1)

    def get_marker_data(self, marker=1, channel=1):
        raise NotImplementedError()

    def get_sweep_data(self):
        frequencies = self.get_freq_data()
        amplitudes = np.zeros((2, len(frequencies)))

        idx = 0
        for segment in self.segments:
            if segment.enabled:
                freqs = frequencies[idx:idx+segment.points]
                amplitudes[1][idx:idx+segment.points] = 0.0
                for mode in self.modes:
                    f0 = random.gauss(mode[0], mode[1]/50.0)
                    bw = random.gauss(mode[1], mode[1]/50.0)
                    real = lorentz_fn(freqs, f0, bw, 0.05)
                    amplitudes[0][idx:idx+segment.points] += real
                idx += segment.points
        return amplitudes

    def get_freq_data(self):
        enabled_pts = 0
        for segment in self.segments:
            if segment.enabled:
                enabled_pts += segment.points

        frequencies = np.zeros(enabled_pts)
        idx = 0
        for segment in self.segments:
            if segment.enabled:
                start = segment.f0-(segment.span/2.0)
                stop = segment.f0+(segment.span/2.0)
                frequencies[idx:idx+segment.points] = np.linspace(start, stop, segment.points)
                idx += segment.points
        return frequencies

    def cleanup(self):
        pass

class Driver(Instrument):
    def __init__(self, config):
        super().__init__()
        self.forced_retrack = False
        self.config = config
        self.cfg = VNAState(config)

    def setup(self):
        if self.config.model == 'N5232A':
            self.driver = N5232A(self.config)
        elif self.config.model == 'E5071X':
            self.driver = E5071X(self.config)
        elif self.config.model == 'S2VNA':
            self.driver = S2VNA(self.config)
        elif self.config.model == 'simulated':
            self.driver = Simulated(self.config)

        if not self.driver.supports_markers():
            self.cfg.use_markers = False

        self.driver.setup(self.cfg.use_markers)
        self.driver.set_segments(self.cfg.segments)
        time.sleep(1.0)
        self.driver.autoscale()
        self.last_sample = None

    def sample(self, elapsed):
        self.driver.trigger(self.cfg.use_markers)

        data = Sample()
        if self.cfg.use_markers:
            try:
                for i in range(len(self.cfg.segments)):
                    bw, f0, q, il = self.driver.get_marker_data(i+1)
                    data.add_segment(bw, f0, q, il)
            except InstrumentError:
                return None

            # Discard duplicate samples
            if self.last_sample:
                if self.last_sample == data:
                    return None
            self.last_sample = data
        else:
            cplx = self.driver.get_sweep_data()
            ampl = np.sqrt(cplx[0]**2 + cplx[1]**2)
            freq = self.driver.get_freq_data()

            start = 0
            lost_track = False
            for seg in self.cfg.segments:
                if seg.enabled:
                    f = freq[start:seg.points+start]
                    a = ampl[start:seg.points+start]
                    start += seg.points
                    try:
                        bw, f0, q, il = lorentz_fit(f,a)
                        data.add_segment(bw, f0, q, il, f, a)
                    except (RuntimeError, ValueError):
                        lost_track = True
                        if self.cfg.track_freq and self.cfg.track_enabled:
                            slope, intercept, rvalue, pvalue, stderr = linregress(f, a)
                            if(slope > 0):
                                seg.f0 += seg.span
                            else:
                                seg.f0 -= seg.span
                else: #segment not enabled
                    data.add_segment(None, None, None, None)

            if lost_track:
                if self.cfg.track_freq and self.cfg.track_enabled:
                    self.driver.set_segments(self.cfg.segments)
                return None

        tracking_enabled = self.cfg.track_freq or self.cfg.track_span
        if tracking_enabled and (self.cfg.track_enabled or self.forced_retrack):
            retracked = False
            for seg, f0, bw in zip(self.cfg.segments, data.f0, data.bw):
                if not seg.enabled:
                    continue
                trackf, tracks = track_window(seg.f0, seg.span, f0, bw,
                                              bw_factor=self.cfg.get_bw_factor())
                if (trackf and self.cfg.track_freq) or (tracks and self.cfg.track_span) or self.forced_retrack:
                    retracked = True
                    if self.cfg.track_freq:
                        seg.f0 = f0
                    if self.cfg.track_span:
                        seg.span = bw*self.cfg.get_bw_factor()
            if retracked:
                self.forced_retrack = False
                self.driver.set_segments(self.cfg.segments)
                self.driver.trigger(self.cfg.use_markers, force=True)

        return data

    def cleanup(self):
        self.driver.cleanup()

    def get_headers(self):
        h = ["Frequency {}/Hz".format(s.name) for s in self.cfg.segments]
        h += ["Q factor {}".format(s.name) for s in self.cfg.segments]
        h += ["Insertion loss {}/dB".format(s.name) for s in self.cfg.segments]
        return h

    def format_sample(self, data):
        return data.f0 + data.q + data.il

    @runlater
    def set_segment_enabled(self, segment, enabled):
        self.cfg.segments[segment].enabled = enabled
        self.driver.set_segments(self.cfg.segments)

    @runlater
    def set_bw_factor_override(self, factor):
        self.cfg.bw_factor_override = factor

    @runlater
    def set_tracking_override(self, enabled):
        self.cfg.track_enabled = enabled

    @runlater
    def reset_segments(self):
        for segment in self.cfg.segments:
            segment.f0 = segment.f0_default
            segment.span = segment.span_default
        self.driver.set_segments(self.cfg.segments)

    @runlater
    def force_retrack(self):
        self.forced_retrack = True

class VNAState(object):
    def __init__(self, config):
        self.segments = []
        for n, s in config.segments.items():
            self.segments.append(Segment(n, s.f0, s.span, s.points,
                                         s.ifbw, s.power))
        self.segments.sort(key=lambda seg: seg.f0)
        self.track_freq = config.track_frequency
        self.track_span = config.track_span
        self.use_markers = config.use_markers
        self.bw_factor = config.bandwidth_factor
        self.bw_factor_override = None
        self.track_enabled = True

    def get_bw_factor(self):
        if self.bw_factor_override is not None:
            return self.bw_factor_override
        else:
            return self.bw_factor


class Segment(object):
    def __init__(self, name, f0=2.495e9, span=50e6, points=51, ifbw=1000, power=0):
        self.name = name
        self.f0 = self.f0_default = f0
        self.span = self.span_default = span
        self.points = points
        self.ifbw = ifbw
        self.power = power
        self.enabled = True

    def copy(self):
        copy = Segment(self.name, self.f0_default, self.span_default,
                       self.points, self.ifbw, self.power)
        copy.enabled = self.enabled
        copy.f0 = self.f0
        copy.span = self.span
        return copy


class Sample(object):
    def __init__(self):
        self.bw = []
        self.f0 = []
        self.q = []
        self.il = []
        self.freq = []
        self.ampl = []

    def add_segment(self, bw, f0, q, il, freq=None, ampl=None):
        self.bw.append(bw)
        self.f0.append(f0)
        self.q.append(q)
        self.il.append(il)
        self.freq.append(freq)
        self.ampl.append(ampl)

    def __eq__(self, other):
        if self.bw != other.bw:
            return False
        if self.f0 != other.f0:
            return False
        if self.q != other.q:
            return False
        if self.il != other.il:
            return False
        if self.freq != other.freq:
            return False
        if self.ampl != other.ampl:
            return False
        return True


def track_window(center, span, f0, bw, center_err=0.8,
                 span_err=0.3, bw_factor=8.0):
    ferr = math.fabs(center-f0) + bw/2 #Ensure +- bw markers stay within
                                       #center_err of window
    retrackf = ferr > span*center_err*0.5

    retracks = (bw*bw_factor)/span > 1 + span_err
    retracks = retracks or span/(bw*bw_factor) > 1 + span_err
    return retrackf, retracks

def lorentz_fn(x, f0, bw, pmax):
    return pmax/np.sqrt(1 + (4*((x-f0)/bw)**2))

def lorentz_fit(freq, ampl, f0=0.5, bw=0.5, pmax=1.0):

    freq = np.array(freq)
    ampl = np.array(ampl)
    maxa = np.max(ampl)
    norma = ampl/maxa
    weights = norma*norma

    minf = np.min(freq)
    maxf = np.max(freq)
    fspan = maxf-minf
    normf = (freq-minf)/fspan
    a1=0.0
    (f0, bw, pmax), pcov = curve_fit(lorentz_fn, normf, norma,
                                     (f0, bw, pmax))
    f0 = (f0*fspan)+minf
    bw = np.fabs(bw)*fspan
    pmax = 20*np.log10(pmax*maxa)
    return bw, f0, f0/bw, pmax
