import CityGeneration.Data.Maps as Maps
import random
import Utility.UtilityMisc as UtilityMisc
import copy

class Building:
    id: int
    minSize: int
    maxSize: int
    coveredCells: []
    mapColor = "yellow"

    def __init__(self, id = 0):
        self.id = id
        self.coveredCells = []

    def PlaceBuildingAtPos(self, position, layers, buildingMap: Maps.BuildingMap, seed):
        #print("Started generating building {}".format(self.id))
        seed += 1
        random.seed(seed)

        possibleFirstMovementStartingCells = []
        neighbours = UtilityMisc.GetCellNeighborsOnBiMap(buildingMap.map, position[0], position[1],
                                                         omitDiagonals=True)
        for n in neighbours:
            if buildingMap.map[n[0]][n[1]] != -1:
                continue

            neighbourIsValid = True
            for i in range(len(layers) - 1):
                for v in layers[i]:
                    if n == v:
                        neighbourIsValid = False
                        break
                if not neighbourIsValid:
                    break
            if not neighbourIsValid:
                continue
            possibleFirstMovementStartingCells.append(n)

        for sp in possibleFirstMovementStartingCells:
            firstMovement = [position]
            firstMovementDirection = [sp[0] - position[0], sp[1] - position[1]]

            # Try to move along the last layer cells
            currentCell = position
            maxMovement = self.minSize
            if self.minSize < self.maxSize:
                maxMovement = random.randrange(self.minSize, self.maxSize)
            #print("Do first movement")
            while len(firstMovement) < maxMovement:
                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(buildingMap.map, currentCell[0], currentCell[1],
                                                                 omitDiagonals=True)
                previousCell = currentCell

                for n in neighbours:
                    if buildingMap.map[n[0]][n[1]] != -1 or n in firstMovement:
                        continue

                    neighbourIsValid = True
                    for i in range(len(layers) - 1):
                        for v in layers[i]:
                            if n == v:
                                neighbourIsValid = False
                                break
                        if not neighbourIsValid:
                            break
                    if not neighbourIsValid:
                        continue

                    if firstMovementDirection == [n[0] - currentCell[0], n[1] - currentCell[1]]:
                        firstMovement.append(n)
                        currentCell = n
                        break

                # Check if it has not been able to move in the movement direction
                if previousCell == currentCell:
                    break

            # Check if it has been able to move on a greater distance than the minimum distance
            if len(firstMovement) < self.minSize:
                #print("Invalid first movement, try with another movement direction")
                continue

            #print("First movement sucess: {}".format(firstMovement))

            secondMovementDirectionID = 0
            if firstMovementDirection[0] != 0:
                secondMovementDirectionID = 1
            #print("Old movement: {} | Next movement ID: {}".format(firstMovementDirection, secondMovementDirectionID))

            secondMovementDirection = [0, 0]
            firstCell = firstMovement[0]
            secondCell = firstMovement[len(firstMovement) - 1]
            secondMovement = [[[firstCell], [secondCell]], [[firstCell], [secondCell]]]
            usedSecondMovement = -1

            # Try to do the second movement (bottom or right)
            secondMovementDirection[secondMovementDirectionID] = 1
            maxMovement = self.minSize
            if self.minSize < self.maxSize:
                maxMovement = random.randrange(self.minSize, self.maxSize)
            #print("Start second movement")
            while len(secondMovement[0][0]) < maxMovement:
                # Get the last registered movement cells ids
                firstID = copy.deepcopy(secondMovement[0][0][len(secondMovement[0][0]) - 1])
                secondID = copy.deepcopy(secondMovement[0][1][len(secondMovement[0][1]) - 1])

                #print("{} | {}".format(firstID, secondID))
                # Move the ids on the movement direction
                firstID[secondMovementDirectionID] += secondMovementDirection[secondMovementDirectionID]
                secondID[secondMovementDirectionID] += secondMovementDirection[secondMovementDirectionID]
                #print("{} | {}".format(firstID, secondID))

                # Check if the movement is outside of the map
                if firstID[secondMovementDirectionID] < 0 or secondID[secondMovementDirectionID] < 0 or \
                        firstID[secondMovementDirectionID] >= len(buildingMap.map) or secondID[secondMovementDirectionID] >= len(buildingMap.map[0]):
                    break

                # Check if both of the cells are valid
                if buildingMap.map[firstID[0]][firstID[1]] != -1 or buildingMap.map[secondID[0]][secondID[1]] != -1:
                    break

                neighbourIsValid = True
                for i in range(len(layers) - 1):
                    for v in layers[i]:
                        if firstID == v or secondID == v:
                            neighbourIsValid = False
                            break
                    if not neighbourIsValid:
                        break
                if not neighbourIsValid:
                    break

                secondMovement[0][0].append(firstID)
                secondMovement[0][1].append(secondID)

            # Check if the movement has moved
            if len(secondMovement[0][0]) < self.minSize:
                #print("Second movement has not been possible, trying the other way...")
                # Try to do the second movement (up or left)
                secondMovementDirection[secondMovementDirectionID] = -1
                while len(secondMovement[1][0]) < maxMovement:
                    # Get the last registered movement cells ids
                    firstID = copy.deepcopy(secondMovement[1][0][len(secondMovement[1][0]) - 1])
                    secondID = copy.deepcopy(secondMovement[1][1][len(secondMovement[1][1]) - 1])

                    #print("{} | {}".format(firstID, secondID))
                    # Move the ids on the movement direction
                    firstID[secondMovementDirectionID] += secondMovementDirection[secondMovementDirectionID]
                    secondID[secondMovementDirectionID] += secondMovementDirection[secondMovementDirectionID]
                    #print("{} | {}".format(firstID, secondID))

                    # Check if the movement is outside of the map
                    if firstID[secondMovementDirectionID] < 0 or secondID[secondMovementDirectionID] < 0 or \
                            firstID[secondMovementDirectionID] >= len(buildingMap.map) or \
                            secondID[secondMovementDirectionID] >= len(buildingMap.map[0]):
                        break

                    # Check if both of the cells are valid
                    if buildingMap.map[firstID[0]][firstID[1]] != -1 or buildingMap.map[secondID[0]][secondID[1]] != -1:
                        break

                    neighbourIsValid = True
                    for i in range(len(layers) - 1):
                        for v in layers[i]:
                            if firstID == v or secondID == v:
                                neighbourIsValid = False
                                break
                        if not neighbourIsValid:
                            break
                    if not neighbourIsValid:
                        break

                    secondMovement[1][0].append(firstID)
                    secondMovement[1][1].append(secondID)

                if len(secondMovement[1][0]) >= self.minSize:
                    usedSecondMovement = 1
            else:
                usedSecondMovement = 0

            # Check if the last movement is invalid
            if usedSecondMovement == -1:
                #print("Impossible to do the second movement, aborting...")
                continue

            #print("Second movement success: {}".format(secondMovement))
            thirdMovementDirectionID = 0
            if secondMovementDirection[0] != 0:
                thirdMovementDirectionID = 1
            #print("Old movement: {} | Next movement ID: {}".format(secondMovementDirection, thirdMovementDirectionID))

            # Get the minimal final point of the second movement
            currentCell = copy.deepcopy(secondMovement[usedSecondMovement][0][len(secondMovement[usedSecondMovement][0]) - 1])
            goalCell = copy.deepcopy(secondMovement[usedSecondMovement][1][len(secondMovement[usedSecondMovement][1]) - 1])
            if goalCell[thirdMovementDirectionID] < currentCell[thirdMovementDirectionID]:
                currentCell = copy.deepcopy(secondMovement[usedSecondMovement][1][len(secondMovement[usedSecondMovement][0]) - 1])
                goalCell = copy.deepcopy(secondMovement[usedSecondMovement][0][len(secondMovement[usedSecondMovement][1]) - 1])

            thirdMovement = []
            if abs(currentCell[thirdMovementDirectionID] - goalCell[thirdMovementDirectionID]) > 1:
                #print("Start third movement({} to {})".format(currentCell, goalCell))
                thirdMovementIsValid = True
                # Move until the other second movement point is reached
                while currentCell != goalCell:
                    currentCell[thirdMovementDirectionID] += 1
                    # Check if both of the cells are valid
                    if buildingMap.map[currentCell[0]][currentCell[1]] != -1:
                        #print("Can't do the third movement")
                        thirdMovementIsValid = False
                        break
                    thirdMovement.append(copy.deepcopy(currentCell))

                if not thirdMovementIsValid:
                    continue

            #print("Third movement success: {}".format(thirdMovement))
            buildingVertices = [
                firstMovement[0],
                firstMovement[len(firstMovement) - 1],
                secondMovement[usedSecondMovement][0][len(secondMovement[usedSecondMovement][0]) - 1],
                secondMovement[usedSecondMovement][1][len(secondMovement[usedSecondMovement][1]) - 1]
            ]

            #print("Definition of the covered area based on the movements")
            # Fill the covered area with the movements
            for v in firstMovement:
                self.coveredCells.append(v)

            for v in secondMovement[usedSecondMovement][0]:
                if v not in self.coveredCells:
                    self.coveredCells.append(v)

            for v in secondMovement[usedSecondMovement][1]:
                if v not in self.coveredCells:
                    self.coveredCells.append(v)

            for v in thirdMovement:
                if v not in self.coveredCells:
                    self.coveredCells.append(v)

            # Check if the building vertices are the only cells contained by the building
            if len(self.coveredCells) == 4:
                return self.coveredCells

            minPos = [9999999, 9999999]
            maxPos = [0, 0]

            # Define the maximum and minimum position of the building
            for v in buildingVertices:
                if v[0] < minPos[0]:
                    minPos[0] = v[0]
                if v[1] < minPos[1]:
                    minPos[1] = v[1]
                if v[0] > maxPos[0]:
                    maxPos[0] = v[0]
                if v[1] > maxPos[1]:
                    maxPos[1] = v[1]

            #print("Definition of the building inner cells")
            # Define the inner building cells
            for i in range(minPos[0] + 1, maxPos[0]):
                for j in range(minPos[1] + 1, maxPos[1]):
                    self.coveredCells.append([i, j])

            cellIsValid = True
            # Check if there is a cell that is invalid
            for v in self.coveredCells:
                for i in range(len(layers) - 1):
                    for v2 in layers[i]:
                        if v == v2:
                            cellIsValid = False
                            break
                    if not cellIsValid:
                        break
                if not cellIsValid:
                    break

            if cellIsValid:
                return self.coveredCells

        return []

class House(Building):
    minSize = 2
    maxSize = 2

class Church(Building):
    minSize = 4
    maxSize = 8
    mapColor = "purple"

class Fort(Building):
    minSize = 5
    maxSize = 10
    mapColor = "red"

class Barracks(Building):
    minSize = 4
    maxSize = 6
    mapColor = "darkred"

class Storage(Building):
    minSize = 3
    maxSize = 5
    mapColor = "orange"