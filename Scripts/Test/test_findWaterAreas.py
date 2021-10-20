from unittest import TestCase

import Colors
import MinecraftMapImporter
import WeightPoint
import MapToImage
import Settings
import UtilityMisc
import ColorMapGen
import os.path
import RiverFinder
import json

class TestFindWaterAreas(TestCase):
    def test_FindWaterAreas(self):
        minWaterAreaSize = 2000
        UtilityMisc.ConvertAllOmapsToWmaps(True, minWaterAreaSize)
        return
        fileName = 'ExportedMap64-2'
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName))

        RiverFinder.FindWaterAreas(minWaterAreaSize, map)

        file = open('{}{}-WM.json'.format(UtilityMisc.MAPS_MW_FOLDER_PATH, fileName), 'w+')

        file.write("{")
        for x in range(len(map)):
            file.write("\"{}\":[".format(x))
            for z in range(len(map[x])):
                file.write("[{},{}]".format(map[x][z][0], map[x][z][1]))
                if z < len(map[x]) - 1:
                    file.write(",")
            file.write("]")
            if x < len(map) - 1:
                file.write(",")

        file.write("}")
        file.close()
