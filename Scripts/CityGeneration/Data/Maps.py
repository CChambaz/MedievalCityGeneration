import Utility.UtilityMisc as UtilityMisc
import ImagePrinter.MapToImage as MapToImage
import Utility.Colors as Colors
import copy
from os import makedirs
from os import path

ROAD_MAPS_FOLDER_PATH = 'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\Files\\Maps\\RoadMaps\\'

districtColorList = [
    "crimson",              # 0
    "azure",                # 1
    "blue",                 # 2
    "darkgreen",            # 3
    "aliceblue",            # 4
    "antiquewhite",         # 5
    "aqua",                 # 6
    "aquamarine",           # 7
    "bisque",               # 8
    "blanchedalmond",       # 9
    "blueviolet"            # 10
    ]
buildingColorList = [
    "burlywood",
    "cadetblue",
    "chartreuse",
    "chocolate",
    "coral",
    "cornflowerblue",
    "cornsilk",
    "crimson",
    "darkblue",
    "darkgoldenrod",
    "darkgray",
    "darkkhaki",
    "darkmagenta",
    "darkolivegreen",
    "darkorange",
    "darkorchid",
    "darkred",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "deeppink",
    "deepskyblue",
    "dimgray",
    "dimgrey",
    "dodgerblue",
    "floralwhite",
    "forestgreen",
    "fuchsia",
    "gainsboro",
    "ghostwhite",
    "goldenrod",
    "greenyellow",
    "grey",
    "honeydew",
    "hotpink",
    "indianred",
    "indigo",
    "ivory",
    "khaki",
    "lavender",
    "lavenderblush",
    "lawngreen",
    "lemonchiffon",
    "lightblue",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgrey",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "lime",
    "limegreen",
    "linen",
    "magenta",
    "maroon",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "oldlace",
    "olive",
    "olivedrab",
    "orange",
    "orangered",
    "orchid",
    "palegoldenrod",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "pink",
    "plum",
    "powderblue",
    "purple",
    "rebeccapurple",
    "red",
    "rosybrown",
    "royalblue",
    "salmon",
    "sandybrown",
    "seagreen",
    "seashell",
    "silver",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "springgreen",
    "steelblue",
    "tan",
    "teal",
    "thistle",
    "tomato",
    "turquoise",
    "violet",
    "wheat",
    "whitesmoke",
    "yellow",
    "yellowgreen",
]

class Map:
    map: []
    defaultCellValue: int

    def __init__(self, map):
        dimensionX = len(map)
        dimensionZ = len(map[0])

        self.map = []
        for x in range(dimensionX):
            self.map.append([])
            for z in range(dimensionZ):
                self.map[x].append(self.defaultCellValue)

    def DrawMapOnMap(self, map, uniformColor=False):
        return

    def SaveMapInFile(self, directory, fileName):
        return

    def LoadMapFromFile(self, directory, fileName):
        return

class RoadMap(Map):
    defaultCellValue = 0

    def AddPathToRoadMap(self, path):
        for id in path:
            self.map[id[0]][id[1]] = 1

    def DrawMapOnMap(self, map, uniformColor=False):
        colorToApplyOnColorMap = [102, 255, 255]

        for x in range(len(self.map)):
            for z in range(len(self.map[0])):
                if self.map[x][z] == 1:
                    map[x][z] = colorToApplyOnColorMap

        return map

    def SaveMapInFile(self, directory, fileName):
        if not path.isdir("{}".format(directory)):
            makedirs("{}".format(directory))

        with open("{}{}".format(directory, fileName), "w") as file:
            for x in range(len(self.map)):
                for z in range(len(self.map[0])):
                    if z != 0:
                        file.write(";")
                    file.write("{}".format(self.map[x][z]))
                file.write("\n")

    def LoadMapFromFile(self, directory, fileName):
        with open("{}{}".format(directory, fileName), "r") as file:
            values = file.readlines()
            for x in range(len(values)):
                subValues = values[x].split(";")
                for y in range(len(subValues)):
                    self.map[x][y] = int(subValues[y])

class DistrictMap(Map):
    defaultCellValue = -1

    def AddDistrictToMap(self, districtArea, id):
        for c in districtArea:
            self.map[c[0]][c[1]] = id

    def DrawMapOnMap(self, map, uniformColor=False):
        Colors.InitRGBColorsDictionary()

        for x in range(len(self.map)):
            for z in range(len(self.map[0])):
                if self.map[x][z] > -1:
                    if uniformColor:
                        map[x][z] = Colors.rgbColors['darkgray']
                    else:
                        colorID = self.map[x][z]
                        while colorID >= len(districtColorList):
                            colorID -= len(districtColorList)
                        map[x][z] = Colors.rgbColors[districtColorList[colorID]]

        return map

    def DrawValidPointsOnMap(self, map, points):
        Colors.InitRGBColorsDictionary()

        for p in points:
            map[p[0]][p[1]] = Colors.rgbColors["yellowgreen"]

        return map

    def GetRoadStartingPoints(self, roadMap: RoadMap, map, concernedDistrict, crossWater=False):
        roadPoints = []
        for x in range(len(self.map)):
            for z in range(len(self.map[0])):
                if roadMap.map[x][z] == 1 and self.map[x][z] in concernedDistrict:
                    neighbors = UtilityMisc.GetCellNeighborsOnBiMap(self.map, x, z)
                    isEnteringPoint = False
                    isBorderedByLand = False

                    for n in neighbors:
                        if self.map[n[0]][n[1]] < 0:
                            if roadMap.map[n[0]][n[1]] == 1:
                                isEnteringPoint = True

                            if map[n[0]][n[1]][0] != 29:
                                isBorderedByLand = True

                    if isEnteringPoint:
                        if isBorderedByLand:
                            roadPoints.append([x, z])
                        elif crossWater:
                            #print("Start crossing water")
                            visitedCells = []
                            propagatingCells = [[x, z]]
                            while len(propagatingCells) > 0:
                                currentlyPropagatingCells = copy.deepcopy(propagatingCells)
                                for c in currentlyPropagatingCells:
                                    propagatingCells.remove(c)
                                    visitedCells.append(c)
                                    neighbors = UtilityMisc.GetCellNeighborsOnBiMap(self.map, c[0], c[1])
                                    isBorderedByLand = False
                                    for n in neighbors:
                                        if self.map[n[0]][n[1]] > -1 or map[n[0]][n[1]][0] != 29 or roadMap.map[n[0]][n[1]] == 0 or n in visitedCells:
                                            continue

                                        nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(self.map, n[0], n[1])
                                        for nn in nNeighbors:
                                            if self.map[nn[0]][nn[1]] > -1 or map[nn[0]][nn[1]][0] == 29 or roadMap.map[nn[0]][nn[1]] == 0 or nn in visitedCells:
                                                continue

                                            isBorderedByLand = True

                                        if isBorderedByLand:
                                            #print("Starting point has been found: {}".format(n))
                                            roadPoints.append(n)
                                            break

                                        #print("Added to propagating cells: {}".format(n))
                                        propagatingCells.append(n)

                                    if isBorderedByLand:
                                        break

                                if isBorderedByLand:
                                    #print("Another point has been found accross the water")
                                    break

        return roadPoints

    def GetDistrictStartingPoints(self, roadMap: RoadMap, map, concernedDistricts):
        # Define all the valid points
        #print("Definition of all the valid points")
        validPoints = []
        pointsValues = []
        for x in range(len(map)):
            for z in range(len(map)):
                if map[x][z][0] == 29 or self.map[x][z] > -1:
                    continue

                neighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, x, z)
                registeredDistricts = []
                cellDistricts = []
                waterAmount = 0

                for n in neighbors:
                    if map[n[0]][n[1]][0] == 29:
                        waterAmount += 1
                        continue

                    if self.map[n[0]][n[1]] > -1:# and self.map[n[0]][n[1]] in concernedDistricts:
                        cellDistricts.append(n)
                        if self.map[n[0]][n[1]] not in registeredDistricts:
                            registeredDistricts.append(self.map[n[0]][n[1]])

                if (waterAmount > 0 and len(registeredDistricts) > 0) or len(registeredDistricts) > 1:
                #if len(registeredDistricts) > 1:
                    validPoints.append([x, z])
                    pointsValues.append(len(cellDistricts) + waterAmount)

        return validPoints
        # Define the clusters formed by the valid points
        print("Defining the groups formed by the valid points")
        groups = []
        visitedCells = []
        for v in validPoints:
            currentGroup = []
            propagatingCells = [v]

            if v in visitedCells:
                continue

            while len(propagatingCells) > 0:
                currentlyPropgatingCells = copy.deepcopy(propagatingCells)

                for c in currentlyPropgatingCells:
                    propagatingCells.remove(c)
                    if c in visitedCells:
                        continue

                    currentGroup.append(c)
                    visitedCells.append(c)
                    neighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, c[0], c[1], omitDiagonals=True)
                    for n in neighbors:
                        if n in validPoints and n not in visitedCells:
                            propagatingCells.append(n)

            if len(currentGroup) > 0:
                groups.append(currentGroup)

        # Define the cell that is the most interesting within the groups
        print("Defining the most interesting points in the grouped points")
        returnedPoints = []
        for g in groups:
            maxValue = 0
            maxID = 0
            for v in range(len(g)):
                currentValue = 0
                # Get v id in validPoints
                for i in range(len(validPoints)):
                    if validPoints[i] == g[v]:
                        currentValue = pointsValues[i]
                        break

                if maxValue < currentValue:
                    maxValue = currentValue
                    maxID = v

            returnedPoints.append(g[maxID])

        print("Finished defining the most interesting starting points")
        return returnedPoints
        #return validPoints

    def FillDistrictsGaps(self, map):
        cellHasBeenAdded = True

        while cellHasBeenAdded:
            cellHasBeenAdded = False
            for i in range(len(self.map)):
                for j in range(len(self.map[0])):
                    if map[i][j][0] == 29 or self.map[i][j] != -1:
                        continue

                    neighbours = UtilityMisc.GetCellNeighborsOnBiMap(self.map, i, j)

                    amountOfCityCells = 0
                    for n in neighbours:
                        if self.map[n[0]][n[1]] != -1:
                            amountOfCityCells += 1

                    if amountOfCityCells >= 5:
                        self.map[i][j] = -2
                        cellHasBeenAdded = True


class BuildingMap(Map):
    defaultCellValue = -1

    def DrawMapOnMap(self, map, uniformColor=False):
        Colors.InitRGBColorsDictionary()

        for x in range(len(self.map)):
            for z in range(len(self.map[0])):
                if self.map[x][z] > -1:
                    colorID = self.map[x][z]
                    if uniformColor:
                        colorID = 120
                    else:
                        while colorID >= len(buildingColorList):
                            colorID -= len(buildingColorList)
                    map[x][z] = Colors.rgbColors[buildingColorList[colorID]]

        return map

    def AddBuildingToMap(self, buildingArea, id):
        for c in buildingArea:
            self.map[c[0]][c[1]] = id