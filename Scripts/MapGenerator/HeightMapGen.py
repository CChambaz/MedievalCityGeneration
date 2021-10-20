import numpy as np


def MapToHeightMap(map, dimensionX, dimensionZ):
    heightMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)
    maxHeight = 0
    minHeight = 255

    # Define the maximum and minimum height
    for x in range(dimensionX):
        for z in range(dimensionZ):
            currentHeight = map[x][z][1]

            if currentHeight > maxHeight:
                maxHeight = currentHeight

            if currentHeight < minHeight:
                minHeight = currentHeight



    # Clamp the heights values between 0 and 255
    for x in range(dimensionX):
        for z in range(dimensionZ):
            newHeight = ((map[x][z][1] - minHeight) * 255) / (maxHeight - minHeight)
            heightMap[x][z] = [newHeight, newHeight, newHeight]

    return heightMap