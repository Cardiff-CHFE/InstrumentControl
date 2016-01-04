
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

class DebugResource:
    def query(cmd):
        print("SCPI query: " + cmd)
        return ""

    def query_ascii_values(cmd, **kwargs):
        print("SCPI query_ascii_values: " + cmd)
        return [1,2,3]

    def query_binary_values(cmd, **kwargs):
        print("SCPI query_binary_values: " + cmd)
        return [1,2,3]

    def write(cmd):
        print("SCPI write: " + cmd)

    def write_ascii_values(cmd, values, **kwargs):
        print("SCPI write_ascii_values: " + cmd)

    def write_binary_values(cmd, values, **kwargs):
        print("SCPI write_binary_values: " + cmd)
