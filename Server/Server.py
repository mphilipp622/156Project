import socket
import pickle
import random
import select
import sys
sys.path.append("..") # Adds higher directory to python modules path.

import Item as itemPackage

class Server:

    def __init__(self, inputFile, newIP, newPort, newMaxNumberOfClients):
        self._ipAddress = newIP
        self._portNumber = newPort
        self._currentItem = None # current item being auctioned
        self._currentHighestBidder = ("", 0) # (IP address, currentBid) of the current highest bidder
        self._isAuctionActive = False # sets true if an auction is active
        self._maxNumberOfClients = newMaxNumberOfClients # Specifies the max number of clients server accepts
        # self._items = dict() # hashtable of (Item, (ipAddress, currentHighestBid)) KV pairs
        self._connections = dict() # hashtable of (ipaddress, socket) KV pairs
        self._items = list()
        self.PopulateItems(inputFile)
        self.StartServerListener()
    
    def StartServerListener(self):

        # initialize server listener socket

        self._serverSocket = socket.socket()
        self._serverSocket.bind((self._ipAddress, self._portNumber))

        self._serverSocket.listen(self._maxNumberOfClients)

        print "Socket Created"

    def UpdateClientConnections(self):
        # Check for new clients and update our client dictionary

        # if len(self._connections) >= self._maxNumberOfClients:
        #     return

        clientSocket, clientAddress = self._serverSocket.accept()

        self._connections[clientAddress[0]] = clientSocket # add this client to the dictionary of connections

        print 'Got connection from', clientAddress

        # inform new connection of current auction if there is one
        if self._isAuctionActive:
            clientSocket.send((self._currentItem, self._currentHighestBidder[1]))

        # if clientSocket.recv(1024) == "disconnect":
        #     clientSocket.close() #Receive from client socket
        #     del self._connections[clientAddress[0]]
        #     print str(clientAddress) + " Disconnected"

        # if self._serverSocket.recv(4096) == "disconnect":
        #     print str(clientAddress) + " Disconnected"

    def StartNewAuction(self):

        # This function should randomize a new item to auction and broadcast the new item to all connected clients
        if len(self._connections) <= 0:
            return

        print "New Auction Started"
        self._currentItem = self._items[random.randint(0, len(self._items))] # get random item from list of items
        self._isAuctionActive = True

        # send to clients a tuple of ("Message", bidItem)
        dataToSend = pickle.dumps(("NewAuction", self._currentItem))

        for key, value in self._connections.items():
            value.send(dataToSend)

        return

    def GetBidFromClient(self):
        # This function should be listening for bid information from connected clients
        self.BroadcastBidUpdate()
        return

    def BroadcastBidUpdate(self):
        # This function will tell all connected clients that the price for the item has changed
        return
    
    def PopulateItems(self, inputFile):
        # This function is called from constructor. It will populate items in dinctionary based on the input file given
        self._items.append(itemPackage.Item("TestItem", 123, "TestDescription", 5, 100))
        return

    def BroadcastToWinner(self):
        # Check to see if the high bidder is still connected
        try:
            self._connections[self._currentHighestBidder[0]].send((self._currentItem, self._currentHighestBidder[1]))
        except socket.error:
            del self._connections[self._currentHighestBidder[0]]


    
def main():
    # Program Execution
    server = Server(None, "", 12345, 5)
    server.UpdateClientConnections()

    server.StartNewAuction()

if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
   
    main()