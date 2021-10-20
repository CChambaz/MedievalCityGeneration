import numpy as np
import Utility.MCUtil as MCUtil

def FindWaterAreas(minSize, map):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    for x in range(dimensionX):
        for z in range(dimensionZ):
            if map[x][z][0] == MCUtil.BlocType['WATER']:
                if CheckIfWaterAreas(minSize, map, dimensionX, dimensionZ, x, z):
                    PropagateFromCell(map, dimensionX, dimensionZ, x, z)


def CheckIfWaterAreas(minSize, map, dimensionX, dimensionZ, indexX, indexZ):
    eligibleCellsCounter = 0
    propagatingCells = [[indexX, indexZ]]
    visitedCells = [[indexX, indexZ]]

    while True:
        currentlyPropagatingCells = propagatingCells.copy()
        for j in range(len(currentlyPropagatingCells)):
            currentX = currentlyPropagatingCells[j][0]
            currentZ = currentlyPropagatingCells[j][1]
            propagatingCells.remove(currentlyPropagatingCells[j])

            # The neighbors index that could be check, the third value define if it has to be check (1) or not (0)
            neighborsIndex = [
                [currentX, currentZ - 1, 1],  # 0 : Top
                [currentX + 1, currentZ - 1, 1],  # 1 : Top right
                [currentX + 1, currentZ, 1],  # 2 : Right
                [currentX + 1, currentZ + 1, 1],  # 3 : Bottom right
                [currentX, currentZ + 1, 1],  # 4 : Bottom
                [currentX - 1, currentZ + 1, 1],  # 5 : Bottom left
                [currentX - 1, currentZ, 1],  # 6 : Left
                [currentX - 1, currentZ - 1, 1],  # 7 : Top left
            ]

            # Check the current position and define which the neighbors that will not be check
            if currentZ == 0:  # Is on top side
                neighborsIndex[0][2] = 0
                neighborsIndex[1][2] = 0
                neighborsIndex[7][2] = 0
            if currentX >= dimensionX - 1:  # Is on right side
                neighborsIndex[1][2] = 0
                neighborsIndex[2][2] = 0
                neighborsIndex[3][2] = 0
            if currentZ >= dimensionZ - 1:  # Is on bottom side
                neighborsIndex[3][2] = 0
                neighborsIndex[4][2] = 0
                neighborsIndex[5][2] = 0
            if currentX == 0:  # Is on left side
                neighborsIndex[5][2] = 0
                neighborsIndex[6][2] = 0
                neighborsIndex[7][2] = 0

            # Check all the valid neighbors
            for k in range(len(neighborsIndex)):
                currentNeighborIndex = [neighborsIndex[k][0], neighborsIndex[k][1]]
                if neighborsIndex[k][2] == 1 and currentNeighborIndex not in visitedCells:
                    if map[currentNeighborIndex[0]][currentNeighborIndex[1]][0] == MCUtil.BlocType['WATER']:
                        eligibleCellsCounter += 1
                        propagatingCells.append(currentNeighborIndex)
                    visitedCells.append(currentNeighborIndex)

        if eligibleCellsCounter > minSize:
            return True

        if len(propagatingCells) == 0:
            return False

def PropagateFromCell(map, dimensionX, dimensionZ, indexX, indexZ):
    propagatingCells = [[indexX, indexZ]]
    visitedCells = [[indexX, indexZ]]

    while True:
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
                    if map[currentNeighborIndex[0]][currentNeighborIndex[1]][0] == MCUtil.BlocType['WATER']:
                        map[currentNeighborIndex[0]][currentNeighborIndex[1]][0] = MCUtil.BlocType['WATER_AREA']
                        propagatingCells.append(currentNeighborIndex)
                    visitedCells.append(currentNeighborIndex)

        if len(propagatingCells) == 0:
            return
