# File used to go through all the process of the city generation, from the terrain analysis to the final layout

# Standard import
from enum import Enum
import sys
import math
import copy
from os import makedirs
from os import path
from time import perf_counter

# Custom import
import Utility.UtilityMisc as UtilityMisc
import Importer.MinecraftMapImporter as MinecraftMapImporter
import TerrainAnalyse.Node.HeightAnalysis as HeightAnalysis
import TerrainAnalyse.Node.WaterAnalysis as WaterAnalysis
import CityGeneration.PathGenerator as PathGenerator
import Pathfinding.AStar as AStar
import CityGeneration.Data.Maps as Maps
import CityGeneration.Data.Districts as Districts
import CityGeneration.Data.Buildings as Buildings
import MapGenerator.ColorMapGen as ColorMapGen
import MapGenerator.HeightMapGen as HeightMapGen
import CityGeneration.GenerationFinalisation as GenerationFinalisation
import Utility.CSVCreator as CSVCreator
import ImagePrinter.MapToImage as MapToImage


class ResearchType(Enum):
    HEIGHT = 1
    WATER = 2

testedSeed = [
    200895,     # 0 | OK - 71
    140618,     # 1 | OK - 71
    80768,      # 2 | OK - 31
    562051,     # 3 | ~OK - 54 - Three districts are not fully filled
    369852      # 4 | ~OK - 65 - Two districts are not fully filled
]

if __name__ == '__main__':
    for x in range(2, 3):
        for z in range(0, 5):
            for y in range(0, 2):
                # General informations
                UtilityMisc.SEED_ID = z
                seed = testedSeed[z]
                fileName = "ExportedMap64-{}".format(x)
                rType = "W"
                if y == 1:
                    rType = "H"
                print("Current test: {} - {} - {}".format(fileName, rType, seed))
                directoryName = "{}\\{}\\{}\\{}\\{}\\".format(UtilityMisc.RESULT_FOLDER_PATH, fileName,
                                                              "RP", rType, seed)
                map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName))
                nodeMap = MinecraftMapImporter.ImportNodeMap(
                    '{}{}-NM.json'.format(UtilityMisc.NODE_MAP_FOLDER_PATH, fileName))
                colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                extension = "DD"

                UtilityMisc.gCSVFile = CSVCreator.CSVFile()
                UtilityMisc.gCSVFile.AddRow()
                #UtilityMisc.gCSVFile.AddDataToRow("SDT")
                #UtilityMisc.gCSVFile.AddDataToRow("SA1")
                #UtilityMisc.gCSVFile.AddDataToRow("SVT")
                #UtilityMisc.gCSVFile.AddDataToRow("SA2")
                UtilityMisc.gCSVFile.AddDataToRow("")
                UtilityMisc.gCSVFile.AddDataToRow("Time")
                UtilityMisc.gCSVFile.AddDataToRow("Status")
                generalCSV = CSVCreator.CSVFile()
                generalCSV.AddRow()
                generalCSV.AddDataToRow("")
                generalCSV.AddDataToRow("DGT")
                generalCSV.AddDataToRow("BPT")
                generalCSV.AddDataToRow("NDDT")
                generalCSV.AddDataToRow("NDBPT")
                generalCSV.AddDataToRow("FDGT")
                generalCSV.AddDataToRow("CSDT")
                generalCSV.AddDataToRow("OWPT")
                generalCSV.AddRow()
                generalCSV.AddDataToRow("Time")
                districtCSV = CSVCreator.CSVFile()
                districtCSV.AddRow()
                districtCSV.AddDataToRow("ID")
                districtCSV.AddDataToRow("GT")
                districtCSV.AddDataToRow("BPT")

                # Check if the directory exist
                if not path.isdir(directoryName):
                    makedirs(directoryName)

                # Define the terrain analysis method to apply
                # Also define the initial district type (WATER = Residential, HEIGHT = Stronghold)
                researchType = ResearchType.WATER
                if y == 1:
                    researchType = ResearchType.HEIGHT

                # Point used as the first cell of the city core
                startingPoint = [-1, -1]

                # Height analysis parameters
                ha_areaSize = 10
                ha_amountOfPointToKeep = 1
                ha_clusterMaxSize = 0
                ha_clusterMinAmount = 0
                ha_amountOfResult = 1

                # Get a starting point based on the height or water analysis if a starting point has not been defined manually
                if startingPoint == [-1, -1]:
                    if researchType == ResearchType.HEIGHT:
                        startingPoint = HeightAnalysis.GetPointsBasedOnHeight(
                            nodeMap, ha_areaSize, ha_amountOfPointToKeep, ha_clusterMaxSize, ha_clusterMinAmount,
                            ha_amountOfResult)
                        extension = "{}H".format(extension)
                    elif researchType == ResearchType.WATER:
                        startingPoint = WaterAnalysis.GetPointsBasedOnWater(nodeMap)
                        extension = "{}W".format(extension)
                    else:
                        sys.exit("No research type specified, abortion...")

                # Pathfinding parameters
                pp_OverwriteFiles = False
                AStar.SLOPE_AMPLIFIER = 32
                AStar.WATER_WEIGHT = 200
                AStar.MAX_WATER_CROSSED = 40
                PathGenerator.CONE_ANGLE = (60 * math.pi) / 180
                pp_amountOfPath = 4

                # District parameters
                Districts.INITIAL_AREA_SIZE = math.pow(15, 2)
                Districts.MIN_MOVEMENT = 10
                Districts.MAX_MOVEMENT = 30
                Districts.MIN_DISTANCE = 5
                Districts.MAX_DISTANCE = 15
                Districts.SEGMENT_MIN_RATIO = 0.4
                Districts.SEGMENT_MAX_RATIO = 0.6
                Districts.RADIUS_MIN_OFFSET = 0.1
                Districts.RADIUS_MAX_OFFSET = 0.8
                Districts.DISTANCE_TO_CENTER_WEIGHT = 2
                Districts.MIN_DISTANCE_TO_SEGMENT = 20
                Districts.GATE_DEAD_ZONE_RADIUS = 2
                Districts.CHURCH_INFLUENCE_RADIUS = 40
                districtMap = Maps.DistrictMap(map)
                districtGenIterationAmount = 12
                dd_crossWater = True

                dd_LayerAmount = 2
                churchesCenters = []
                GenerationFinalisation.OUTER_WALLS_THIKNESS = 3

                buildingMap = Maps.BuildingMap(map)
                # Define multiple roads to the result point of the previous analysis
                roadMap = Maps.RoadMap(map)
                rmDirectory = "{}{}\\{}\\".format(Maps.ROAD_MAPS_FOLDER_PATH, rType, seed)
                rmFileName = "{}.txt".format(fileName)
                if pp_OverwriteFiles is False and path.isfile("{}{}".format(rmDirectory, rmFileName)):
                    roadMap.LoadMapFromFile(rmDirectory, rmFileName)
                else:
                    PathGenerator.GetMultiplePath(map, startingPoint, roadMap, pp_amountOfPath, seed)
                    roadMap.SaveMapInFile(rmDirectory, rmFileName)
                    UtilityMisc.gCSVFile.SaveFile(directoryName, "RoadGenTimes")

                if researchType == ResearchType.HEIGHT:
                    initialDistrict = Districts.Stronghold()
                else:
                    initialDistrict = Districts.Residential(0)

                districts = [initialDistrict]

                t1Start = perf_counter()
                t2Start = perf_counter()
                districtMap.AddDistrictToMap(
                    initialDistrict.DefineInitialDistrictArea(startingPoint, districtMap, roadMap, map, seed), 0)
                t2Stop = perf_counter()
                districtCSV.AddRow()
                districtCSV.AddDataToRow(0)
                districtCSV.AddDataToRow(t2Stop - t2Start)

                currentDistrictID = 1
                newlyDefinedDistricts = [0]
                # Add districts
                for i in range(districtGenIterationAmount):
                    validPoints = districtMap.GetRoadStartingPoints(roadMap, map, newlyDefinedDistricts,
                                                                    crossWater=dd_crossWater)

                    for p in validPoints:
                        t2Start = perf_counter()
                        newDistrict = Districts.District(id=currentDistrictID)
                        districtArea = newDistrict.DefineDistrictAreaBasedOnRoads(p, districtMap, roadMap, map, seed)
                        if len(districtArea) > 0:
                            districtMap.AddDistrictToMap(districtArea, currentDistrictID)
                            t2Stop = perf_counter()
                            districtCSV.AddRow()
                            districtCSV.AddDataToRow(currentDistrictID)
                            districtCSV.AddDataToRow(t2Stop - t2Start)
                            newlyDefinedDistricts.append(currentDistrictID)
                            districts.append(newDistrict)
                            currentDistrictID += 1

                    validPoints = districtMap.GetDistrictStartingPoints(roadMap, map, newlyDefinedDistricts)
                    for p in validPoints:
                        t2Start = perf_counter()
                        newDistrict = Districts.District(id=currentDistrictID)
                        districtArea = newDistrict.DefineDistrictArea(p, districtMap, roadMap, map, seed)
                        if len(districtArea) > 0:
                            districtMap.AddDistrictToMap(districtArea, currentDistrictID)
                            t2Stop = perf_counter()
                            districtCSV.AddRow()
                            districtCSV.AddDataToRow(currentDistrictID)
                            districtCSV.AddDataToRow(t2Stop - t2Start)
                            newlyDefinedDistricts.append(currentDistrictID)
                            districts.append(newDistrict)
                            currentDistrictID += 1

                t1Stop = perf_counter()
                generalCSV.AddDataToRow(t1Stop - t1Start)
                t1Start = perf_counter()
                orderedDistricts = sorted(districts, key=lambda d: len(d.areaCells), reverse=True)
                for d in orderedDistricts:
                    t2Start = perf_counter()
                    d.PlaceBuildings(dd_LayerAmount, districtMap, buildingMap, roadMap, map, seed, churchesCenters)
                    t2Stop = perf_counter()
                    districtCSV.AddDataToRow(t2Stop - t2Start, d.id + 1)
                    # Check if a church has been placed
                    for b in d.buildings:
                        if type(b) is Buildings.Church:
                            # Define the center of the church
                            center = [0, 0]
                            for p in b.coveredCells:
                                center[0] += p[0]
                                center[1] += p[1]
                            center = [int(center[0] / len(b.coveredCells)), int(center[1] / len(b.coveredCells))]
                            churchesCenters.append(copy.deepcopy(center))

                t1Stop = perf_counter()
                generalCSV.AddDataToRow(t1Stop - t1Start)
                t1Start = perf_counter()
                newDistricts = []
                for i in range(len(districtMap.map)):
                    for j in range(len(districtMap.map[0])):
                        if districtMap.map[i][j] == -2:
                            t2Start = perf_counter()
                            d = GenerationFinalisation.DefineDistrictFromUnusedCells([i, j], districtMap,
                                                                                     currentDistrictID)
                            if len(d.areaCells) > 1:
                                districtMap.AddDistrictToMap(d.areaCells, currentDistrictID)
                                t2Stop = perf_counter()
                                districtCSV.AddRow()
                                districtCSV.AddDataToRow(currentDistrictID)
                                districtCSV.AddDataToRow(t2Stop - t2Start)
                                newDistricts.append(copy.deepcopy(d))
                                currentDistrictID += 1
                t1Stop = perf_counter()
                generalCSV.AddDataToRow(t1Stop - t1Start)
                t1Start = perf_counter()

                for d in newDistricts:
                    t2Start = perf_counter()
                    d.PlaceBuildings(dd_LayerAmount, districtMap, buildingMap, roadMap, map, seed, churchesCenters)
                    t2Stop = perf_counter()
                    if len(d.buildings) > 0:
                        districtCSV.AddDataToRow(t2Stop - t2Start, d.id + 1)

                t1Stop = perf_counter()
                generalCSV.AddDataToRow(t1Stop - t1Start)
                t1Start = perf_counter()

                # Fill the gaps of the district map
                districtMap.FillDistrictsGaps(map)

                t1Stop = perf_counter()
                generalCSV.AddDataToRow(t1Stop - t1Start)
                t1Start = perf_counter()

                cityShape = GenerationFinalisation.DefineCityShapes(map, districtMap)

                t1Stop = perf_counter()
                generalCSV.AddDataToRow(t1Stop - t1Start)
                t1Start = perf_counter()
                wallsLinkingPoints = GenerationFinalisation.PlaceOuterWalls(districtMap, map, cityShape)
                t1Stop = perf_counter()
                generalCSV.AddDataToRow(t1Stop - t1Start)

                #generalCSV.SaveFile(directoryName, "GeneralTimes")
                #districtCSV.SaveFile(directoryName, "DistrictsTime")
                #UtilityMisc.gCSVFile.SaveFile(directoryName, "CSDT")
                colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                UtilityMisc.PrintCityFocusedImage(districtMap, roadMap, colorMap, districts, wallsLinkingPoints,
                                                  directoryName, "_Result_Focused_ColorMap.png")
                roadImage = roadMap.DrawMapOnMap(colorMap)
                finalImage = UtilityMisc.PrintResultOnMap(roadImage, districts, wallsLinkingPoints)
                MapToImage.PrintImage(finalImage, "{}_Result_ColorMap.png".format(directoryName))

                #heightMap = HeightMapGen.MapToHeightMap(map, len(map), len(map[0]))
                #UtilityMisc.PrintCityFocusedImage(districtMap, roadMap, heightMap, districts, wallsLinkingPoints,
                #                                  directoryName,
                #                                  "_Result_Focused_HeightMap.png")
                #roadImage = roadMap.DrawMapOnMap(heightMap)
                #finalImage = UtilityMisc.PrintResultOnMap(roadImage, districts, wallsLinkingPoints)
                #MapToImage.PrintImage(finalImage, "{}_Result_HeightMap.png".format(directoryName))

    sys.exit(0)