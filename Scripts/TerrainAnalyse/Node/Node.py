import Importer.MinecraftMapImporter as MinecraftMapImporter
import Utility.UtilityMisc as UtilityMisc
import Utility.MCUtil as MCUtil
import copy
import os.path
import ImagePrinter.MapToImage as MapToImage
import numpy as np
import cv2
import math
from enum import Enum
from os import makedirs
from os import path
from os import listdir
from os.path import isfile, join
from time import perf_counter



class SelectionMode(Enum):
    WATER = 0,
    HEIGHT = 1


class Node:
    position = [0, 0]
    nearestWaterDistance: int = -2
    nearestWaterDirection = []
    heightAverage: float = 0

    def __init__(self):
        self.position = [0, 0]
        self.nearestWaterDistance = -2
        self.nearestWaterDirection = []
        self.heightAverage = 0


def CreateNodeGridFromFile(filePath, minWaterSize):
    map = MinecraftMapImporter.ImportMap(filePath)

    dimensionX = len(map)
    dimensionZ = len(map[0])

    nodeMap = []
    waterNodes = []
    nodeMapX = -1

    t1Start = perf_counter()
    # Fill the bidimensional node array
    for x in range(1, dimensionX, 3):
        nodeMap.append([])
        nodeMapX += 1
        for z in range(1, dimensionZ, 3):
            node = Node()
            node.position = [x, z]

            # The neighbors index that could be check, the third value define if it has to be check (1) or not (0)
            neighborsIndex = UtilityMisc.GetCellNeighborsOnBiMap(map, x, z)

            totalHeight = 0
            totalHeight += map[x][z][1]
            if map[x][z][0] == MCUtil.BlocType['WATER']:
                node.nearestWaterDistance = 0

            for i in range(len(neighborsIndex)):
                totalHeight += map[neighborsIndex[i][0]][neighborsIndex[i][1]][1]
                if map[neighborsIndex[i][0]][neighborsIndex[i][1]][0] == MCUtil.BlocType['WATER']:
                    node.nearestWaterDistance = 0

            node.heightAverage = totalHeight / len(neighborsIndex)

            if node.nearestWaterDistance == 0:
                waterNodes.append([nodeMapX, len(nodeMap[nodeMapX]), node])

            nodeMap[nodeMapX].append(node)

    t1Stop = perf_counter()
    print("Base grid generation time: {}".format(t1Stop - t1Start))

    confirmedWaterNodeID = []
    print("Water amount: {}".format(len(waterNodes)))

    t1Start = perf_counter()
    # Check if the water nodes can be considered as is
    for i in range(len(waterNodes)):
        if [waterNodes[i][0], waterNodes[i][1]] in confirmedWaterNodeID or nodeMap[waterNodes[i][0]][waterNodes[i][1]].nearestWaterDistance == -1:
            continue

        waterChain = GetWaterGroupFromCell(nodeMap, waterNodes[i][0], waterNodes[i][1])

        if len(waterChain) >= minWaterSize:
            for j in waterChain:
                confirmedWaterNodeID.append(j)
        else:
            for j in waterChain:
                nodeMap[j[0]][j[1]].nearestWaterDistance = -1

    t1Stop = perf_counter()
    print("Water validation time: {}".format(t1Stop - t1Start))

    t1Start = perf_counter()
    # Set the water distance and direction to all the nodes
    for x in range(len(nodeMap)):
        for z in range(len(nodeMap[x])):
            if nodeMap[x][z].nearestWaterDistance != 0:
                minValue = 999999
                for c in confirmedWaterNodeID:
                    w = nodeMap[c[0]][c[1]]
                    d = [
                        w.position[0] - nodeMap[x][z].position[0],
                        w.position[1] - nodeMap[x][z].position[1]
                    ]
                    m = UtilityMisc.GetVec2Magnitude(d)
                    if nodeMap[x][z].nearestWaterDistance == -2 or m <= nodeMap[x][z].nearestWaterDistance:
                        minValue = m
                        nodeMap[x][z].nearestWaterDistance = m
                        d = UtilityMisc.GetNormalizedVec2(d)
                        d.append(m)
                        nodeMap[x][z].nearestWaterDirection.append(d)
                nodeMap[x][z].nearestWaterDirection = [e for e in nodeMap[x][z].nearestWaterDirection if
                                                       e[2] <= minValue]
                for i in range(len(nodeMap[x][z].nearestWaterDirection)):
                    nodeMap[x][z].nearestWaterDirection[i].pop(2)
                #PropagateWaterFromCell(nodeMap, x, z)

    t1Stop = perf_counter()
    print("Water direction and magnitude definition time: {}".format(t1Stop - t1Start))

    #for x in range(len(nodeMap)):
     #   for z in range(len(nodeMap[x])):
      #      minValue = 999999

       #     if nodeMap[x][z].nearestWaterDistance == 0:
        #        continue

         #   for i in nodeMap[x][z].nearestWaterDirection:
          #      if i[2] < minValue:
           #         minValue = i[2]

            #nodeMap[x][z].nearestWaterDirection = [e for e in nodeMap[x][z].nearestWaterDirection if e[2] > minValue]

    return nodeMap


def GetWaterGroupFromCell(nodeMap, x, z):
    propagatingCells = [[x, z]]
    visitedCells = [[x, z]]
    encounteredCellsID = [[x, z]]

    while len(propagatingCells) > 0:
        currentlyPropagatingCells = propagatingCells.copy()

        for j in range(len(currentlyPropagatingCells)):
            currentX = currentlyPropagatingCells[j][0]
            currentZ = currentlyPropagatingCells[j][1]
            propagatingCells.remove(currentlyPropagatingCells[j])

            # The neighbors index that could be check, the third value define if it has to be check (1) or not (0)
            neighborsIndex = UtilityMisc.GetCellNeighborsOnBiMap(nodeMap, currentX, currentZ)

            # Check all the valid neighbors
            for k in range(len(neighborsIndex)):
                if neighborsIndex[k] not in visitedCells:
                    if nodeMap[neighborsIndex[k][0]][neighborsIndex[k][1]].nearestWaterDistance == 0:
                        encounteredCellsID.append([neighborsIndex[k][0], neighborsIndex[k][1]])
                        propagatingCells.append(neighborsIndex[k])
                    visitedCells.append(neighborsIndex[k])

    return encounteredCellsID


def CreateScoreMapFromNodeMap(nodeMap, setting):
    dimensionX = len(nodeMap)
    dimensionZ = len(nodeMap[0])

    scoreMap = []

    minScore = 99999999
    maxScore = 0

    for x in range(dimensionX):
        scoreMap.append([])
        for z in range(dimensionZ):
            score = 0
            if nodeMap[x][z].nearestWaterDistance != 0:
                score = ((nodeMap[x][z].heightAverage * setting.heightWeight) + (nodeMap[x][z].nearestWaterDistance * setting.waterWeight)) * len(nodeMap[x][z].nearestWaterDirection)

                if score < minScore:
                    minScore = score

                if score > maxScore:
                    maxScore = score

            scoreMap[x].append(score)

    return scoreMap


def SaveNodeMapInFile(nodeMap, filePath):
    file = open(filePath, 'w+')

    file.write("{\"lines\":[")
    for x in range(len(nodeMap)):
        file.write("[")
        for z in range(len(nodeMap[x])):
            file.write("{")
            file.write("\"pos\":[{},{}],".format(nodeMap[x][z].position[0], nodeMap[x][z].position[1]))
            file.write("\"wDist\":{},".format(nodeMap[x][z].nearestWaterDistance))
            file.write("\"wDir\":[")
            #file.write("\"wDir\":[{},{}],".format(nodeMap[x][z].nearestWaterDirection[0],
             #                                     nodeMap[x][z].nearestWaterDirection[1]))
            for i in range(len(nodeMap[x][z].nearestWaterDirection)):
                file.write("[{},{}]".format(nodeMap[x][z].nearestWaterDirection[i][0],
                                            nodeMap[x][z].nearestWaterDirection[i][1]))
                if i < len(nodeMap[x][z].nearestWaterDirection) - 1:
                    file.write(",")
            file.write("],")
            file.write("\"hAvg\":{}".format(nodeMap[x][z].heightAverage))
            file.write("}")
            if z < len(nodeMap[x]) - 1:
                file.write(",")
        file.write("]")
        if x < len(nodeMap) - 1:
            file.write(",")
    file.write("]}")
    file.close()


def CreateNodeMapImage(map, nodeMap, fileName):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    dimensionX = len(map)
    dimensionZ = len(map[0])

    heightMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)
    waterMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)
    waterSourceMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    heightMaxValue = 0
    heightMinValue = 999999

    waterMaxValue = 0
    waterMinValue = 9999999

    for x in range(len(nodeMap)):
        for z in range(len(nodeMap[x])):
            if nodeMap[x][z].heightAverage > heightMaxValue:
                heightMaxValue = nodeMap[x][z].heightAverage

            if nodeMap[x][z].heightAverage < heightMinValue:
                heightMinValue = nodeMap[x][z].heightAverage

            if nodeMap[x][z].nearestWaterDistance > waterMaxValue:
                waterMaxValue = nodeMap[x][z].nearestWaterDistance

            if nodeMap[x][z].nearestWaterDistance < waterMinValue:
                waterMinValue = nodeMap[x][z].nearestWaterDistance

            if nodeMap[x][z].nearestWaterDistance == 0:
                waterSourceMap[nodeMap[x][z].position[0]][nodeMap[x][z].position[1]] = [0, 0, 255]
            elif nodeMap[x][z].nearestWaterDistance == -1:
                waterSourceMap[nodeMap[x][z].position[0]][nodeMap[x][z].position[1]] = [255, 0, 0]
            else:
                waterSourceMap[nodeMap[x][z].position[0]][nodeMap[x][z].position[1]] = [255, 255, 255]

    for x in range(len(nodeMap)):
        for z in range(len(nodeMap[x])):
            newHeight = ((nodeMap[x][z].heightAverage - heightMinValue) * 255) / (heightMaxValue - heightMinValue)
            newWaterDist = ((nodeMap[x][z].nearestWaterDistance - waterMinValue) * 255) / (waterMaxValue - waterMinValue)

            heightMap[nodeMap[x][z].position[0]][nodeMap[x][z].position[1]] = [newHeight, newHeight, newHeight]
            waterMap[nodeMap[x][z].position[0]][nodeMap[x][z].position[1]] = [0, 0, newWaterDist]

    MapToImage.PrintImage(heightMap, '{}{}-NMHeight.png'.format(currentDirectory, fileName))
    MapToImage.PrintImage(waterMap, '{}{}-NMWater.png'.format(currentDirectory, fileName))
    MapToImage.PrintImage(waterSourceMap, '{}{}-NMWaterSource.png'.format(currentDirectory, fileName))


def CreateScoreMapImage(map, scoreMap, nodeMap, fileName, settingName):
    currentDirectory = '{}{}\\{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName, settingName)
    dimensionX = len(map)
    dimensionZ = len(map[0])

    oMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    minScore = 99999999
    maxScore = 0

    for x in range(len(scoreMap)):
        for z in range(len(scoreMap[x])):
            score = scoreMap[x][z]
            if score < minScore:
                minScore = score

            if score > maxScore:
                maxScore = score

    for x in range(len(scoreMap)):
        for z in range(len(scoreMap[x])):
            newScore = ((scoreMap[x][z] - minScore) * 255) / (maxScore - minScore)
            oMap[nodeMap[x][z].position[0]][nodeMap[x][z].position[1]] = [newScore, newScore, 0]

    MapToImage.PrintImage(oMap, '{}{}-NMScore.png'.format(currentDirectory, fileName))

def CreateScore2MapImage(map, scoreList, fileName, mode=SelectionMode.HEIGHT):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    extension = ''

    if mode == SelectionMode.HEIGHT:
        extension = 'BestHeights'
    else:
        extension = 'BestWater'

    dimensionX = len(map)
    dimensionZ = len(map[0])

    oMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    minScore = 99999999
    maxScore = 0

    for i in scoreList:
        if i[2] > maxScore:
            maxScore = i[2]

        if i[2] < minScore:
            minScore = i[2]

    for i in scoreList:
        if maxScore == minScore:
            oMap[i[0]][i[1]] = [255, 255, 0]
        else:
            newScore = ((i[2] - minScore) * 255) / (maxScore - minScore)
            oMap[i[0]][i[1]] = [newScore, newScore, 0]

    MapToImage.PrintImage(oMap, '{}{}-NM{}.png'.format(currentDirectory, fileName, extension))

def CreateScore2MapOnColorMap(colorMap, heightMap, scoreList, fileName, gapBetweenPoints, mode=SelectionMode.HEIGHT, optEndName=''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)
    extension = ''

    if mode == SelectionMode.HEIGHT:
        extension = 'BestHeights'
    else:
        extension = 'BestWater'

    dimensionX = len(colorMap)
    dimensionZ = len(colorMap[0])

    colorToApplyOnColorMap = [102, 255, 255]
    colorToApplyOnHeightMap = [255, 0, 0]

    for i in scoreList:
        pos = [i[0], i[1]]

        # Draw left vertical line
        for z in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] - gapBetweenPoints
            zPos = pos[1] + z

            if xPos < 0:
                xPos = 0

            if zPos < 0:
                zPos = 0
            elif zPos >= dimensionZ:
                zPos = dimensionZ - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos + 1][zPos] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos + 1][zPos] = colorToApplyOnHeightMap

        # Draw right vertical line
        for z in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] + gapBetweenPoints
            zPos = pos[1] + z

            if xPos >= dimensionX:
                xPos = dimensionX - 1

            if zPos < 0:
                zPos = 0
            elif zPos >= dimensionZ:
                zPos = dimensionZ - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos - 1][zPos] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos - 1][zPos] = colorToApplyOnHeightMap

        # Draw top horizontal line
        for x in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] + x
            zPos = pos[1] - gapBetweenPoints

            if zPos < 0:
                zPos = 0

            if xPos < 0:
                xPos = 0
            elif xPos >= dimensionX:
                xPos = dimensionX - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos][zPos + 1] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos][zPos + 1] = colorToApplyOnHeightMap

        # Draw bottom horizontal line
        for x in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] + x
            zPos = pos[1] + gapBetweenPoints

            if zPos >= dimensionZ:
                zPos = dimensionZ - 1

            if xPos < 0:
                xPos = 0
            elif xPos >= dimensionX:
                xPos = dimensionX - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos][zPos - 1] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos][zPos - 1] = colorToApplyOnHeightMap

    MapToImage.PrintImage(colorMap, '{}{}-NMCM{}{}.png'.format(currentDirectory, fileName, extension, optEndName))
    MapToImage.PrintImage(heightMap, '{}{}-NMHM{}{}.png'.format(currentDirectory, fileName, extension, optEndName))

def CreateScore2MapOnColorMapWithArrows(colorMap, heightMap, scoreHeight, nodeMap, fileName, gapBetweenPoints, mode=SelectionMode.HEIGHT, optEndName=''):
    currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)

    extension = ''

    if mode == SelectionMode.HEIGHT:
        extension = 'BestHeights'
    else:
        extension = 'BestWater'

    dimensionX = len(colorMap)
    dimensionZ = len(colorMap[0])

    colorToApplyOnColorMap = [102, 255, 255]
    colorToApplyOnHeightMap = [255, 0, 0]

    for i in scoreHeight:
        pos = [i[0], i[1]]

        # Draw left vertical line
        for z in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] - gapBetweenPoints
            zPos = pos[1] + z

            if xPos < 0:
                xPos = 0

            if zPos < 0:
                zPos = 0
            elif zPos >= dimensionZ:
                zPos = dimensionZ - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos + 1][zPos] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos + 1][zPos] = colorToApplyOnHeightMap

        # Draw right vertical line
        for z in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] + gapBetweenPoints
            zPos = pos[1] + z

            if xPos >= dimensionX:
                xPos = dimensionX - 1

            if zPos < 0:
                zPos = 0
            elif zPos >= dimensionZ:
                zPos = dimensionZ - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos - 1][zPos] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos - 1][zPos] = colorToApplyOnHeightMap

        # Draw top horizontal line
        for x in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] + x
            zPos = pos[1] - gapBetweenPoints

            if zPos < 0:
                zPos = 0

            if xPos < 0:
                xPos = 0
            elif xPos >= dimensionX:
                xPos = dimensionX - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos][zPos + 1] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos][zPos + 1] = colorToApplyOnHeightMap

        # Draw bottom horizontal line
        for x in range(-gapBetweenPoints, gapBetweenPoints):
            xPos = pos[0] + x
            zPos = pos[1] + gapBetweenPoints

            if zPos >= dimensionZ:
                zPos = dimensionZ - 1

            if xPos < 0:
                xPos = 0
            elif xPos >= dimensionX:
                xPos = dimensionX - 1

            colorMap[xPos][zPos] = colorToApplyOnColorMap
            colorMap[xPos][zPos - 1] = colorToApplyOnColorMap

            heightMap[xPos][zPos] = colorToApplyOnHeightMap
            heightMap[xPos][zPos - 1] = colorToApplyOnHeightMap

    MapToImage.PrintImage(colorMap, '{}{}-NMACM{}{}.png'.format(currentDirectory, fileName, extension, optEndName))
    MapToImage.PrintImage(heightMap, '{}{}-NMAHM{}{}.png'.format(currentDirectory, fileName, extension, optEndName))
    colorImage = cv2.imread('{}{}-NMACM{}{}.png'.format(currentDirectory, fileName, extension, optEndName), cv2.IMREAD_COLOR)
    heightImage = cv2.imread('{}{}-NMAHM{}{}.png'.format(currentDirectory, fileName, extension, optEndName), cv2.IMREAD_COLOR)
    bgrColor = (colorToApplyOnColorMap[2], colorToApplyOnColorMap[1], colorToApplyOnColorMap[0])
    bgrHeight = (colorToApplyOnHeightMap[2], colorToApplyOnHeightMap[1], colorToApplyOnHeightMap[0])

    for i in scoreHeight:
        node = Node()
        for r in nodeMap:
            t = [e for e in r if e.position == [i[0], i[1]]]
            if t:
                node = t
                break

        for d in node[0].nearestWaterDirection:
            distance = node[0].nearestWaterDistance
            dF = [d[0] * distance, d[1] * distance]
            point1 = (i[1], i[0])
            point2 = (int(UtilityMisc.proper_round(i[1] + dF[1])), int(UtilityMisc.proper_round(i[0] + dF[0])))
            cv2.arrowedLine(colorImage, point1, point2, bgrColor, 1)
            cv2.arrowedLine(heightImage, point1, point2, bgrHeight, 1)

    cv2.imwrite('{}{}-NMACM{}{}.png'.format(currentDirectory, fileName, extension, optEndName), colorImage)
    cv2.imwrite('{}{}-NMAHM{}{}.png'.format(currentDirectory, fileName, extension, optEndName), heightImage)

if __name__ == '__main__':
    originalsMapInDirectory = [f for f in listdir(UtilityMisc.MAPS_FOLDER_PATH) if isfile(join(UtilityMisc.MAPS_FOLDER_PATH, f))]
    settingsInDirectory = [f for f in listdir(UtilityMisc.SETTINGS_FOLDER_PATH) if isfile(join(UtilityMisc.SETTINGS_FOLDER_PATH, f))]

    for o in originalsMapInDirectory:
        fileName = o.split('.', 1)

        print(fileName[0])
        t1Start = perf_counter()
        nodeMap = CreateNodeGridFromFile('{}{}'.format(UtilityMisc.MAPS_FOLDER_PATH, o), 30)
        t1Stop = perf_counter()
        print("Node generation time: {}".format(t1Stop - t1Start))
