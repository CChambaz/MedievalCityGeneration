import TerrainAnalyse.Node.Cluster as Cluster
import Utility.UtilityMisc as UtilityMisc
import Importer.MinecraftMapImporter as MinecraftMapImporter
from os import makedirs
from os import path
from os import listdir
from os.path import isfile, join
from time import perf_counter

def GetPointsBasedOnHeight(nodeMap, areaSize, amountOfPointToKeep, clusterMaxSize, clusterMinAmount, amountOfResults):
    # Get base height score list
    t1Start = perf_counter()
    heightScore = DefineHeightVariation(nodeMap, areaSize)
    t1Stop = perf_counter()
    #print("Height variation time: {}".format(t1Stop - t1Start))

    t1Start = perf_counter()
    DefineHeightScores(nodeMap, heightScore)
    t1Stop = perf_counter()
    #print("Height score time: {}".format(t1Stop - t1Start))

    t1Start = perf_counter()
    #heightScore.sort(key=lambda x: x[2], reverse=True)
    heightScore.sort(key=lambda x: x[5], reverse=True)

    del heightScore[amountOfPointToKeep:len(heightScore)]

    # Remove clusters
    if clusterMinAmount != 0:
        heightScore = Cluster.RemoveClustersFromList(heightScore, clusterMaxSize, clusterMinAmount)

    #heightScore.sort(key=lambda x: x[2], reverse=True)
    heightScore.sort(key=lambda x: x[5], reverse=True)

    # del sortedHeightList[int(math.ceil((setting.minPercentage * len(sortedHeightList)) / 100)):len(sortedHeightList)]
    if amountOfResults != amountOfPointToKeep:
        del heightScore[amountOfResults:len(heightScore)]

    t1Stop = perf_counter()
    #print("Ordering height score time: {}".format(t1Stop - t1Start))

    return [heightScore[0][0], heightScore[0][1]]

def GetMinimumHeight(nodeMap):
    dimensionX = len(nodeMap)
    dimensionZ = len(nodeMap[0])

    minHeight = 999999

    for x in range(dimensionX):
        for z in range(dimensionZ):
            if nodeMap[x][z].heightAverage < minHeight:
                minHeight = nodeMap[x][z].heightAverage

    return minHeight

def DefineHeightScores(nodeMap, heightScores):
    dimensionX = len(nodeMap)
    dimensionZ = len(nodeMap[0])

    minHeight = GetMinimumHeight(nodeMap)

    #sortedHeightList = []

    for i in range(len(heightScores)):
        x = heightScores[i][2]
        z = heightScores[i][3]
        heightScores[i].append((nodeMap[x][z].heightAverage - minHeight - heightScores[i][4]) * (len(nodeMap[x][z].nearestWaterDirection)))

    #for x in range(dimensionX):
     #   for z in range(dimensionZ):
      #      if nodeMap[x][z].nearestWaterDistance == 0:
       #         continue

        #    sortedHeightList.append([nodeMap[x][z].position[0], nodeMap[x][z].position[1],
         #                            (nodeMap[x][z].heightAverage) * len(nodeMap[x][z].nearestWaterDirection)])

    #sortedHeightList.sort(key=lambda x: x[2], reverse=True)

    #del sortedHeightList[int(math.ceil((setting.minPercentage * len(sortedHeightList)) / 100)):len(sortedHeightList)]
    #del sortedHeightList[amountOfPointToKeep:len(sortedHeightList)]

    #sortedHeightList = RemoveClustersFromList(sortedHeightList, 140, 50)
    #return sortedHeightList

def DefineHeightVariation(nodeMap, areaSize):
    dimensionX = len(nodeMap)
    dimensionZ = len(nodeMap[0])

    halfAreaSize = int(UtilityMisc.proper_round(areaSize / 2))

    heightScores = []

    for x in range(dimensionX):
        for z in range(dimensionZ):
            if nodeMap[x][z].nearestWaterDistance == 0:
                continue

            minHeight = 99999
            maxHeight = 0
            for i in range(-halfAreaSize, halfAreaSize):
                for j in range(-halfAreaSize, halfAreaSize):
                    currentX = x + i
                    currentZ = z + j

                    if currentX < 0 or currentZ < 0 or currentX >= dimensionX or currentZ >= dimensionZ or nodeMap[currentX][currentZ].nearestWaterDistance == 0:
                        continue

                    if nodeMap[currentX][currentZ].heightAverage > maxHeight:
                        maxHeight = nodeMap[currentX][currentZ].heightAverage

                    if nodeMap[currentX][currentZ].heightAverage < minHeight:
                        minHeight = nodeMap[currentX][currentZ].heightAverage

            heightScores.append([nodeMap[x][z].position[0], nodeMap[x][z].position[1], x, z, maxHeight - minHeight])

    return heightScores

if __name__ == '__main__':
    nodeMapInDirectory = [f for f in listdir(UtilityMisc.NODE_MAP_FOLDER_PATH) if isfile(join(UtilityMisc.NODE_MAP_FOLDER_PATH, f))]

    for o in nodeMapInDirectory:
        fileName = o.split('.', 1)
        originalName = fileName[0].rsplit('-', 1)
        map = MinecraftMapImporter.ImportMap('{}{}.json'.format(UtilityMisc.MAPS_FOLDER_PATH, originalName[0]))
        nodeMap = MinecraftMapImporter.ImportNodeMap('{}{}'.format(UtilityMisc.NODE_MAP_FOLDER_PATH, o))

        currentDirectory = '{}{}\\'.format(UtilityMisc.RESULT_FOLDER_PATH, originalName[0])

        if not path.isdir(currentDirectory):
            makedirs(currentDirectory)

        print(originalName[0])
        t1Start = perf_counter()
        heightScore = GetPointsBasedOnHeight(nodeMap, 10, 1, 0, 0, 1)
        t1Stop = perf_counter()
        print("Height score definition time: {}".format(t1Stop - t1Start))