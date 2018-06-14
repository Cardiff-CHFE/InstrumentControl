import json
import time
import csv
import os
import os.path
import itertools
from datetime import datetime, timedelta, timezone

class InstrumentException(Exception):
    pass

class Backend(object):
    def __init__(self):
        self.instrument_drivers = {}
        self.instruments = {}
        self.config = None
        self.data_logger = None
        self.logging = False
        self.config_dir = None

    def set_config(self, value, directory):
        self.config = value
        self.config_dir = directory

        if self.config.master_instrument == '' and len(self.config.instruments):
            for name, inst in self.config.instruments.items():
                self.config.master_instrument = name
                if inst.type_ == 'vna':
                    break

    def register_instrument(self, name, driver):
        self.instrument_drivers[name] = driver

    def start(self):
        self.data_logger = DataLogger(self.config.flush_datafiles)

        for name, instcfg in self.config.instruments.items():
            driver_cls = self.instrument_drivers[instcfg.type_]
            self.instruments[name] = driver_cls(instcfg)

        self.start_time = datetime.now(timezone.utc)
        for name, inst in self.instruments.items():
            inst.start()

    def stop(self):
        for inst in self.instruments.values():
            inst.stop()
        self.instruments = {}
        if self.logging:
            self.stop_logging()
        self.data_logger = None

    def start_logging(self, sample_name):
        datadir = os.path.normpath(os.path.join(self.config_dir, self.config.datadir))
        exists = self.data_logger.open_files(self.instruments.keys(), datadir, sample_name)
        for ((name, inst), existing) in zip(self.instruments.items(), exists):
            if not existing:
                self.data_logger.write(name, ["Timestamp", "Time (s)"] + inst.get_headers())
        self.logging = True
        self.log_time = None
        if self.config.record_samples > 0:
            self.remaining_samples = self.config.record_samples
        else:
            self.remaining_samples = -1
        for inst in self.instruments.values():
            inst.on_record_start()

    def stop_logging(self):
        if not self.logging:
            return
        self.logging = False
        self.data_logger.close_files()
        for inst in self.instruments.values():
            inst.on_record_stop()

    def process_samples(self, fns):
        for name, inst in self.instruments.items():
            samples = inst.get_samples()
            if self.logging:
                for s in samples:
                    if self.remaining_samples != 0 or name != self.config.master_instrument:
                        if name == self.config.master_instrument:
                            self.remaining_samples -= 1
                            if self.log_time is None:
                                self.log_time = s[0]
                        self.data_logger.write(name, itertools.chain([s[0].timestamp(), (s[0]-self.log_time).total_seconds()], inst.format_sample(s[1])))
                    
            if name in fns:
                for s in samples:
                    fns[name]((s[0]-self.start_time).total_seconds(), s[1])

        if self.logging and self.remaining_samples == 0:
            self.stop_logging()
            return False

        if self.config.record_duration > 0.0 and self.logging:
            if (datetime.now(timezone.utc) - self.log_time).total_seconds() > self.config.record_duration:
                self.stop_logging()
                return False
        return True


class DataLogger(object):
    def __init__(self, doflush):
        self.files = {}
        self.writers = {}
        self.last_write = {}
        self.doflush = doflush
        self.flushinterval = 10.0 # Seconds

    def open_files(self, names, datadir, sample_name):
        exists = []
        if not os.path.exists(datadir):
            os.makedirs(datadir)
        for name in names:
            fname = os.path.join(datadir, sample_name)
            fname += '_' + name + ".csv"
            if os.path.isfile(fname):
                exists.append(True)
            else:
                exists.append(False)
            fp = open(fname, 'a', newline='')
            self.files[name] = fp
            self.writers[name] = csv.writer(fp)
            self.last_write[name] = time.time()
        return exists

    def close_files(self):
        for f in self.files.values():
            f.close()
        self.files = {}
        self.writers = {}

    def write(self, name, data):
        self.writers[name].writerow(data)
        if self.doflush and (time.time() - self.last_write[name] > self.flushinterval):
            self.last_write[name] += self.flushinterval
            fh = self.files[name]
            fh.flush()
            os.fsync(fh.fileno())
