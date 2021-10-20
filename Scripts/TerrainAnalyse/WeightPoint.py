from enum import Enum

import math
import Utility.MCUtil as MCUtil
import numpy as np
import Settings


class PrintableMode(Enum):
    WATER_SCORE = 0,
    HEIGHT_AVERAGE = 1,
    HEIGHT_VARIATION = 2,
    TOTAL_SCORE = 3


class WeightPoint:
    position = [0, 0]
    waterScore: float = 0
    heightAverage: float = 0
    heightVariation: int = 0
    totalScore: float = 0.0


def GenarateWeightPoints(map, sizeCoveredByWP, settings):
    dimensionX = len(map)
    dimensionZ = len(map[0])

    if sizeCoveredByWP % 2 != 0:
        sizeCoveredByWP += 1

    amountOfWPInARow = int(math.floor(dimensionX / (sizeCoveredByWP + 1)))
    offset = int(math.floor((dimensionX % (sizeCoveredByWP + 1)) / 2))

    gapBetweenPoints = int(math.floor(sizeCoveredByWP / 2))  # int(math.floor(dimensionX ** (1. / 3)))
    weightPoints = []

    print("Size = {}; Amount = {}; Offset = {}; Gap = {}".format(sizeCoveredByWP, amountOfWPInARow, offset,
                                                                 gapBetweenPoints))
    # Initialize each weight points with the indexes
    # for x in range(int(math.floor(dimensionX / (gapBetweenPoints + 1)))):
    for x in range(amountOfWPInARow):
        currentCoord = [0, 0]

        if x == 0:
            currentCoord[0] = int(offset + sizeCoveredByWP / 2)
        else:
            currentCoord[0] = int(offset + sizeCoveredByWP / 2 + sizeCoveredByWP * x + x)

        # for z in range(int(math.floor(dimensionZ / (gapBetweenPoints + 1)))):
        for z in range(amountOfWPInARow):
            if z == 0:
                currentCoord[1] = int(offset + sizeCoveredByWP / 2)
            else:
                currentCoord[1] = int(offset + sizeCoveredByWP / 2 + sizeCoveredByWP * z + z)

            weightPoint = WeightPoint()
            weightPoint.position = currentCoord.copy()
            weightPoints.append(weightPoint)
            # if x == 0:
            #   currentCoord[0] = gapBetweenPoints
            # else:
            #   currentCoord[0] = x * gapBetweenPoints + gapBetweenPoints + x

            # if z == 0:
            #   currentCoord[1] = gapBetweenPoints
            # else:
            #   currentCoord[1] = z * gapBetweenPoints + gapBetweenPoints + z

            # Check if the current point is not too close from the boundaries of the map to run the full check
            # if currentCoord[0] + gapBetweenPoints < dimensionX and currentCoord[1] + gapBetweenPoints < dimensionZ:
            #   weightPoint = WeightPoint()
            #  weightPoint.position = currentCoord
            # weightPoints.append(weightPoint)

    minValues = [
        999999,  # Water score
        999999,  # Height average
        999999  # Height variation
    ]

    maxValues = [
        0,  # Water score
        0,  # Height average
        0  # Height variation
    ]

    # Go through each weight point and assigne the values
    for i in weightPoints:
        # Array to store each cells value concerned
        waterEncounteredInDirection = [
            0,  # Top
            0,  # Right
            0,  # Bottom
            0  # Left
        ]

        checkedCellsHeight = []
        currentCell = []
        index = i.position

        # Do the top check
        for z in range(1, gapBetweenPoints):
            currentCell = map[index[0]][index[1] - z]
            checkedCellsHeight.append(currentCell[1])

            if currentCell[0] == MCUtil.BlocType['WATER']:
                waterEncounteredInDirection[0] = 1

        # Do the right check
        for x in range(1, gapBetweenPoints):
            currentCell = map[index[0] + x][index[1]]
            checkedCellsHeight.append(currentCell[1])

            if currentCell[0] == MCUtil.BlocType['WATER']:
                waterEncounteredInDirection[1] = 1

        # Do the bottom check
        for z in range(1, gapBetweenPoints):
            currentCell = map[index[0]][index[1] + z]
            checkedCellsHeight.append(currentCell[1])

            if currentCell[0] == MCUtil.BlocType['WATER']:
                waterEncounteredInDirection[2] = 1

        # Do the left check
        for x in range(1, gapBetweenPoints):
            currentCell = map[index[0] - x][index[1]]
            checkedCellsHeight.append(currentCell[1])

            if currentCell[0] == MCUtil.BlocType['WATER']:
                waterEncounteredInDirection[3] = 1

        # Assign the average and variation height to the weight point
        i.heightAverage = sum(checkedCellsHeight) / len(checkedCellsHeight)
        i.heightVariation = max(checkedCellsHeight) - min(checkedCellsHeight)

        if i.heightAverage > maxValues[1]:
            maxValues[1] = i.heightAverage

        if i.heightAverage < minValues[1]:
            minValues[1] = i.heightAverage

        if i.heightVariation > maxValues[2]:
            maxValues[2] = i.heightVariation

        if i.heightVariation < minValues[2]:
            minValues[2] = i.heightVariation

        # Calculate the water score and assign it to the weight point
        multiplier = 0
        for j in waterEncounteredInDirection:
            #i.waterScore += j
            if j > 0:
                i.waterScore += 1

        #i.waterScore *= multiplier

        if i.waterScore > maxValues[0]:
            maxValues[0] = i.waterScore

        if i.heightVariation < minValues[0]:
            minValues[0] = i.waterScore

    # Define the final score for each weight points
    for i in weightPoints:
        # Scale the various score between the max and min values
        scaledWS = (i.waterScore - minValues[0]) / (maxValues[0] - minValues[0])
        scaledHA = (i.heightAverage - minValues[1]) / (maxValues[1] - minValues[1])
        scaledHV = (i.heightVariation - minValues[2]) / (maxValues[2] - minValues[2])

        i.totalScore = (scaledWS * settings.waterWeight) + \
                       (scaledHA * settings.heightWeight) - \
                       (scaledHV * settings.variationWeight)

    return weightPoints


def GetBestWeightPoint(map, sizeCoveredByWP, weightPoints, setting):
    weightPoints.sort(key=lambda x: x.totalScore, reverse=True)

    for i in weightPoints:
        print("{} => {}".format(i.position, i.totalScore))

    if sizeCoveredByWP % 2 != 0:
        sizeCoveredByWP += 1

    gapBetweenPoints = int(math.floor(sizeCoveredByWP / 2))

    for i in weightPoints:
        waterAmount = 0
        buildableAmount = 0
        print("Range x => {} --> {} | Range z => {} --> {}".format(i.position[0] - gapBetweenPoints,
                                                                   i.position[0] + gapBetweenPoints,
                                                                   i.position[1] - gapBetweenPoints,
                                                                   i.position[1] + gapBetweenPoints))
        for x in range(i.position[0] - gapBetweenPoints, i.position[0] + gapBetweenPoints):
            for z in range(i.position[1] - gapBetweenPoints, i.position[1] + gapBetweenPoints):
                if map[x][z][0] == MCUtil.BlocType['WATER']:
                    waterAmount += 1
                else:
                    buildableAmount += 1

        if buildableAmount / (waterAmount + buildableAmount) >= setting.minBuildableArea:
            print("Buildable amount = {}; Water amount = {}; Total = {}; Percentage = {}".format(buildableAmount,
                                                                                                 waterAmount,
                                                                                                 waterAmount + buildableAmount,
                                                                                                 buildableAmount / (waterAmount + buildableAmount)))
            return i




def GeneratePrintableWeightPointsMap(map, weightPoints, areaSize, mode: PrintableMode):
    dimensionX = len(map)
    dimensionZ = len(map[0])
    outMap = np.zeros((dimensionZ, dimensionX, 3), np.uint8)

    if areaSize % 2 != 0:
        areaSize += 1

    gapBetweenPoints = int(math.floor(areaSize / 2))

    minValue = 9999999
    maxValue = 0

    if mode == PrintableMode.WATER_SCORE:
        for i in weightPoints:
            if minValue > i.waterScore:
                minValue = i.waterScore
            if maxValue < i.waterScore:
                maxValue = i.waterScore
    elif mode == PrintableMode.HEIGHT_AVERAGE:
        for i in weightPoints:
            if minValue > i.heightAverage:
                minValue = i.heightAverage
            if maxValue < i.heightAverage:
                maxValue = i.heightAverage
    elif mode == PrintableMode.HEIGHT_VARIATION:
        for i in weightPoints:
            if minValue > i.heightVariation:
                minValue = i.heightVariation
            if maxValue < i.heightVariation:
                maxValue = i.heightVariation
    else:
        minValue = 0.0
        maxValue = 1.0

    for i in weightPoints:
        currentIndex = i.position
        valueToApply = 0

        if mode == PrintableMode.WATER_SCORE:
            valueToApply = i.waterScore
        elif mode == PrintableMode.HEIGHT_AVERAGE:
            valueToApply = i.heightAverage
        elif mode == PrintableMode.HEIGHT_VARIATION:
            valueToApply = i.heightVariation
        else:
            valueToApply = i.totalScore

        # Scale the value between 0 and 255
        valueToApply = ((valueToApply - minValue) * 255) / (maxValue - minValue)

        for x in range(-gapBetweenPoints, gapBetweenPoints):
            for z in range(-gapBetweenPoints, gapBetweenPoints):
                outMap[currentIndex[0] + x][currentIndex[1] + z] = [0, valueToApply, 0]

    return outMap


def GenPrintableColorMapWithHighScoreArea(colorMap, weightPoints, areaSize):
    gapBetweenPoints = int(math.floor(areaSize / 2))

    wpWithHighestScore = WeightPoint()

    # Get the weight point with the highest total score
    for i in weightPoints:
        if i.totalScore > wpWithHighestScore.totalScore:
            wpWithHighestScore = i

    wpPos = wpWithHighestScore.position
    colorToApply = [204, 204, 0]

    # Draw left vertical line
    for z in range(-gapBetweenPoints, gapBetweenPoints):
        colorMap[wpPos[0] - gapBetweenPoints][wpPos[1] + z] = colorToApply
        colorMap[wpPos[0] - gapBetweenPoints + 1][wpPos[1] + z] = colorToApply

    # Draw right vertical line
    for z in range(-gapBetweenPoints, gapBetweenPoints):
        colorMap[wpPos[0] + gapBetweenPoints][wpPos[1] + z] = colorToApply
        colorMap[wpPos[0] + gapBetweenPoints - 1][wpPos[1] + z] = colorToApply

    # Draw top horizontal line
    for x in range(-gapBetweenPoints, gapBetweenPoints):
        colorMap[wpPos[0] + x][wpPos[1] - gapBetweenPoints] = colorToApply
        colorMap[wpPos[0] + x][wpPos[1] - gapBetweenPoints + 1] = colorToApply

    # Draw bottom horizontal line
    for x in range(-gapBetweenPoints, gapBetweenPoints):
        colorMap[wpPos[0] + x][wpPos[1] + gapBetweenPoints] = colorToApply
        colorMap[wpPos[0] + x][wpPos[1] + gapBetweenPoints - 1] = colorToApply

    return colorMap

def GenPrintableColorMapWithAllWeightPoints(colorMap, weightPoints, areaSize):
    gapBetweenPoints = int(math.floor(areaSize / 2))
    colorToApply = [204, 204, 0]

    for i in weightPoints:
        wpPos = i.position

        # Draw left vertical line
        for z in range(-gapBetweenPoints, gapBetweenPoints):
            colorMap[wpPos[0] - gapBetweenPoints][wpPos[1] + z] = colorToApply
            colorMap[wpPos[0] - gapBetweenPoints + 1][wpPos[1] + z] = colorToApply

        # Draw right vertical line
        for z in range(-gapBetweenPoints, gapBetweenPoints):
            colorMap[wpPos[0] + gapBetweenPoints][wpPos[1] + z] = colorToApply
            colorMap[wpPos[0] + gapBetweenPoints - 1][wpPos[1] + z] = colorToApply

        # Draw top horizontal line
        for x in range(-gapBetweenPoints, gapBetweenPoints):
            colorMap[wpPos[0] + x][wpPos[1] - gapBetweenPoints] = colorToApply
            colorMap[wpPos[0] + x][wpPos[1] - gapBetweenPoints + 1] = colorToApply

        # Draw bottom horizontal line
        for x in range(-gapBetweenPoints, gapBetweenPoints):
            colorMap[wpPos[0] + x][wpPos[1] + gapBetweenPoints] = colorToApply
            colorMap[wpPos[0] + x][wpPos[1] + gapBetweenPoints - 1] = colorToApply

    return colorMap