from enum import Enum
import CityGeneration.Data.Maps as Maps
import Utility.UtilityMisc as UtilityMisc
import copy
import math
import random
import numpy as np
import CityGeneration.Data.Buildings as Buildings

global INITIAL_AREA_SIZE
global MIN_MOVEMENT
global MAX_MOVEMENT
global MIN_DISTANCE
global MAX_DISTANCE
global SEGMENT_MIN_RATIO
global SEGMENT_MAX_RATIO
global RADIUS_MIN_OFFSET
global RADIUS_MAX_OFFSET
global DISTANCE_TO_CENTER_WEIGHT
global MIN_DISTANCE_TO_SEGMENT
global GATE_DEAD_ZONE_RADIUS
global CHURCH_INFLUENCE_RADIUS

class ErrorCode(Enum):
    NONE = 0
    VERTEX_O_F_E = 1
    VERTEX_F_S_E = 2
    VERTEX_E = 3
    LINK_S_F = 4
    LINK_T_F = 5
    CENTER_ON_BORDER = 6
    CENTER_OUTSIDE = 7
    DIR_E_ZERO = 8

class District:
    id: int
    buildings: []
    districtVertex: []
    areaCells: []
    layerCells: []
    innerCells: []
    neighbouringDistricts: []
    errorCode: ErrorCode

    # Used to render the process
    rp_linking1v2v: []
    rp_linking1v3v: []
    rp_linking2v4v: []
    rp_linking3v4v: []
    rp_circleCenters: []
    rp_circleRadius: []
    rp_circlePoints: []
    rp_segmentPoint: []
    rp_districtCenter: []
    rp_direction: []
    rp_polyVertices: []


    def __init__(self, id=0):
        self.id = id
        self.buildings = []
        self.districtVertex = []
        self.areaCells = []
        self.layerCells = []
        self.innerCells = []
        self.neighbouringDistricts = []
        self.errorCode = ErrorCode.NONE

        self.rp_linking1v2v = []
        self.rp_linking1v3v = []
        self.rp_linking2v4v = []
        self.rp_linking3v4v = []
        self.rp_circleCenters = []
        self.rp_circleRadius = []
        self.rp_circlePoints = []
        self.rp_segmentPoint = [-1, -1]
        self.rp_districtCenter = []
        self.rp_direction = []
        self.rp_polyVertices = []

    def DefineInitialDistrictArea(self, p, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map, seed):
        # TODO: Actually implement this function
        return

    def DefineDistrictAreaBasedOnRoads(self, p, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map, seed):
        #print("District n°{} area definition based on road start with starting point {}".format(self.id, p))
        seed += 1
        random.seed(seed)

        areaCells = []

        # Define the real starting point
        neighbors = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, p[0], p[1])
        minDistance = 999999
        minID = p
        for n in neighbors:
            if roadMap.map[n[0]][n[1]] == 0 or map[n[0]][n[1]][0] == 29 or map[n[0]][n[1]][0] == 40 or districtMap.map[n[0]][n[1]] > -1:
                continue

            d = UtilityMisc.GetVec2Magnitude([n[0] - p[0], n[1] - p[1]])
            if d < minDistance:
                minDistance = d
                minID = [n[0], n[1]]

        if minID == p:
            #print("Given point is equal to first vertex: {} - {}".format(p, minID))
            self.errorCode = ErrorCode.VERTEX_O_F_E
            return []

        currentPoint = minID
        areaCells.append(currentPoint)
        self.districtVertex.append(currentPoint)

        # Move along the road for a defined movement
        previousMinID = minID
        movement = random.randrange(MIN_MOVEMENT, MAX_MOVEMENT)
        #print("Move along the road for {}".format(movement))
        for i in range(movement):
            neighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1])
            minDistance = 999999
            for n in neighbors:
                if roadMap.map[n[0]][n[1]] == 0 or map[n[0]][n[1]][0] == 29 or map[n[0]][n[1]][0] == 40 \
                        or districtMap.map[n[0]][n[1]] > -1 or n in areaCells \
                        or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, n):
                    continue

                d = UtilityMisc.GetVec2Magnitude([n[0] - currentPoint[0], n[1] - currentPoint[1]])
                if d < minDistance:
                    minDistance = d
                    minID = [n[0], n[1]]

            if minID != previousMinID:
                areaCells.append(minID)
                self.rp_linking1v2v.append(minID)
                currentPoint = minID
                previousMinID = minID
            else:
                break

        self.districtVertex.append(minID)

        if self.districtVertex[0] == minID:
            #print("First vertex is equal to second vertex: {} - {}".format(self.districtVertex[0], minID))
            self.errorCode = ErrorCode.VERTEX_F_S_E
            self.areaCells = areaCells
            return []

        direction = UtilityMisc.GetNormalizedVec2([self.districtVertex[1][0] - self.districtVertex[0][0], self.districtVertex[1][1] - self.districtVertex[0][1]])

        currentPoint = self.districtVertex[0]
        minID = currentPoint
        previousMinID = minID
        movement = random.randrange(MIN_MOVEMENT, MAX_MOVEMENT)
        visitedCells = [minID]
        #print("Move along the districts for {}".format(movement))
        for i in range(movement):
            neighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1], omitDiagonals=True)
            minAngle = 0#math.pi
            minDistance = 99999

            cellDistances = []
            cellAngles = []
            cellIDs = []
            cellBorderedByWaterOrDistrict = []
            for n in neighbors:
                if map[n[0]][n[1]][0] == 29 or map[n[0]][n[1]][0] == 29 or districtMap.map[n[0]][n[1]] > -1 \
                        or n in visitedCells or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, n):
                    continue

                # Specific values in order to be able to add a road if it is close to water
                isRoad = False
                borderedByWater = False

                if roadMap.map[n[0]][n[1]] == 1:
                    isRoad = True

                cellDistances.append(UtilityMisc.GetVec2Magnitude([n[0] - currentPoint[0], n[1] - currentPoint[1]]))
                cellAngles.append(UtilityMisc.GetAngleBetweenVec2(direction, [n[0] - currentPoint[0], n[1] - currentPoint[1]]))
                cellBorderedByWaterOrDistrict.append(False)
                cellIDs.append(n)
                nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1])

                for nn in nNeighbors:
                    if isRoad:
                        if map[nn[0]][nn[1]][0] == 29:
                            borderedByWater = True
                            cellBorderedByWaterOrDistrict[len(cellBorderedByWaterOrDistrict) - 1] = True
                            break
                    elif districtMap.map[nn[0]][nn[1]] > -1 or roadMap.map[nn[0]][nn[1]] == 1 or map[nn[0]][nn[1]][0] == 29:
                        cellBorderedByWaterOrDistrict[len(cellBorderedByWaterOrDistrict) - 1] = True
                        break

                # Check if the current cell is surounded by already assigned cells (in order to avoid going into a hole)
                nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1], omitDiagonals=True)
                freeCellAmount = 0
                for nn in nNeighbors:
                    if districtMap.map[nn[0]][nn[1]] == -1 and roadMap.map[nn[0]][nn[1]] != 1 and map[nn[0]][nn[1]][0] != 29 and map[nn[0]][nn[1]][0] != 40 and nn != n and nn not in visitedCells:
                        freeCellAmount += 1

                if freeCellAmount == 0 or (isRoad and not borderedByWater):
                    cellBorderedByWaterOrDistrict[len(cellBorderedByWaterOrDistrict) - 1] = False

            for j in range(len(cellBorderedByWaterOrDistrict)):
                if cellBorderedByWaterOrDistrict[j] and cellDistances[j] <= minDistance and cellAngles[j] >= minAngle:
                    minDistance = cellDistances[j]
                    minAngle = cellAngles[j]
                    minID = cellIDs[j]

            if minID != previousMinID:
                if minID not in areaCells:
                    areaCells.append(minID)
                self.rp_linking1v3v.append(minID)
                currentPoint = minID
                previousMinID = minID
                visitedCells.append(minID)
            else:
                break

        self.districtVertex.append(minID)

        # Check if the vertex are not equal
        if self.districtVertex[0] == self.districtVertex[1] \
                or self.districtVertex[0] == self.districtVertex[2] \
                or self.districtVertex[1] == self.districtVertex[2]:
            #print("One of the vertices is equal to another: 0 = {} | 1 = {} | 2 = {}".format(self.districtVertex[0], self.districtVertex[1], self.districtVertex[2]))
            self.errorCode = ErrorCode.VERTEX_E
            self.areaCells = areaCells
            return []

        direction = [0, 0]

        neighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, self.districtVertex[0][0], self.districtVertex[0][1])
        for n in neighbors:
            if districtMap.map[n[0]][n[1]] > -1 or roadMap.map[n[0]][n[1]] == 1 or map[n[0]][n[1]][0] == 29:
                direction[0] += (self.districtVertex[0][0] - n[0])
                direction[1] += (self.districtVertex[0][1] - n[1])

        if direction == [0, 0]:
            #print("Direction equal to zero, backup definition")
            for n in neighbors:
                if districtMap.map[n[0]][n[1]] > -1 or map[n[0]][n[1]][0] == 29:
                    direction[0] += (self.districtVertex[0][0] - n[0])
                    direction[1] += (self.districtVertex[0][1] - n[1])

        #print(direction)
        self.rp_direction = direction
        direction = UtilityMisc.GetNormalizedVec2(direction)

        c1 = UtilityMisc.GetPointOnSegment(self.districtVertex[0], self.districtVertex[1], random.uniform(0.6, 0.9))
        c2 = UtilityMisc.GetPointOnSegment(self.districtVertex[0], self.districtVertex[2], random.uniform(0.6, 0.9))
        #print("Define position of the fourth vertex based on circles")
        fourthVertex = self.DefineVertex(self.districtVertex[0], c1, c2, direction)
        fourthVertexIsInvalid = fourthVertex is None

        if not fourthVertexIsInvalid:
            fourthVertexIsInvalid = UtilityMisc.PointIsInsideTriangle(fourthVertex, self.districtVertex[0],
                                                                      self.districtVertex[1], self.districtVertex[2])

        if fourthVertexIsInvalid:
            #print("Fourth vertex based on circles ({}) is invalid, getting new point based on segment".format(fourthVertex))
            ratio = random.uniform(0.2, 0.8)
            pointOnSegment = UtilityMisc.GetPointOnSegment(self.districtVertex[1], self.districtVertex[2], ratio)
            distance = random.randrange(MIN_DISTANCE, MAX_DISTANCE)
            fourthVertex = [int(pointOnSegment[0] + direction[0] * distance),
                            int(pointOnSegment[1] + direction[1] * distance)]
            self.rp_segmentPoint = fourthVertex

        d = UtilityMisc.GetDistanceFromSegment(self.districtVertex[1], self.districtVertex[2],
                                              self.districtVertex[0])
        #print("-------Distance to segment = {}".format(d))
        if d < MIN_DISTANCE_TO_SEGMENT:
            #print("Fourth vertex too close from the first one, moving it further away")
            fourthVertex = [int(fourthVertex[0] + direction[0] * MAX_DISTANCE),
                            int(fourthVertex[1] + direction[1] * MAX_DISTANCE)]

        if fourthVertex[0] < 0:
            fourthVertex[0] = 0
        if fourthVertex[1] < 0:
            fourthVertex[1] = 0
        if fourthVertex[0] >= len(map):
            fourthVertex[0] = len(map) - 1
        if fourthVertex[1] >= len(map[0]):
            fourthVertex[1] = len(map[0]) - 1

        if districtMap.map[fourthVertex[0]][fourthVertex[1]] > -1 or map[fourthVertex[0]][fourthVertex[1]][0] == 29:
            #print("Initial point invalid, looking for a point on the segment linking first and fourth vertex")
            initialFourthVertex = fourthVertex
            for i in np.arange(0.9, 0.1, -0.1):
                for v in self.districtVertex:
                    point = UtilityMisc.GetPointOnSegment(v, fourthVertex, i)
                    point = [int(point[0]), int(point[1])]
                    if districtMap.map[point[0]][point[1]] > -1 or map[point[0]][point[1]][0] == 29 or map[point[0]][point[1]][0] == 40:
                        continue
                    fourthVertex = point
                    break

                if initialFourthVertex != fourthVertex:
                    break

        self.districtVertex.append(fourthVertex)
        #areaCells.append(fourthVertex)
        #print("{}".format(self.districtVertex))

        #print("Linking second to fourth vertex")
        if not self.LinkVertices(self.districtVertex[1], self.districtVertex[3], districtMap, map, areaCells, self.rp_linking2v4v):
            #print("Can't link second to fourth vertex")
            self.errorCode = ErrorCode.LINK_S_F
            self.areaCells = areaCells
            return []

        #print("Linking Third to fourth vertex")
        if not self.LinkVertices(self.districtVertex[2], self.districtVertex[3], districtMap, map, areaCells, self.rp_linking3v4v):
            #print("Can't link third to fourth vertex")
            self.errorCode = ErrorCode.LINK_T_F
            self.areaCells = areaCells
            return []

        #districtCenter = [0, 0]

        # Define the district center
        #for v in areaCells:
        #    districtCenter[0] += v[0]
        #    districtCenter[1] += v[1]

        #districtCenter = [int(districtCenter[0] / len(areaCells)),
        #                  int(districtCenter[1] / len(areaCells))]
        #self.rp_districtCenter = districtCenter
        #print(districtCenter)

        #if districtCenter in areaCells:
        #    #print("Center is contained within the area cells")
        #    self.errorCode = ErrorCode.CENTER_ON_BORDER
        #    self.rp_areaCells = areaCells
        #    return []

        #self.rp_polyVertices = self.DefinePolygoneVertices(map, areaCells)
        #centerIsInsideShape = self.CheckIfPointIsInDistrict(districtCenter, self.rp_polyVertices)

        #for i in range(len(self.districtVertex)):
        #    if UtilityMisc.SegmentsIntersect(self.districtVertex[0], self.districtVertex[1], self.districtVertex[i], districtCenter)\
        #            or UtilityMisc.SegmentsIntersect(self.districtVertex[0], self.districtVertex[2], self.districtVertex[i], districtCenter)\
        #            or UtilityMisc.SegmentsIntersect(self.districtVertex[1], self.districtVertex[3], self.districtVertex[i], districtCenter)\
        #            or UtilityMisc.SegmentsIntersect(self.districtVertex[2], self.districtVertex[3], self.districtVertex[i], districtCenter):
        #        centerIsInsideShape = False

        #if not centerIsInsideShape:
        #    #print("District center is not within the district")
        #    self.errorCode = ErrorCode.CENTER_OUTSIDE
        #    self.rp_areaCells = areaCells
        #    return []

        #cNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, districtCenter[0], districtCenter[1])
        #for n in cNeighbors:
        #    if n in areaCells:
        #        #print("District center is close to the border")
        #        self.errorCode = ErrorCode.CENTER_OUTSIDE
        #        self.rp_areaCells = areaCells
        #        return []

        # Add the cells contained within the district limits
        #print("Definition of the inner district cells")
        orderedVertices = [
            self.districtVertex[0],
            self.districtVertex[1],
            self.districtVertex[3],
            self.districtVertex[2],
        ]
        fullPath = []
        for v in self.rp_linking1v2v:
            if v not in fullPath:
                fullPath.append(v)

        for v in self.rp_linking2v4v:
            if v not in fullPath:
                fullPath.append(v)

        if len(self.rp_linking3v4v) > 1:
            for i in range(len(self.rp_linking3v4v)):
                v = self.rp_linking3v4v[len(self.rp_linking3v4v) - 1 - i]
                if v not in fullPath:
                    fullPath.append(v)

        if len(self.rp_linking1v3v) > 1:
            for i in range(len(self.rp_linking1v3v)):
                v = self.rp_linking1v3v[len(self.rp_linking1v3v) - 1 - i]
                if v not in fullPath:
                    fullPath.append(v)

        self.defineInnerDistrictCellsRayCast(fullPath, districtMap, map, areaCells)
        #self.DefineInnerDistrictCells(districtCenter, districtMap, roadMap, map, areaCells)

        #print("District n°{} area definition completed".format(self.id))
        self.areaCells = areaCells
        return areaCells

    def DefineDistrictArea(self, p, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map, seed, takeIntoAccountRoad=True):
        #print("District n°{} area definition start".format(self.id))
        seed += 1
        random.seed(seed)

        areaCells = []
        currentPoint = p
        self.districtVertex.append(currentPoint)
        areaCells.append(currentPoint)

        # Move along the water, districts and roads for the defined movement
        movement = random.randrange(MIN_MOVEMENT, MAX_MOVEMENT)
        #print("Do first movement of {}".format(movement))
        for i in range(movement):
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1], omitDiagonals=False)
            cellDistances = []
            cellBorderedByWaterOrDistrict = []
            cellIDs = []
            canMove = []

            for n in range(len(cellNeighbors)):
                # Check if the cell is water or is already in another district
                if map[cellNeighbors[n][0]][cellNeighbors[n][1]][0] == 29 \
                        or map[cellNeighbors[n][0]][cellNeighbors[n][1]][0] == 29 \
                        or districtMap.map[cellNeighbors[n][0]][cellNeighbors[n][1]] > -1 \
                        or (roadMap.map[cellNeighbors[n][0]][cellNeighbors[n][1]] == 1 and takeIntoAccountRoad) \
                        or cellNeighbors[n] in areaCells or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, cellNeighbors[n]):
                    continue

                cellDistances.append(UtilityMisc.GetVec2Magnitude([cellNeighbors[n][0] - currentPoint[0], cellNeighbors[n][1] - currentPoint[1]]))
                cellBorderedByWaterOrDistrict.append(False)
                canMove.append(False)
                cellIDs.append(cellNeighbors[n])
                nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, cellNeighbors[n][0], cellNeighbors[n][1],
                                                                     omitDiagonals=False)
                for nn in nNeighbors:
                    if districtMap.map[nn[0]][nn[1]] > -1 or (roadMap.map[nn[0]][nn[1]] == 1 and takeIntoAccountRoad) or map[nn[0]][nn[1]][0] == 29:
                        cellBorderedByWaterOrDistrict[len(cellBorderedByWaterOrDistrict) - 1] = True
                    elif nn not in areaCells and nn != cellNeighbors[n] and UtilityMisc.CheckAngleBetweenCells(map, nn, cellNeighbors[n]):
                        canMove[len(canMove) - 1] = True

            minID = currentPoint
            minDistance = 999999
            for j in range(len(cellBorderedByWaterOrDistrict)):
                if canMove[j] and cellBorderedByWaterOrDistrict[j] and cellDistances[j] < minDistance:
                    minDistance = cellDistances[j]
                    minID = cellIDs[j]

            # Check if the movement is blocked
            if minID == currentPoint:
                break
            else:
                areaCells.append(minID)
                self.rp_linking1v2v.append(minID)
                currentPoint = minID

        self.districtVertex.append(currentPoint)

        if currentPoint == p:
            #print("Given point is equal to first vertex: {} - {}".format(p, currentPoint))
            self.errorCode = ErrorCode.VERTEX_F_S_E
            self.areaCells = areaCells
            return []

        currentPoint = self.districtVertex[0]

        # Repeat the movement on the other direction
        movement = random.randrange(MIN_MOVEMENT, MAX_MOVEMENT)
        #print("Do second movement of {}".format(movement))
        for i in range(movement):
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1],
                                                                omitDiagonals=False)
            cellDistances = []
            cellBorderedByWaterOrDistrict = []
            canMove = []
            cellIDs = []

            for n in range(len(cellNeighbors)):
                # Check if the cell is water or is already in another district
                if map[cellNeighbors[n][0]][cellNeighbors[n][1]][0] == 29 \
                        or map[cellNeighbors[n][0]][cellNeighbors[n][1]][0] == 40 \
                        or districtMap.map[cellNeighbors[n][0]][cellNeighbors[n][1]] > -1 \
                        or (roadMap.map[cellNeighbors[n][0]][cellNeighbors[n][1]] == 1 and takeIntoAccountRoad) \
                        or cellNeighbors[n] in areaCells or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, cellNeighbors[n]):
                    continue

                cellDistances.append(UtilityMisc.GetVec2Magnitude(
                    [cellNeighbors[n][0] - currentPoint[0], cellNeighbors[n][1] - currentPoint[1]]))
                cellBorderedByWaterOrDistrict.append(False)
                canMove.append(False)
                cellIDs.append(cellNeighbors[n])
                nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, cellNeighbors[n][0], cellNeighbors[n][1],
                                                                 omitDiagonals=False)
                for nn in nNeighbors:
                    if districtMap.map[nn[0]][nn[1]] > -1 or (roadMap.map[nn[0]][nn[1]] == 1 and takeIntoAccountRoad) or map[nn[0]][nn[1]][0] == 29:
                        cellBorderedByWaterOrDistrict[len(cellBorderedByWaterOrDistrict) - 1] = True
                    elif nn not in areaCells and nn != cellNeighbors[n] and UtilityMisc.CheckAngleBetweenCells(map, nn, cellNeighbors[n]):
                        canMove[len(canMove) - 1] = True

            minID = currentPoint
            minDistance = 999999
            for j in range(len(cellBorderedByWaterOrDistrict)):
                if canMove[j] and cellBorderedByWaterOrDistrict[j] and cellDistances[j] < minDistance:
                    minDistance = cellDistances[j]
                    minID = cellIDs[j]

            # Check if the movement is blocked
            if minID == currentPoint:
                break
            else:
                areaCells.append(minID)
                self.rp_linking1v3v.append(minID)
                currentPoint = minID

        self.districtVertex.append(currentPoint)

        if currentPoint == p:
            #print("Given point is equal to second vertex: {} - {}".format(p, currentPoint))
            self.errorCode = ErrorCode.VERTEX_E
            self.areaCells = areaCells
            return []

        # Check if the vertex are not equal
        if self.districtVertex[0] == self.districtVertex[1] \
            or self.districtVertex[0] == self.districtVertex[2] \
            or self.districtVertex[1] == self.districtVertex[2]:
            #print("One of the vertices is equal to another: 0 = {} | 1 = {} | 2 = {}".format(self.districtVertex[0], self.districtVertex[1], self.districtVertex[2]))
            self.errorCode = ErrorCode.VERTEX_E
            self.areaCells = areaCells
            return []

        direction = [0, 0]

        neighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, self.districtVertex[0][0], self.districtVertex[0][1])
        for n in neighbors:
            if districtMap.map[n[0]][n[1]] > -1 or (roadMap.map[n[0]][n[1]] == 1 and takeIntoAccountRoad) or map[n[0]][n[1]][0] == 29:
                direction[0] += (self.districtVertex[0][0] - n[0])
                direction[1] += (self.districtVertex[0][1] - n[1])

        if direction == [0, 0]:
            #print("Direction equal to zero, backup definition")
            for n in neighbors:
                if districtMap.map[n[0]][n[1]] > -1 or map[n[0]][n[1]][0] == 29:
                    direction[0] += (self.districtVertex[0][0] - n[0])
                    direction[1] += (self.districtVertex[0][1] - n[1])

        if direction == [0, 0]:
            #print("Direction still equal to zero, aborting")
            self.errorCode = ErrorCode.DIR_E_ZERO
            self.areaCells = areaCells
            return []

        self.rp_direction = direction
        direction = UtilityMisc.GetNormalizedVec2(direction)
        #print("{}".format(self.districtVertex))
        c1 = UtilityMisc.GetPointOnSegment(self.districtVertex[0], self.districtVertex[1], random.uniform(0.6, 0.9))
        c2 = UtilityMisc.GetPointOnSegment(self.districtVertex[0], self.districtVertex[2], random.uniform(0.6, 0.9))
        #print("Define position of the fourth vertex based on circles")
        fourthVertex = self.DefineVertex(self.districtVertex[0], c1, c2, direction)
        fourthVertexIsInvalid = fourthVertex is None

        if not fourthVertexIsInvalid:
            fourthVertexIsInvalid = UtilityMisc.PointIsInsideTriangle(fourthVertex, self.districtVertex[0],
                                                                      self.districtVertex[1], self.districtVertex[2])

        if fourthVertexIsInvalid:
            #print("Fourth vertex based on circles is invalid, getting new point based on segment")
            ratio = random.uniform(0.2, 0.8)
            pointOnSegment = UtilityMisc.GetPointOnSegment(self.districtVertex[1], self.districtVertex[2], ratio)
            distance = random.randrange(MIN_DISTANCE, MAX_DISTANCE)
            fourthVertex = [int(pointOnSegment[0] + direction[0] * distance),
                            int(pointOnSegment[1] + direction[1] * distance)]
            self.rp_segmentPoint = fourthVertex

        if UtilityMisc.GetDistanceFromSegment(self.districtVertex[1], self.districtVertex[2], self.districtVertex[0]) < MIN_DISTANCE_TO_SEGMENT:
            #print("Fourth vertex too close from the first one, moving it further away")
            fourthVertex = [int(fourthVertex[0] + direction[0] * MAX_DISTANCE),
                            int(fourthVertex[1] + direction[1] * MAX_DISTANCE)]

        # Check if the fourth vertex is within the border of the map
        if fourthVertex[0] < 0:
            fourthVertex[0] = 0
        if fourthVertex[1] < 0:
            fourthVertex[1] = 0
        if fourthVertex[0] >= len(map):
            fourthVertex[0] = len(map) - 1
        if fourthVertex[1] >= len(map[0]):
            fourthVertex[1] = len(map[0]) - 1

        if districtMap.map[fourthVertex[0]][fourthVertex[1]] > -1 or map[fourthVertex[0]][fourthVertex[1]][0] == 29 or map[fourthVertex[0]][fourthVertex[1]][0] == 40:
            #print("Initial point invalid, looking for a point on the segment linking first and fourth vertex")
            initialFourthVertex = fourthVertex
            for i in np.arange(0.9, 0.1, -0.1):
                for v in self.districtVertex:
                    point = UtilityMisc.GetPointOnSegment(v, fourthVertex, i)
                    point = [int(point[0]), int(point[1])]
                    if districtMap.map[point[0]][point[1]] > -1 or map[point[0]][point[1]][0] == 29:
                        continue
                    fourthVertex = point
                    break

                if initialFourthVertex != fourthVertex:
                    break

        self.districtVertex.append(fourthVertex)
        #areaCells.append(fourthVertex)
        #print("{} | {}".format(self.districtVertex, fourthVertex))
        #print("Linking second to fourth vertex")
        if not self.LinkVertices(self.districtVertex[1], self.districtVertex[3], districtMap, map, areaCells, self.rp_linking2v4v):
            #print("Can't link second to fourth vertex")
            self.errorCode = ErrorCode.LINK_S_F
            self.areaCells = areaCells
            return []

        #print("Linking Third to fourth vertex")
        if not self.LinkVertices(self.districtVertex[2], self.districtVertex[3], districtMap, map, areaCells, self.rp_linking3v4v):
            #print("Can't link third to fourth vertex")
            self.errorCode = ErrorCode.LINK_T_F
            self.areaCells = areaCells
            return []

        #districtCenter = [0, 0]

        #for v in areaCells:
        #    districtCenter[0] += v[0]
        #    districtCenter[1] += v[1]

        #districtCenter = [int(districtCenter[0] / len(areaCells)),
        #                  int(districtCenter[1] / len(areaCells))]

        #print(districtCenter)
        #self.rp_districtCenter = districtCenter

        #if districtCenter in areaCells:
            #print("District center is contained within area cells")
        #    self.errorCode = ErrorCode.CENTER_ON_BORDER
        #    self.rp_areaCells = areaCells
        #    return []

        #self.rp_polyVertices = self.DefinePolygoneVertices(map, areaCells)
        #centerIsInsideShape = self.CheckIfPointIsInDistrict(districtCenter, self.rp_polyVertices)
        #for i in range(len(self.districtVertex)):
        #    if UtilityMisc.SegmentsIntersect(self.districtVertex[0], self.districtVertex[1], self.districtVertex[i],
        #                                     districtCenter) \
        #            or UtilityMisc.SegmentsIntersect(self.districtVertex[0], self.districtVertex[2],
        #                                             self.districtVertex[i], districtCenter) \
        #            or UtilityMisc.SegmentsIntersect(self.districtVertex[1], self.districtVertex[3],
        #                                             self.districtVertex[i], districtCenter) \
        #            or UtilityMisc.SegmentsIntersect(self.districtVertex[2], self.districtVertex[3],
        #                                             self.districtVertex[i], districtCenter):
        #        centerIsInsideShape = False

        #if not centerIsInsideShape:
        #    #print("District center is not within the district")
        #    self.errorCode = ErrorCode.CENTER_OUTSIDE
        #    self.rp_areaCells = areaCells
        #    return []

        #cNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, districtCenter[0], districtCenter[1])
        #for n in cNeighbors:
        #    if n in areaCells:
        #        #print("District center is close to the border")
        #        self.errorCode = ErrorCode.CENTER_OUTSIDE
        #        self.rp_areaCells = areaCells
        #        return []

        # Add the cells contained within the district limits
        #print("Definition of the inner district cells")
        #if self.id == 6:
        #    print("--------------- Debug RETURN ---------------------")
        #    self.rp_areaCells = areaCells
        #    return areaCells
        orderedVertices = [
            self.districtVertex[0],
            self.districtVertex[1],
            self.districtVertex[3],
            self.districtVertex[2],
        ]
        fullPath = []
        for v in self.rp_linking1v2v:
            if v not in fullPath:
                fullPath.append(v)

        for v in self.rp_linking2v4v:
            if v not in fullPath:
                fullPath.append(v)

        if len(self.rp_linking3v4v) > 1:
            for i in range(len(self.rp_linking3v4v)):
                v = self.rp_linking3v4v[len(self.rp_linking3v4v) - 1 - i]
                if v not in fullPath:
                    fullPath.append(v)

        if len(self.rp_linking1v3v) > 1:
            for i in range(len(self.rp_linking1v3v)):
                v = self.rp_linking1v3v[len(self.rp_linking1v3v) - 1 - i]
                if v not in fullPath:
                    fullPath.append(v)

        self.defineInnerDistrictCellsRayCast(fullPath, districtMap, map, areaCells)
        #self.DefineInnerDistrictCells(districtCenter, districtMap, roadMap, map, areaCells)

        #print("District n°{} area definition completed".format(self.id))
        self.areaCells = areaCells
        return areaCells

    def PlaceBuildings(self, layerAmount, districtMap: Maps.DistrictMap, buildingMap: Maps.BuildingMap, roadMap: Maps.RoadMap, map, seed, churchesCenters):
        # Define the layers of the district
        self.DefineLayerCells(layerAmount, districtMap, roadMap)

        # Get the first cell of the last layer
        for p in self.layerCells[len(self.layerCells) - 1]:
            if buildingMap.map[p[0]][p[1]] > -1:
                continue

            # Initialize the new house
            currentHouse = Buildings.House(len(self.buildings))
            currentHouseArea = currentHouse.PlaceBuildingAtPos(p, self.layerCells, buildingMap, seed)
            if len(currentHouseArea) > 0:
                buildingMap.AddBuildingToMap(currentHouseArea, len(self.buildings))
                self.buildings.append(currentHouse)

        districtMap.AddDistrictToMap(self.DefineLayerCellsBasedOnBuildings(layerAmount, districtMap, buildingMap), -2)

        if len(self.innerCells) == 0:
            return

        # Define the center of the inner cells
        innerCellsCenter = [0, 0]
        for p in self.innerCells:
            innerCellsCenter[0] += p[0]
            innerCellsCenter[1] += p[1]
        innerCellsCenter = [int(innerCellsCenter[0] / len(self.innerCells)), int(innerCellsCenter[1] / len(self.innerCells))]

        # Define if the center is within the influence of another church
        for c in churchesCenters:
            if UtilityMisc.GetVec2Magnitude([c[0] - innerCellsCenter[0], c[1] - innerCellsCenter[1]]) < CHURCH_INFLUENCE_RADIUS:
                return

        # Place church at center of the inner cells
        church = Buildings.Church(len(self.buildings))
        churchArea = church.PlaceBuildingAtPos(innerCellsCenter, self.layerCells, buildingMap, seed)
        if len(churchArea) > 0:
            buildingMap.AddBuildingToMap(churchArea, len(self.buildings))
            self.buildings.append(church)

    def LinkVertices(self, start, end, districtMap: Maps.DistrictMap, map, areaCells, rpArray: []):
        currentPoint = start
        currentGoal = end

        # Check if it is possible to move from the starting point
        canMove = False
        cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1])
        for c in cellNeighbors:
            if map[c[0]][c[1]][0] == 29 or map[c[0]][c[1]][0] == 40 or districtMap.map[c[0]][c[1]] > -1 \
                    or c in areaCells or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, c):
                continue
            canMove = True

        # Goes through the cells already in the area cells in order to get a starting point that can move
        if not canMove:
            #print("Can't move from initial cell, searching for another")
            visitedCells = []
            propagatingCells = [currentPoint]
            while len(propagatingCells) > 0:
                currentlyPropagatingCells = copy.deepcopy(propagatingCells)

                # Get the neighboring cells that are contained within area cells
                for k in currentlyPropagatingCells:
                    cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, k[0], k[1])
                    visitedCells.append(k)
                    propagatingCells.remove(k)
                    for c in cellNeighbors:
                        if map[c[0]][c[1]][0] == 29 or map[c[0]][c[1]][0] == 40 or districtMap.map[c[0]][c[1]] > -1 or c in visitedCells:
                            continue

                        if c in areaCells:
                            propagatingCells.append(c)

                # Check if one of the cells can be used as a starting point
                for k in propagatingCells:
                    cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, k[0], k[1])

                    for c in cellNeighbors:
                        if map[c[0]][c[1]][0] == 29 or districtMap.map[c[0]][c[1]] > -1 or c in areaCells:
                            continue

                        currentPoint = k
                        break

                if currentPoint != start:
                    #print("New starting point has been defined")
                    break

        # Link the vertices
        while currentPoint != currentGoal:
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1],
                                                                omitDiagonals=False)
            if currentGoal in cellNeighbors:
                currentPoint = currentGoal
                if currentGoal not in areaCells:
                    areaCells.append(currentGoal)
                break

            minID = currentPoint
            minDistance = UtilityMisc.GetVec2Magnitude([currentGoal[0] - currentPoint[0], currentGoal[1] - currentPoint[1]])

            distances = []
            closeToWaterOrDistrict = []
            ids = []
            # Define all the values concerning the valid neighboring cells
            for c in cellNeighbors:
                if map[c[0]][c[1]][0] == 29 or map[c[0]][c[1]][0] == 40 or districtMap.map[c[0]][c[1]] > -1 \
                        or c in areaCells or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, c):
                    continue
                distances.append(UtilityMisc.GetVec2Magnitude([currentGoal[0] - c[0], currentGoal[1] - c[1]]))
                ids.append(c)
                closeToWaterOrDistrict.append(False)
                neighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, c[0], c[1])
                for n in neighbors:
                    if map[n[0]][n[1]][0] == 29 or districtMap.map[n[0]][n[1]] > -1:
                        closeToWaterOrDistrict[len(closeToWaterOrDistrict) - 1] = True

            # Goes over all the cells that are close to a district or water
            for i in range(len(closeToWaterOrDistrict)):
                if closeToWaterOrDistrict[i]:
                    if distances[i] < minDistance:
                        minDistance = distances[i]
                        minID = ids[i]

            if minID == currentPoint:
                for i in range(len(closeToWaterOrDistrict)):
                    if not closeToWaterOrDistrict[i]:
                        if distances[i] < minDistance:
                            minDistance = distances[i]
                            minID = ids[i]

            if currentPoint == minID:
                break

            areaCells.append(minID)
            rpArray.append(minID)
            currentPoint = minID

        return currentPoint == currentGoal

    def DefineVertex(self, o, c1, c2, direction):
        self.rp_circleCenters.append(c1)
        self.rp_circleCenters.append(c2)
        D = [c2[0] - c1[0], c2[1] - c1[1]]
        d = UtilityMisc.GetVec2Magnitude(D)

        ps = UtilityMisc.GetPointOnSegment(c1, c2, random.uniform(SEGMENT_MIN_RATIO, SEGMENT_MAX_RATIO))
        dc1ps = UtilityMisc.GetVec2Magnitude([ps[0] - c1[0], ps[1] - c1[1]])
        dc2ps = UtilityMisc.GetVec2Magnitude([ps[0] - c2[0], ps[1] - c2[1]])

        if d == 0:
            return None

        pd1 = (dc1ps * 100) / d
        pd2 = (dc2ps * 100) / d

        pr1 = random.uniform(pd1 + RADIUS_MIN_OFFSET, RADIUS_MAX_OFFSET)
        pr2 = random.uniform(pd2 + RADIUS_MIN_OFFSET, RADIUS_MAX_OFFSET)

        r1 = (pr1 * d) / 100
        r2 = (pr2 * d) / 100

        self.rp_circleRadius.append(r1)
        self.rp_circleRadius.append(r2)

        a = (math.pow(r1, 2) - math.pow(r2, 2) + math.pow(d, 2)) / (2 * d)
        h = math.sqrt(math.fabs(math.pow(r1, 2) - math.pow(a, 2)))
        xm = c1[0] + a * D[0] / d
        ym = c1[1] + a * D[1] / d

        p1 = [int(xm + h * D[1] / d), int(ym - h * D[0] / d)]
        p2 = [int(xm - h * D[1] / d), int(ym + h * D[0] / d)]

        self.rp_circlePoints.append(p1)
        self.rp_circlePoints.append(p2)

        p1IsValid = True
        p2IsValid = True

        op1 = [p1[0] - o[0], p1[1] - o[1]]
        op2 = [p2[0] - o[0], p2[1] - o[1]]

        a1 = math.pi
        a2 = math.pi

        if op1 != [0, 0]:
            a1 = UtilityMisc.GetAngleBetweenVec2(op1, direction)

        if op2 != [0, 0]:
            a2 = UtilityMisc.GetAngleBetweenVec2(op2, direction)

        if a1 > math.pi / 2:
            p1IsValid = False

        if a2 > math.pi / 2:
            p2IsValid = False

        if not p1IsValid and not p2IsValid:
            return None
        elif p1IsValid and p2IsValid:
            if a1 < a2:
                return p1
            else:
                return p2
        elif p1IsValid:
            return p1
        else:
            return p2

    def DefinePolygoneVertices(self, map, polyCells):
        vertices = [self.districtVertex[0]]
        currentPoint = self.districtVertex[0]
        visitedCells = []
        currentDirection = [0, 0]

        while len(visitedCells) < len(polyCells):
            visitedCells.append(currentPoint)
            neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1])

            distances = []
            direction = []
            ids = []

            for n in neighbours:
                # Check if the neighbour is part of the polygone and not already
                if n not in polyCells or n in visitedCells:
                    continue

                ids.append(n)
                distances.append(UtilityMisc.GetVec2Magnitude([n[0] - currentPoint[0], n[1] - currentPoint[1]]))
                direction.append([n[0] - currentPoint[0], n[1] - currentPoint[1]])

            # Check if valid points has been found
            if len(ids) == 0:
                # Try to go back on the chain until one got a valid point
                for i in range(len(vertices)):
                    v = vertices[len(vertices) - 1 - i]
                    neighbours = UtilityMisc.GetCellNeighborsOnBiMap(map, v[0], v[1])

                    distances = []
                    direction = []
                    ids = []

                    for n in neighbours:
                        # Check if the neighbour is part of the polygone and not already
                        if n not in polyCells or n in visitedCells:
                            continue

                        ids.append(n)
                        distances.append(UtilityMisc.GetVec2Magnitude([n[0] - currentPoint[0], n[1] - currentPoint[1]]))
                        direction.append([n[0] - currentPoint[0], n[1] - currentPoint[1]])

                    # Check if a vertices that got a valid point has been found
                    if len(ids) > 0:
                        currentPoint = v
                        del vertices[len(vertices) - 1 - i:len(vertices) - 1]
                        break

            # Check if another vertices with valid points has been found
            if len(ids) == 0:
                break

            minDistance = 99999
            minDistanceID = -1
            sameDirectionID = -1
            for i in range(len(ids)):
                dir = direction[i]
                dist = distances[i]

                if dist < minDistance:
                    minDistance = dist
                    minDistanceID = i

                if dir == currentDirection:
                    sameDirectionID = i

            # The movement is continuing
            if sameDirectionID != -1:
                currentPoint = ids[sameDirectionID]
            # The movement has not been defined
            elif currentDirection == [0, 0]:
                currentDirection = [ids[minDistanceID][0] - currentPoint[0], ids[minDistanceID][1] - currentPoint[1]]
                currentPoint = ids[minDistanceID]
            # The movement has been interrupted
            else:
                vertices.append(currentPoint)
                currentDirection = [ids[minDistanceID][0] - currentPoint[0], ids[minDistanceID][1] - currentPoint[1]]
                currentPoint = ids[minDistanceID]

        return vertices

    def defineInnerDistrictCellsRayCast(self, polyVertices, districtMap: Maps.DistrictMap, map, areaCells: []):
        minPosition = [99999, 99999]
        maxPosition = [0, 0]

        for v in areaCells:
            if v[0] < minPosition[0]:
                minPosition[0] = v[0]
            if v[1] < minPosition[1]:
                minPosition[1] = v[1]
            if v[0] > maxPosition[0]:
                maxPosition[0] = v[0]
            if v[1] > maxPosition[1]:
                maxPosition[1] = v[1]

        for x in range(minPosition[0], maxPosition[0] + 1):
            for z in range(minPosition[1], maxPosition[1] + 1):
                if districtMap.map[x][z] > -1 or map[x][z][0] == 29 or map[x][z][0] == 40 or [x, z] in areaCells:
                    continue

                if UtilityMisc.CheckIfPointIsInPolygone([x, z], polyVertices):
                    areaCells.append([x, z])

        initialCells = copy.deepcopy(areaCells)
        for c in initialCells:
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, c[0], c[1], omitDiagonals=True)
            for cn in cellNeighbors:
                if cn in areaCells or districtMap.map[cn[0]][cn[1]] > -1 or map[cn[0]][cn[1]][0] == 29:
                    continue

                neigbhors = UtilityMisc.GetCellNeighborsOnBiMap(map, cn[0], cn[1], omitDiagonals=True)
                nSurroundedByAreaCells = True
                for n in neigbhors:
                    if n not in areaCells:
                        nSurroundedByAreaCells = False
                        break

                if nSurroundedByAreaCells:
                    areaCells.append(cn)
                    continue

                neigbhors = UtilityMisc.GetCellNeighborsOnBiMap(map, cn[0], cn[1])
                surroundedBy = 0
                for n in neigbhors:
                    if districtMap.map[n[0]][n[1]] > -1 or map[n[0]][n[1]][0] == 29 or n in areaCells:
                        surroundedBy += 1

                if surroundedBy >= 5:
                    areaCells.append(cn)

    def DefineInnerDistrictCells(self, startingPoint, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map, areaCells):
        addedCells = []
        initialCells = copy.deepcopy(areaCells)
        for c in initialCells:
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, c[0], c[1], omitDiagonals=True)
            for cn in cellNeighbors:
                if cn in areaCells or districtMap.map[cn[0]][cn[1]] > -1 or map[cn[0]][cn[1]][0] == 29:
                    continue

                neigbhors = UtilityMisc.GetCellNeighborsOnBiMap(map, cn[0], cn[1], omitDiagonals=True)
                nSurroundedByAreaCells = True
                for n in neigbhors:
                    if n not in areaCells:
                        nSurroundedByAreaCells = False
                        break

                if nSurroundedByAreaCells:
                    areaCells.append(cn)
                    continue

                neigbhors = UtilityMisc.GetCellNeighborsOnBiMap(map, cn[0], cn[1])
                surroundedBy = 0
                for n in neigbhors:
                    if districtMap.map[n[0]][n[1]] > -1 or map[n[0]][n[1]][0] == 29 or roadMap.map[n[0]][n[1]] == 1 or n in areaCells:
                        surroundedBy += 1

                if surroundedBy >= 5:
                    areaCells.append(cn)
                    addedCells.append(cn)

        propagatingCells = [startingPoint]
        while len(propagatingCells) > 0:
            currentlyPropagatingCells = copy.deepcopy(propagatingCells)
            for c in currentlyPropagatingCells:
                propagatingCells.remove(c)
                cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, c[0], c[1], omitDiagonals=True)

                for cn in cellNeighbors:
                    if map[cn[0]][cn[1]][0] == 29 or districtMap.map[cn[0]][cn[1]] > -1 or (cn in areaCells and cn not in addedCells):
                        continue

                    if cn not in areaCells:
                        areaCells.append(cn)

                    if cn in addedCells:
                        addedCells.remove(cn)

                    propagatingCells.append(cn)

    def DefineLayerCells(self, layerAmount, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap):
        # Define outer layer cells and the neighbouring districts
        self.layerCells.append([])

        #print("Definition of the layer 0")
        for c in self.areaCells:
            neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, c[0], c[1], omitDiagonals=False)

            for n in neighbours:
                if districtMap.map[n[0]][n[1]] != self.id:
                    if c not in self.layerCells[0]:
                        self.layerCells[0].append(c)

                    if districtMap.map[n[0]][n[1]] != -1 and districtMap.map[n[0]][n[1]] not in self.neighbouringDistricts:
                        self.neighbouringDistricts.append(districtMap.map[n[0]][n[1]])

        while len(self.layerCells) < layerAmount:
            #print("Definition of the layer {}".format(len(self.layerCells)))
            self.layerCells.append([])

            for c in self.areaCells:
                # Check if the cell is already in another layer
                if any(c in layer for layer in self.layerCells):
                    continue

                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, c[0], c[1], omitDiagonals=False)

                for n in neighbours:
                    if n in self.layerCells[len(self.layerCells) - 2]:
                        self.layerCells[len(self.layerCells) - 1].append(c)
                        break

        # Define the inner district cells
        for p in self.areaCells:
            if any(p in layer for layer in self.layerCells):
                continue

            self.innerCells.append(p)

    def DefineLayerCellsBasedOnBuildings(self, layerAmount, districtMap: Maps.DistrictMap, buildingMap: Maps.BuildingMap):
        newLayers = [[]]
        # Definition of the building layer
        for c in self.areaCells:
            if buildingMap.map[c[0]][c[1]] > -1:
                if c not in newLayers[0]:
                    newLayers[0].append(c)

        while len(newLayers) < layerAmount:
            #print("Definition of the layer {}".format(len(self.layerCells)))
            newLayers.append([])

            for c in self.areaCells:
                # Check if the cell is already in another layer
                if any(c in layer for layer in newLayers):
                    continue

                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, c[0], c[1], omitDiagonals=False)

                for n in neighbours:
                    if n in newLayers[len(newLayers) - 2]:
                        newLayers[len(newLayers) - 1].append(c)
                        break

        cellsToRemove = []
        for p in self.areaCells:
            # Remove the inner district cells that are contained within one of the new layers from the inner cells
            if any(p in layer for layer in newLayers) and p in self.innerCells:
                self.innerCells.remove(p)
                continue

            # Set cells that are not contained within one of the new layers and that are not an inner cells
            if not any(p in layer for layer in newLayers) and p not in self.innerCells:
                cellsToRemove.append(p)

        # Remove the cells that need to be removed from the area cells
        self.areaCells = [x for x in self.areaCells if x not in cellsToRemove]

        # Set the new layers as the active layers
        self.layerCells = copy.deepcopy(newLayers)

        # Return the points that need to be removed from the district map
        return cellsToRemove

class Stronghold(District):
    def DefineInitialDistrictArea(self, p, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map, seed):
        #print("Initial district area of a stronghold")
        areaCells = []
        initialHeight = map[p[0]][p[1]][1]
        heightOffset = 1
        directions = [
            [1, 0],
            [1, 1],
            [0, 1],
            [-1, 1],
            [-1, 0],
            [-1, -1],
            [0, -1],
            [1, -1]
        ]
        movements = []

        # Initial movements
        for d in directions:
            movements.append([p])
            for i in range(MAX_DISTANCE):
                c = movements[-1][-1]
                n = [c[0] + d[0], c[1] + d[1]]
                dh = abs(map[n[0]][n[1]][1] - initialHeight)

                # Check if the movement can continue
                if map[n[0]][n[1]][0] == 29 or not UtilityMisc.CheckAngleBetweenCells(map, c, n) or dh > heightOffset:
                    break

                movements[-1].append(n)

        # Link the vertices of each
        links = []
        for i in range(-1, len(movements) - 1):
            self.LinkVertices(movements[i][-1], movements[i + 1][-1], districtMap, map, links, areaCells)

        # Add the inner district cells
        self.defineInnerDistrictCellsRayCast(links, districtMap, map, areaCells)

        # Check if the covered area is large enough
        if len(areaCells) < INITIAL_AREA_SIZE:
            areaCells = []
            for i in range(heightOffset + 1, 100):
                # Initial movements
                for k in range(MIN_DISTANCE):
                    tmpMovement = []
                    for j in range(len(directions)):
                        c = movements[j][-1]
                        n = [c[0] + directions[j][0], c[1] + directions[j][1]]
                        dh = abs(map[n[0]][n[1]][1] - initialHeight)
                        tmpMovement.append([0, 0])
                        # Check if the movement is definitely blocked
                        if map[n[0]][n[1]][0] == 29 or not UtilityMisc.CheckAngleBetweenCells(map, c, n):
                            tmpMovement[-1] = [-1, -1]
                            continue

                        if dh > i:
                            continue

                        tmpMovement[-1] = copy.deepcopy(n)

                    if [0, 0] in tmpMovement:
                        break
                    for j in range(len(tmpMovement)):
                        if tmpMovement[j] != [-1, -1]:
                            movements[j].append(tmpMovement[j])


                # Link the vertices of each
                links = []
                for i in range(-1, len(movements) - 1):
                    self.LinkVertices(movements[i][-1], movements[i + 1][-1], districtMap, map, links, areaCells)

                # Add the inner district cells
                self.defineInnerDistrictCellsRayCast(links, districtMap, map, areaCells)
                if len(areaCells) >= INITIAL_AREA_SIZE:
                    break
                areaCells = []

        self.areaCells = copy.deepcopy(areaCells)
        return areaCells

    def PlaceBuildings(self, layerAmount, districtMap: Maps.DistrictMap, buildingMap: Maps.BuildingMap, roadMap: Maps.RoadMap, map, seed, churchesCenters):
        # Define the layers of the district
        self.DefineLayerCells(layerAmount, districtMap, roadMap)

        # Placement of the fort
        for p in self.layerCells[len(self.layerCells) - 1]:
            if buildingMap.map[p[0]][p[1]] > -1:
                continue

            # Initialize the new house
            fort = Buildings.Fort(len(self.buildings))
            fortArea = fort.PlaceBuildingAtPos(p, self.layerCells, buildingMap, seed)
            if len(fortArea) > 0:
                buildingMap.AddBuildingToMap(fortArea, len(self.buildings))
                self.buildings.append(fort)
                break

        # Placement of the barracks
        for p in self.layerCells[len(self.layerCells) - 1]:
            if buildingMap.map[p[0]][p[1]] > -1:
                continue

            barracks = Buildings.Barracks(len(self.buildings))
            barracksArea = barracks.PlaceBuildingAtPos(p, self.layerCells, buildingMap, seed)
            if len(barracksArea) > 0:
                buildingMap.AddBuildingToMap(barracksArea, len(self.buildings))
                self.buildings.append(barracks)
                break

        # Placement of the storage
        for p in self.layerCells[len(self.layerCells) - 1]:
            if buildingMap.map[p[0]][p[1]] > -1:
                continue

            storage = Buildings.Storage(len(self.buildings))
            storageArea = storage.PlaceBuildingAtPos(p, self.layerCells, buildingMap, seed)
            if len(storageArea) > 0:
                buildingMap.AddBuildingToMap(storageArea, len(self.buildings))
                self.buildings.append(storage)
                break

        districtMap.AddDistrictToMap(self.DefineLayerCellsBasedOnBuildings(layerAmount, districtMap, buildingMap), -2)

    def DefineLayerCells(self, layerAmount, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap):
        # Define outer layer cells and the neighbouring districts
        self.layerCells.append([])

        # print("Definition of the layer 0")
        for c in self.areaCells:
            neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, c[0], c[1], omitDiagonals=False)

            for n in neighbours:
                if districtMap.map[n[0]][n[1]] != self.id:
                    if c not in self.layerCells[0]:
                        self.layerCells[0].append(c)

                    if districtMap.map[n[0]][n[1]] != -1 and districtMap.map[n[0]][
                        n[1]] not in self.neighbouringDistricts:
                        self.neighbouringDistricts.append(districtMap.map[n[0]][n[1]])

        while len(self.layerCells) < layerAmount + 1:
            # print("Definition of the layer {}".format(len(self.layerCells)))
            self.layerCells.append([])
            for c in self.areaCells:
                # Check if the cell is already in another layer
                if any(c in layer for layer in self.layerCells):
                    continue

                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, c[0], c[1], omitDiagonals=False)

                for n in neighbours:
                    if n in self.layerCells[len(self.layerCells) - 2]:
                        self.layerCells[len(self.layerCells) - 1].append(c)
                        break

        self.layerCells.append(self.layerCells[-1])
        self.layerCells[-2] = []
        # Define the gate dead zone layer
        for p in self.layerCells[-1]:
            if roadMap.map[p[0]][p[1]] == 1:
                propagatingCells = [p]
                visitedCells = []
                while len(propagatingCells) > 0:
                    currentlyPropagatingCells = copy.deepcopy(propagatingCells)
                    propagatingCells = []
                    for p2 in currentlyPropagatingCells:
                        visitedCells.append(p2)
                        if p2 not in self.layerCells[-2]:
                            self.layerCells[-2].append(p2)

                        neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, p2[0], p2[1])

                        for n in neighbours:
                            if n in visitedCells:
                                continue

                            isContainedWithinUpperLayer = False

                            for i in range(len(self.layerCells) - 1):
                                if n in self.layerCells[i]:
                                    isContainedWithinUpperLayer = True
                                    break

                            if isContainedWithinUpperLayer:
                                continue

                            d = UtilityMisc.GetVec2Magnitude([p2[0] - p[0], p2[1] - p[1]])
                            if d < GATE_DEAD_ZONE_RADIUS:
                                propagatingCells.append(n)

        # Define the inner district cells
        for p in self.areaCells:
            if any(p in layer for layer in self.layerCells):
                continue

            self.innerCells.append(p)

    def DefineLayerCellsBasedOnBuildings(self, layerAmount, districtMap: Maps.DistrictMap, buildingMap: Maps.BuildingMap):
        newLayers = [self.layerCells[-1], self.layerCells[-2], self.layerCells[-3]]

        while len(newLayers) < layerAmount + 2:
            #print("Definition of the layer {}".format(len(self.layerCells)))
            newLayers.append([])

            for c in self.areaCells:
                # Check if the cell is already in another layer
                if any(c in layer for layer in newLayers):
                    continue

                neighbours = UtilityMisc.GetCellNeighborsOnBiMap(districtMap.map, c[0], c[1], omitDiagonals=False)

                for n in neighbours:
                    if n in newLayers[len(newLayers) - 2]:
                        newLayers[len(newLayers) - 1].append(c)
                        break

        cellsToRemove = []
        for p in self.areaCells:
            # Remove the inner district cells that are contained within one of the new layers from the inner cells
            if any(p in layer for layer in newLayers) and p in self.innerCells:
                self.innerCells.remove(p)
                continue

            # Set cells that are not contained within one of the new layers and that are not an inner cells
            if not any(p in layer for layer in newLayers) and p not in self.innerCells:
                cellsToRemove.append(p)

        # Remove the cells that need to be removed from the area cells
        self.areaCells = [x for x in self.areaCells if x not in cellsToRemove]

        # Set the new layers as the active layers
        self.layerCells = copy.deepcopy(newLayers)

        # Return the points that need to be removed from the district map
        return cellsToRemove


class Residential(District):
    rp_linking4v5v: []

    def __init__(self, id):
        super(Residential, self).__init__(id)
        self.rp_linking4v5v = []

    def DefineInitialDistrictArea(self, p, districtMap: Maps.DistrictMap, roadMap: Maps.RoadMap, map, seed):
        #print("Initial district area of a residential one")
        seed += 1
        random.seed(seed)

        areaCells = []
        currentPoint = p

        # Check if p is on the border of water
        pOnWaterCoast = False
        cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1], omitDiagonals=False)
        for n in cellNeighbors:
            if map[n[0]][n[1]][0] == 29 or map[n[0]][n[1]][0] == 40:
                pOnWaterCoast = True
                break

        # Propagate from p until a cell that is bordered by water is encountered is reached
        if not pOnWaterCoast:
            #print("Given point is not bordered by water")
            propagatingCells = [p]
            visitedCells = []
            while not pOnWaterCoast:
                currentlyPropagatingCells = copy.deepcopy(propagatingCells)
                for c in currentlyPropagatingCells:
                    propagatingCells.remove(c)

                    if c in visitedCells or map[c[0]][c[1]][0] == 29 or map[c[0]][c[1]][0] == 40:
                        continue

                    cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, c[0], c[1], omitDiagonals=False)

                    for n in cellNeighbors:
                        nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1], omitDiagonals=False)
                        propagatingCells.append(n)
                        for nn in nNeighbors:
                            if map[nn[0]][nn[1]][0] == 29 or map[nn[0]][nn[1]][0] == 40:
                                currentPoint = n
                                pOnWaterCoast = True
                                break

                        if pOnWaterCoast:
                            break

                    if pOnWaterCoast:
                        #print("Point boredered by water has been found")
                        break

        self.districtVertex.append(currentPoint)
        areaCells.append(currentPoint)

        # Move along the water for the defined movement
        #print("Do first movement")
        movement = random.randrange(MIN_MOVEMENT, MAX_MOVEMENT)
        for i in range(movement):
            #print("Move from {}".format(currentPoint))
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1], omitDiagonals=True)
            currentCellCount = len(areaCells)

            for n in cellNeighbors:
                if map[n[0]][n[1]][0] == 29 or map[n[0]][n[1]][0] == 40 or n in areaCells:# or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, n):
                    #if not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, n):
                    #    print("Invalid neighbor ({}) because of the slope".format(n))
                    continue

                nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1], omitDiagonals=False)

                for nn in nNeighbors:
                    if map[nn[0]][nn[1]][0] == 29 or map[nn[0]][nn[1]][0] == 40:
                        areaCells.append(n)
                        self.rp_linking1v2v.append(n)
                        currentPoint = n
                        break

                if len(areaCells) > currentCellCount:
                    #print("No valid points have been found")
                    break

        self.districtVertex.append(currentPoint)
        movement = random.randrange(MIN_MOVEMENT, MAX_MOVEMENT)
        currentPoint = self.districtVertex[0]
        # Move along the water in the other direction
        #print("Do second movement")
        for i in range(movement):
            #print("Move from {}".format(currentPoint))
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1], omitDiagonals=True)
            currentCellCount = len(areaCells)

            for n in cellNeighbors:
                if map[n[0]][n[1]][0] == 29 or map[n[0]][n[1]][0] == 40 or n in areaCells:# or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, n):
                    #if not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, n):
                    #    print("Invalid neighbor ({}) because of the slope".format(n))
                    continue

                nNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, n[0], n[1], omitDiagonals=False)

                for nn in nNeighbors:
                    if map[nn[0]][nn[1]][0] == 29 or map[nn[0]][nn[1]][0] == 40:
                        areaCells.append(n)
                        self.rp_linking1v3v.append(n)
                        currentPoint = n
                        break

                if len(areaCells) > currentCellCount:
                    #print("No valid points have been found")
                    break

        self.districtVertex.append(currentPoint)

        # Define position of the fourth vertex
        #print("Define position of the fourth vertex")
        direction = [0, 0]

        cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, self.districtVertex[0][0], self.districtVertex[0][1], omitDiagonals=False)
        for n in cellNeighbors:
            if map[n[0]][n[1]][0] == 29 or map[n[0]][n[1]][0] == 40:
                v = [self.districtVertex[0][0] - n[0], self.districtVertex[0][1] - n[1]]
                direction[0] += v[0]
                direction[1] += v[1]

        self.rp_direction = direction
        direction = UtilityMisc.GetNormalizedVec2(direction)
        fourthVertex = self.DefineVertex(self.districtVertex[0], self.districtVertex[0], self.districtVertex[1], direction)
        if fourthVertex is None:
            #print("Fourth vertex based on circles ({}) is invalid, getting new point based on segment".format(fourthVertex))
            ratio = random.uniform(0.2, 0.8)
            pointOnSegment = UtilityMisc.GetPointOnSegment(self.districtVertex[1], self.districtVertex[2], ratio)
            distance = random.randrange(MIN_DISTANCE, MAX_DISTANCE)
            fourthVertex = [int(pointOnSegment[0] + direction[0] * distance),
                            int(pointOnSegment[1] + direction[1] * distance)]
            self.rp_segmentPoint = fourthVertex
        self.districtVertex.append(fourthVertex)
        if self.districtVertex[3][0] < 0:
            self.districtVertex[3][0] = 0
        if self.districtVertex[3][1] < 0:
            self.districtVertex[3][1] = 0
        if self.districtVertex[3][0] >= len(map):
            self.districtVertex[3][0] = len(map) - 1
        if self.districtVertex[3][1] >= len(map[0]):
            self.districtVertex[3][1] = len(map[0]) - 1
        areaCells.append(self.districtVertex[3])

        # Define position of the fifth vertex
        #print("Define position of the fifth vertex")
        fifthVertex = self.DefineVertex(self.districtVertex[0], self.districtVertex[0], self.districtVertex[2], direction)
        if fifthVertex is None:
            #print("Fifth vertex based on circles ({}) is invalid, getting new point based on segment".format(fourthVertex))
            ratio = random.uniform(0.2, 0.8)
            pointOnSegment = UtilityMisc.GetPointOnSegment(self.districtVertex[1], self.districtVertex[2], ratio)
            distance = random.randrange(MIN_DISTANCE, MAX_DISTANCE)
            fifthVertex = [int(pointOnSegment[0] + direction[0] * distance),
                            int(pointOnSegment[1] + direction[1] * distance)]
            self.rp_segmentPoint = fifthVertex
        self.districtVertex.append(fifthVertex)
        if self.districtVertex[4][0] < 0:
            self.districtVertex[4][0] = 0
        if self.districtVertex[4][1] < 0:
            self.districtVertex[4][1] = 0
        if self.districtVertex[4][0] >= len(map):
            self.districtVertex[4][0] = len(map) - 1
        if self.districtVertex[4][1] >= len(map[0]):
            self.districtVertex[4][1] = len(map[0]) - 1
        areaCells.append(self.districtVertex[4])

        #print(self.districtVertex)

        # Link the second vertex to the fourth or fifth vertex
        currentPoint = self.districtVertex[1]
        currentGoal = self.districtVertex[3]

        if UtilityMisc.GetVec2Magnitude([self.districtVertex[4][0] - self.districtVertex[1][0], self.districtVertex[4][1] - self.districtVertex[1][1]]) < \
            UtilityMisc.GetVec2Magnitude([self.districtVertex[3][0] - self.districtVertex[1][0], self.districtVertex[3][1] - self.districtVertex[1][1]]):
            #print("Linking second vertex to fifth vertex")
            currentGoal = self.districtVertex[4]
        #else:
            #print("Linking second vertex to fourth vertex")

        while currentPoint != currentGoal:
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1], omitDiagonals=False)
            minID = currentPoint
            minDistance = UtilityMisc.GetVec2Magnitude([currentGoal[0] - currentPoint[0], currentGoal[1] - currentPoint[1]])
            for c in cellNeighbors:
                if map[c[0]][c[1]][0] == 29 or map[c[0]][c[1]][0] == 40:# or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, c):# or c in areaCells:
                    continue

                distance = UtilityMisc.GetVec2Magnitude([currentGoal[0] - c[0], currentGoal[1] - c[1]])

                if distance < minDistance:
                    minDistance = distance
                    minID = c

            areaCells.append(minID)
            self.rp_linking2v4v.append(minID)
            currentPoint = minID

        # Link the third vertex to the fourth or fifth vertex
        currentPoint = self.districtVertex[2]

        if currentGoal == self.districtVertex[3]:
            currentGoal = self.districtVertex[4]
            #print("Linking third vertex to fifth vertex")
        else:
            currentGoal = self.districtVertex[3]
            #print("Linking third vertex to fourth vertex")

        while currentPoint != currentGoal:
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1],
                                                                omitDiagonals=False)
            minID = currentPoint
            minDistance = UtilityMisc.GetVec2Magnitude([currentGoal[0] - currentPoint[0], currentGoal[1] - currentPoint[1]])
            for c in cellNeighbors:
                if map[c[0]][c[1]][0] == 29 or map[c[0]][c[1]][0] == 40:# or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, c):
                    continue

                distance = UtilityMisc.GetVec2Magnitude([currentGoal[0] - c[0], currentGoal[1] - c[1]])

                if distance < minDistance:
                    minDistance = distance
                    minID = c

            areaCells.append(minID)
            self.rp_linking3v4v.append(minID)
            currentPoint = minID

        # Link the fourth vertex to the fifth vertex
        currentPoint = self.districtVertex[3]
        currentGoal = self.districtVertex[4]
        #print("Linking fourth vertex to fifth vertex")
        while currentPoint != currentGoal:
            cellNeighbors = UtilityMisc.GetCellNeighborsOnBiMap(map, currentPoint[0], currentPoint[1],
                                                                omitDiagonals=False)
            minID = currentPoint
            minDistance = UtilityMisc.GetVec2Magnitude([currentGoal[0] - currentPoint[0], currentGoal[1] - currentPoint[1]])
            for c in cellNeighbors:
                if map[c[0]][c[1]][0] == 29 or map[c[0]][c[1]][0] == 40:# or not UtilityMisc.CheckAngleBetweenCells(map, currentPoint, c):
                    continue

                distance = UtilityMisc.GetVec2Magnitude([currentGoal[0] - c[0], currentGoal[1] - c[1]])

                if distance < minDistance:
                    minDistance = distance
                    minID = c

            areaCells.append(minID)
            self.rp_linking4v5v.append(minID)
            currentPoint = minID

        #self.rp_polyVertices = self.DefinePolygoneVertices(map, areaCells)
        #districtCenter = [0, 0]

        # Define the district center
        #for v in areaCells:
        #    districtCenter[0] += v[0]
        #    districtCenter[1] += v[1]

        #districtCenter = [int(districtCenter[0] / len(areaCells)),
        #                  int(districtCenter[1] / len(areaCells))]

        #self.rp_districtCenter = districtCenter
        # Add the cells contained within the district limits
        #print("Definition of the inner district cells")
        orderedVertices = [
            self.districtVertex[0],
            self.districtVertex[1],
            self.districtVertex[3],
            self.districtVertex[4],
            self.districtVertex[2],
        ]
        # Check the order of the fourth and fifth vertex
        if UtilityMisc.SegmentsIntersect(self.districtVertex[1], self.districtVertex[3], self.districtVertex[2], self.districtVertex[4]):
            orderedVertices[2] = self.districtVertex[4]
            orderedVertices[3] = self.districtVertex[3]

        self.defineInnerDistrictCellsRayCast(orderedVertices, districtMap, map, areaCells)
        #self.DefineInnerDistrictCells(districtCenter, districtMap, roadMap, map, areaCells)

        #print("Initial resiedential district area definition completed")
        self.areaCells = areaCells
        return areaCells
