from unittest import TestCase
import Node
import UtilityMisc
import MinecraftMapImporter
import Settings
import HeightAnalysis

class TestCreateScoreMapImage(TestCase):
    def test_CreateScoreMapImage(self):
        #areaSize = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        areaSize = [10]
        amountOfPointToKeep = 200
        amountOfResults = 1
        clusterMaxSize = 140
        clusterMinAmount = 50

        UtilityMisc.CreateAllScoreHeightImage(10, amountOfPointToKeep, clusterMaxSize, clusterMinAmount, amountOfResults)
        return

        #extension = 'WMNA1R{}CR0'.format(amountOfResults)
        #UtilityMisc.CreateAllScoreHeightImage(10, amountOfPointToKeep, clusterMaxSize, clusterMinAmount, amountOfResults, optEndName=extension)

        # Generate results with height average and cluster removal and single result
        #for i in areaSize:
         #   extension = 'WM{}CR{}AS{}RA{}'.format(amountOfPointToKeep, clusterMinAmount, i, amountOfResults)
          #  UtilityMisc.CreateAllScoreHeightImage(i, amountOfPointToKeep, clusterMaxSize, clusterMinAmount, amountOfResults, optEndName=extension)

        clusterMinAmount = 0
        amountOfResults = amountOfPointToKeep

        # Generate results with height average without cluster removal and multiple results
        for i in areaSize:
            extension = 'WMMH{}CR{}AS{}RA{}'.format(amountOfPointToKeep, clusterMinAmount, i, amountOfResults)
            UtilityMisc.CreateAllScoreHeightImage(i, amountOfPointToKeep, clusterMaxSize, clusterMinAmount, amountOfResults, optEndName=extension)

        amountOfResults = 5
        # Generate results with height average without cluster removal and five results
        for i in areaSize:
            extension = 'WMMH{}CR{}AS{}RA{}'.format(amountOfPointToKeep, clusterMinAmount, i, amountOfResults)
            UtilityMisc.CreateAllScoreHeightImage(i, amountOfPointToKeep, clusterMaxSize, clusterMinAmount,
                                                  amountOfResults, optEndName=extension)

        amountOfResults = 1
        # Generate results with height average without cluster removal and single results
        for i in areaSize:
            extension = 'WMMH{}CR{}AS{}RA{}'.format(amountOfPointToKeep, clusterMinAmount, i, amountOfResults)
            UtilityMisc.CreateAllScoreHeightImage(i, amountOfPointToKeep, clusterMaxSize, clusterMinAmount,
                                                      amountOfResults, optEndName=extension, printDebug=False)
        return
        fileName = 'ExportedMap-16'
        settingsName = 'Settings1'
        filePath = '{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, fileName)
        nodeFilePath = '{}{}-NM.json'.format(UtilityMisc.NODE_MAP_FOLDER_PATH, fileName)
        settings = Settings.Settings('{}{}.json'.format(UtilityMisc.SETTINGS_FOLDER_PATH, settingsName))

        map = MinecraftMapImporter.ImportMap(filePath)
        nodeMap = MinecraftMapImporter.ImportNodeMap(nodeFilePath)
        scoreMap = Node.CreateScoreMapFromNodeMap(nodeMap, settings)
        heightScore = HeightAnalysis.GetHighestHeightNodes(nodeMap)

        Node.CreateScore2MapImage(map, heightScore, fileName)
        #Node.CreateScoreMapImage(map, scoreMap, nodeMap, fileName, settingsName)
        self.assertTrue(True, "Test completed")
