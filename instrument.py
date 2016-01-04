import queue
import threading
import time

def get_resource_names(rm):
    resources = rm.list_resources()
    resnames = {}
    for ident in resources:
        handle = rm.open_resource(ident)
        resnames[ident] = handle.query("*IDN?")
        handle.close()
    return resnames

def onoff(b):
    return "ON" if b else "OFF"

class Wrapper(object):
    """Handy wrapper to make SCPI commands easier to write"""
    def __init__(self, resource):
        self.res = resource

    def reset(self):
        return self.res.write("*RST")

    def query(self, cmd, *args, **kwargs):
        return self.res.query(cmd.format(*args, **kwargs))

    def query_ascii_values(self, cmd, *args, **kwargs):
        return self.res.query_ascii_values(cmd.format(*args, **kwargs))

    def write_ascii_values(self, cmd, data, *args, **kwargs):
        self.res.write(cmd.format(*args, **kwargs) + " " + ",".join([str(x) for x in data]))
        #self.res.write_ascii_values(cmd.format(*args, **kwargs), data)

    def write(self, cmd, *args, **kwargs):
        self.res.write(cmd.format(*args, **kwargs))

    def close(self):
        self.res.close()

class Instrument(object):
    def __init__(self):
        self.queue = queue.Queue()
        self.running = False
        self.thread = threading.Thread(target=self._run)

    @staticmethod
    def match_device(devname):
        """Override this to determine if an instrument is the correct type"""
        return False

    def setup(self, config):
        """Override this to initialize the instrument"""

    def sample(self, elapsed):
        """Override this to acquire/write a sample"""
        return []

    def cleanup(self):
        """Override this to close the instrument cleanly"""

    def get_headers(self):
        """Override this to return a list of logfile headers"""
        return []

    def format_sample(self, sample):
        """Override this for convert samples into a list for logging"""
        return []

    def _run(self):
        while self.running:
            elapsed = time.time()-self.timestart
            s = self.sample(elapsed)
            if s is not None:
                self.queue.put((elapsed, s))

    def start(self, timestart):
        """Start the acquire loop"""
        self.running = True
        self.timestart = timestart
        self.thread.start()

    def stop(self):
        """Stop the acquire loop"""
        self.running = False
        self.thread.join()

    def get_samples(self):
        """Retrieve all collected samples from the sample queue"""
        results = []
        while True:
            try:
                results.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return results
