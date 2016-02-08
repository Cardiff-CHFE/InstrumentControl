from instrument import Instrument
import scpi
from scpi import onoff
import math
import time
import copy
from collections import deque

class DCPower(Instrument):
    def __init__(self, resource):
        super().__init__()
        self.res = scpi.Wrapper(resource)
        self.cfg = {}

    @staticmethod
    def match_device(devname):
        model = devname.split(",")[1].strip()
        return model == "E3631A"

    def setup(self, config):
        self.cfg = DCConfig(config)
        self.channel = 1
        self.voltages = [0]*self.cfg.channels
        self.currents = [0]*self.cfg.channels
        self.output = False

    def sample(self, elapsed):
        if len(self.cfg.commands):
            cmd = self.cfg.commands.popleft()
            cmd.run(self)
        else:
            time.sleep(1.0)
        return [self.voltages, self.currents, self.output]

    def cleanup(self):
        self.res.write(":OUTP:STAT {}", onoff(False))
        self.res.close()
        pass

    def get_headers(self):
        """Override this to return a list of logfile headers"""
        headers = ["Voltage {} (V)".format(n) for n in range(self.cfg.channels)]
        headers += ["Current {} (A)".format(n) for n in range(self.cfg.channels)]
        headers += ["State"]
        return headers

    def format_sample(self, sample):
        """Override this for convert samples into a list for logging"""
        return sample[0] + sample[1] + [sample[2]]

    def set_channel(self, channel):
        if self.channel != channel:
            self.res.write(":INST:NSEL {}", channel)
            self.channel = channel

    def set_voltage(self, voltage):
        self.res.write(":SOUR:VOLT {}", voltage)
        self.voltages[self.channel-1] = voltage

    def set_current(self, current):
        self.res.write(":SOUR:CURR {}", current)
        self.currents[self.channel-1] = current

    def set_output(self, state):
        self.res.write(":OUTP {}", onoff(state))
        self.output = state


class DCConfig(object):
    def __init__(self, config):
        self.channels = config["channels"]

        cmds = copy.deepcopy(config["commands"])
        self.commands = deque()
        for cmd in cmds:
            action = cmd["cmd"]
            del cmd["cmd"]
            if action == "voltage":
                self.commands.append(SetVoltageCommand(**cmd))
            elif action == "current":
                self.commands.append(SetCurrentCommand(**cmd))
            elif action == "output":
                self.commands.append(SetOutputCommand(**cmd))
            elif action == "wait":
                self.commands.append(WaitCommand(**cmd))


class SetVoltageCommand(object):
    def __init__(self, voltage, channel=None):
        self.voltage = voltage
        self.channel = channel

    def run(self, inst):
        if self.channel is not None:
            inst.set_channel(self.channel)
        inst.set_voltage(self.voltage)

class SetCurrentCommand(object):
    def __init__(self, voltage, channel=None):
        self.voltage = voltage
        self.channel = channel

    def run(self, inst):
        if self.channel is not None:
            inst.set_channel(self.channel)
        inst.set_current(self.voltage)

class SetOutputCommand(object):
    def __init__(self, state):
        self.state = state

    def run(self, inst):
        inst.set_output(self.state)

class WaitCommand(object):
    def __init__(self, duration):
        self.duration = duration

    def run(self, inst):
        time.sleep(self.duration)
