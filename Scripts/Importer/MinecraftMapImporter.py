import json
import math
import TerrainAnalyse.Node.Node as Node

def ImportMap(filePath):
    file = open(filePath, "r")
    data = json.load(file)
    file.close()
    dimension = data['dimension']
    chunkSize = 16
    chunkIterator = 0
    map = []

    # Fill the array with empty values
    for x in range(dimension * chunkSize):
        map.append([])
        for z in range(dimension * chunkSize):
            map[x].append([])

    # Export the datat from the file to the array
    for chunks in data['chunks']:
        blockIterator = 0
        for block in chunks['blocks']:
            xIndex = 0
            if blockIterator == 0:
                xIndex = (chunkIterator % dimension) * chunkSize
            else:
                xIndex = (chunkIterator % dimension) * chunkSize + blockIterator % chunkSize

            zIndex = 0
            if chunkIterator == 0 and blockIterator == 0:
                zIndex = 0
            elif blockIterator == 0:
                zIndex = (math.floor(chunkIterator / dimension)) * chunkSize
            else:
                zIndex = (math.floor(chunkIterator / dimension)) * chunkSize + math.floor(blockIterator / chunkSize)

            if block['type'] is None:
                map[xIndex][zIndex].append(40)
            else:
                map[xIndex][zIndex].append(block['type'])
            map[xIndex][zIndex].append(block['posY'])
            blockIterator = blockIterator + 1
        chunkIterator = chunkIterator + 1
    return map


def ImportWMap(filePath):
    file = open(filePath, "r")
    data = json.load(file)
    file.close()

    map = []

    for l in data['lines']:
        map.append(l)

    return map


def ImportNodeMap(filePath):
    file = open(filePath, "r")
    data = json.load(file)
    file.close()

    map = []
    currentX = 0

    for l in data['lines']:
        map.append([])
        for n in l:
            node = Node.Node()
            node.position = n['pos']
            node.nearestWaterDistance = n['wDist']
            node.nearestWaterDirection = n['wDir']
            node.heightAverage = n['hAvg']
            map[currentX].append(node)
        currentX += 1

    return map



