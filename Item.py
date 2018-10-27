import uuid # used for generating GUID's for items

class Item:

    def __init__(self, newName, newUnits, newInitialPrice):
        self._id = uuid.uuid4().hex
        self._name = newName
        # self._id = newID
        # self._description = newDescription
        self._units = newUnits
        self._initialPrice = newInitialPrice

    def GetName(self):
        return self._name

    def GetID(self):
        return self._id

    # def GetDescription(self):
    #     return self._description

    def GetUnits(self):
        return self._units
    
    def GetInitialPrice(self):
        return self._initialPrice