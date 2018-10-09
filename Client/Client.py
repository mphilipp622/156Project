import socket
import sys
sys.path.append("..") # Adds higher directory to python modules path.

import Item as itemPackage

class Client:

    # Recommend referring to this site for basic intro: https://www.geeksforgeeks.org/socket-programming-python/
    # Recommend installing Python plugins for VS Code. The intellisense is awesome

    def __init__(self, inputFile, newIP, newPort, newBalance):
        self._ipAddress = newIP
        self._portNumber = newPort
        self._balance = newBalance # the amount of money this client has
        self._isParticipatingInAuction = False # sets True if this client is participating in an active auction
        self._items = dict() # hashtable of (Item, maxBidPrice) key-value pairs
        self._inventory = list() # list containing the items this client has won
        self.PopulateItemMaxPrices(inputFile)
        self.ConnectToServer()

    def PopulateItemMaxPrices(self, inputFile):
        # this function will read the input file containing item information and add them to the __items dictionary
        # This is dependent on the structure of the file Ming Li is looking to give us
        # newItem = itemPackage.Item("itemName", 123, "description", 20, 100).
        return

    def ConnectToServer(self):
        # this function should connect the client to the server. Need to establish connection still
        return

    def GetAuction(self):
        # This function listens for a new auction from the server. Server will probably send tuple (item, startingBid)
        # This function will also use some kind of randomization to determine if this client will participate
        # Client should send its starting bid to the server at the end of this function. SendBid(newBid)
        return
    
    def SendBid(self):
        # This function will send a new bid to the server. Likely will use socket.send(bidValue)
        # Client should NOT be able to bid if the amount they are looking to spend is larger than their current balance
        return

    def GetAuctionUpdate(self):
        # this function will listen for auction data from the server. 
        # Server will send a tuple of (item, newPrice) through the socket
        return

    def GetWonItem(self):
        # this function should listen for the server to send an item to this client upon winning a bid.
        # The item will be sent as an (item, cost) tuple
        # The client should add the new item to the inventory list and subtract the cost from their current balance
        return

def main():
    # implement main client execution here. I imagine this is for a single client.
    # We can simulate multiple clients by opening multiple consoles.
    # Or we could just have this single file create a list of clients. Not sure how to approach it at the moment.
    return

if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
    main()