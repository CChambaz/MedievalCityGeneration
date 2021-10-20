import json
import os.path


class Settings:
    heightWeight = 1.0
    waterWeight = 1.0
    variationWeight = 1.0
    minBuildableArea = 1.0
    amountOfPointToKeep = 100

    def __init__(self, filePath):
        # check if the file exist
        if os.path.isfile(filePath):
            # load setting from file
            file = open(filePath, "r")
            data = json.load(file)
            file.close()

            self.heightWeight = data['heightWeight']
            self.waterWeight = data['waterWeight']
            self.variationWeight = data['variationWeight']
            self.minBuildableArea = data['minBuildableArea']
            self.amountOfPointToKeep = data['amountOfPointToKeep']
