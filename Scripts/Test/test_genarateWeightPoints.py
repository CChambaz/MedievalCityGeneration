from unittest import TestCase

import math
import Colors
import MinecraftMapImporter
import WeightPoint
import MapToImage
import Settings
import UtilityMisc
import ColorMapGen
import HeightMapGen
import os.path

class TestGenarateWeightPoints(TestCase):
    def test_GenarateWeightPoints(self):
        #Colors.InitRGBColorsDictionary()
        areaSize = 200

        UtilityMisc.RunAllWeightPoinsTest(areaSize)
        return

        fileName = 'ExportedMap64-5'
        settingsName = 'Settings1'
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName))
        settings = Settings.Settings('{}{}.json'.format(UtilityMisc.SETTINGS_FOLDER_PATH, settingsName))
        weightPoints = WeightPoint.GenarateWeightPoints(map, areaSize, settings)

        #colorMapWithWeightPoints = WeightPoint.GenPrintableColorMapWithAllWeightPoints(
         #   HeightMapGen.MapToHeightMap(map, len(map), len(map[0])), weightPoints, areaSize)
        #MapToImage.PrintImage(colorMapWithWeightPoints,
          #                    '{}{}\\WPHeightMap_{}.png'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName, areaSize))

        #bestWayPoint = WeightPoint.GetBestWeightPoint(map, areaSize, weightPoints, settings)
        #return

        printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
                                                                             WeightPoint.PrintableMode.WATER_SCORE)

        currentDirectory = '{}{}\\{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName, settingsName)

        if not os.path.isdir(currentDirectory):
            os.makedirs(currentDirectory)

        MapToImage.PrintImage(printableWeightPoints,
                              '{}WPMap_WaterScore_{}.png'.format(currentDirectory, areaSize))
        printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
                                                                             WeightPoint.PrintableMode.HEIGHT_AVERAGE)
        MapToImage.PrintImage(printableWeightPoints,
                              '{}WPMap_HeightAverage_{}.png'.format(currentDirectory, areaSize))
        printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
                                                                             WeightPoint.PrintableMode.HEIGHT_VARIATION)
        MapToImage.PrintImage(printableWeightPoints,
                              '{}WPMap_HeightVariation_{}.png'.format(currentDirectory, areaSize))
        printableWeightPoints = WeightPoint.GeneratePrintableWeightPointsMap(map, weightPoints, areaSize,
                                                                             WeightPoint.PrintableMode.TOTAL_SCORE)
        MapToImage.PrintImage(printableWeightPoints,
                              '{}WPMap_TotalScore_{}.png'.format(currentDirectory, areaSize))

        colorMap = WeightPoint.GenPrintableColorMapWithHighScoreArea(
                              ColorMapGen.MapToColorMap(map, len(map), len(map[0])), weightPoints, areaSize)
        MapToImage.PrintImage(colorMap,
                              '{}CMap_StartingPoint_{}.png'.format(currentDirectory, areaSize))

        self.assertTrue(True, "Test completed")
