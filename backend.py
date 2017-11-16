import json
import time
import csv
import os
import os.path

class InstrumentException(Exception):
    pass

class Backend(object):
    def __init__(self):
        self.instrument_drivers = {}
        self.instruments = {}
        self.config = None
        self.data_logger = DataLogger()
        self.logging = False

    def set_config(self, value, directory):
        self.config = value
        self.datadir = os.path.normpath(os.path.join(directory, self.config.datadir))

        if self.config.master_instrument == '' and len(self.config.instruments):
            for name, inst in self.config.instruments.items():
                self.config.master_instrument = name
                if inst.type_ == 'vna':
                    break

    def register_instrument(self, name, driver):
        self.instrument_drivers[name] = driver

    def start(self):
        for name, instcfg in self.config.instruments.items():
            driver_cls = self.instrument_drivers[instcfg.type_]
            self.instruments[name] = driver_cls(instcfg)

        stime = time.time()
        for name, inst in self.instruments.items():
            inst.start(stime)

    def stop(self):
        for inst in self.instruments.values():
            inst.stop()
        self.instruments = {}

    def start_logging(self, sample_name):
        exists = self.data_logger.open_files(self.instruments.keys(),
                                    os.path.join(self.datadir, sample_name))
        for ((name, inst), existing) in zip(self.instruments.items(), exists):
            if not existing:
                self.data_logger.write(name, ["Time (s)"] + inst.get_headers())
        self.logging = True
        if self.config.record_duration > 0.0:
            self.log_start = time.time()
        for inst in self.instruments.values():
            inst.on_record_start()

    def stop_logging(self):
        self.logging = False
        self.data_logger.close_files()
        for inst in self.instruments.values():
            inst.on_record_stop()

    def process_samples(self, fns):
        for name, inst in self.instruments.items():
            samples = inst.get_samples()
            if self.logging:
                for s in samples:
                    self.data_logger.write(name, [s[0]] + inst.format_sample(s[1]))
            if name in fns:
                for s in samples:
                    fns[name](s[0], s[1])
        if self.config.record_duration > 0.0 and self.logging:
            if time.time() - self.log_start > self.config.record_duration:
                self.stop_logging()
                return False
        return True


class DataLogger(object):
    def __init__(self):
        self.files = {}
        self.writers = {}

    def open_files(self, names, path):
        exists = []
        if not os.path.exists(path):
            os.makedirs(path)
        for name in names:
            fname = os.path.join(path, name + ".csv")
            if os.path.isfile(fname):
                exists.append(True)
            else:
                exists.append(False)
            fp = open(fname, 'a', newline='')
            self.files[name] = fp
            self.writers[name] = csv.writer(fp)
        return exists

    def close_files(self):
        for f in self.files.values():
            f.close()
        self.files = {}
        self.writers = {}

    def write(self, name, data):
        self.writers[name].writerow(data)
