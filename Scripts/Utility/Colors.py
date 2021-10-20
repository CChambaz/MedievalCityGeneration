import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

hexColors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
rgbColors = dict()


def InitRGBColorsDictionary():
    for i in hexColors:
        if len(i) > 1:
            rgbColors[i] = HexToRGB(hexColors[i])


def PrintColors():
    print("--------------- Color list ---------------")
    print("colorList = [")
    for i in hexColors:
        print("\"{}\",".format(i))
    print("]")

    print("--------------- Hex values ---------------")
    for i in hexColors:
        print("{} = {}".format(i, hexColors[i]))

    print("--------------- RGB values ---------------")
    for i in rgbColors:
        print("{} = {}".format(i, rgbColors[i]))


def HexToRGB(hex):
    hex = hex.lstrip('#')
    hlen = len(hex)
    return tuple(int(hex[i:i + hlen // 3], 16) for i in range(0, hlen, hlen // 3))
