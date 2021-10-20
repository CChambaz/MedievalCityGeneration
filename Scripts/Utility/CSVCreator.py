from os import makedirs
from os import path
import decimal

ctx = decimal.Context()
ctx.prec = 10

def float_to_str(f):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')

class CSVFile:
    data: []

    def __init__(self):
        self.data = []

    def AddDataToRow(self, d, id=-1):
        self.data[id].append(d)

    def AddRow(self):
        self.data.append([])

    def SaveFile(self, directoryName, fileName):
        if not path.isdir("{}".format(directoryName)):
            makedirs("{}".format(directoryName))

        with open("{}{}.csv".format(directoryName, fileName), "w") as file:
            for r in self.data:
                if len(r) < len(self.data[0]):
                    continue
                for d in r:
                    v = d
                    if type(d) == float:
                        v = float_to_str(d)
                        v = v.replace('.', ',')
                    file.write("{};".format(v))
                file.write("\n")