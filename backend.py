import json
import scpi
import visa
import time
import csv
import os


class InstrumentException(Exception):
    pass

class Backend(object):
    def __init__(self):
        self.instrument_drivers = {}
        self.instruments = {}
        self.configuration = {}
        self.data_logger = DataLogger()
        self.logging = False

    def load_configfile(self, path):
        self.path = path
        try:
            with open(os.path.join(path, "config.json")) as fp:
                self.load_config(fp)
        except FileNotFoundError:
            pass
        if not "instruments" in self.config:
            self.config["instruments"] = {}


    def save_configfile(self):
        with open(os.path.join(self.path, "config.json", 'w')) as fp:
            self.save_config(fp)

    def load_config(self, fp):
        self.config = json.load(fp)

    def save_config(self, fp):
        json.dump(self.config, fp, indent=4, separators=(',', ': '))

    def load_instruments(self):
        rm = visa.ResourceManager()
        names = scpi.get_resource_names(rm)

        for name, inst in self.config["instruments"].items():
            driver_cls = self.instrument_drivers[inst["type"]]
            ident = None
            for iden, model in names.items():
                if driver_cls.match_device(model):
                    ident = iden
                    break
            if ident is None:
                raise InstrumentException("Instrument of type '{}' not found".format(inst["type"]))

            self.instruments[name] = driver_cls(rm.open_resource(ident))

    def start(self):
        self.load_instruments()

        for name, inst in self.instruments.items():
            inst.setup(self.config["instruments"][name])

        stime = time.time()
        for name, inst in self.instruments.items():
            inst.start(stime)

    def stop(self):
        for inst in self.instruments.values():
            inst.stop()
        for inst in self.instruments.values():
            inst.cleanup()
        self.instruments = {}

    def start_logging(self, sample_name):
        self.data_logger.open_files(self.instruments.keys(),
                                    os.path.join(self.path, sample_name))
        for name, inst in self.instruments.items():
            self.data_logger.write(name, ["Time (s)"] + inst.get_headers())
        self.logging = True

    def stop_logging(self):
        self.logging = False
        self.data_logger.close_files()

    def process_samples(self, fns):
        for name, inst in self.instruments.items():
            samples = inst.get_samples()
            if self.logging:
                for s in samples:
                    self.data_logger.write(name, [s[0]] + inst.format_sample(s[1]))
            if name in fns:
                for s in samples:
                    fns[name](s[0], s[1])


class DataLogger(object):
    def __init__(self):
        self.files = {}
        self.writers = {}

    def open_files(self, names, path):
        if not os.path.exists(path):
            os.makedirs(path)
        for name in names:
            fp = open(os.path.join(path, name + ".csv"), 'a', newline='')
            self.files[name] = fp
            self.writers[name] = csv.writer(fp)

    def close_files(self):
        for f in self.files.values():
            f.close()
        self.files = {}
        self.writers = {}

    def write(self, name, data):
        self.writers[name].writerow(data)
