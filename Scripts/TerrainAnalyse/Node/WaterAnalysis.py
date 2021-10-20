import TerrainAnalyse.Node.Cluster as Cluster
import Utility.UtilityMisc as UtilityMisc
import ImagePrinter.MapToImage as MapToImage
import numpy as np
import math
import operator
import cv2
import Importer.MinecraftMapImporter as MinecraftMapImporter
from os import makedirs
from os import path
from os import listdir
from os.path import isfile, join
from time import perf_counter

def GetPointsBasedOnWater(nodeMap):
    waterCoasts = GetWaterCoast(nodeMap)

    flexionPoints = GetFlexionPoints(waterCoasts)

    shapes = CreateShapeFromFlexionPoints(nodeMap, waterCoasts, flexionPoints)

    clearedShapes = ClearShapes(nodeMap, waterCoasts, flexionPoints, shapes)

    bestShape = GetShapeWithHighestArea(clearedShapes, perWaterCoast=False)[0][0]

    return bestShape[int(len(bestShape) / 2)]



def GetNodesCloserToMostWater(nodeMap, amountOfPointToKeep=0):
    dimensionX = len(nodeMap)
    dimensionZ = len(nodeMap[0])

    sortedWaterList = []
    waterAmount = 0

    for x in range(dimensionX):
        for z in range(dimensionZ):
            if nodeMap[x][z].nearestWaterDistance == 0:
                waterAmount += 1
                continue

            sortedWaterList.append([nodeMap[x][z].position[0], nodeMap[x][z].position[1],
                                     len(nodeMap[x][z].nearestWaterDirection)])

    sortedWaterList.sort(key=lambda x: x[2], reverse=True)

    #del sortedHeightList[int(math.ceil((setting.minPercentage * len(sortedHeightList)) / 100)):len(sortedHeightList)]
    if amountOfPointToKeep > 0:
        del sortedWaterList[amountOfPointToKeep:len(sortedWaterList)]

    return sortedWaterList

def GetWaterCoast(nodeMap):
    waterCoasts = []

    dimensionX = len(nodeMap)
    dimensionZ = len(nodeMap[0])

    for x in range(dimensionX):
        for z in range(dimensionZ):
            # Check if it is a water node
            if nodeMap[x][z].nearestWaterDistance == 0:
                continue

            isAlreadyInACoast = False

            for i in waterCoasts:
                if [x, z] in i:
                    isAlreadyInACoast = True

            isBorderedByWater = False

            # Check if it is located on the water
            neighborsIndex = UtilityMisc.GetCellNeighborsOnBiMap(nodeMap, x, z)

            for i in neighborsIndex:
                if nodeMap[i[0]][i[1]].nearestWaterDistance == 0:
                    isBorderedByWater = True

            if isAlreadyInACoast is False and isBorderedByWater is True:
                neighborsIndex = UtilityMisc.GetCellNeighborsOnBiMap(nodeMap, x, z)
                validNeighborsCount = 0

                # Define the amount of neighbors that are valid
                for j in range(len(neighborsIndex)):
                    if 0 < nodeMap[neighborsIndex[j][0]][neighborsIndex[j][1]].nearestWaterDistance <= 3:
                        validNeighborsCount += 1

                # Check if it is the extremity of a coast
                if validNeighborsCount > 1:
                    continue

                waterCoasts.append([[x, z]])

                propagatingCells = [[x, z]]
                visitedCells = [[x, z]]

                while len(propagatingCells) > 0:
                    currentlyPropagatingCells = propagatingCells.copy()

                    for i in range(len(currentlyPropagatingCells)):
                        currentX = currentlyPropagatingCells[i][0]
                        currentZ = currentlyPropagatingCells[i][1]
                        propagatingCells.remove(currentlyPropagatingCells[i])

                        # The neighbors index that could be check, the third value define if it has to be check (1) or not (0)
                        neighborsIndex = UtilityMisc.GetCellNeighborsOnBiMap(nodeMap, currentX, currentZ, omitDiagonals=True)

                        validNeighbors = []
                        # Check all the valid neighbors
                        for j in range(len(neighborsIndex)):
                            if neighborsIndex[j] not in visitedCells:
                                if 0 < nodeMap[neighborsIndex[j][0]][neighborsIndex[j][1]].nearestWaterDistance < 4.25:
                                    validNeighbors.append([neighborsIndex[j][0], neighborsIndex[j][1]])

                        if len(validNeighbors) == 1:
                            waterCoasts[len(waterCoasts) - 1].append([validNeighbors[0][0], validNeighbors[0][1]])
                            propagatingCells.append(validNeighbors[0])
                            visitedCells.append(validNeighbors[0])
                        else:
                            vector = [0, 0]
                            for k in nodeMap[currentX][currentZ].nearestWaterDirection:
                                vector[0] += k[0]
                                vector[1] += k[1]

                            for j in range(len(validNeighbors)):
                                currentVector = [0, 0]

                                for k in nodeMap[validNeighbors[j][0]][validNeighbors[j][1]].nearestWaterDirection:
                                    currentVector[0] += k[0]
                                    currentVector[1] += k[1]

                                resultingVector = [currentVector[0] - vector[0], currentVector[1] - vector[1]]

                                # Check if they are not opposite vector
                                #if UtilityMisc.GetVec2Magnitude(resultingVector) == 0:
                                #    continue

                                currentAngle = 0

                                if (currentVector[0] != 0.0 or currentVector[1] != 0.0) and (vector[0] != 0.0 or vector[1] != 0.0):
                                    currentAngle = math.fabs(UtilityMisc.GetAngleBetweenVec2(vector, currentVector))

                                if currentAngle < (math.pi / 2):
                                    waterCoasts[len(waterCoasts) - 1].append([validNeighbors[j][0], validNeighbors[j][1]])
                                    propagatingCells.append(validNeighbors[j])
                                    visitedCells.append(validNeighbors[j])
                                    break

    clearedWaterCoast = []

    for i in waterCoasts:
        clearedWaterCoast.append([])

        for j in i:
            if nodeMap[j[0]][j[1]].nearestWaterDistance < 3.1:
                clearedWaterCoast[len(clearedWaterCoast) - 1].append(j)

    closedWaterCoast = []

    # Remove water coast that are not closed on the map borders
    for i in clearedWaterCoast:
        firstID = i[0]
        lastID = i[len(i) - 1]

        if firstID[0] == 0 or firstID[1] == 0 or firstID[0] >= dimensionX - 1 or firstID[1] >= dimensionZ - 1:
            if lastID[0] == 0 or lastID[1] == 0 or lastID[0] >= dimensionX - 1 or lastID[1] >= dimensionZ - 1:
                closedWaterCoast.append(i)


    return closedWaterCoast

def GetFlexionPoints(waterCoasts):
    flexionPoints = []

    for i in waterCoasts:
        flexionPoints.append([0])
        counter = 0
        while counter < len(i) - 2:
            direction = [i[counter + 1][0] - i[counter][0], i[counter + 1][1] - i[counter][1]]

            if direction[0] > 0:
                direction[0] = 1
            elif direction[0] < 0:
                direction[0] = -1

            if direction[1] > 0:
                direction[1] = 1
            elif direction[1] < 0:
                direction[1] = -1

            while True:
                counter += 1
                if counter >= len(i) - 2:
                    if counter + 1 not in flexionPoints[len(flexionPoints) - 1]:
                        flexionPoints[len(flexionPoints) - 1].append(counter + 1)
                    break

                currentDirection = [i[counter + 1][0] - i[counter][0], i[counter + 1][1] - i[counter][1]]

                if currentDirection[0] > 0:
                    currentDirection[0] = 1
                elif currentDirection[0] < 0:
                    currentDirection[0] = -1

                if currentDirection[1] > 0:
                    currentDirection[1] = 1
                elif currentDirection[1] < 0:
                    currentDirection[1] = -1

                isFlexionPoint = False

                # Check if the horizontal direction has been defined
                if direction[0] == 0:
                    direction[0] = currentDirection[0]
                elif direction[0] != currentDirection[0]:
                    isFlexionPoint = True

                # Check if the vertical direction has been defined
                if direction[1] == 0:
                    direction[1] = currentDirection[1]
                elif direction[1] != currentDirection[1]:
                    isFlexionPoint = True

                if isFlexionPoint:
                    flexionPoints[len(flexionPoints) - 1].append(counter)
                    break

    return flexionPoints

def SecondPassOnFlexionPoints(waterCoasts, flexionPoints):
    newFlexionPoints = []

    for i in flexionPoints:
        newFlexionPoints.append([0])
        counter = 0
        while counter < len(i) - 2:
            direction = [waterCoasts[len(newFlexionPoints) - 1][i[counter + 1]][0] - waterCoasts[len(newFlexionPoints) - 1][i[counter]][0], waterCoasts[len(newFlexionPoints) - 1][i[counter + 1]][1] - waterCoasts[len(newFlexionPoints) - 1][i[counter]][1]]

            if direction[0] > 0:
                direction[0] = 1
            elif direction[0] < 0:
                direction[0] = -1

            if direction[1] > 0:
                direction[1] = 1
            elif direction[1] < 0:
                direction[1] = -1

            while True:
                counter += 1
                if counter >= len(i) - 2:
                    if counter + 1 not in newFlexionPoints[len(newFlexionPoints) - 1]:
                        newFlexionPoints[len(newFlexionPoints) - 1].append(i[counter + 1])
                    break

                currentDirection = [waterCoasts[len(newFlexionPoints) - 1][i[counter + 1]][0] - waterCoasts[len(newFlexionPoints) - 1][i[counter]][0], waterCoasts[len(newFlexionPoints) - 1][i[counter + 1]][1] - waterCoasts[len(newFlexionPoints) - 1][i[counter]][1]]

                if currentDirection[0] > 0:
                    currentDirection[0] = 1
                elif currentDirection[0] < 0:
                    currentDirection[0] = -1

                if currentDirection[1] > 0:
                    currentDirection[1] = 1
                elif currentDirection[1] < 0:
                    currentDirection[1] = -1

                isFlexionPoint = False

                # Check if the horizontal direction has been defined
                if direction[0] == 0:
                    direction[0] = currentDirection[0]
                elif currentDirection[0] != 0 and direction[0] != currentDirection[0]:
                    isFlexionPoint = True

                # Check if the vertical direction has been defined
                if direction[1] == 0:
                    direction[1] = currentDirection[1]
                elif currentDirection[1] != 0 and direction[1] != currentDirection[1]:
                    isFlexionPoint = True

                if isFlexionPoint:
                    newFlexionPoints[len(newFlexionPoints) - 1].append(i[counter])
                    break

    return newFlexionPoints

def ReduceFlexionPoints(nodeMap, waterCoast, flexionPoints, angleTolerance):
    reducedFlexionPoints = []
    angleToleranceRad = (angleTolerance * math.pi) / 180

    for i in range(len(flexionPoints)):
        reducedFlexionPoints.append([0])
        counter = 0
        currentPoint = 0

        while counter < len(flexionPoints[i]) - 1:
            counter += 1

            # Check if it is the last point
            if counter == len(flexionPoints[i]) - 1:
                reducedFlexionPoints[len(reducedFlexionPoints) - 1].append(flexionPoints[i][counter])
                break

            # Avoid the situation with two points only
            if counter == currentPoint + 1:
                continue

            # Define the current points
            firstPoint = nodeMap[waterCoast[i][flexionPoints[i][currentPoint]][0]][waterCoast[i][flexionPoints[i][currentPoint]][1]].position
            lastPoint = nodeMap[waterCoast[i][flexionPoints[i][counter]][0]][waterCoast[i][flexionPoints[i][counter]][1]].position

            # Check with all the points between the current one and the last one
            for j in range(currentPoint + 1, counter):
                p1 = nodeMap[waterCoast[i][flexionPoints[i][j - 1]][0]][waterCoast[i][flexionPoints[i][j - 1]][1]].position
                p2 = nodeMap[waterCoast[i][flexionPoints[i][j]][0]][waterCoast[i][flexionPoints[i][j]][1]].position

                # Check if the three points are colinear
                if UtilityMisc.PointsAreColinear(firstPoint, p2, lastPoint):
                    continue

                # Check if the two segments interects
                if UtilityMisc.SegmentsIntersect(p1, p2, firstPoint, lastPoint):
                    reducedFlexionPoints[len(reducedFlexionPoints) - 1].append(flexionPoints[i][counter])
                    currentPoint = counter
                    break

                # Check if the angle between (firstPoint, p2) and (p2, lastPoint) is important
                #firstVector = [p2[0] - firstPoint[0], p2[1] - firstPoint[1]]
                #secondVector = [lastPoint[0] - p2[0], lastPoint[1] - p2[1]]

                #if UtilityMisc.GetAngleBetweenVec2(firstVector, secondVector) > angleToleranceRad:
                #    reducedFlexionPoints[len(reducedFlexionPoints) - 1].append(flexionPoints[i][counter])
                #    currentPoint = counter
                #    break

    #for i in range(len(flexionPoints)):
    #    reducedFlexionPoints.append([0])
    #    counter = 0

    #    while counter < len(flexionPoints[i]) - 2:
    #        counter += 1

    #        previousPosition = nodeMap[waterCoast[i][flexionPoints[i][counter - 1]][0]][waterCoast[i][flexionPoints[i][counter - 1]][1]].position
    #        currentPosition = nodeMap[waterCoast[i][flexionPoints[i][counter]][0]][waterCoast[i][flexionPoints[i][counter]][1]].position
    #        nextPosition = nodeMap[waterCoast[i][flexionPoints[i][counter + 1]][0]][waterCoast[i][flexionPoints[i][counter + 1]][1]].position

    #        currentVector = [currentPosition[0] - previousPosition[0], currentPosition[1] - previousPosition[1]]
    #        nextVector = [nextPosition[0] - currentPosition[0], nextPosition[1] - currentPosition[1]]

    #        currentAngle = math.fabs(UtilityMisc.GetAngleBetweenVec2(currentVector, nextVector))

    #        if currentAngle > angleToleranceRad:
    #            reducedFlexionPoints[len(reducedFlexionPoints) - 1].append(flexionPoints[i][counter])

    #    if flexionPoints[i][len(flexionPoints[i]) - 1] not in reducedFlexionPoints[len(reducedFlexionPoints) - 1]:
    #        reducedFlexionPoints[len(reducedFlexionPoints) - 1].append(flexionPoints[i][len(flexionPoints[i]) - 1])

    #for i in range(len(flexionPoints)):
    #    reducedFlexionPoints.append([0])
    #    counter = 0
    #    currentPoint = 0
    #    currentAngle = 0
    #    currentPosition = [0, 0]
    #    nextPosition = [0, 0]
    #    currentVector = [0, 0]
    #    nextVector = [0, 0]

    #    while counter < len(flexionPoints[i]) - 1:
    #        counter += 1

    #        if counter == currentPoint + 1:
    #            currentPosition = nodeMap[waterCoast[i][flexionPoints[i][currentPoint]][0]][waterCoast[i][flexionPoints[i][currentPoint]][1]].position
    #            nextPosition = nodeMap[waterCoast[i][flexionPoints[i][counter]][0]][waterCoast[i][flexionPoints[i][counter]][1]].position

    #            currentVector = [nextPosition[0] - currentPosition[0], nextPosition[1] - currentPosition[1]]
    #        elif counter == len(flexionPoints[i]) - 1:
    #            reducedFlexionPoints[len(reducedFlexionPoints) - 1].append(flexionPoints[i][counter])
    #            break
    #        else:
    #            nextPosition = nodeMap[waterCoast[i][flexionPoints[i][counter]][0]][waterCoast[i][flexionPoints[i][counter]][1]].position
    #            nextVector = [nextPosition[0] - currentPosition[0], nextPosition[1] - currentPosition[1]]

    #            currentAngle = math.fabs(UtilityMisc.GetAngleBetweenVec2(currentVector, nextVector))

    #            if currentAngle > angleToleranceRad:
    #                reducedFlexionPoints[len(reducedFlexionPoints) - 1].append(flexionPoints[i][counter])
    #                currentPoint = counter

    return reducedFlexionPoints

def CreateShapeFromFlexionPoints(nodeMap, waterCoasts, flexionPoints):
    shapes = []

    for i in range(len(flexionPoints)):
        shapes.append([])

        currentAmountOfShapes = 0
        counter = 0
        shapeStartingPoint = 0
        shapeStartingPosition = nodeMap[waterCoasts[i][flexionPoints[i][counter]][0]][waterCoasts[i][flexionPoints[i][counter]][1]].position

        while counter < len(flexionPoints[i]) - 1:
            counter += 1
            breakTheShape = False

            if counter != len(flexionPoints[i]) - 1:
                nextPosition = nodeMap[waterCoasts[i][flexionPoints[i][counter + 1]][0]][waterCoasts[i][flexionPoints[i][counter + 1]][1]].position

                for j in range(shapeStartingPoint, counter):
                    jPoint0 = nodeMap[waterCoasts[i][flexionPoints[i][j]][0]][waterCoasts[i][flexionPoints[i][j]][1]].position
                    jPoint1 = nodeMap[waterCoasts[i][flexionPoints[i][j + 1]][0]][waterCoasts[i][flexionPoints[i][j + 1]][1]].position

                    if UtilityMisc.SegmentsIntersect(jPoint0, jPoint1, shapeStartingPosition, nextPosition):
                        breakTheShape = True
            else:
                breakTheShape = True

            if breakTheShape:
                shapes[i].append([])

                for j in range(shapeStartingPoint, counter + 1):
                    p = nodeMap[waterCoasts[i][flexionPoints[i][j]][0]][waterCoasts[i][flexionPoints[i][j]][1]].position
                    shapes[i][currentAmountOfShapes].append(p)

                currentAmountOfShapes += 1
                shapeStartingPoint += 1
                counter = shapeStartingPoint
                shapeStartingPosition = nodeMap[waterCoasts[i][flexionPoints[i][counter]][0]][waterCoasts[i][flexionPoints[i][counter]][1]].position

    return shapes

def ClearShapes(nodeMap, waterCoasts, flexionPoints, shapes):
    newShapes = []

    for i in range(len(shapes)):
        newShapes.append([])

        for j in shapes[i]:
            shapeCenter = Cluster.GetClusterCenterFromPoints(j)
            shapeTriangles = UtilityMisc.GetShapeTriangles(j, shapeCenter)

            currentShapeIsValid = True

            # Get the indexes of the first and last point of the shape on the node map
            nmFirstID = [int(j[0][0] / 3), int(j[0][1] / 3)]
            nmLastID = [int(j[len(j) - 1][0] / 3), int(j[len(j) - 1][1] / 3)]

            # Get the first and last indexe of the shape in the water coast
            wcFirstID = waterCoasts[i].index(nmFirstID)
            wcLastID = waterCoasts[i].index(nmLastID)

            # Get the first and last index of the shape in the flexion points
            fpFirstID = flexionPoints[i].index(wcFirstID)
            fpLastID = flexionPoints[i].index(wcLastID)

            for k in range(fpFirstID, fpLastID + 1):
                id = waterCoasts[i][flexionPoints[i][k]]
                currentNode = nodeMap[id[0]][id[1]]
                #nwdResultingVector = [0, 0]

                for l in currentNode.nearestWaterDirection:
                    pointPosition = [currentNode.position[0] + l[0], currentNode.position[1] + l[1]]
                    #nwdResultingVector = [nwdResultingVector[0] + l[0], nwdResultingVector[1] + l[1]]
                    for m in shapeTriangles:
                        if UtilityMisc.PointIsInsideTriangle(pointPosition, m[0], m[1], m[2]):
                            currentShapeIsValid = False
                            break

                    if currentShapeIsValid is False:
                        break

                if currentShapeIsValid is False:
                    break

            if currentShapeIsValid is True:
                newShapes[len(newShapes) - 1].append(j)

    return newShapes

def GetShapeWithHighestArea(shapes, perWaterCoast=True):
    returnedShapes = []

    globalMaxArea = [0, 0, 0]

    for i in range(len(shapes)):
        returnedShapes.append([])

        maxArea = [0, 0]

        for j in range(len(shapes[i])):
            if len(shapes[i][j]) < 3:
                continue

            shapeCenter = Cluster.GetClusterCenterFromPoints(shapes[i][j])
            shapeArea = UtilityMisc.GetShapeArea(shapes[i][j], shapeCenter)

            if shapeArea > maxArea[0]:
                maxArea = [shapeArea, j]

            if shapeArea > globalMaxArea[0]:
                globalMaxArea = [shapeArea, i, j]

        if maxArea[0] != 0:
            returnedShapes[len(returnedShapes) - 1].append(shapes[i][maxArea[1]])

    uniqueReturn = [[shapes[globalMaxArea[1]][globalMaxArea[2]]]]

    if perWaterCoast:
        return returnedShapes
    else:
        return uniqueReturn

def GetMidPointFromShape(shape):
    return shape[int(len(shape) / 2)]

def CreateTrianglesFromFlexionPoints(nodeMap, waterCoasts, flexionPoints):
    tri = []

    for i in flexionPoints:
        tri.append([])

        for j in range(len(i)):
            currentX = waterCoasts[len(tri) - 1][i[j]][0]
            currentZ = waterCoasts[len(tri) - 1][i[j]][1]

            currentPos = nodeMap[currentX][currentZ].position

            nearestWaterVector = []
            nearestWaterPoint = []
            nearestWaterVector.append([0, 0])
            for k in nodeMap[currentX][currentZ].nearestWaterDirection:
                nearestWaterVector[0][0] += k[0]
                nearestWaterVector[0][1] += k[1]

            nearestWaterVector[0] = UtilityMisc.GetNormalizedVec2(nearestWaterVector[0])
            nearestWaterPoint.append([currentPos[0] + nearestWaterVector[0][0], currentPos[1] + nearestWaterVector[0][1]])

            for k in range(j + 1, len(i)):
                secondX = waterCoasts[len(tri) - 1][i[k]][0]
                secondZ = waterCoasts[len(tri) - 1][i[k]][1]

                secondPos = nodeMap[secondX][secondZ].position

                nearestWaterVector.append([0, 0])
                for l in nodeMap[secondX][secondZ].nearestWaterDirection:
                    nearestWaterVector[1][0] += l[0]
                    nearestWaterVector[1][1] += l[1]

                nearestWaterVector[1] = UtilityMisc.GetNormalizedVec2(nearestWaterVector[1])
                nearestWaterPoint.append([secondPos[0] + nearestWaterVector[1][0], secondPos[1] + nearestWaterVector[1][1]])

                for l in range(k + 1, len(i)):
                    thirdX = waterCoasts[len(tri) - 1][i[l]][0]
                    thirdZ = waterCoasts[len(tri) - 1][i[l]][1]

                    thirdPos = nodeMap[thirdX][thirdZ].position

                    nearestWaterVector.append([0, 0])
                    for m in nodeMap[secondX][secondZ].nearestWaterDirection:
                        nearestWaterVector[2][0] += m[0]
                        nearestWaterVector[2][1] += m[1]

                    nearestWaterVector[2] = UtilityMisc.GetNormalizedVec2(nearestWaterVector[2])
                    nearestWaterPoint.append([thirdPos[0] + nearestWaterVector[2][0], thirdPos[1] + nearestWaterVector[2][1]])

                    waterPointIsInTriangle = False

                    for m in nearestWaterPoint:
                        if UtilityMisc.PointIsInsideTriangle(m, currentPos, secondPos, thirdPos):
                            waterPointIsInTriangle = True
                            break

                    if waterPointIsInTriangle is False:
                        tri[len(tri) - 1].append([currentPos, secondPos, thirdPos])

    return tri

def GetTriangleWithTheHighestSurface(triangles, perWaterCoast=True):
    returnedTriangles = []

    globalMaxArea = [0, 0, 0]

    for i in range(len(triangles)):
        if len(triangles[i]) == 0:
            continue

        returnedTriangles.append([])

        maxArea = [0, 0]
        for j in range(len(triangles[i])):
            currentArea = UtilityMisc.GetTriangleArea(triangles[i][j][0], triangles[i][j][1], triangles[i][j][2])

            if currentArea > maxArea[0]:
                maxArea = [currentArea, j]

            if currentArea > globalMaxArea[0]:
                globalMaxArea = [currentArea, i, j]

        returnedTriangles[len(returnedTriangles) - 1].append(triangles[i][maxArea[1]])

    uniqueReturn = [[triangles[globalMaxArea[1]][globalMaxArea[2]]]]

    if perWaterCoast:
        return returnedTriangles
    else:
        return uniqueReturn

def PrintWaterCoast(map, waterCoasts, nodeMap, fileName, extension=''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    dimensionX = len(map)
    dimensionZ = len(map[0])

    oMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    for i in waterCoasts:
        for j in i:
            oMap[nodeMap[j[0]][j[1]].position[0]][nodeMap[j[0]][j[1]].position[1]] = [255, 0, 0]

    MapToImage.PrintImage(oMap, '{}{}-WaterCoasts{}.png'.format(currentDirectory, fileName, extension))

def PrintWaterCoastWithFlexionPoints(map, waterCoasts, flexionPoints, nodeMap, fileName, extension=''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    dimensionX = len(map)
    dimensionZ = len(map[0])

    oMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    for i in waterCoasts:
        for j in i:
            oMap[nodeMap[j[0]][j[1]].position[0]][nodeMap[j[0]][j[1]].position[1]] = [255, 0, 0]

    for i in range(len(flexionPoints)):
        for j in flexionPoints[i]:
            currentCoord = [waterCoasts[i][j][0], waterCoasts[i][j][1]]
            currentPos = [nodeMap[currentCoord[0]][currentCoord[1]].position[0], nodeMap[currentCoord[0]][currentCoord[1]].position[1]]
            oMap[currentPos[0]][currentPos[1]] = [255, 255, 0]

    MapToImage.PrintImage(oMap, '{}{}-WaterCoastsWithFlexionPoints{}.png'.format(currentDirectory, fileName, extension))

def PrintWaterCoastWithReducedFlexionPoints(map, waterCoasts, reduceFlexionPoints, nodeMap, fileName, extension = ''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    dimensionX = len(map)
    dimensionZ = len(map[0])

    oMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    for i in waterCoasts:
        for j in i:
            oMap[nodeMap[j[0]][j[1]].position[0]][nodeMap[j[0]][j[1]].position[1]] = [255, 0, 0]

    for i in range(len(reduceFlexionPoints)):
        for j in reduceFlexionPoints[i]:
            currentCoord = [waterCoasts[i][j][0], waterCoasts[i][j][1]]
            currentPos = [nodeMap[currentCoord[0]][currentCoord[1]].position[0], nodeMap[currentCoord[0]][currentCoord[1]].position[1]]
            oMap[currentPos[0]][currentPos[1]] = [255, 255, 0]

    MapToImage.PrintImage(oMap, '{}{}-WaterCoastsWithReduceFlexionPoints2-{}.png'.format(currentDirectory, fileName, extension))

def PrintWaterCoastWithTriangles(map, waterCoasts, nodeMap, triangles, fileName, extension=''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    dimensionX = len(map)
    dimensionZ = len(map[0])

    oMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    for i in triangles:
        for j in i:
            firstPoint = (j[0][1], j[0][0])
            secondPoint = (j[1][1], j[1][0])
            thirdPoint = (j[2][1], j[2][0])
            oMap = cv2.line(oMap, firstPoint, secondPoint, (0, 255, 255), 1)
            oMap = cv2.line(oMap, secondPoint, thirdPoint, (0, 255, 255), 1)
            oMap = cv2.line(oMap, thirdPoint, firstPoint, (0, 255, 255), 1)

    for i in waterCoasts:
        for j in i:
            oMap[nodeMap[j[0]][j[1]].position[0]][nodeMap[j[0]][j[1]].position[1]] = [255, 0, 0]

    MapToImage.PrintImage(oMap, '{}{}-WaterCoastsWithTriangles{}.png'.format(currentDirectory, fileName,
                                                                                         extension))

def PrintWaterCoastWithShapes(map, waterCoasts, nodeMap, shapes, fileName, extension=''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    dimensionX = len(map)
    dimensionZ = len(map[0])

    oMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    for i in shapes:
        for j in i:
            for k in range(len(j) - 1):
                firstPoint = (j[k][1], j[k][0])
                secondPoint = (j[k + 1][1], j[k + 1][0])
                oMap = cv2.line(oMap, firstPoint, secondPoint, (0, 255, 255), 1)

            firstPoint = (j[0][1], j[0][0])
            secondPoint = (j[len(j) - 1][1], j[len(j) - 1][0])
            oMap = cv2.line(oMap, firstPoint, secondPoint, (0, 255, 255), 1)

    for i in waterCoasts:
        for j in i:
            oMap[nodeMap[j[0]][j[1]].position[0]][nodeMap[j[0]][j[1]].position[1]] = [255, 0, 0]

    MapToImage.PrintImage(oMap, '{}{}-WaterCoastsWithShapes{}.png'.format(currentDirectory, fileName,
                                                                                         extension))

def PrintResultPointOnColorMap(colorMap, shape, gapBetweenPoints, fileName, extension=''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    dimensionX = len(colorMap)
    dimensionZ = len(colorMap[0])

    resultingPoint = GetMidPointFromShape(shape)

    colorToApplyOnColorMap = [102, 255, 255]

    for i in range(len(shape) - 1):
        firstPoint = (shape[i][1], shape[i][0])
        secondPoint = (shape[i + 1][1], shape[i + 1][0])
        colorMap = cv2.line(colorMap, firstPoint, secondPoint, (102, 255, 255), 1)

    firstPoint = (shape[0][1], shape[0][0])
    secondPoint = (shape[len(shape) - 1][1], shape[len(shape) - 1][0])
    colorMap = cv2.line(colorMap, firstPoint, secondPoint, (102, 255, 255), 1)

    for z in range(-gapBetweenPoints, gapBetweenPoints):
        xPos = resultingPoint[0] - gapBetweenPoints
        zPos = resultingPoint[1] + z

        if xPos < 0:
            xPos = 0

        if zPos < 0:
            zPos = 0
        elif zPos >= dimensionZ:
            zPos = dimensionZ - 1

        colorMap[xPos][zPos] = colorToApplyOnColorMap
        colorMap[xPos + 1][zPos] = colorToApplyOnColorMap

    # Draw right vertical line
    for z in range(-gapBetweenPoints, gapBetweenPoints):
        xPos = resultingPoint[0] + gapBetweenPoints
        zPos = resultingPoint[1] + z

        if xPos >= dimensionX:
            xPos = dimensionX - 1

        if zPos < 0:
            zPos = 0
        elif zPos >= dimensionZ:
            zPos = dimensionZ - 1

        colorMap[xPos][zPos] = colorToApplyOnColorMap
        colorMap[xPos - 1][zPos] = colorToApplyOnColorMap

    # Draw top horizontal line
    for x in range(-gapBetweenPoints, gapBetweenPoints):
        xPos = resultingPoint[0] + x
        zPos = resultingPoint[1] - gapBetweenPoints

        if zPos < 0:
            zPos = 0

        if xPos < 0:
            xPos = 0
        elif xPos >= dimensionX:
            xPos = dimensionX - 1

        colorMap[xPos][zPos] = colorToApplyOnColorMap
        colorMap[xPos][zPos + 1] = colorToApplyOnColorMap

    # Draw bottom horizontal line
    for x in range(-gapBetweenPoints, gapBetweenPoints):
        xPos = resultingPoint[0] + x
        zPos = resultingPoint[1] + gapBetweenPoints

        if zPos >= dimensionZ:
            zPos = dimensionZ - 1

        if xPos < 0:
            xPos = 0
        elif xPos >= dimensionX:
            xPos = dimensionX - 1

        colorMap[xPos][zPos] = colorToApplyOnColorMap
        colorMap[xPos][zPos - 1] = colorToApplyOnColorMap

    MapToImage.PrintImage(colorMap, '{}{}-WSResult{}.png'.format(currentDirectory, fileName,
                                                                          extension))

if __name__ == '__main__':
    nodeMapInDirectory = [f for f in listdir(UtilityMisc.NODE_MAP_FOLDER_PATH) if
                          isfile(join(UtilityMisc.NODE_MAP_FOLDER_PATH, f))]

    for o in nodeMapInDirectory:
        fileName = o.split('.', 1)
        originalName = fileName[0].rsplit('-', 1)
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, originalName[0]))
        nodeMap = MinecraftMapImporter.ImportNodeMap('{}{}'.format(UtilityMisc.NODE_MAP_FOLDER_PATH, o))

        currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, originalName[0])

        if not path.isdir(currentDirectory):
            makedirs(currentDirectory)

        print(originalName[0])
        tTotalStart = perf_counter()
        t1Start = perf_counter()
        waterCoasts = GetWaterCoast(nodeMap)
        t1Stop = perf_counter()
        print("Water coast definition time: {}".format(t1Stop - t1Start))

        t1Start = perf_counter()
        flexionPoints = GetFlexionPoints(waterCoasts)
        t1Stop = perf_counter()
        print("Flexion point definition time: {}".format(t1Stop - t1Start))

        t1Start = perf_counter()
        shapes = CreateShapeFromFlexionPoints(nodeMap, waterCoasts, flexionPoints)
        t1Stop = perf_counter()
        print("Shape creation time: {}".format(t1Stop - t1Start))

        t1Start = perf_counter()
        clearedShapes = ClearShapes(nodeMap, waterCoasts, flexionPoints, shapes)
        t1Stop = perf_counter()
        print("Clearing shape time: {}".format(t1Stop - t1Start))

        t1Start = perf_counter()
        bestShapes = GetShapeWithHighestArea(clearedShapes, perWaterCoast=False)
        t1Stop = perf_counter()
        print("Getting best shape time: {}".format(t1Stop - t1Start))

        tTotalEnd = perf_counter()
        print("Total time: {}".format(tTotalEnd - tTotalStart))