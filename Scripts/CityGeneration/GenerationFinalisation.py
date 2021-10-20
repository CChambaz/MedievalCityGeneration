import copy
import Utility.Colors as Colors
import Utility.UtilityMisc as UtilityMisc
import CityGeneration.Data.Maps as Maps
import CityGeneration.Data.Districts as Districts
import math
from time import perf_counter


global OUTER_WALLS_THIKNESS

def DefineDistrictFromUnusedCells(startingPoint, districtMap: Maps.DistrictMap, districtID):
    newDistrict = Districts.Residential(districtID)
    districtCells = [startingPoint]

    propagatingCells = [startingPoint]

    while len(propagatingCells) > 0:
        currentlyPropagatingCells = copy.deepcopy(propagatingCells)
        propagatingCells = []

        for p in currentlyPropagatingCells:
            neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, p[0], p[1])

            for n in neighbours:
                if districtMap.map[n[0]][n[1]] == -2 and n not in districtCells:
                    districtCells.append(n)
                    propagatingCells.append(n)

    if len(districtCells) > 1:
        newDistrict.areaCells = copy.deepcopy(districtCells)

    return newDistrict


def DefineCityShapes(map, districtMap: Maps.DistrictMap):
    dimX = len(districtMap.map)
    dimY = len(districtMap.map[0])
    cityShapes = []

    UtilityMisc.gCSVFile.AddRow()
    t1Start = perf_counter()
    #print("Started city shape definition")
    for x in range(dimX):
        for y in range(dimY):
            if map[x][y][0] == 29 or map[x][y][0] == 40 or districtMap.map[x][y] != -1 or any([x, y] in shapes for shapes in cityShapes):
                continue

            # Check if the cell at x, y is on the border of the city
            cellIsCloseToDistrict = False
            neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, x, y)
            for n in neighbours:
                if districtMap.map[n[0]][n[1]] != -1:
                    #print("District cell found at: {}; {}".format(n[0], n[1]))
                    cellIsCloseToDistrict = True
                    break

            # If not, check the next cell
            if not cellIsCloseToDistrict:
                continue

            #print("Shape starting point found at [{}; {}]".format(x, y))
            currentCell = [x, y]
            previousCell = [-1, -1]
            cityShapes.append([])
            visitedCells = []

            # Move along the city border until it can not anymore in order to have a correct starting point for the shape definition
            while currentCell != previousCell:
                visitedCells.append(currentCell)
                previousCell = currentCell
                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, currentCell[0], currentCell[1], omitDiagonals=True)

                for n in neighbours:
                    if map[n[0]][n[1]][0] == 29 or districtMap.map[n[0]][n[1]] != -1 or n in visitedCells:
                        continue

                    cellIsCloseToDistrict = False
                    canMove = False
                    nNeighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1])
                    for nn in nNeighbours:
                        if districtMap.map[nn[0]][nn[1]] == -1 and map[nn[0]][nn[1]][0] != 29:
                            canMove = True
                        if districtMap.map[nn[0]][nn[1]] != -1:
                            cellIsCloseToDistrict = True

                    if cellIsCloseToDistrict and canMove:
                        currentCell = n
                        break

            #print("Movement stopped at [{}; {}]".format(currentCell[0], currentCell[1]))
            cityShapes[-1] = list(reversed(visitedCells))

            currentCell = cityShapes[-1][-1]
            previousCell = [-1, -1]

            while currentCell != previousCell:
                visitedCells.append(currentCell)
                previousCell = currentCell
                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, currentCell[0], currentCell[1],
                                                                 omitDiagonals=True)

                for n in neighbours:
                    if map[n[0]][n[1]][0] == 29 or districtMap.map[n[0]][n[1]] != -1 or n in visitedCells:
                        continue

                    cellIsCloseToDistrict = False
                    canMove = False
                    nNeighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1])
                    for nn in nNeighbours:
                        if districtMap.map[nn[0]][nn[1]] == -1 and map[nn[0]][nn[1]][0] != 29 and nn not in cityShapes[-1]:
                            canMove = True
                        if districtMap.map[nn[0]][nn[1]] != -1:
                            cellIsCloseToDistrict = True

                    if cellIsCloseToDistrict and canMove:
                        currentCell = n
                        cityShapes[-1].append(n)
                        break

            #print("Movement finalized with n° of cells = {}".format(len(cityShapes[-1])))
    t1Stop = perf_counter()
    UtilityMisc.gCSVFile.AddDataToRow("{}".format(t1Stop - t1Start))
    UtilityMisc.gCSVFile.AddDataToRow("{}".format(len(cityShapes)))

    t1Start = perf_counter()
    # Check if one shape intersect with another shape
    invalidShapes = []
    for i in range(len(cityShapes)):
        if i in invalidShapes:
            continue

        if len(cityShapes[i]) < 10:
            invalidShapes.append(i)
            continue

        for p1 in cityShapes[i]:
            for j in range(i, len(cityShapes)):
                if j == i or j in invalidShapes:
                    continue
                if p1 in cityShapes[j]:
                    if len(cityShapes[i]) > len(cityShapes[j]):
                        invalidShapes.append(j)
                    else:
                        invalidShapes.append(i)

    finalShapes = []
    for i in range(len(cityShapes)):
        if i not in invalidShapes:
            finalShapes.append(cityShapes[i])
    t1Stop = perf_counter()
    UtilityMisc.gCSVFile.AddDataToRow("{}".format(t1Stop - t1Start))
    UtilityMisc.gCSVFile.AddDataToRow("{}".format(len(finalShapes)))

    return finalShapes


def PlaceOuterWalls(districtMap: Maps.DistrictMap, map, cityShape: [[[int, int]]]):
    outerWalls = []
    stepAmount = []

    for i in range(len(cityShape)):
        # Check if the first and last point of the shape are close to each other
        if UtilityMisc.GetVec2Magnitude([cityShape[i][0][0] - cityShape[i][-1][0], cityShape[i][0][1] - cityShape[i][-1][1]]) <= 5:
            #print("Need to change the order of the shape n°{}".format(i))
            # Define the center of the shape
            shapeCenter = [0, 0]
            for p in cityShape[i]:
                shapeCenter[0] += p[0]
                shapeCenter[1] += p[1]
            shapeCenter = [shapeCenter[0] / len(cityShape[i]), shapeCenter[1] / len(cityShape[i])]

            # Get the id of the border cell that is the farest from the shape center
            maxID = 0
            maxDistance = 0
            for j in range(len(cityShape[i])):
                d = UtilityMisc.GetVec2Magnitude([cityShape[i][j][0] - shapeCenter[0], cityShape[i][j][1] - shapeCenter[1]])
                if d > maxDistance:
                    maxDistance = d
                    maxID = j

            cityShape[i].extend(cityShape[i][:maxID])
            del cityShape[i][:maxID]

    for s in cityShape:
        outerWalls.append([])
        stepAmount.append(0)
        previousPath = []
        i = 0
        lastID = 0
        lastValidID = 0

        if UtilityMisc.GetVec2Magnitude([s[0][0] - s[-1][0], s[0][1] - s[-1][1]]) <= 5:
            # Do the first part definition based on the first half of the border
            #print("Len of the current shape: {}".format(len(s)))
            #print("Start first half of the movement")
            while i < len(s) / 2:
                #print("Starting movement at ID: {}".format(i))
                for j in range(i + 1, int(len(s) * 0.7)):
                    currentPoint = s[i]
                    currentPath = [s[i]]
                    movementIsValid = True
                    while currentPoint != s[j]:
                        neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1])

                        neighboursPosition = []
                        neighboursDistances = []
                        for n in neighbours:
                            if map[n[0]][n[1]][0] == 29:
                                continue

                            neighboursPosition.append(n)
                            neighboursDistances.append(UtilityMisc.GetVec2Magnitude([s[j][0] - n[0], s[j][1] - n[1]]))

                        minID = 0
                        minDist = neighboursDistances[0]
                        for k in range(len(neighboursDistances)):
                            if neighboursDistances[k] < minDist:
                                minDist = neighboursDistances[k]
                                minID = k

                        if districtMap.map[neighboursPosition[minID][0]][neighboursPosition[minID][1]] != -1:
                            movementIsValid = False
                            break
                        else:
                            currentPoint = neighboursPosition[minID]
                            #print("CurrentPoint: {}".format(currentPoint))
                            currentPath.append(neighboursPosition[minID])
                            lastID = j

                    if movementIsValid:
                        lastValidID = lastID
                        previousPath = copy.deepcopy(currentPath)

                #print("Ended movement going from {} to {}".format(previousPath[0], previousPath[-1]))
                outerWalls[-1].extend(previousPath)
                stepAmount[-1] += 1
                i = lastValidID

            # Finish the placement on the second half border
            # print("Len of the current shape: {}".format(len(s)))
            #print("Start second half of the movement")
            while i < len(s) - 1:
                # print("Starting movement at ID: {}".format(i))
                for j in range(i + 1, len(s)):
                    currentPoint = s[i]
                    currentPath = [s[i]]
                    movementIsValid = True
                    while currentPoint != s[j]:
                        neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1])

                        neighboursPosition = []
                        neighboursDistances = []
                        for n in neighbours:
                            if map[n[0]][n[1]][0] == 29:
                                continue

                            neighboursPosition.append(n)
                            neighboursDistances.append(UtilityMisc.GetVec2Magnitude([s[j][0] - n[0], s[j][1] - n[1]]))

                        minID = 0
                        minDist = neighboursDistances[0]
                        for k in range(len(neighboursDistances)):
                            if neighboursDistances[k] < minDist:
                                minDist = neighboursDistances[k]
                                minID = k

                        if districtMap.map[neighboursPosition[minID][0]][neighboursPosition[minID][1]] != -1:
                            movementIsValid = False
                            break
                        else:
                            currentPoint = neighboursPosition[minID]
                            # print("CurrentPoint: {}".format(currentPoint))
                            currentPath.append(neighboursPosition[minID])
                            lastID = j

                    if movementIsValid:
                        lastValidID = lastID
                        previousPath = copy.deepcopy(currentPath)

                # print("Ended movement going from {} to {}".format(previousPath[0], previousPath[-1]))
                outerWalls[-1].extend(previousPath)
                stepAmount[-1] += 1
                i = lastValidID
        else:
            #print("Place base walls witht the simple methode")
            #print(len(s))
            while i < len(s) - 1:
                #print("Starting movement at ID: {}".format(i))
                for j in range(i + 1, len(s)):
                    currentPoint = s[i]
                    currentPath = [s[i]]
                    movementIsValid = True
                    while currentPoint != s[j]:
                        neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1])

                        neighboursPosition = []
                        neighboursDistances = []
                        for n in neighbours:
                            if map[n[0]][n[1]][0] == 29:
                                continue

                            neighboursPosition.append(n)
                            neighboursDistances.append(UtilityMisc.GetVec2Magnitude([s[j][0] - n[0], s[j][1] - n[1]]))

                        minID = 0
                        minDist = neighboursDistances[0]
                        for k in range(len(neighboursDistances)):
                            if neighboursDistances[k] < minDist:
                                minDist = neighboursDistances[k]
                                minID = k

                        if districtMap.map[neighboursPosition[minID][0]][neighboursPosition[minID][1]] != -1:
                            movementIsValid = False
                            break
                        else:
                            currentPoint = neighboursPosition[minID]
                            # print("CurrentPoint: {}".format(currentPoint))
                            currentPath.append(neighboursPosition[minID])
                            lastID = j

                    if movementIsValid:
                        lastValidID = lastID
                        previousPath = copy.deepcopy(currentPath)

                # print("Ended movement going from {} to {}".format(previousPath[0], previousPath[-1]))
                outerWalls[-1].extend(previousPath)
                stepAmount[-1] += 1
                i = lastValidID

    # Check each generated walls and remove those that has done only one movement
    #print("Definition of the valid walls")
    validWalls = []
    for i in range(len(stepAmount)):
        if stepAmount[i] > 1:
            validWalls.append(outerWalls[i])

    #print("Add the additional walls over the base walls")
    wallsCount = len(validWalls)
    for i in range(OUTER_WALLS_THIKNESS):
        currentWallsCount = len(validWalls)
        for j in range(i * wallsCount, currentWallsCount):
            currentPoint = [-1, -1]
            previousPoint = [-1, -1]

            for k in range(len(validWalls[j])):
                if map[validWalls[j][k][0]][validWalls[j][k][1]][0] == 40:
                    continue

                # Get the nearest city cell
                nearestCityCell = [-1, -1]
                propagatingCells = [validWalls[j][k]]
                while nearestCityCell == [-1, -1]:
                    currentlyPropagatingCells = copy.deepcopy(propagatingCells)
                    propagatingCells = []
                    encounteredCityCells = []
                    encounteredCityCellsDistances = []

                    for p in currentlyPropagatingCells:
                        if map[p[0]][p[1]][0] == 29:
                            continue

                        neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, p[0], p[1])

                        for n in neighbours:
                            if map[n[0]][n[1]][0] == 29:
                                continue

                            if districtMap.map[n[0]][n[1]] != -1:
                                encounteredCityCells.append(n)
                                encounteredCityCellsDistances.append(UtilityMisc.GetVec2Magnitude([validWalls[j][k][0] - n[0], validWalls[j][k][1] - n[1]]))
                            else:
                                propagatingCells.append(n)

                    # Check if a city cells has been encountered in this iteration
                    if len(encounteredCityCells) > 0:
                        minID = 0
                        minDistance = encounteredCityCellsDistances[0]

                        for l in range(len(encounteredCityCells)):
                            if encounteredCityCellsDistances[l] < minDistance:
                                minDistance = encounteredCityCellsDistances[l]
                                minID = l

                        nearestCityCell = encounteredCityCells[minID]

                # Define current starting point
                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, validWalls[j][k][0], validWalls[j][k][1])
                cToncDistance = UtilityMisc.GetVec2Magnitude([validWalls[j][k][0] - nearestCityCell[0], validWalls[j][k][1] - nearestCityCell[1]])
                cellIDs = []
                cellDistances = []
                possibleMovements = []

                for n in neighbours:
                    if map[n[0]][n[1]][0] == 29 or districtMap.map[n[0]][n[1]] != -1 or any(n in walls for walls in validWalls):
                        continue

                    cellIDs.append(n)
                    cellDistances.append(UtilityMisc.GetVec2Magnitude([n[0] - nearestCityCell[0], n[1] - nearestCityCell[1]]))
                    possibleMovements.append(0)
                    if cellDistances[-1] <= math.sqrt(2.0):
                        continue
                    nNeighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1], omitDiagonals=True)
                    for nn in nNeighbours:
                        if map[nn[0]][nn[1]][0] == 29 or districtMap.map[nn[0]][nn[1]] != -1 or any(nn in walls for walls in validWalls):
                            continue

                        nnNeighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, nn[0], nn[1])
                        for nnn in nnNeighbours:
                            if nnn in validWalls[j]:
                                possibleMovements[-1] += 1
                                break

                if len(cellIDs) == 0:
                    continue

                minID = -1
                minDistance = 0
                minMovement = 10

                for l in range(len(cellIDs)):
                    if possibleMovements[l] == 0:
                        continue

                    if possibleMovements[l] < minMovement:
                        minMovement = possibleMovements[l]

                for l in range(len(cellIDs)):
                    if possibleMovements[l] == 0:
                        continue

                    if possibleMovements[l] == minMovement and cellDistances[l] > minDistance:
                        minDistance = cellDistances[l]
                        minID = l

                if minID != -1:
                    currentPoint = cellIDs[minID]
                    break

            if currentPoint != previousPoint:
                validWalls.append([])

            while currentPoint != previousPoint:
                previousPoint = currentPoint
                validWalls[-1].append(currentPoint)
                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1], omitDiagonals=True)

                cellIDs = []
                cellDistances = []
                possibleMovements = []

                for n in neighbours:
                    if map[n[0]][n[1]][0] == 29 or districtMap.map[n[0]][n[1]] != -1 or any(n in walls for walls in validWalls):
                        continue

                    nNeighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1])
                    vpn = [n[0] - currentPoint[0], n[1] - currentPoint[1]]
                    cellIDs.append(n)
                    cellDistances.append(UtilityMisc.GetVec2Magnitude(vpn))
                    possibleMovements.append(0)

                    for nn in nNeighbours:
                        if nn in validWalls[j]:
                            possibleMovements[-1] += 1
                            break

                if len(cellIDs) == 0:
                    continue

                minID = -1
                minDistance = 10
                minMovement = 10

                for k in range(len(cellIDs)):
                    if possibleMovements[k] == 0:
                        continue

                    if possibleMovements[k] < minMovement:
                        minMovement = possibleMovements[k]

                for k in range(len(cellIDs)):
                    if possibleMovements[k] == 0:
                        continue

                    if possibleMovements[k] == minMovement and cellDistances[k] < minDistance:
                        minDistance = cellDistances[k]
                        minID = k

                if minID != -1:
                    currentPoint = cellIDs[minID]

    #print("Ended outer wall placement")
    return validWalls


def ClearCityShapes(cityShapes):
    validDistricts = []
    for i in range(len(cityShapes) - 1):
        currentDistrictIsValid = True
        for p in cityShapes[i]:
            for j in range(len(cityShapes) - 1):
                if i == j:
                    continue
                if UtilityMisc.CheckIfPointIsInPolygone(p, cityShapes[j]):
                    currentDistrictIsValid = False
                    break
            if not currentDistrictIsValid:
                break
        if currentDistrictIsValid:
            validDistricts.append(i)

    validShapes = []
    for id in validDistricts:
        validShapes.append(copy.deepcopy(cityShapes[id]))

    return validShapes

def DefineOuterWallsLinkingPoints(cityShapes):
    wallsLinkingPointsID = []
    for s in cityShapes:
        wallsLinkingPointsID.append([0])
        lastValidPoint = 0
        for i in range(len(s) - 1):
            i = lastValidPoint
            for j in range(i, len(s) - 1):
                intersectPreviousSegment = False
                for k in range(i + 1, j - 1):
                    if UtilityMisc.SegmentsIntersect(s[i], s[j], s[k - 1], s[k]):
                        intersectPreviousSegment = True
                        break
                if not intersectPreviousSegment:
                    lastValidPoint = j
            wallsLinkingPointsID[-1].append(lastValidPoint)

    wallsLinkingPoints = []
    for i in range(len(wallsLinkingPointsID)):
        wallsLinkingPoints.append([])
        for id in wallsLinkingPointsID[i]:
            wallsLinkingPoints[-1].append(cityShapes[i][id])

    return wallsLinkingPoints

def PrintCityShapesOnMap(map, cityShapes):
    for s in range(len(cityShapes)):
        for p in cityShapes[s]:
            map[p[0], p[1]] = Colors.rgbColors[Maps.buildingColorList[s]]

    return map