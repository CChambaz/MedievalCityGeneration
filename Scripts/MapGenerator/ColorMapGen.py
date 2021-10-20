import numpy as np
import Utility.MCUtil as MCUtil
import Utility.Colors as Colors


def MapToColorMap(map, dimensionX, dimensionZ):
    Colors.InitRGBColorsDictionary()
    colorMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    for x in range(dimensionX):
        for z in range(dimensionZ):
            currentColor = Colors.rgbColors[MCUtil.TerrainTypeColor[map[x][z][0]]]
            colorMap[x][z][0] = currentColor[0]
            colorMap[x][z][1] = currentColor[1]
            colorMap[x][z][2] = currentColor[2]

    return colorMap