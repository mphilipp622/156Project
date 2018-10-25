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
        self._items = dict() # hashtable of item key with a value of (price, bidder)
        self._getBidLock = threading.Lock()
        self.PopulateItems(inputFile) # initialize random items
        self.StartServerListener()
    
    def StartServerListener(self):

        # initialize server listener socket

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((self._ipAddress, self._portNumber))

        self._serverSocket.listen(self._maxNumberOfClients)

        print("Socket Created")

    def UpdateClientConnections(self):
        # Check for new clients and update our client dictionary

        # if len(self._connections) >= self._maxNumberOfClients:
        #     return
        while True:
            clientSocket, clientAddress = self._serverSocket.accept()

            clientSocket.settimeout(60)

            # start a thread that listens for a bid from the newly connected client
            # threading.Thread(target = self.GetBidFromClient, args = (clientSocket, clientAddress)).start()

            print('Got connection from', clientAddress)

            # inform new connection of current auction if there is one
            if self._isAuctionActive:
                dataToSend = pickle.dumps((self._currentItem, self._currentHighestBidder))
                clientSocket.send(dataToSend)

            self._connections[clientSocket] = 0 # add this client to the dictionary of connections

        # if clientSocket.recv(1024) == "disconnect":
        #     clientSocket.close() #Receive from client socket
        #     del self._connections[clientAddress[0]]
        #     print str(clientAddress) + " Disconnected"

        # if self._serverSocket.recv(4096) == "disconnect":
        #     print str(clientAddress) + " Disconnected"
        

    def ServerLoop(self):
        print("ServerLoop")

        # while True:
            # if not self._isAuctionActive:
            #     self.StartNewAuction()

            # set a new high bidder
            # self.GetBidsFromClient()

            # broadcast new high bidder to clients
            # self.BroadcastBidUpdate()

    def StartAuction(self, itemForSale):
        auctionMessage = "New Auction Started for item " + itemForSale.GetName() + ". Starting bid is $" + str(itemForSale.GetInitialPrice()) + "\n"
        print(auctionMessage)

        # self._isAuctionActive = True

        # send to clients a tuple of ("Message", bidItem)
        dataToSend = pickle.dumps(("NewAuction", itemForSale))

        for key, value in self._connections.items():
            key.send(dataToSend)

    def StartNewAuction(self):
        # This function should randomize a new item to auction and broadcast the new item to all connected clients
        if len(self._connections) <= 0:
            return

        self._currentItem = self._items[random.randint(0, len(self._items) - 1)] # get random item from list of items
        self._currentHighestBidder = (None, self._currentItem.GetInitialPrice())
        
        auctionMessage = "New Auction Started for item " + self._currentItem.GetName() + ". Starting bid is $" + str(self._currentItem.GetInitialPrice()) + "\n"
        print(auctionMessage)

        self._isAuctionActive = True

        # send to clients a tuple of ("Message", bidItem)
        dataToSend = pickle.dumps(("NewAuction", self._currentItem))

        for key, value in self._connections.items():
            key.send(dataToSend)

        return

    def GetBidsFromClient(self):

        # Non-threaded implementation. Pool the clients and get all their bids, keeping track of the highest one along the way.
        currentHighBid = 0
        for key, value in self._connections.items():
            try:
                data = key.recv(1024)

                if data:
                    if data > currentHighBid:
                        currentHighBid = data
                        self._currentHighestBidder = (key, currentHighBid)
                else:
                    raise error("Client disconnected")

            except:
                key.close()
                return

            # key.send(dataToSend)

    def GetBidFromClient(self, client, address):
        # This function should be listening for bid information from a single client. Multithreaded
        while True:

            self._getBidLock.acquire() # check out a lock to ensure we're reading and writing data atomically

            try:
                data = client.recv(1024)
                if data:
                    if data > self._currentHighestBidder[1]:
                        self._currentHighestBidder = (client, data)
                        self.BroadcastBidUpdate()
                    # response = data
                    # client.send(response)
                else:
                    raise error('Client disconnected')

            except:
                client.close()
                self._getBidLock.release() # be sure to release lock if we lose connection
                return False
            
            self._getBidLock.release()

    def BroadcastBidUpdate(self):
        # This function will tell all connected clients that the price for the item has changed

        # self.BroadcastToWinner()
        return
    
    def PopulateItems(self, inputFile):
        # This function is called from constructor. It will populate items in dinctionary based on the input file given
        
        words = list()

        for line in inputFile:
            for word in line.split():
                words.append(word)

        i = 3 # skip the top line
        while i < len(words):
            # i + 0 = itemName
            # i + 1 = units
            # i + 2 = price
            newItem = itemPackage.Item(words[i], int(words[i + 1]), int(words[i + 2]))
            self._items[newItem] = (None, int(words[i + 2]))
            self.StartAuction(newItem)
            i += 3

        # for i in range(1, random.randint(2, 20)):
        #     newPrice = random.randint(20, 300)
        #     newItem = itemPackage.Item("TestItem" + str(i), i, "TestDescription" + str(i), random.randint(1, 10), newPrice)
        #     self._items[newItem] = (None, newPrice) 
        #     self.StartAuction(newItem)
        # self._items[new Item("TestItem", 123, "TestDescription", 5, 100)] = 100
        # self._items.append(itemPackage.Item("TestItem", 123, "TestDescription", 5, 100))
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

    if len(sys.argv) > 1:
        inputFile = sys.argv[1]
    else:
        print("Please provide an input txt file")
        exit()

    # port 12345. Max clients = 5. Blank IP
    server = Server(open(inputFile, 'r'), "", 12345, 5)

    threading.Thread(target = server.UpdateClientConnections).start() # Thread for listening to new clients
    threading.Thread(target = server.ServerLoop).start() # thread for main server loop

if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
   
    main()