import Utility.UtilityMisc as UtilityMisc

def RemoveClustersFromList(points, clusterMaxSize, removedAtCount):
    clusters = []

    # Try to form a cluster from each point
    for x in range(len(points)):
        currentCluster = [x]
        currentCenter = [points[x][0], points[x][1]]
        for j in range(len(points)):
            if j == x:
                continue

            m = UtilityMisc.GetVec2Magnitude([points[j][0] - currentCenter[0], points[j][1] - currentCenter[1]])
            if m < clusterMaxSize:
                currentCluster.append(j)

                avg = [0, 0]
                for e in currentCluster:
                    avg[0] = avg[0] + points[e][0]
                    avg[1] = avg[1] + points[e][1]

                currentCenter = [avg[0] / len(currentCluster), avg[1] / len(currentCluster)]
            clusters.append(currentCluster)

    # Define the points that are in a to wide cluster
    indexesToRemove = []
    for c in clusters:
        if len(c) >= removedAtCount:
            for i in c:
                if i not in indexesToRemove:
                    indexesToRemove.append(i)

    # Create the resulting list and assigne the kept values
    newPoints = []
    for x in range(len(points)):
        if x not in indexesToRemove:
            newPoints.append(points[x])

    return newPoints

def GetClusterCenterFromPoints(points):
    cx = 0
    cy = 0

    for i in points:
        cx += i[0]
        cy += i[1]

    cx = cx / len(points)
    cy = cy / len(points)

    return [cx, cy]