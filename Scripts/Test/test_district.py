from unittest import TestCase
import numpy as np
import sys
import math
import copy
from os import makedirs
from os import path
from enum import Enum
import datetime

# Custom import
import UtilityMisc
import MinecraftMapImporter
import HeightAnalysis
import WaterAnalysis
import PathGenerator
import AStar
import Maps
import Districts
import Buildings
import ColorMapGen
import HeightMapGen
import MapToImage
import Colors
import GenerationFinalisation

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

class TestDistrict(TestCase):
    def test_DefineDistrictArea(self):
        Colors.InitRGBColorsDictionary()
        imageBorderCellSize = 2
        imageCellSize = 5

        for x in range(3, 4):
            for z in range(0, 5):
                for y in range(0, 1):
                    # General informations
                    UtilityMisc.SEED_ID = z
                    seed = testedSeed[z]
                    print("Currently tested seed: {}".format(seed))
                    fileName = "ExportedMap64-{}".format(x)
                    directoryName = "{}\\{}\\{}\\{}\\".format(UtilityMisc.RESULT_FOLDER_PATH, fileName,
                                                            "RP\\DistrictDefinition", seed)
                    map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName))
                    nodeMap = MinecraftMapImporter.ImportNodeMap(
                        '{}{}-NM.json'.format(UtilityMisc.NODE_MAP_FOLDER_PATH, fileName))
                    colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                    extension = "DD"
    
                    # Check if the directory exist
                    if not path.isdir(directoryName):
                        makedirs(directoryName)
    
                    # Define the terrain analysis method to apply
                    # Also define the initial district type (WATER = Residential, HEIGHT = Stronghold)
                    researchType = ResearchType.WATER
                    if y == 1:
                        researchType = ResearchType.HEIGHT

                    rType = "W"
                    if researchType == ResearchType.HEIGHT:
                        rType = "H"
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
    
                    #print(startingPoint)
                    # Pathfinding parameters
                    pp_OverwriteFiles = False
                    AStar.SLOPE_AMPLIFIER = 32
                    AStar.WATER_WEIGHT = 200
                    AStar.MAX_WATER_CROSSED = 40
                    PathGenerator.CONE_ANGLE = (60 * math.pi) / 180
                    pp_amountOfPath = 4

                    # Define multiple roads to the result point of the previous analysis
                    roadMap = Maps.RoadMap(map)
                    rmDirectory = "{}{}\\{}\\".format(Maps.ROAD_MAPS_FOLDER_PATH, rType, seed)
                    rmFileName = "{}.txt".format(fileName)
                    if pp_OverwriteFiles is False and path.isfile("{}{}".format(rmDirectory, rmFileName)):
                        print("Loading existing path")
                        roadMap.LoadMapFromFile(rmDirectory, rmFileName)
                    else:
                        print("Started road generation ad {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        PathGenerator.GetMultiplePath(map, startingPoint, roadMap, pp_amountOfPath, seed)
                        print("Saving generated path...")
                        roadMap.SaveMapInFile(rmDirectory, rmFileName)

                    #continue
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
                    districtGenIterationAmount = 6
                    dd_crossWater = True
    
                    # Define the initial district area
                    if researchType == ResearchType.HEIGHT:
                        #print("Initial district is a stronghold")
                        initialDistrict = Districts.Stronghold()
                    else:
                        #print("Initial district is a residential")
                        initialDistrict = Districts.Residential(0)
    
                    districts = [initialDistrict]
                    directoryCount = 0
    
                    print("Start initial district area definition")
                    districtMap.AddDistrictToMap(
                        initialDistrict.DefineInitialDistrictArea(startingPoint, districtMap, roadMap, map, seed), 0)
                    #PrintRPImageForDistrict(districtMap, roadMap, colorMap, initialDistrict, "{}{}\\".format(directoryName, directoryCount), imageBorderCellSize, imageCellSize)
                    #directoryCount += 1
    
                    currentDistrictID = 1
                    previouslyDefinedDistricts = []
                    newlyDefinedDistricts = [0]
                    # Add districts
                    print("Start adding districts")
                    for i in range(districtGenIterationAmount):
                        print("Start iteration {} out of {}".format(i + 1, districtGenIterationAmount))
                        #if not path.isdir("{}_IT{}\\".format(directoryName, i)):
                        #    makedirs("{}_IT{}\\".format(directoryName, i))
                        previouslyDefinedDistricts = copy.deepcopy(newlyDefinedDistricts)
                        #newlyDefinedDistricts = []
                        #print("Definition of the valid points relative to the roads")
                        validPoints = districtMap.GetRoadStartingPoints(roadMap, map, previouslyDefinedDistricts,
                                                                        crossWater=dd_crossWater)
    
                        #districtImage = districtMap.DrawMapOnMap(colorMap)
                        #roadImage = roadMap.DrawMapOnMap(districtImage)
                        #MapToImage.PrintImage(CreateImageFrom2DArray(roadImage, imageBorderCellSize, imageCellSize), "{}_IT{}\\R.png".format(directoryName, i))
                        #pointsImage = districtMap.DrawValidPointsOnMap(roadImage, validPoints)
                        #MapToImage.PrintImage(CreateImageFrom2DArray(pointsImage, imageBorderCellSize, imageCellSize),
                        #                      "{}_IT{}\\R-VP.png".format(directoryName, i))
    
                        #print("Generating districts close to the roads")
                        for p in validPoints:
                            newDistrict = Districts.District(id=currentDistrictID)
                            #print("ID: {}".format(currentDistrictID))
                            districtArea = newDistrict.DefineDistrictAreaBasedOnRoads(p, districtMap, roadMap, map, seed)
                            if len(districtArea) > 0:
                                districtMap.AddDistrictToMap(districtArea, currentDistrictID)
                                newlyDefinedDistricts.append(currentDistrictID)
                                districts.append(newDistrict)
                                currentDistrictID += 1
                            #PrintRPImageForDistrict(districtMap, roadMap, colorMap, newDistrict,
                            #                        "{}{}\\".format(directoryName, directoryCount), imageBorderCellSize,
                            #                        imageCellSize)
                            #directoryCount += 1
    
                        #print("Definition of the valid points based on the districts")
                        validPoints = districtMap.GetDistrictStartingPoints(roadMap, map, previouslyDefinedDistricts)
                        #districtImage = districtMap.DrawMapOnMap(colorMap)
                        #roadImage = roadMap.DrawMapOnMap(districtImage)
                        #MapToImage.PrintImage(CreateImageFrom2DArray(roadImage, imageBorderCellSize, imageCellSize),
                        #                      "{}_IT{}\\D.png".format(directoryName, i))
                        #pointsImage = districtMap.DrawValidPointsOnMap(roadImage, validPoints)
                        #MapToImage.PrintImage(CreateImageFrom2DArray(pointsImage, imageBorderCellSize, imageCellSize),
                        #                      "{}_IT{}\\D-VP.png".format(directoryName, i))
    
                        #print("Generate districts")
                        for p in validPoints:
                            newDistrict = Districts.District(id=currentDistrictID)
                            #print("ID: {}".format(currentDistrictID))
                            districtArea = newDistrict.DefineDistrictArea(p, districtMap, roadMap, map, seed)
                            if len(districtArea) > 0:
                                districtMap.AddDistrictToMap(districtArea, currentDistrictID)
                                newlyDefinedDistricts.append(currentDistrictID)
                                districts.append(newDistrict)
                                currentDistrictID += 1
                            #PrintRPImageForDistrict(districtMap, roadMap, colorMap, newDistrict,
                            #                    "{}{}\\".format(directoryName, directoryCount), imageBorderCellSize,
                            #                    imageCellSize)
                            #directoryCount += 1
    
                    print("Ended district generation")
                    directoryName = "{}\\{}\\{}\\{}\\{}\\".format(UtilityMisc.RESULT_FOLDER_PATH, fileName,
                                                            "RP", rType, seed)
    
                    if not path.isdir("{}".format(directoryName)):
                        makedirs("{}".format(directoryName))
    
                    #colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                    #roadImage = roadMap.DrawMapOnMap(colorMap)
                    #districtImage = districtMap.DrawMapOnMap(roadImage, uniformColor=True)
                    #MapToImage.PrintImage(CreateImageFrom2DArray(districtImage, imageBorderCellSize, imageCellSize),
                    #                    "{}_Result_0.png".format(directoryName))
    
                    buildingMap = Maps.BuildingMap(map)
                    orderedDistricts = sorted(districts, key=lambda d: len(d.areaCells), reverse=True)
                    dd_LayerAmount = 2
                    directoryCount = 0
                    churchesCenters = []
                    print("Definition of the districts layers and buildings placement")
                    for d in orderedDistricts:
                        d.PlaceBuildings(dd_LayerAmount, districtMap, buildingMap, roadMap, map, seed, churchesCenters)
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
                        #if type(d) is Districts.Stronghold:
                        #    PrintRPImageForBuildings(districtMap, roadMap, buildingMap, colorMap, d,
                        #                    "{}{}\\".format(directoryName, directoryCount), imageBorderCellSize,
                        #                    imageCellSize)
                        #    directoryCount += 1
    
                    #colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                    #roadImage = roadMap.DrawMapOnMap(colorMap)
                    #districtImage = districtMap.DrawMapOnMap(roadImage, uniformColor=True)
                    #buildingImage = buildingMap.DrawMapOnMap(districtImage, uniformColor=True)
                    #MapToImage.PrintImage(CreateImageFrom2DArray(buildingImage, imageBorderCellSize, imageCellSize),
                    #                    "{}_Result_1.png".format(directoryName))
    
                    print("Start to generate districts with the unused district cells")
                    newDistricts = []
                    for i in range(len(districtMap.map)):
                        for j in range(len(districtMap.map[0])):
                            if districtMap.map[i][j] == -2:
                                d = GenerationFinalisation.DefineDistrictFromUnusedCells([i, j], districtMap, currentDistrictID)
                                if len(d.areaCells) > 1:
                                    newDistricts.append(copy.deepcopy(d))
                                    districtMap.AddDistrictToMap(d.areaCells, currentDistrictID)
                                    currentDistrictID += 1
    
                    print("Start the building generation for the newly defined districts")
                    for d in newDistricts:
                        d.PlaceBuildings(dd_LayerAmount, districtMap, buildingMap, roadMap, map, seed, churchesCenters)
                        #if len(d.areaCells) > 1:
                        #    PrintRPImageForBuildings(districtMap, roadMap, buildingMap, colorMap, d,
                        #                         "{}{}\\".format(directoryName, directoryCount), imageBorderCellSize,
                        #                         imageCellSize)
                        #    directoryCount += 1

                    districts.extend(newDistricts)
                    #colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                    #roadImage = roadMap.DrawMapOnMap(colorMap)
                    #districtImage = districtMap.DrawMapOnMap(roadImage, uniformColor=True)
                    #buildingImage = buildingMap.DrawMapOnMap(districtImage, uniformColor=True)
                    #MapToImage.PrintImage(CreateImageFrom2DArray(buildingImage, imageBorderCellSize, imageCellSize),
                    #                    "{}_Result_2.png".format(directoryName))
    
                    GenerationFinalisation.OUTER_WALLS_THIKNESS = 3
    
                    # Fill the gaps of the district map
                    districtMap.FillDistrictsGaps(map)
                    wallsLinkingPoints = []
                    if not(len(districts) == 1 and type(districts[0]) is Districts.Stronghold):
                        print("Definition of the city shape")
                        cityShape = GenerationFinalisation.DefineCityShapes(map, districtMap)
                        print("Amount of shape returned: {}".format(len(cityShape)))
                        #colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                        #roadImage = roadMap.DrawMapOnMap(colorMap)
                        #districtImage = districtMap.DrawMapOnMap(roadImage, uniformColor=True)
                        #buildingImage = buildingMap.DrawMapOnMap(districtImage, uniformColor=True)
                        #shapeImage = GenerationFinalisation.PrintCityShapesOnMap(buildingImage, cityShape)
                        #MapToImage.PrintImage(CreateImageFrom2DArray(shapeImage, imageBorderCellSize, imageCellSize),
                        #                    "{}_Result_3.png".format(directoryName))
    
                        #validShapes = GenerationFinalisation.ClearCityShapes(cityShape)
                        #print("Amount of valid shape: {}".format(len(validShapes)))
                        print("Walls placement")
                        wallsLinkingPoints = GenerationFinalisation.PlaceOuterWalls(districtMap, map, cityShape)
                        print("Finished placement of outer walls")
                        #colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                        #roadImage = roadMap.DrawMapOnMap(colorMap)
                        #districtImage = districtMap.DrawMapOnMap(roadImage, uniformColor=True)
                        #buildingImage = buildingMap.DrawMapOnMap(districtImage, uniformColor=True)
                        #shapeImage = GenerationFinalisation.PrintCityShapesOnMap(buildingImage, wallsLinkingPoints)
                        #MapToImage.PrintImage(CreateImageFrom2DArray(shapeImage, imageBorderCellSize, imageCellSize),
                        #                    "{}_Result_4.png".format(directoryName))

                    colorMap = ColorMapGen.MapToColorMap(map, len(map), len(map[0]))
                    UtilityMisc.PrintCityFocusedImage(districtMap, roadMap, colorMap, districts, wallsLinkingPoints, directoryName, "_Result_Focused_ColorMap.png")
                    roadImage = roadMap.DrawMapOnMap(colorMap)
                    finalImage = UtilityMisc.PrintResultOnMap(roadImage, districts, wallsLinkingPoints)
                    MapToImage.PrintImage(finalImage, "{}_Result_ColorMap.png".format(directoryName))

                    heightMap = HeightMapGen.MapToHeightMap(map, len(map), len(map[0]))
                    UtilityMisc.PrintCityFocusedImage(districtMap, roadMap, heightMap, districts, wallsLinkingPoints, directoryName,
                                          "_Result_Focused_HeightMap.png")
                    roadImage = roadMap.DrawMapOnMap(heightMap)
                    finalImage = UtilityMisc.PrintResultOnMap(roadImage, districts, wallsLinkingPoints)
                    MapToImage.PrintImage(finalImage, "{}_Result_HeightMap.png".format(directoryName))

        self.assertTrue(True, "Test completed")
