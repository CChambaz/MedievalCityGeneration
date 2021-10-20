from unittest import TestCase
import Colors
import MCUtil

class TestPrintColors(TestCase):
    def test_PrintColors(self):
        Colors.InitRGBColorsDictionary()
        for i in MCUtil.TerrainTypeColor:
            print("Terrain type with ID {} is colored with {} {}".format(i, MCUtil.TerrainTypeColor[i], Colors.rgbColors[MCUtil.TerrainTypeColor[i]]))
        self.assertTrue(True, "Test completed")
