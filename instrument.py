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
        self.commandqueue = queue.Queue()

    def setup(self):
        """Override this to setup the instrument"""

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
        self.setup()
        while self.running:
            while True:
                try:
                    self.commandqueue.get_nowait()(self) # Get and execute command
                except queue.Empty:
                    break
            current_time = time.time()
            elapsed = current_time-self.timestart
            s = self.sample(elapsed)
            if s is not None:
                self.queue.put((current_time, s))
        self.cleanup()

    def start(self, timestart):
        """Start the acquire loop"""
        self.running = True
        self.timestart = timestart
        self.thread.start()

    def stop(self):
        """Stop the acquire loop"""
        self.running = False
        self.thread.join()

    def runcmd(self, command):
        self.commandqueue.put(command)

    def get_samples(self):
        """Retrieve all collected samples from the sample queue"""
        results = []
        while True:
            try:
                results.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return results

    def on_record_start(self):
        """Called when datalogging has started"""
        pass

    def on_record_stop(self):
        """Called when datalogging has stopped"""
        pass

def runlater(func):
    def func_wrapper(self, *args, **kwargs):
        self.runcmd(lambda self: func(self, *args, **kwargs))
    return func_wrapper

class DataWindow(object):

    def start(self):
        """
        Override this to finish configuration

        This is called after the widget has been added to a Window/Tab.
        """
        pass

    def stop(self):
        """
        Override this to set window back to stopped state

        This is called before the window/tab containing this widget is removed.
        """
        pass

    def add_sample(self, time, sample):
        """Override this to add a sample to the window"""
        pass

    def refresh(self):
        """Override this to refresh the window (e.g. update graphs)"""
        pass

class ConfigWindow(object):
    def load_config(self, config):
        """Override this to update the window with the provided configuration"""
        pass

    def get_config(self):
        """Override this to return the current configuration"""
        pass
