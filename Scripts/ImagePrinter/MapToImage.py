from PIL import Image
from enum import Enum
import MapGenerator.HeightMapGen as HeightMapGen
import MapGenerator.ColorMapGen as ColorMapGen
import MapGenerator.WaterAccessMap as WaterAccessMap

class MapType(Enum):
    COLOR = 1
    HEIGHT = 2
    WATER = 3

def MapToImage(map, outMapType):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    print("Map dimension : {}:{}".format(dimensionX, dimensionZ))

    if outMapType == MapType.COLOR:
        print("Generating color map")
        PrintImage(ColorMapGen.MapToColorMap(map, dimensionX, dimensionZ),
                   'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\ResultImage\\ColorMap.png')
    elif outMapType == MapType.HEIGHT:
        print("Generating height map")
        PrintImage(HeightMapGen.MapToHeightMap(map, dimensionX, dimensionZ),
                   'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\ResultImage\\HeightMap.png')
    elif outMapType == MapType.WATER:
        print("Generating water access map")
        PrintImage(WaterAccessMap.GetPrintableWaterAccessMap(map, dimensionX, dimensionZ),
                   'D:\\Dev\\SAE\\Bachelor\\CMN63XX\\Project\\pyProject\\ResultImage\\WaterAccessMap.png')
    else:
        print("Error : Incorrect map type")

def PrintImage(data, fileName):
    image = Image.fromarray(data, 'RGB')
    image.save(fileName)
    #image.show()