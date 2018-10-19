from instrument import Instrument, runlater, InstrumentError
from datetime import datetime, timezone, timedelta
import queue

class HaltException(Exception):
    pass

class Driver(Instrument):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.recording = False
        self.res = None

        def pause(delay):
            endtime = datetime.now(timezone.utc) + timedelta(seconds=delay)
            delaytime = delay
            while delaytime > 0:
                try:
                    self.commandqueue.get(timeout=delaytime)(self) # Get and execute command
                except queue.Empty:
                    pass
                self.check_running()
                delaytime = (endtime - datetime.now(timezone.utc)).total_seconds()

        def record_wait(start=True):
            while True:
                try:
                    self.commandqueue.get(timeout=0.2)(self) # Get and execute command
                except queue.Empty:
                    self.check_running()
                if self.recording == start:
                    break

        def log(message):
            sampletime = datetime.now(timezone.utc)
            self.queue.put((sampletime, message))

        self._locals = {'pause': pause, 'record_wait': record_wait, 'log': log}

    @property
    def locals_(self):
        locals_ = {'res': self.res}
        locals_.update(self._locals)
        return locals_

    def _run(self):
        self.setup()
        
        while self.running:
            try:
                exec(self.config.script, globals(), self.locals_)
            except HaltException:
                pass
        self.cleanup()

    def setup(self):
        import visa
        from pyvisa.errors import VisaIOError
        import scpi
        from scpi import onoff
        rm = visa.ResourceManager()
        self.res = scpi.Wrapper(rm.open_resource(self.config.resource))

    def check_running(self):
        if not self.running:
            raise HaltException()

    def cleanup(self):
        self.res.close()

    def get_headers(self):
        return ["message"]

    def format_sample(self, sample):
        return [sample]

    @runlater
    def on_record_start(self):
        self.recording = True

    @runlater
    def on_record_stop(self):
        self.recording = False

    @runlater
    def eval_command(self, command):
        exec(command, globals(), self.locals_)

    def stop(self):
        """Stop the acquire loop"""
        self.running = False
        self.runcmd(self.check_running)
        self.thread.join()