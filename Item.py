class Item:

    def __init__(self, newName, newID, newDescription, newUnits, newInitialPrice):
        self.__name = newName
        self.__id = newID
        self.__description = newDescription
        self.__units = newUnits
        self.__initialPrice = newInitialPrice

    def GetName(self):
        return self.__name

    def GetID(self):
        return self.__id

    def GetDescription(self):
        return self.__description

    def GetUnits(self):
        return self.__units
    
    def GetInitialPrice(self):
        return self.__initialPrice