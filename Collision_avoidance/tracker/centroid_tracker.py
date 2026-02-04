from scipy.spatial import distance
import numpy as np

class CentroidTracker:
    def __init__(self):
        self.nextObjectID = 0
        self.objects = {}

    def register(self, centroid):
        self.objects[self.nextObjectID] = centroid
        self.nextObjectID += 1

    def update(self, rects):
        if len(rects) == 0:
            return self.objects

        inputCentroids = []

        for (x1,y1,x2,y2) in rects:
            cx = int((x1+x2)/2)
            cy = int((y1+y2)/2)
            inputCentroids.append((cx,cy))

        if len(self.objects) == 0:
            for c in inputCentroids:
                self.register(c)
        else:
            objectIDs = list(self.objects.keys())
            objectCentroids = list(self.objects.values())

            D = distance.cdist(np.array(objectCentroids), np.array(inputCentroids))

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            usedRows = set()
            usedCols = set()

            for (row,col) in zip(rows,cols):
                if row in usedRows or col in usedCols:
                    continue

                objectID = objectIDs[row]
                self.objects[objectID] = inputCentroids[col]

                usedRows.add(row)
                usedCols.add(col)

            unusedCols = set(range(0,len(inputCentroids))).difference(usedCols)

            for col in unusedCols:
                self.register(inputCentroids[col])

        return self.objects
