import math

import Utility.Colors as Colors
import Importer.MinecraftMapImporter as MinecraftMapImporter
import ImagePrinter.MapToImage as MapToImage
import DataModifier.RiverFinder as RiverFinder
import MapGenerator.HeightMapGen as HeightMapGen
import MapGenerator.ColorMapGen as ColorMapGen
import TerrainAnalyse.WeightPoint as WeightPoint
import CityGeneration.Data.Districts as Districts
import CityGeneration.Data.Buildings as Buildings
import CityGeneration.Data.Maps as Maps
#import Settings.Settings as Settings
import TerrainAnalyse.Node.Node as Node
import TerrainAnalyse.Node.HeightAnalysis as HeightAnalysis
import TerrainAnalyse.Node.WaterAnalysis as WaterAnalysis
import Utility.CSVCreator as CSVCreator
from os import makedirs
from os import path
from os import listdir
from os.path import isfile, join
from time import perf_counter
import copy
import numpy as np

MAPS_FOLDER_PATH = 'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\Files\\Maps\\Originals\\'
MAPS_MW_FOLDER_PATH = 'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\Files\\Maps\\MWater\\'
NODE_MAP_FOLDER_PATH = 'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\Files\\Maps\\NodeMap\\'
SETTINGS_FOLDER_PATH = 'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\Files\\Settings\\'
RESULT_FOLDER_PATH = 'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\ResultImage\\'

global RND_SEED
global SEED_ID
global gCSVFile

cellMaxAngle = (45 * math.pi) / 180

colorList = [
    'darkgray',     # 0 = Other district color
    'darkgray',     # 1 = Road color
    'red',          # 2 = Vertex 1
    'yellow',       # 3 = Vertex 2
    'orange',       # 4 = Vertex 3
    'pink',         # 5 = Vertex 4
    'blue',         # 6 = Vertex 5
    'violet',       # 7 = Link 1 to 2
    'darkviolet',   # 8 = Link 1 to 3
    'aqua',         # 9 = Link 2 to 4
    'snow',         # 10 = Link 3 to 4
    'darkblue',     # 11 = Link 4 to 5
    'darkred',      # 12 = Circle position
    'darkred',      # 13 = Segment position
    'magenta',      # 14 = District center
    'deeppink'      # 15 = Inner cells
]

wallsColor = "limegreen"
districtsLayerColor = "tan"

def DefineSeed(seed):
    RND_SEED = seed

def proper_round(num, dec=0):
    num = str(num)[:str(num).index('.')+dec+2]
    if num[-1]>='5':
        a = num[:-2-(not dec)]       # integer part
        if num[-2-(not dec)] != '.':
            b = int(float(num[-2-(not dec)]))+1 # decimal part
        else:
            b = int(float(num[-1 - (not dec)]))  # decimal part
        return float(a)+b**(-dec+1) if a and b == 10 else float(a+str(b))
    return float(num[:-1])


def CountTypeInMap(map):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    counter = dict()

    for x in range(dimensionX):
        for z in range(dimensionZ):
            if map[x][z][0] in counter:
                counter[map[x][z][0]] += 1
            else:
                counter[map[x][z][0]] = 1

    for i in counter:
        print("Amount of {} = {}".format(i, counter[i]))


def CalculateAreaValueWithoutOffset(mapSize):
    for x in range(mapSize):
        currentSize = x

        if currentSize % 2 != 0:
            currentSize += 1

        offset = int(math.floor((1024 % (currentSize + 1)) / 2))
        if offset == 0:
            print("Offset is equal to 0 with an area of size {}".format(x))


def GetCellNeighborsOnBiMap(map, x, z, omitDiagonals=False):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    sideCheck = [
        True if z == 0 else False,                   # Top side
        True if x >= dimensionX - 1 else False,      # Right side
        True if z >= dimensionZ - 1 else False,      # Bottom side
        True if x == 0 else False                    # Left side
    ]

    # The neighbors index that could be check, the third value define if it has to be check (1) or not (0)
    neighborsIndex = []

    # Top left
    if sideCheck[0] is False and sideCheck[3] is False and omitDiagonals is False:
        neighborsIndex.append([x - 1, z - 1])

    # Top
    if sideCheck[0] is False:
        neighborsIndex.append([x, z - 1])

    # Top right
    if sideCheck[0] is False and sideCheck[1] is False and omitDiagonals is False:
        neighborsIndex.append([x + 1, z - 1])

    # Right
    if sideCheck[1] is False:
        neighborsIndex.append([x + 1, z])

    # Bottom right
    if sideCheck[1] is False and sideCheck[2] is False and omitDiagonals is False:
        neighborsIndex.append([x + 1, z + 1])

    # Bottom
    if sideCheck[2] is False:
        neighborsIndex.append([x, z + 1])

    # Bottom left
    if sideCheck[2] is False and sideCheck[3] is False and omitDiagonals is False:
        neighborsIndex.append([x - 1, z + 1])

    # Left
    if sideCheck[3] is False:
        neighborsIndex.append([x - 1, z])

    return neighborsIndex

def GetVec2Magnitude(vector):
    return math.sqrt((vector[0] * vector[0]) + (vector[1] * vector[1]))

def GetVec3Magnitude(vector):
    return math.sqrt((vector[0] * vector[0]) + (vector[1] * vector[1]) + (vector[2] * vector[2]))

def GetNormalizedVec2(vector):
    m = GetVec2Magnitude(vector)
    return [vector[0] / m, vector[1] / m]

def GetAngleBetweenVec2(v1, v2):
    m1 = proper_round(float(GetVec2Magnitude(v1)), 2)
    m2 = proper_round(float(GetVec2Magnitude(v2)), 2)

    r0 = proper_round(float(v1[0] * v2[0]), 2)
    r1 = proper_round(float(v1[1] * v2[1]), 2)

    r = (r0 + r1) / (m1 * m2)

    if r > 1.0:
        r = 1.0
    elif r < -1.0:
        r = -1.0

    return math.acos(r)

def DotProduct(v1, v2):
    r = 0
    for i in range(len(v1)):
        r += (v1[i] * v2[i])
    return r

def GetAngleBetweenVec3(v1, v2):
    dp = DotProduct(v1, v2)
    v1m = GetVec3Magnitude(v1)
    v2m = GetVec3Magnitude(v2)

    r = dp / (v1m * v2m)
    if r > 1.0:
        r = 1.0
    elif r < -1.0:
        r = -1.0

    return math.acos(r)


def SegmentsIntersect(sp1, sp2, sq1, sq2):
    dx0 = sp2[0] - sp1[0]
    dx1 = sq2[0] - sq1[0]
    dy0 = sp2[1] - sp1[1]
    dy1 = sq2[1] - sq1[1]

    p0 = dy1 * (sq2[0] - sp1[0]) - dx1 * (sq2[1] - sp1[1])
    p1 = dy1 * (sq2[0] - sp2[0]) - dx1 * (sq2[1] - sp2[1])
    p2 = dy0 * (sp2[0] - sq1[0]) - dx0 * (sp2[1] - sq1[1])
    p3 = dy0 * (sp2[0] - sq2[0]) - dx0 * (sp2[1] - sq2[1])

    return (p0 * p1 < 0) & (p2 * p3 < 0)

def GetAngleBetweenSegments(sp1, sp2, sq1, sq2):
    sv1 = GetNormalizedVec2([sp2[0] - sp1[0], sp2[1] - sp1[1]])
    sv2 = GetNormalizedVec2([sq2[0] - sq1[0], sq2[1] - sq1[1]])

    dot = sv1[0] * sv2[0] + sv1[1] * sv2[1]

    return math.acos(dot)

def PointsAreColinear(p1, p2, p3):
    det = p1[0] * p2[1] + p2[0] * p3[1] + p3[0] * p1[1] - p1[0] * p3[1] - p2[0] * p1[1] - p3[0] * p2[1]

    return det == 0

def GetPointOnSegment(p1, p2, d):
    return [(1 - d) * p1[0] + d * p2[0], (1 - d) * p1[1] + d * p2[1]]

def GetDistanceFromSegment(p1, p2, p3):
    p1p2 = [p2[0] - p1[0], p2[1] - p1[1]]
    p3p1 = [p1[0] - p3[0], p1[1] - p3[1]]
    return math.fabs(p1p2[0] * p3p1[1] - p3p1[0] * p1p2[1]) / math.sqrt(GetVec2Magnitude(p1p2))

def PointIsInsideTriangle(p, v1, v2, v3):
    v1px = p[0] - v1[0]
    v1py = p[1] - v1[1]

    pv1v2 = (v2[0] - v1[0]) * v1py - (v2[1] - v1[1]) * v1px > 0

    if ((v3[0] - v1[0]) * v1py - (v3[1] - v1[1]) * v1px > 0) == pv1v2:
        return False

    if ((v3[0] - v2[0]) * (p[1] - v2[1]) - (v3[1] - v2[1]) * (p[0] - v2[0]) > 0) != pv1v2:
        return False

    return True

def GetTriangleArea(v1, v2, v3):
    a = GetVec2Magnitude([v2[0] - v1[0], v2[1] - v1[1]])
    b = GetVec2Magnitude([v3[0] - v2[0], v3[1] - v2[1]])
    c = GetVec2Magnitude([v1[0] - v3[0], v1[1] - v3[1]])

    s = (a + b + c) / 2

    return math.sqrt(s * (s - a) * (s - b) * (s - c))

def GetShapeArea(shape, shapeCenter):
    tri = GetShapeTriangles(shape, shapeCenter)

    area = 0

    for i in tri:
        if PointsAreColinear(i[0], i[1], i[2]) is False:
            area += GetTriangleArea(i[0], i[1], i[2])

    return area

def GetShapeTriangles(shape, shapeCenter):
    tri = []

    for i in range(len(shape) - 1):
        tri.append([shape[i], shapeCenter, shape[i + 1]])
    tri.append([shape[len(shape) - 1], shapeCenter, shape[0]])

    return tri

def CheckIfPointIsInPolygone(point, polyVertices):
    x = point[0]
    y = point[1]
    num = len(polyVertices)
    i = 0
    j = num - 1
    c = False
    for i in range(num):
        if ((polyVertices[i][1] >= y) != (polyVertices[j][1] >= y)) and \
                (x <= polyVertices[i][0] + (polyVertices[j][0] - polyVertices[i][0]) * (y - polyVertices[i][1]) /
                 (polyVertices[j][1] - polyVertices[i][1])):
            c = not c
        j = i
    return c

def CheckAngleBetweenCells(map, c1: [int, int], c2: [int, int]):
    h1 = map[c1[0]][c1[1]][1]
    h2 = map[c2[0]][c2[1]][1]

    return abs(h1 - h2) <= 1

def ConvertAllOmapsToWmaps(overwrite, minWaterAreaSize):
    originalsMapInDirectory = [f for f in listdir(MAPS_FOLDER_PATH) if isfile(join(MAPS_FOLDER_PATH, f))]

    for o in originalsMapInDirectory:
        fileName = o.split('.', 1)

        hasToBeConverted = True

        if overwrite is False and path.isfile("{}{}-WM.json".format(MAPS_MW_FOLDER_PATH, fileName[0])):
            hasToBeConverted = False

        if hasToBeConverted:
            map = MinecraftMapImporter.ImportMap('{}{}'.format(MAPS_FOLDER_PATH, o))

            RiverFinder.FindWaterAreas(minWaterAreaSize, map)

            file = open('{}{}-WM.json'.format(MAPS_MW_FOLDER_PATH, fileName[0]), 'w+')
            file.truncate()
            file.write("{\"lines\":[")
            for x in range(len(map)):
                file.write("[")
                for z in range(len(map[x])):
                    file.write("[{},{}]".format(map[x][z][0], map[x][z][1]))
                    if z < len(map[x]) - 1:
                        file.write(",")
                file.write("]")
                if x < len(map) - 1:
                    file.write(",")

            file.write("]}")
            file.close()


def RunAllWeightPoinsTest(areaSize):
    Colors.InitRGBColorsDictionary()
    settingsInDirectory = [f for f in listdir(SETTINGS_FOLDER_PATH) if isfile(join(SETTINGS_FOLDER_PATH, f))]
    mapsInDirectory = [f for f in listdir(MAPS_FOLDER_PATH) if isfile(join(MAPS_FOLDER_PATH, f))]

    for setFile in settingsInDirectory:
        settingsName = setFile.split('.', 1)
        #settings = Settings.Settings('{}{}'.format(SETTINGS_FOLDER_PATH, setFile))

        for mapFile in mapsInDirectory:
            fileName = mapFile.split('.', 1)
            map = MinecraftMapImporter.ImportMap('{}{}'.format(MAPS_FOLDER_PATH, mapFile))
            #weightPoints = WeightPoint.GenarateWeightPoints(map, areaSize, settings)
            #printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
            #                                                                     WeightPoint.PrintableMode.WATER_SCORE)
            currentDirectory = '{}{}\\{}\\'.format(RESULT_FOLDER_PATH, fileName[0], settingsName[0])

            if not path.isdir(currentDirectory):
                makedirs(currentDirectory)

            #MapToImage.PrintImage(printableWeightPoints,
            #                      '{}WPMap_WaterScore_{}.png'.format(currentDirectory, areaSize))
            #printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
            #                                                                     WeightPoint.PrintableMode.HEIGHT_AVERAGE)
            #MapToImage.PrintImage(printableWeightPoints,
            #                      '{}WPMap_HeightAverage_{}.png'.format(currentDirectory, areaSize))
            #printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
            #                                                                     WeightPoint.PrintableMode.HEIGHT_VARIATION)
            #MapToImage.PrintImage(printableWeightPoints,
            #                      '{}WPMap_HeightVariation_{}.png'.format(currentDirectory, areaSize))
            #printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
            #                                                                     WeightPoint.PrintableMode.TOTAL_SCORE)
            #MapToImage.PrintImage(printableWeightPoints,
            #                      '{}WPMap_TotalScore_{}.png'.format(currentDirectory, areaSize))

            #colorMap = WeightPoint.GenPrintableColorMapWithHighScoreArea(
            #    ColorMapGen.MapToColorMap(map, len(map), len(map[0])), weightPoints, areaSize)
            #MapToImage.PrintImage(colorMap,
            #                      '{}CMap_StartingPoint_{}.png'.format(currentDirectory, areaSize))


def CreateAllColorMap():
    Colors.InitRGBColorsDictionary()

    originalsMapInDirectory = [f for f in listdir(MAPS_FOLDER_PATH) if isfile(join(MAPS_FOLDER_PATH, f))]
    waterMapInDirectory = [f for f in listdir(MAPS_MW_FOLDER_PATH) if isfile(join(MAPS_MW_FOLDER_PATH, f))]

    for file in originalsMapInDirectory:
        fileName = file.split('.', 1)

        currentDirectory = '{}{}\\'.format(RESULT_FOLDER_PATH, fileName[0])

        if not path.isdir(currentDirectory):
            makedirs(currentDirectory)

        map = MinecraftMapImporter.ImportMap('{}{}'.format(MAPS_FOLDER_PATH, file))
        MapToImage.PrintImage(ColorMapGen.MapToColorMap(map, len(map), len(map[0])),
                              '{}ColorMap.png'.format(currentDirectory))

    for file in waterMapInDirectory:
        fileName = file.rsplit('-', 1)

        currentDirectory = '{}{}\\'.format(RESULT_FOLDER_PATH, fileName[0])

        if not path.isdir(currentDirectory):
            makedirs(currentDirectory)

        map = MinecraftMapImporter.ImportWMap('{}{}'.format(MAPS_MW_FOLDER_PATH, file))
        MapToImage.PrintImage(ColorMapGen.MapToColorMap(map, len(map), len(map[0])),
                              '{}ColorWMap.png'.format(currentDirectory))


def CreateAllNodeMap(overwrite):
    originalsMapInDirectory = [f for f in listdir(MAPS_FOLDER_PATH) if isfile(join(MAPS_FOLDER_PATH, f))]
    settingsInDirectory = [f for f in listdir(SETTINGS_FOLDER_PATH) if isfile(join(SETTINGS_FOLDER_PATH, f))]

    for o in originalsMapInDirectory:
        fileName = o.split('.', 1)

        hasToBeConverted = True

        #if overwrite is False and path.isfile("{}{}-NM.json".format(NODE_MAP_FOLDER_PATH, fileName[0])):
        #    hasToBeConverted = False

        if hasToBeConverted:
            map = MinecraftMapImporter.ImportMap('{}{}'.format(MAPS_FOLDER_PATH, o))
            print(fileName[0])
            t1Start = perf_counter()
            nodeMap = Node.CreateNodeGridFromFile('{}{}'.format(MAPS_FOLDER_PATH, o), 30)
            t1Stop = perf_counter()
            print("Node generation time: {}".format(t1Stop - t1Start))
            #Node.SaveNodeMapInFile(nodeMap, "{}{}-NM.json".format(NODE_MAP_FOLDER_PATH, fileName[0]))
            #Node.CreateNodeMapImage(map, nodeMap, fileName[0])

            #for s in settingsInDirectory:
            #    settingsName = s.split('.', 1)
            #    settings = Settings.Settings('{}{}'.format(SETTINGS_FOLDER_PATH, s))

            #    currentDirectory = '{}{}\\{}\\'.format(RESULT_FOLDER_PATH, fileName[0], settingsName[0])

            #    if not path.isdir(currentDirectory):
            #        makedirs(currentDirectory)

            #    scoreMap = Node.CreateScoreMapFromNodeMap(nodeMap, settings)
            #    Node.CreateScoreMapImage(map, scoreMap, nodeMap, fileName[0], settingsName[0])


def CreateAllNodeMapImage():
    originalsMapInDirectory = [f for f in listdir(MAPS_FOLDER_PATH) if isfile(join(MAPS_FOLDER_PATH, f))]

    for o in originalsMapInDirectory:
        fileName = o.split('.', 1)
        map = MinecraftMapImporter.ImportMap('{}{}'.format(MAPS_FOLDER_PATH, o))
        nodeMap = MinecraftMapImporter.ImportNodeMap('{}{}-NM.json'.format(NODE_MAP_FOLDER_PATH, fileName[0]))
        Node.CreateNodeMapImage(map, nodeMap, fileName[0])

def CreateAllScoreHeightImage(areaSize, amountOfPointToKeep, clusterMaxSize, clusterMinAmount, amountOfResults, optEndName='', printDebug=False):
    nodeMapInDirectory = [f for f in listdir(NODE_MAP_FOLDER_PATH) if isfile(join(NODE_MAP_FOLDER_PATH, f))]

    for o in nodeMapInDirectory:
        fileName = o.split('.', 1)
        originalName = fileName[0].rsplit('-', 1)
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(MAPS_FOLDER_PATH, originalName[0]))
        nodeMap = MinecraftMapImporter.ImportNodeMap('{}{}'.format(NODE_MAP_FOLDER_PATH, o))

        currentDirectory = '{}{}\\'.format(RESULT_FOLDER_PATH, originalName[0])

        if not path.isdir(currentDirectory):
            makedirs(currentDirectory)

        print(originalName[0])
        t1Start = perf_counter()
        heightScore = HeightAnalysis.GetPointsBasedOnHeight(nodeMap, areaSize, amountOfPointToKeep, clusterMaxSize, clusterMinAmount, amountOfResults)
        t1Stop = perf_counter()
        print("Height score definition time: {}".format(t1Stop - t1Start))
        #if printDebug:
        #    print('--------------------------------------- {}'.format(fileName))
        #    for i in range(len(heightScore)):
        #        print('--')
        #        print('Point n°{} with position ({};{}) values:'.format(i, heightScore[i][0], heightScore[i][1]))
        #        print('Height average = {}'.format(nodeMap[heightScore[i][2]][heightScore[i][3]].heightAverage))
        #        print('Height directions count = {}'.format(len(nodeMap[heightScore[i][2]][heightScore[i][3]].nearestWaterDirection)))
        #        print('Height variation = {}'.format(heightScore[i][4]))
        #        print('Height score = {}'.format(heightScore[i][5]))
        #        print('--')
        #    print('----------------------------------------------------------------------------------------')

        #Node.CreateScore2MapImage(map, heightScore, originalName[0])
        #Node.CreateScore2MapOnColorMap(ColorMapGen.MapToColorMap(map, len(map), len(map[0])), HeightMapGen.MapToHeightMap(map, len(map), len(map[0])), heightScore, originalName[0], 10, optEndName=optEndName)
        #Node.CreateScore2MapOnColorMapWithArrows(ColorMapGen.MapToColorMap(map, len(map), len(map[0])), HeightMapGen.MapToHeightMap(map, len(map), len(map[0])), heightScore, nodeMap, originalName[0], 10, optEndName=optEndName)

        #waterScore = WaterAnalysis.GetPointsBasedOnWater(nodeMap)
        #Node.CreateScore2MapImage(map, waterScore, originalName[0], Node.SelectionMode.WATER)
        #Node.CreateScore2MapOnColorMap(ColorMapGen.MapToColorMap(map, len(map), len(map[0])), HeightMapGen.MapToHeightMap(map, len(map), len(map[0])), waterScore, originalName[0], 10, Node.SelectionMode.WATER)
        #Node.CreateScore2MapOnColorMapWithArrows(ColorMapGen.MapToColorMap(map, len(map), len(map[0])), HeightMapGen.MapToHeightMap(map, len(map), len(map[0])), waterScore, nodeMap, originalName[0], 10, Node.SelectionMode.WATER)

def createImageGridOfSize(X, Y, borderSize, cellSize):
    grid = np.zeros(
        ((borderSize * X + borderSize) + (cellSize * X), (borderSize * Y + borderSize) + (cellSize * Y), 3), np.uint8)

    for x in range(len(grid)):
        for y in range(len(grid[0])):
            grid[x][y] = Colors.rgbColors['black']

    return grid

def CreateImageFrom2DArray(array, borderSize, cellSize):
    X = len(array)
    Y = len(array[0])

    resultImage = np.zeros(((borderSize * X + borderSize) + (cellSize * X),
                                (borderSize * Y + borderSize) + (cellSize * Y), 3), np.uint8)

    for x in range(X):
        for y in range(Y):
            rx = (cellSize * x) + (borderSize * x) + borderSize
            ry = (cellSize * y) + (borderSize * y) + borderSize

            for i in range(rx, rx + cellSize):
                for j in range(ry, ry + cellSize):
                    resultImage[i][j] = array[x][y]

    return resultImage

def CreateDistrictDataFile(district: Districts.District, directory, minPos: []):
    with open("{}districtData.txt".format(directory), "w") as file:
        if len(district.rp_direction) == 0:
            file.write("District direction: \tUndefined\n")
        else:
            file.write("District direction: \t{}\n".format(district.rp_direction))
        file.write("District circle centers:\n")
        for p in district.rp_circleCenters:
            pr = [p[0] - minPos[0], p[1] - minPos[1]]
            if p is None or len(p) == 0:
                file.write("\tAbsolute: None\t\tRelative: None\n")
            else:
                file.write("\tAbsolute: {}\t\tRelative: {}\n".format(p, pr))
        file.write("District circle radius:\n")
        for p in district.rp_circleRadius:
            file.write("\t{}\n".format(p))
        file.write("District circle points:\n")
        for p in district.rp_circlePoints:
            pr = [p[0] - minPos[0], p[1] - minPos[1]]
            if p is None or len(p) == 0:
                file.write("\tAbsolute: None\t\tRelative: None\n")
            else:
                file.write("\tAbsolute: {}\t\tRelative: {}\n".format(p, pr))
        file.write("District polygon vertices:\n")
        for p in district.rp_polyVertices:
            pr = [p[0] - minPos[0], p[1] - minPos[1]]
            if p is None or len(p) == 0:
                file.write("\tAbsolute: None\t\tRelative: None\n")
            else:
                file.write("\tAbsolute: {}\t\tRelative: {}\n".format(p, pr))

def PrintCityFocusedImage(districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map,
                          districts: [Districts.District], outerWalls, directory, fileName, offset=5):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    # Check if the directory exist
    if not path.isdir(directory):
        makedirs(directory)

    # Define maximum and minimum position of the district
    minPos = [999999, 9999999]
    maxPos = [-1, -1]

    for x in range(dimensionX):
        for y in range(dimensionZ):
            if districtMap.map[x][y] != -1:
                if x < minPos[0]:
                    minPos[0] = x
                if x > maxPos[0]:
                    maxPos[0] = x
                if y < minPos[1]:
                    minPos[1] = y
                if y > maxPos[1]:
                    maxPos[1] = y

    for w in outerWalls:
        for p in w:
            if p[0] < minPos[0]:
                minPos[0] = p[0]
            if p[0] > maxPos[0]:
                maxPos[0] = p[0]
            if p[1] < minPos[1]:
                minPos[1] = p[1]
            if p[1] > maxPos[1]:
                maxPos[1] = p[1]

    # Apply the offset to the minimum and maximum position
    minPos[0] -= offset
    minPos[1] -= offset
    maxPos[0] += offset
    maxPos[1] += offset

    # Check if the new position are not outside the map
    if minPos[0] < 0:
        minPos[0] = 0
    if minPos[1] < 0:
        minPos[1] = 0
    if maxPos[0] >= dimensionX:
        maxPos[0] = dimensionX - 1
    if maxPos[1] >= dimensionZ:
        maxPos[1] = dimensionZ - 1

    newDimensionX = maxPos[0] - minPos[0] + 1
    newDimensionZ = maxPos[1] - minPos[1] + 1

    # Prepare the array focusing on the district
    values = []
    for x in range(newDimensionX):
        values.append([])
        for z in range(newDimensionZ):
            values[len(values) - 1].append([])

    # Write the colors of the map into the array
    for x in range(newDimensionX):
        for z in range(newDimensionZ):
            rx = minPos[0] + x
            rz = minPos[1] + z
            if roadMap.map[rx][rz] == 1:
                values[x][z] = [102, 255, 255]
            else:
                values[x][z] = map[rx][rz]

    for d in districts:
        if type(d) is Districts.Stronghold:
            for i in range(2, len(d.layerCells)):
                for p in d.layerCells[i]:
                    rx = p[0] - minPos[0]
                    rz = p[1] - minPos[1]
                    values[rx][rz] = Colors.rgbColors[wallsColor]

            for p in d.layerCells[0]:
                rx = p[0] - minPos[0]
                rz = p[1] - minPos[1]
                values[rx][rz] = Colors.rgbColors[districtsLayerColor]

            for p in d.layerCells[1]:
                rx = p[0] - minPos[0]
                rz = p[1] - minPos[1]
                values[rx][rz] = Colors.rgbColors[districtsLayerColor]
        else:
            for l in d.layerCells:
                for p in l:
                    rx = p[0] - minPos[0]
                    rz = p[1] - minPos[1]
                    values[rx][rz] = Colors.rgbColors[districtsLayerColor]

        for p in d.innerCells:
            rx = p[0] - minPos[0]
            rz = p[1] - minPos[1]
            values[rx][rz] = Colors.rgbColors[districtsLayerColor]

        for b in d.buildings:
            for p in b.coveredCells:
                rx = p[0] - minPos[0]
                rz = p[1] - minPos[1]
                values[rx][rz] = Colors.rgbColors[b.mapColor]

    for w in outerWalls:
        for p in w:
            rx = p[0] - minPos[0]
            rz = p[1] - minPos[1]
            values[rx][rz] = Colors.rgbColors[wallsColor]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, 0, 1), "{}{}".format(directory, fileName))

def PrintRPImageForDistrict(districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map, district: Districts.District,
                            directory, borderSize, cellSize, offset=5):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    # Check if the directory exist
    if not path.isdir(directory):
        makedirs(directory)

    # Define maximum and minimum position of the district
    minPos = [999999, 9999999]
    maxPos = [-1, -1]
    if district.errorCode == Districts.ErrorCode.NONE:
        for x in range(dimensionX):
            for y in range(dimensionZ):
                if districtMap.map[x][y] == district.id:
                    if x < minPos[0]:
                        minPos[0] = x
                    if x > maxPos[0]:
                        maxPos[0] = x
                    if y < minPos[1]:
                        minPos[1] = y
                    if y > maxPos[1]:
                        maxPos[1] = y
    else:
        for x in range(dimensionX):
            for y in range(dimensionZ):
                if [x, y] in district.areaCells:
                    if x < minPos[0]:
                        minPos[0] = x
                    if x > maxPos[0]:
                        maxPos[0] = x
                    if y < minPos[1]:
                        minPos[1] = y
                    if y > maxPos[1]:
                        maxPos[1] = y

    # Check if a position within the circle is the minimum or maximum position
    for v in district.rp_circlePoints:
        if v[0] < minPos[0]:
            minPos[0] = v[0]
        if v[0] > maxPos[0]:
            maxPos[0] = v[0]
        if v[1] < minPos[1]:
            minPos[1] = v[1]
        if v[1] > maxPos[1]:
            maxPos[1] = v[1]

    # Check if one of the vertices position is the minimum or maximum position
    for v in district.districtVertex:
        if v[0] < minPos[0]:
            minPos[0] = v[0]
        if v[0] > maxPos[0]:
            maxPos[0] = v[0]
        if v[1] < minPos[1]:
            minPos[1] = v[1]
        if v[1] > maxPos[1]:
            maxPos[1] = v[1]

    # Check if the segment point of the district is the minimum or maximum position
    if district.rp_segmentPoint != [-1, -1]:
        if district.rp_segmentPoint[0] < minPos[0]:
            minPos[0] = district.rp_segmentPoint[0]
        if district.rp_segmentPoint[0] > maxPos[0]:
            maxPos[0] = district.rp_segmentPoint[0]
        if district.rp_segmentPoint[1] < minPos[1]:
            minPos[1] = district.rp_segmentPoint[1]
        if district.rp_segmentPoint[1] > maxPos[1]:
            maxPos[1] = district.rp_segmentPoint[1]

    # Apply the offset to the minimum and maximum position
    minPos[0] -= offset
    minPos[1] -= offset
    maxPos[0] += offset
    maxPos[1] += offset

    # Check if the new position are not outside the map
    if minPos[0] < 0:
        minPos[0] = 0
    if minPos[1] < 0:
        minPos[1] = 0
    if maxPos[0] >= dimensionX:
        maxPos[0] = dimensionX - 1
    if maxPos[1] >= dimensionZ:
        maxPos[1] = dimensionZ - 1

    newDimensionX = maxPos[0] - minPos[0] + 1
    newDimensionZ = maxPos[1] - minPos[1] + 1

    # Prepare the array focusing on the district
    values = []
    for x in range(newDimensionX):
        values.append([])
        for z in range(newDimensionZ):
            values[len(values) - 1].append([])

    # Write the colors of the map into the array
    for x in range(newDimensionX):
        for z in range(newDimensionZ):
            rx = minPos[0] + x
            rz = minPos[1] + z
            if districtMap.map[rx][rz] > -1 and districtMap.map[rx][rz] != district.id:
                values[x][z] = Colors.rgbColors[colorList[0]]
            elif roadMap.map[rx][rz] == 1:
                values[x][z] = Colors.rgbColors[colorList[1]]
            else:
                values[x][z] = map[rx][rz]

    if district.errorCode == Districts.ErrorCode.VERTEX_O_F_E:
        CreateDistrictDataFile(district, directory, minPos)
        return

        # Define 1st and 2nd vertex specific colors
    if len(district.districtVertex) >= 1:
        values[district.districtVertex[0][0] - minPos[0]][district.districtVertex[0][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[2]]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize),
                          "{}0_StartingPoint.png".format(directory))

    # Add the link of the 1 to 2 vertex
    for v in district.rp_linking1v2v:
        rx = v[0] - minPos[0]
        rz = v[1] - minPos[1]
        values[rx][rz] = Colors.rgbColors[colorList[7]]

    # Define 1st and 2nd vertex specific colors
    if len(district.districtVertex) >= 1:
        values[district.districtVertex[0][0] - minPos[0]][district.districtVertex[0][1] - minPos[1]] = \
        Colors.rgbColors[colorList[2]]
    if len(district.districtVertex) >= 2:
        values[district.districtVertex[1][0] - minPos[0]][district.districtVertex[1][1] - minPos[1]] = \
        Colors.rgbColors[colorList[3]]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize),
                          "{}1_Link1to2.png".format(directory))

    # Check if an issue has been encountered
    if district.errorCode == Districts.ErrorCode.VERTEX_F_S_E:
        CreateDistrictDataFile(district, directory, minPos)
        return

    # Add the link of the 1 to 3 vertex
    for v in district.rp_linking1v3v:
        rx = v[0] - minPos[0]
        rz = v[1] - minPos[1]
        values[rx][rz] = Colors.rgbColors[colorList[8]]

    # Define 1st and 3rd vertex specific colors
    if len(district.districtVertex) >= 1:
        values[district.districtVertex[0][0] - minPos[0]][district.districtVertex[0][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[2]]
    if len(district.districtVertex) >= 3:
        values[district.districtVertex[2][0] - minPos[0]][district.districtVertex[2][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[4]]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize),
                          "{}2_Link1to3.png".format(directory))

    # Check if an issue has been encountered
    if district.errorCode == Districts.ErrorCode.VERTEX_E or district.errorCode == Districts.ErrorCode.DIR_E_ZERO:
        CreateDistrictDataFile(district, directory, minPos)
        return

    tmpValues = copy.deepcopy(values)
    # Add the definition of the fourth vertex based on circles if applicable
    for v in district.rp_circlePoints:
        rx = v[0] - minPos[0]
        rz = v[1] - minPos[1]
        tmpValues[rx][rz] = Colors.rgbColors[colorList[12]]

    MapToImage.PrintImage(CreateImageFrom2DArray(tmpValues, borderSize, cellSize),
                          "{}3_0_CircleDef.png".format(directory))

    # Otherwise, based on the segment
    if district.rp_segmentPoint != [-1, -1]:
        tmpValues = copy.deepcopy(values)
        rx = district.rp_segmentPoint[0] - minPos[0]
        rz = district.rp_segmentPoint[1] - minPos[1]
        tmpValues[rx][rz] = Colors.rgbColors[colorList[13]]

        MapToImage.PrintImage(CreateImageFrom2DArray(tmpValues, borderSize, cellSize),
                              "{}3_1_SegDef.png".format(directory))

    # Add the link between 2nd to 4th vertex
    for v in district.rp_linking2v4v:
        rx = v[0] - minPos[0]
        rz = v[1] - minPos[1]
        values[rx][rz] = Colors.rgbColors[colorList[9]]

    # Define 2nd and 4th vertex specific colors
    if len(district.districtVertex) >= 2:
        values[district.districtVertex[1][0] - minPos[0]][district.districtVertex[1][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[3]]
    if len(district.districtVertex) >= 4:
        values[district.districtVertex[3][0] - minPos[0]][district.districtVertex[3][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[5]]
    if type(district) is Districts.Residential and len(district.districtVertex) >= 5:
        values[district.districtVertex[4][0] - minPos[0]][district.districtVertex[4][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[6]]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize),
                          "{}4_1_Link2to4.png".format(directory))

    # Check if an issue has been encountered
    if district.errorCode == Districts.ErrorCode.LINK_S_F:
        CreateDistrictDataFile(district, directory, minPos)
        return

    # Add the link between 3rd to 4th vertex
    for v in district.rp_linking3v4v:
        rx = v[0] - minPos[0]
        rz = v[1] - minPos[1]
        values[rx][rz] = Colors.rgbColors[colorList[10]]

    # Define 3nd and 4th vertex specific colors
    if len(district.districtVertex) >= 3:
        values[district.districtVertex[2][0] - minPos[0]][district.districtVertex[2][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[4]]
    if len(district.districtVertex) >= 4:
        values[district.districtVertex[3][0] - minPos[0]][district.districtVertex[3][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[5]]
    if type(district) is Districts.Residential and len(district.districtVertex) >= 5:
        values[district.districtVertex[4][0] - minPos[0]][district.districtVertex[4][1] - minPos[1]] = \
        Colors.rgbColors[
            colorList[6]]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize),
                          "{}4_2_Link3to4.png".format(directory))

    # Check if an issue has been encountered
    if district.errorCode == Districts.ErrorCode.LINK_T_F:
        CreateDistrictDataFile(district, directory, minPos)
        return

    # Add the link between the 4th and 5th vertex (if residential)
    if type(district) is Districts.Residential:
        for v in district.rp_linking4v5v:
            rx = v[0] - minPos[0]
            rz = v[1] - minPos[1]
            values[rx][rz] = Colors.rgbColors[colorList[11]]

        # Define 4th and 5th vertex specific colors
        if len(district.districtVertex) >= 4:
            values[district.districtVertex[3][0] - minPos[0]][district.districtVertex[3][1] - minPos[1]] = \
            Colors.rgbColors[
                colorList[5]]
        if len(district.districtVertex) >= 5:
            values[district.districtVertex[4][0] - minPos[0]][district.districtVertex[4][1] - minPos[1]] = \
            Colors.rgbColors[
                colorList[6]]

        MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize),
                              "{}4_3R_Link4to5.png".format(directory))

    # Add the center of the district
    if len(district.rp_districtCenter) > 0:
        rx = district.rp_districtCenter[0] - minPos[0]
        rz = district.rp_districtCenter[1] - minPos[1]
        values[rx][rz] = Colors.rgbColors[colorList[14]]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize), "{}5_DCenter.png".format(directory))

    # Check if an issue has been encountered
    if district.errorCode == (Districts.ErrorCode.CENTER_OUTSIDE or Districts.ErrorCode.CENTER_ON_BORDER):
        CreateDistrictDataFile(district, directory, minPos)
        return

    # Add the inner district cells
    for v in district.areaCells:
        if v in district.rp_linking1v2v or v in district.rp_linking2v4v or v in district.rp_linking1v3v or v in district.rp_linking3v4v or v in district.districtVertex:
            continue
        else:
            if type(district) is Districts.Residential:
                if v in district.rp_linking4v5v:
                    continue
            rx = v[0] - minPos[0]
            rz = v[1] - minPos[1]
            values[rx][rz] = Colors.rgbColors[colorList[15]]

    MapToImage.PrintImage(CreateImageFrom2DArray(values, borderSize, cellSize), "{}6_Result.png".format(directory))
    CreateDistrictDataFile(district, directory, minPos)

def PrintRPImageForBuildings(districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, buildingMap: Maps.BuildingMap,
                             map, district: Districts.District, directory, borderSize, cellSize, offset=5):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    # Check if the directory exist
    if not path.isdir(directory):
        makedirs(directory)

    # Define maximum and minimum position of the district
    minPos = [999999, 9999999]
    maxPos = [-1, -1]
    if district.errorCode == Districts.ErrorCode.NONE:
        for x in range(dimensionX):
            for y in range(dimensionZ):
                if districtMap.map[x][y] == district.id:
                    if x < minPos[0]:
                        minPos[0] = x
                    if x > maxPos[0]:
                        maxPos[0] = x
                    if y < minPos[1]:
                        minPos[1] = y
                    if y > maxPos[1]:
                        maxPos[1] = y
    else:
        for x in range(dimensionX):
            for y in range(dimensionZ):
                if [x, y] in district.areaCells:
                    if x < minPos[0]:
                        minPos[0] = x
                    if x > maxPos[0]:
                        maxPos[0] = x
                    if y < minPos[1]:
                        minPos[1] = y
                    if y > maxPos[1]:
                        maxPos[1] = y

    # Check if a position within the circle is the minimum or maximum position
    for v in district.rp_circlePoints:
        if v[0] < minPos[0]:
            minPos[0] = v[0]
        if v[0] > maxPos[0]:
            maxPos[0] = v[0]
        if v[1] < minPos[1]:
            minPos[1] = v[1]
        if v[1] > maxPos[1]:
            maxPos[1] = v[1]

    # Check if one of the vertices position is the minimum or maximum position
    for v in district.districtVertex:
        if v[0] < minPos[0]:
            minPos[0] = v[0]
        if v[0] > maxPos[0]:
            maxPos[0] = v[0]
        if v[1] < minPos[1]:
            minPos[1] = v[1]
        if v[1] > maxPos[1]:
            maxPos[1] = v[1]

    # Check if the segment point of the district is the minimum or maximum position
    if district.rp_segmentPoint != [-1, -1]:
        if district.rp_segmentPoint[0] < minPos[0]:
            minPos[0] = district.rp_segmentPoint[0]
        if district.rp_segmentPoint[0] > maxPos[0]:
            maxPos[0] = district.rp_segmentPoint[0]
        if district.rp_segmentPoint[1] < minPos[1]:
            minPos[1] = district.rp_segmentPoint[1]
        if district.rp_segmentPoint[1] > maxPos[1]:
            maxPos[1] = district.rp_segmentPoint[1]

    # Apply the offset to the minimum and maximum position
    minPos[0] -= offset
    minPos[1] -= offset
    maxPos[0] += offset
    maxPos[1] += offset

    # Check if the new position are not outside the map
    if minPos[0] < 0:
        minPos[0] = 0
    if minPos[1] < 0:
        minPos[1] = 0
    if maxPos[0] >= dimensionX:
        maxPos[0] = dimensionX - 1
    if maxPos[1] >= dimensionZ:
        maxPos[1] = dimensionZ - 1

    newDimensionX = maxPos[0] - minPos[0] + 1
    newDimensionZ = maxPos[1] - minPos[1] + 1

    # Prepare the array focusing on the district
    valuesBuilding = []
    valuesLayers = []
    # valuesVertices = []
    valuesMainVertices = []
    for x in range(newDimensionX):
        valuesBuilding.append([])
        valuesLayers.append([])
        # valuesVertices.append([])
        valuesMainVertices.append([])
        for z in range(newDimensionZ):
            valuesBuilding[len(valuesBuilding) - 1].append([])
            valuesLayers[len(valuesLayers) - 1].append([])
            # valuesVertices[len(valuesLayers) - 1].append([])
            valuesMainVertices[len(valuesLayers) - 1].append([])

    # Write the colors of the map into the array
    for x in range(newDimensionX):
        for z in range(newDimensionZ):
            rx = minPos[0] + x
            rz = minPos[1] + z

            if districtMap.map[rx][rz] == district.id:
                valuesBuilding[x][z] = Colors.rgbColors[colorList[15]]
                valuesLayers[x][z] = Colors.rgbColors[colorList[15]]
                # valuesVertices[x][z] = Colors.rgbColors[colorList[15]]
                valuesMainVertices[x][z] = Colors.rgbColors[colorList[15]]
            elif districtMap.map[rx][rz] == -2:
                valuesBuilding[x][z] = Colors.rgbColors[colorList[7]]
                valuesLayers[x][z] = Colors.rgbColors[colorList[7]]
                # valuesVertices[x][z] = Colors.rgbColors[colorList[15]]
                valuesMainVertices[x][z] = Colors.rgbColors[colorList[7]]
            elif districtMap.map[rx][rz] > -1:
                valuesBuilding[x][z] = Colors.rgbColors[colorList[0]]
                valuesLayers[x][z] = Colors.rgbColors[colorList[0]]
                # valuesVertices[x][z] = Colors.rgbColors[colorList[0]]
                valuesMainVertices[x][z] = Colors.rgbColors[colorList[0]]
            elif roadMap.map[rx][rz] == 1:
                valuesBuilding[x][z] = Colors.rgbColors[colorList[1]]
                valuesLayers[x][z] = Colors.rgbColors[colorList[1]]
                # valuesVertices[x][z] = Colors.rgbColors[colorList[1]]
                valuesMainVertices[x][z] = Colors.rgbColors[colorList[1]]
            else:
                valuesBuilding[x][z] = map[rx][rz]
                valuesLayers[x][z] = map[rx][rz]
                # valuesVertices[x][z] = map[rx][rz]
                valuesMainVertices[x][z] = map[rx][rz]

            if buildingMap.map[rx][rz] > -1:
                colorID = buildingMap.map[rx][rz]
                while colorID >= len(Maps.districtColorList):
                    colorID -= len(Maps.districtColorList)
                valuesBuilding[x][z] = Colors.rgbColors[Maps.districtColorList[colorID]]

            # if [rx, rz] in district.rp_polyVertices:
            #    valuesVertices[x][z] = Colors.rgbColors[colorList[9]]

    # Goes over the district layers and set the color values in the array
    for i in range(len(district.layerCells)):
        currentColor = colorList[2 + i]
        for p in district.layerCells[i]:
            rx = p[0] - minPos[0]
            rz = p[1] - minPos[1]
            valuesLayers[rx][rz] = Colors.rgbColors[currentColor]

    for i in range(len(district.districtVertex)):
        colorID = 2 + i
        rx = district.districtVertex[i][0] - minPos[0]
        rz = district.districtVertex[i][1] - minPos[1]
        valuesMainVertices[rx][rz] = Colors.rgbColors[colorList[colorID]]

    MapToImage.PrintImage(CreateImageFrom2DArray(valuesBuilding, borderSize, cellSize),
                          "{}Buildings.png".format(directory))
    MapToImage.PrintImage(CreateImageFrom2DArray(valuesLayers, borderSize, cellSize),
                          "{}Layers.png".format(directory))
    # MapToImage.PrintImage(CreateImageFrom2DArray(valuesVertices, borderSize, cellSize), "{}Vertices.png".format(directory))
    MapToImage.PrintImage(CreateImageFrom2DArray(valuesMainVertices, borderSize, cellSize),
                          "{}MainVertices.png".format(directory))

def PrintResultOnMap(map, districts: [Districts.District], outerWalls):
    for d in districts:
        if type(d) is Districts.Stronghold:
            for i in range(2, len(d.layerCells)):
                for p in d.layerCells[i]:
                    map[p[0]][p[1]] = Colors.rgbColors[wallsColor]

            for p in d.layerCells[1]:
                map[p[0]][p[1]] = Colors.rgbColors[districtsLayerColor]
        else:
            for l in d.layerCells:
                for p in l:
                    map[p[0]][p[1]] = Colors.rgbColors[districtsLayerColor]

        for p in d.innerCells:
            map[p[0]][p[1]] = Colors.rgbColors[districtsLayerColor]

        for b in d.buildings:
            for p in b.coveredCells:
                map[p[0]][p[1]] = Colors.rgbColors[b.mapColor]

    for w in outerWalls:
        for p in w:
            map[p[0]][p[1]] = Colors.rgbColors[wallsColor]

    return map