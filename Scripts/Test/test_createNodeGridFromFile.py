from unittest import TestCase
import Node
import UtilityMisc
import os.path
import MinecraftMapImporter


class TestCreateNodeGridFromFile(TestCase):
    def test_CreateNodeGridFromFile(self):
        #UtilityMisc.CreateAllNodeMapImage()
        #return
        fileName = 'ExportedMap-16'
        filePath = '{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName)
        nodeFilePath = '{}{}-NM.json'.format(UtilityMisc.NODE_MAP_FOLDER_PATH, fileName)

        if not os.path.isdir(UtilityMisc.NODE_MAP_FOLDER_PATH):
            os.makedirs(UtilityMisc.NODE_MAP_FOLDER_PATH)

        UtilityMisc.CreateAllNodeMap(True)
        return
        map = MinecraftMapImporter.ImportMap(filePath)
        #nodeMap = MinecraftMapImporter.ImportNodeMap(nodeFilePath)
        #Node.CreateNodeMapImage(map, nodeMap, fileName)

        #return
        nodeMap = Node.CreateNodeGridFromFile(filePath, 30)
        Node.SaveNodeMapInFile(nodeMap, nodeFilePath)
        Node.CreateNodeMapImage(map, nodeMap, fileName)
        self.assertTrue(True, "Test completed")
