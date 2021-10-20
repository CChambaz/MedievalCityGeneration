from unittest import TestCase

import MinecraftMapImporter


class TestMinecraftMapImporter(TestCase):
    def test_ImportMap(self):
        map = MinecraftMapImporter.ImportMap('C:\\Users\\Cedric\\Desktop\\ExportedMap64.json')
        print("Block value at 10:30 : Type = {}; PosY = {}".format(map[10][30][0], map[10][30][1]))
        self.assertTrue(True, "Test completed")