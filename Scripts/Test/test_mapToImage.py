from unittest import TestCase
import MinecraftMapImporter
import MapToImage
from MapToImage import MapType
import Colors
import UtilityMisc
import HeightMapGen
import ColorMapGen
import WaterAccessMap
import os.path

class TestMapToImage(TestCase):
    def test_MapToImage(self):
        UtilityMisc.CreateAllColorMap()
        return
        Colors.InitRGBColorsDictionary()
        fileName = 'ExportedMap16'
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName))
        wMap = MinecraftMapImporter.ImportWMap('{}{}-WM.json'.format(UtilityMisc.MAPS_MW_FOLDER_PATH, fileName))
        currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, fileName)

        if not os.path.isdir(currentDirectory):
            os.makedirs(currentDirectory)

        dimensionX = len(map)
        dimensionZ = len(map[0])

        MapToImage.PrintImage(ColorMapGen.MapToColorMap(map, dimensionX, dimensionZ),
                              '{}ColorMap.png'.format(currentDirectory))
        MapToImage.PrintImage(ColorMapGen.MapToColorMap(wMap, len(wMap), len(wMap[0])),
                              '{}ColorWMap.png'.format(currentDirectory))
        MapToImage.PrintImage(HeightMapGen.MapToHeightMap(map, dimensionX, dimensionZ),
                              '{}HeightMap.png'.format(currentDirectory))
        #MapToImage.PrintImage(WaterAccessMap.GetPrintableWaterAccessMap(map, dimensionX, dimensionZ),
         #                     '{}WaterAccessMap.png'.format(currentDirectory))
        self.assertTrue(True, "Test completed")
