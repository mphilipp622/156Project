import socket
import pickle
import sys
sys.path.append("..") # Adds higher directory to python modules path.
import Item
import random

class Client:

    # Recommend referring to this site for basic intro: https://www.geeksforgeeks.org/socket-programming-python/
    # Recommend installing Python plugins for VS Code. The intellisense is awesome

    def __init__(self, inputFile, newIP, newPort, newBalance):
        self._ipAddress = newIP
        self._portNumber = newPort
        self._balance = newBalance              # the amount of money this client has
        self._activeAuction = None              # this Will be used to determine which auction the client is engaged in 
        self._inventory = list()                # list containing the items this client has won. Can use Item.AddUnit() to increase the number of units of the item

        self.ConnectToServer()

    def ConnectToServer(self):
        # this function should connect the client to the server.
        return

    def StartBid(self):
        # This function should first check if this client has an active auction or not.
        # If we don't have an active auction, then we want to receive a message from the server
        # The server sends a list of auctions in this format:
            # ("NewRound", auctionDictionary)
            # auctionDictionary has GUID strings as a key and Auction class objects as types.
        
        return
    
    def SendBid(self):
        # This function will send a new bid to the server. Likely will use socket.send(bidValue)
        # Client should NOT be able to bid if the amount they are looking to spend is larger than their current balance
        # Client should send None if it is not bidding on an item
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
    # We can simulate multiple clients by opening multiple consoles and running python Client.py

    port = 12345

    s = socket.socket()
    s.connect(("127.0.0.1", port))

    while True:
        data = s.recv(4096)

        dataDecomp = pickle.loads(data)

        if dataDecomp[0] == "AuctionWon":
            print("Won " + dataDecomp[1][0].GetName())
        elif dataDecomp[0] == "NewRound":
            itemChoice = random.choice(list(dataDecomp[1]))
            dataToSend = pickle.dumps((itemChoice, 3999))
            s.send(dataToSend)

if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
    main()