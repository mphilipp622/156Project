class Item:

    def __init__(self, newName, newUnits, newInitialPrice):
        self._name = newName
        self._units = newUnits
        self._initialPrice = newInitialPrice

    def GetName(self):
        return self._name

    def GetUnits(self):
        return self._units
    
    def GetInitialPrice(self):
        return self._initialPrice

    def RemoveUnit(self):
        self._units -= 1

    def AddUnit(self):
        self._units += 1