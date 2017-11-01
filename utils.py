from collections import OrderedDict

si_prefixes = OrderedDict([
    ('Y', 1e24),
    ('Z', 1e21),
    ('E', 1e18),
    ('P', 1e15),
    ('T', 1e12),
    ('G', 1e9),
    ('M', 1e6),
    ('k', 1e3),
    ('', 1.0),
    ('m', 1e-3),
    ('u', 1e-6),
    ('n', 1e-9),
    ('p', 1e-12),
    ('f', 1e-15),
    ('a', 1e-18),
    ('z', 1e-21),
    ('y', 1e-24)
])


def float_to_si(value, precision=4):
    if value < 0:
        prefix = "-"
        value = -value
    else:
        prefix = ""

    for s, exp in si_prefixes.items():
        result = value / exp
        if 0.9999999 <= result < 1000.0:
            return "{0}{1:.{2}f}{3}".format(prefix, result, precision, s)
    return "{}0.0".format(prefix)


def si_to_float(string):
    try:
        exp = si_prefixes[string[-1]]
        return float(string[:-1])*exp
    except KeyError:
        return float(string)
    except IndexError:
        return 0.0
