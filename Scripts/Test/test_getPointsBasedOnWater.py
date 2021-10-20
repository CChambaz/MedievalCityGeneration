from unittest import TestCase
import UtilityMisc
import MinecraftMapImporter
import WaterAnalysis
import ColorMapGen
import PlotGenerator
from time import perf_counter

class TestGetPointsBasedOnWater(TestCase):
    def test_GetPointsBasedOnWater(self):
        angleTolerance = [5, 10, 15, 20, 25, 30]
        labels = ['T1', 'T2', 'T3', 'T4']
        dataLabel = ['WC', 'FP', 'SC', 'CS', 'GS', 'TT']
        datas = [[], [], [], [], [], []]
        for i in range(2, 6):
            fileName = 'ExportedMap64-{}'.format(i)
            print(fileName)
            #filePath = '{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName)
            nodeFilePath = '{}{}-NM.json'.format(UtilityMisc.NODE_MAP_FOLDER_PATH, fileName)

            #map = MinecraftMapImporter.ImportMap(filePath)
            nodeMap = MinecraftMapImporter.ImportNodeMap(nodeFilePath)
            tTotalStart = perf_counter()
            t1Start = perf_counter()
            waterCoasts = WaterAnalysis.GetWaterCoast(nodeMap)
            t1Stop = perf_counter()
            datas[0].append(UtilityMisc.proper_round(t1Stop - t1Start, 2))
            print("Water coast definition time: {}".format(t1Stop - t1Start))
            #WaterAnalysis.PrintWaterCoast(map, waterCoasts, nodeMap, fileName, extension='WOD')
            t1Start = perf_counter()
            flexionPoints = WaterAnalysis.GetFlexionPoints(waterCoasts)
            t1Stop = perf_counter()
            datas[1].append(UtilityMisc.proper_round(t1Stop - t1Start, 2))
            print("Flexion point definition time: {}".format(t1Stop - t1Start))
            #WaterAnalysis.PrintWaterCoastWithFlexionPoints(map, waterCoasts, flexionPoints, nodeMap, fileName, extension='FPM')
            #newFlexionPoints = WaterAnalysis.SecondPassOnFlexionPoints(waterCoasts, flexionPoints)
            #WaterAnalysis.PrintWaterCoastWithFlexionPoints(map, waterCoasts, newFlexionPoints, nodeMap, fileName, extension='2')
            #for j in angleTolerance:
            #reducedFlexionPoints = WaterAnalysis.ReduceFlexionPoints(nodeMap, waterCoasts, flexionPoints, 75)
            #WaterAnalysis.PrintWaterCoastWithReducedFlexionPoints(map, waterCoasts, reducedFlexionPoints, nodeMap,
            #                                                          fileName, extension='Segment')
            #triangles = WaterAnalysis.CreateTrianglesFromFlexionPoints(nodeMap, waterCoasts, flexionPoints)
            #orderedTriangles = WaterAnalysis.GetTriangleWithTheHighestSurface(triangles, perWaterCoast=False)
            #WaterAnalysis.PrintWaterCoastWithTriangles(map, waterCoasts, nodeMap, triangles, fileName, extension='')
            #WaterAnalysis.PrintWaterCoastWithTriangles(map, waterCoasts, nodeMap, orderedTriangles, fileName, extension='O')
            t1Start = perf_counter()
            shapes = WaterAnalysis.CreateShapeFromFlexionPoints(nodeMap, waterCoasts, flexionPoints)
            t1Stop = perf_counter()
            datas[2].append(UtilityMisc.proper_round(t1Stop - t1Start, 2))
            print("Shape creation time: {}".format(t1Stop - t1Start))
            t1Start = perf_counter()
            clearedShapes = WaterAnalysis.ClearShapes(nodeMap, waterCoasts, flexionPoints, shapes)
            t1Stop = perf_counter()
            datas[3].append(UtilityMisc.proper_round(t1Stop - t1Start, 2))
            print("Clearing shape time: {}".format(t1Stop - t1Start))
            #bestShapes = WaterAnalysis.GetShapeWithHighestArea(clearedShapes, perWaterCoast=True)
            #WaterAnalysis.PrintWaterCoastWithShapes(map, waterCoasts, nodeMap, shapes, fileName, extension='')
            #WaterAnalysis.PrintWaterCoastWithShapes(map, waterCoasts, nodeMap, clearedShapes, fileName, extension='C')
            #WaterAnalysis.PrintWaterCoastWithShapes(map, waterCoasts, nodeMap, bestShapes, fileName, extension='FPM')
            t1Start = perf_counter()
            bestShapes = WaterAnalysis.GetShapeWithHighestArea(clearedShapes, perWaterCoast=False)
            t1Stop = perf_counter()
            datas[4].append(UtilityMisc.proper_round(t1Stop - t1Start, 2))
            print("Getting best shape time: {}".format(t1Stop - t1Start))

            tTotalEnd = perf_counter()
            datas[5].append(UtilityMisc.proper_round(tTotalEnd - tTotalStart, 2))
            print("Total time: {}".format(tTotalEnd - tTotalStart))
            #bestShape = []

            #for i in bestShapes:
            #    if len(i) == 0:
            #        continue

            #    bestShape = i[0]

            #WaterAnalysis.PrintResultPointOnColorMap(ColorMapGen.MapToColorMap(map, len(map), len(map[0])), bestShape, 10, fileName, extension='SAFROCM')

        PlotGenerator.GenerateBarChart(labels, dataLabel, datas, 'Water based research execution time', 'Time (seconds)', barWidth=0.35)
        self.assertTrue(True, "Test completed")
