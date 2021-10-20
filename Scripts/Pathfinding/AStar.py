import Importer.MinecraftMapImporter as MinecraftMapImporter
import Utility.UtilityMisc as UtilityMisc
import ImagePrinter.MapToImage as MapToImage
import MapGenerator.ColorMapGen as ColorMapGen
import math
import CityGeneration.Data.Maps as Maps

global SLOPE_AMPLIFIER
global WATER_WEIGHT
global MAX_WATER_CROSSED
maxSlope = (45 * math.pi) / 180


class PNode:
    position: [int, int]
    height: int
    water: int
    parent: [int, int]
    costToGoal: float
    costToParent: float
    onWaterSince: int

    def __init__(self):
        self.position = [0, 0]
        self.height = 0
        self.water = 0
        self.parent = [0, 0]
        self.costToGoal = 0
        self.costToParent = 0
        self.onWaterSince = 0

    def GetTotalCost(self):
        return self.costToGoal + self.costToParent


def DefineSlopeAmplifier(value):
    SLOPE_AMPLIFIER = value


def DefineCostFromTo(p1, p2, waterWeight):
    if p1.position == p2.position:
        return 0

    v = [p2.position[0] - p1.position[0], p2.position[1] - p1.position[1], p2.height - p1.height]
    distance = UtilityMisc.GetVec3Magnitude(v)
    vx = [p2.position[0] - p1.position[0], p2.position[1] - p1.position[1], 0]
    angle = UtilityMisc.GetAngleBetweenVec3(v, vx)
    return distance + distance * (1 - angle) * SLOPE_AMPLIFIER + waterWeight


def GetPathFromTo(p1, p2, map, roadMap):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    openList = []

    nodeMap = []

    #print("Generate Node Map")
    for x in range(dimensionX):
        nodeMap.append([])
        for z in range(dimensionZ):
            n = PNode()
            n.position = [x, z]
            n.height = map[x][z][1]
            if map[x][z][0] == 29 or map[x][z][0] == 40:
                n.water = 1
            nodeMap[x].append(n)

    n1 = nodeMap[p1[0]][p1[1]]
    n2 = nodeMap[p2[0]][p2[1]]
    n1.parent = p1

    lastCell = [-1, -1]
    openList.append(n1.position)
    closedList = []

    #print("Start main loop")
    while len(openList) > 0:
        minValue = 9223372036854775807
        minID = 0

        for i in range(len(openList)):
            totalCost = nodeMap[openList[i][0]][openList[i][1]].GetTotalCost()
            if totalCost < minValue and openList[i] not in closedList:
                minValue = totalCost
                minID = i

        closedList.append(openList[minID])
        p = nodeMap[openList[minID][0]][openList[minID][1]]
        openList.remove(openList[minID])

        if p.position == p2 or roadMap[p.position[0]][p.position[1]] == 1:
            lastCell = p.position
            break

        if p.onWaterSince > MAX_WATER_CROSSED:
            continue

        neighbors = UtilityMisc.GetCellNeighborsOnBiMap(nodeMap, p.position[0], p.position[1])

        for id in neighbors:
            if id in closedList or abs(p.height - nodeMap[id[0]][id[1]].height) > 1:
                continue

            costToParent = DefineCostFromTo(nodeMap[id[0]][id[1]], p, nodeMap[id[0]][id[1]].water * WATER_WEIGHT)
            costToGoal = DefineCostFromTo(nodeMap[id[0]][id[1]], n2, nodeMap[id[0]][id[1]].water * WATER_WEIGHT)

            if id not in openList:
                nodeMap[id[0]][id[1]].parent = p.position
                nodeMap[id[0]][id[1]].costToParent = costToParent
                nodeMap[id[0]][id[1]].costToGoal = costToGoal
                if p.water == 1:
                    nodeMap[id[0]][id[1]].onWaterSince = p.onWaterSince + 1
                openList.append(id)
            elif costToParent + costToGoal < nodeMap[id[0]][id[1]].GetTotalCost():
                nodeMap[id[0]][id[1]].parent = p.position
                nodeMap[id[0]][id[1]].costToParent = costToParent
                if p.water == 1:
                    nodeMap[id[0]][id[1]].onWaterSince = p.onWaterSince + 1

    if lastCell == [-1, -1]:
        #print("Can't reach the destination")
        return []

    #print("Start reverse path generation")
    path = [lastCell]
    currentCell = lastCell
    while currentCell != p1:
        path.append(nodeMap[currentCell[0]][currentCell[1]].parent)
        currentCell = nodeMap[currentCell[0]][currentCell[1]].parent


    return path


def DrawPathOnColorMap(colorMap, path, directoryName, fileName, extension=''):
    currentDirectory = '{}\\RoadTest\\{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, directoryName)
    colorToApplyOnColorMap = [102, 255, 255]

    for p in path:
        for x in range(len(p)):
            colorMap[p[x][0]][p[x][1]] = colorToApplyOnColorMap

    MapToImage.PrintImage(colorMap, '{}{}-{}-RoadTest.png'.format(currentDirectory, fileName, extension))


if __name__ == '__main__':
    #SMValues = [4, 8, 16, 32, 64, 128]
    #WWValues = [1, 2, 4, 8, 16, 32]
    WWValues = [40]
    SMValues = [32]

    for x in range(2, 6):
        fileName = "ExportedMap64-{}".format(x)
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName))
        roadMap = Maps.RoadMap(map)
        for sm in SMValues:
            SLOPE_AMPLIFIER = sm
            for ww in WWValues:
                WATER_WEIGHT = ww
                ext = "SM{}-WW{}".format(SLOPE_AMPLIFIER, WATER_WEIGHT)
                path = []
                path.append(GetPathFromTo([275, 275], [750, 750], map, roadMap.roadMap))
                DrawPathOnColorMap(ColorMapGen.MapToColorMap(map, len(map), len(map[0])), path, "O9", fileName,
                               extension=ext)

    print("Success!")
