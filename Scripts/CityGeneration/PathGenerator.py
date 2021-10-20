import Pathfinding.AStar as AStar
import Utility.UtilityMisc as UtilityMisc
import random
import Importer.MinecraftMapImporter as MinecraftMapImporter
import MapGenerator.ColorMapGen as ColorMapGen
import math
import CityGeneration.Data.Maps as Maps
import Utility.CSVCreator as CSVCreator
from time import perf_counter
import datetime

global CONE_ANGLE
availibleCells = []


def SetConeAngle(angle):
    CONE_ANGLE = (angle * math.pi) / 180


class AvailibleCells:
    cells: []

    def __init__(self, map):
        dimensionX = len(map)
        dimensionZ = len(map[0])

        self.cells = []
        # Left column
        for x in range(dimensionX):
            if map[x][0][0] != 29 and map[x][0][0] != 40:
                self.cells.append([x, 0])

        # Right column
        for x in range(dimensionX):
            if map[x][dimensionZ - 1][0] != 29 and map[x][dimensionZ - 1][0] != 40:
                self.cells.append([x, dimensionZ - 1])

        # Top row
        for z in range(1, dimensionZ - 1):
            if map[0][z][0] != 29 and map[0][z][0] != 40:
                self.cells.append([0, z])

        # Bottom row
        for z in range(1, dimensionZ - 1):
            if map[dimensionX - 1][z][0] != 29 and map[dimensionX - 1][z][0] != 40:
                self.cells.append([dimensionX - 1, z])

    def GetPointOnBorder(self, map, p, seed):
        seed += 1
        random.seed(seed)

        if len(self.cells) == 0:
            return [-1, -1]

        point = self.cells[random.randrange(0, len(self.cells))]
        direction = [point[0] - p[0], point[1] - p[1]]
        direction = UtilityMisc.GetNormalizedVec2(direction)

        validCells = []

        for id in self.cells:
            v = [id[0] - p[0], id[1] - p[1]]
            a = UtilityMisc.GetAngleBetweenVec2(direction, v)

            if a <= CONE_ANGLE / 2:
                validCells.append(id)

        minHeight = 99999
        for vc in validCells:
            if map[vc[0]][vc[1]][1] < minHeight:
                minHeight = map[vc[0]][vc[1]][1]

        lowestCells = []
        for vc in validCells:
            if map[vc[0]][vc[1]][1] == minHeight:
                lowestCells.append(vc)

        returnedCell = lowestCells[random.randrange(0, len(lowestCells))]
        direction = [returnedCell[0] - p[0], returnedCell[1] - p[1]]
        validCells = []
        for id in self.cells:
            v = [id[0] - p[0], id[1] - p[1]]
            a = UtilityMisc.GetAngleBetweenVec2(direction, v)

            if a <= CONE_ANGLE / 2:
                validCells.append(id)

        for id in validCells:
            self.cells.remove(id)

        return returnedCell


def GetMultiplePath(map, basePoint, roadMap: Maps.RoadMap, amountOfPath, seed):
    borderingCells = AvailibleCells(map)

    point = borderingCells.GetPointOnBorder(map, basePoint, seed)

    while point != [-1, -1] and amountOfPath > 0:
        print("Started road generation at {} | Path left to generate: {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), amountOfPath))
        #print("Current point: {} | Goal point type: {} | Path left to generate: {}".format(point, map[basePoint[0]][basePoint[1]][0], amountOfPath))
        amountOfPath -= 1
        #roadMap.AddPathToRoadMap(AStar.GetPathFromTo(basePoint, point, map, roadMap.map))
        UtilityMisc.gCSVFile.AddRow()
        UtilityMisc.gCSVFile.AddDataToRow(amountOfPath)
        t1Start = perf_counter()
        path = AStar.GetPathFromTo(point, basePoint, map, roadMap.map)
        roadMap.AddPathToRoadMap(path)
        t1Stop = perf_counter()
        UtilityMisc.gCSVFile.AddDataToRow(t1Stop - t1Start)
        if len(path) > 0:
            UtilityMisc.gCSVFile.AddDataToRow('C')
        else:
            UtilityMisc.gCSVFile.AddDataToRow('A')
        point = borderingCells.GetPointOnBorder(map, basePoint, seed)

if __name__ == '__main__':
    AStar.SLOPE_AMPLIFIER = 32
    AStar.WATER_WEIGHT = 400
    AStar.MAX_WATER_CROSSED = 40
    basePoint = [750, 750]
    seed = 200895

    for x in range(2, 6):
        fileName = "ExportedMap64-{}".format(x)
        print("Start generating path for {}".format(fileName))
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName))
        ext = "SM{}-8".format(AStar.SLOPE_AMPLIFIER)

        roadMap = Maps.RoadMap(map)
        borderingCells = AvailibleCells(map)
        point = borderingCells.GetPointOnBorder(map, basePoint, seed)
        amountOfPath = 1

        while point != [-1, -1] and amountOfPath > 0:
            amountOfPath -= 1
            roadMap.AddPathToRoadMap(AStar.GetPathFromTo(point, basePoint, map, roadMap.map))
            point = borderingCells.GetPointOnBorder(map, basePoint, seed)

        roadMap.DrawMapOnMap(ColorMapGen.MapToColorMap(map, len(map), len(map[0])), "O11", fileName, extension=ext)
        print("Ended generating path for {}".format(fileName))

    print("Success!")