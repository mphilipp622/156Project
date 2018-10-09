import socket
import pickle
import random
import select
import sys

# import thread module 
import threading
sys.path.append("..") # Adds higher directory to python modules path.

import Item as itemPackage

class Server:

    def __init__(self, inputFile, newIP, newPort, newMaxNumberOfClients):
        self._ipAddress = newIP
        self._portNumber = newPort
        self._currentItem = None # current item being auctioned
        self._currentHighestBidder = (None, 0) # (socket, currentBid) of the current highest bidder
        self._isAuctionActive = False # sets true if an auction is active
        self._maxNumberOfClients = newMaxNumberOfClients # Specifies the max number of clients server accepts
        # self._items = dict() # hashtable of (Item, (ipAddress, currentHighestBid)) KV pairs
        self._connections = dict() # hashtable of (socket, bidAmount) KV pairs
        self._items = list()
        self.PopulateItems(inputFile)
        self.StartServerListener()
    
    def StartServerListener(self):

        # initialize server listener socket

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((self._ipAddress, self._portNumber))

        self._serverSocket.listen(self._maxNumberOfClients)

        print "Socket Created"

    def UpdateClientConnections(self):
        # Check for new clients and update our client dictionary

        # if len(self._connections) >= self._maxNumberOfClients:
        #     return

        clientSocket, clientAddress = self._serverSocket.accept()

        self._connections[clientSocket] = 0 # add this client to the dictionary of connections

        clientSocket.settimeout(60)
        threading.Thread(target = self.GetBidFromClient, args = (clientSocket, clientAddress)).start()

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
        

    def ServerLoop(self):
        print "ServerLoop"

        while True:
            if not self._isAuctionActive:
                self.StartNewAuction

            self.GetBidFromClient()

            self.BroadcastBidUpdate()

    def StartNewAuction(self):

        # This function should randomize a new item to auction and broadcast the new item to all connected clients
        if len(self._connections) <= 0:
            return

        self._currentItem = self._items[random.randint(0, len(self._items) - 1)] # get random item from list of items
        print "New Auction Started for item " + self._currentItem.GetName() + ". Starting bid is $" + self._currentItem.GetInitialPrice()
        self._isAuctionActive = True

        # send to clients a tuple of ("Message", bidItem)
        dataToSend = pickle.dumps(("NewAuction", self._currentItem))

        for key, value in self._connections.items():
            key.send(dataToSend)

        return

    def GetBidFromClient(self, client, address):
        # This function should be listening for bid information from connected clients
        while True:
            try:
                data = client.recv(1024)
                if data:
                    if data > self._currentHighestBidder[1]:
                        self._currentHighestBidder = (client, data)
                    # response = data
                    # client.send(response)
                else:
                    raise error('Client disconnected')
            except:
                client.close()
                return False

        self.BroadcastBidUpdate()
        return

    def BroadcastBidUpdate(self):
        # This function will tell all connected clients that the price for the item has changed

        # self.BroadcastToWinner()
        return
    
    def PopulateItems(self, inputFile):
        # This function is called from constructor. It will populate items in dinctionary based on the input file given
        self._items.append(itemPackage.Item("TestItem", 123, "TestDescription", 5, 100))
        return

    def BroadcastToWinner(self):
        # Check to see if the high bidder is still connected
        try:
            self._currentHighestBidder[0].send((self._currentItem, self._currentHighestBidder[1]))
        except socket.error:
            del self._connections[self._currentHighestBidder[0]]

        self._isAuctionActive = False


    
def main():
    # Program Execution
    server = Server(None, "", 12345, 5)

    threading.Thread(target = server.UpdateClientConnections).start() # Thread for listening to new clients
    threading.Thread(target = server.ServerLoop).start() # thread for main server loop

if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
   
    main()