import numpy as np
import Utility.MCUtil as MCUtil

propagationStrenght = 50
propagationStrenghtLose = 2

def GetPrintableWaterAccessMap(map, dimensionX, dimensionZ):
    waterAccessMap = MapToWaterAccessMap(map, dimensionX, dimensionZ)
    printableWaterAccessMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    for x in range(dimensionX):
        for z in range(dimensionZ):
            printableWaterAccessMap[x][z] = [waterAccessMap[x][z], 0, 0]

    return printableWaterAccessMap

def MapToWaterAccessMap(map, dimensionX, dimensionZ):
    waterAccessMap = np.zeros((dimensionZ, dimensionX, 1), np.uint8)

    # Apply the propagation from each cell that is water
    for x in range(dimensionX):
        for z in range(dimensionZ):
            if map[x][z][0] == MCUtil.BlocType['WATER']:
                waterAccessMap = PropagateFromCell(map, waterAccessMap, dimensionX, dimensionZ, x, z)

    # Get maximum and minimum values
    maxValue = waterAccessMap.max()
    minValue = waterAccessMap.min()

    # Graduate the map values between 0 and 255
    for x in range(dimensionX):
        for z in range(dimensionZ):
            newValue = 0
            if minValue != 0:
                newValue = ((waterAccessMap[x][z][0] - minValue) * 255) / (maxValue - minValue)
            elif waterAccessMap[x][z] == 0:
                newValue = 0
            else:
                newValue = (waterAccessMap[x][z][0] * 255) / maxValue

            waterAccessMap[x][z][0] = newValue

    return waterAccessMap


def PropagateFromCell(map, waterMap, dimensionX, dimensionZ, indexX, indexZ):
    temporaryMap = waterMap.copy()
    propagatingCells = [[indexX, indexZ]]
    visitedCells = [[indexX, indexZ]]
    currentPropagationStrenght = propagationStrenght

    for i in range(int(propagationStrenght / propagationStrenghtLose)):
        currentlyPropagatingCells = propagatingCells.copy()
        for j in range(len(currentlyPropagatingCells)):
            currentX = currentlyPropagatingCells[j][0]
            currentZ = currentlyPropagatingCells[j][1]
            propagatingCells.remove(currentlyPropagatingCells[j])

            # The neighbors index that could be check, the third value define if it has to be check (1) or not (0)
            neighborsIndex = [
                [currentX, currentZ - 1, 1],        # 0 : Top
                [currentX + 1, currentZ - 1, 1],    # 1 : Top right
                [currentX + 1, currentZ, 1],        # 2 : Right
                [currentX + 1, currentZ + 1, 1],    # 3 : Bottom right
                [currentX, currentZ + 1, 1],        # 4 : Bottom
                [currentX - 1, currentZ + 1, 1],    # 5 : Bottom left
                [currentX - 1, currentZ, 1],        # 6 : Left
                [currentX - 1, currentZ - 1, 1],    # 7 : Top left
            ]

            # Check the current position and define which the neighbors that will not be check
            if currentZ == 0:                                               # Is on top side
                neighborsIndex[0][2] = 0
                neighborsIndex[1][2] = 0
                neighborsIndex[7][2] = 0
            if currentX >= dimensionX - 1:                                  # Is on right side
                neighborsIndex[1][2] = 0
                neighborsIndex[2][2] = 0
                neighborsIndex[3][2] = 0
            if currentZ >= dimensionZ - 1:                                  # Is on bottom side
                neighborsIndex[3][2] = 0
                neighborsIndex[4][2] = 0
                neighborsIndex[5][2] = 0
            if currentX == 0:                                               # Is on left side
                neighborsIndex[5][2] = 0
                neighborsIndex[6][2] = 0
                neighborsIndex[7][2] = 0

            # Check all the valid neighbors
            for k in range(len(neighborsIndex)):
                currentNeighborIndex = [neighborsIndex[k][0], neighborsIndex[k][1]]
                if neighborsIndex[k][2] == 1 and currentNeighborIndex not in visitedCells:
                    if map[currentNeighborIndex[0]][currentNeighborIndex[1]][0] != MCUtil.BlocType['WATER']:
                        temporaryMap[currentNeighborIndex[0]][currentNeighborIndex[1]] += currentPropagationStrenght
                        propagatingCells.append(currentNeighborIndex)
                    visitedCells.append(currentNeighborIndex)

        # Decrement propagation value
        currentPropagationStrenght -= propagationStrenghtLose

    return temporaryMap




