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
        self._connections = dict() # hashtable of (userID, socket) KV pairs
        self._items = dict() # hashtable of itemID key with a value of (Item, bidder, price)
        self._getBidLock = threading.Lock()
        self.PopulateItems(inputFile) # initialize random items
        self.StartServerListener()

        self._lifetimeConnectionCount = 0 # tracks how many clients have connected over the lifetime of execution. Used for grabbing sockets from _connections
    
    def StartServerListener(self):

        # initialize server listener socket

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((self._ipAddress, self._portNumber))

        self._serverSocket.listen(self._maxNumberOfClients)

        print("Socket Created")

    def UpdateClientConnections(self):
        # Check for new clients and update our client dictionary

        while True:
            clientSocket, clientAddress = self._serverSocket.accept()

            clientSocket.settimeout(60)

            print('Got connection from', clientAddress)

            # inform new connection of current auction if there is one
            if self._isAuctionActive:
                dataToSend = pickle.dumps((self._currentItem, self._currentHighestBidder))
                clientSocket.send(dataToSend)

            self._lifetimeConnectionCount += 1
            self._connections[self._lifetimeConnectionCount] = clientSocket# add this client to the dictionary of connections    

    def StartAuction(self, itemForSale):
        auctionMessage = "New Auction Started for item " + itemForSale.GetName() + ". Starting bid is $" + str(itemForSale.GetInitialPrice()) + "\n"
        print(auctionMessage)

        # self._isAuctionActive = True

        # send to clients a tuple of ("Message", bidItem)

    def GetBidsFromClients(self):

        # Non-threaded implementation. Pool the clients and get all their bids.

        for key, value in self._connections.items():
            try:
                data = value.recv(4096)

                # should receive a tuple (itemName, clientBid) from client
                itemID, clientBid = pickle.loads(data)

                item = self._items[itemID][0] # grab the Item instance
                print(itemID)
                print(item.GetName())

                if clientBid > self._items[itemID][1]:
                    print("Received Bid From Client " + str(key))
                    self._items[itemID] = (item, key, clientBid)
                    print("Client " + str(key) + " Has Highest Bid on " + item.GetName() + ":\t$" + str(clientBid))
                # else:
                #     raise error("Client disconnected")

            except:
                print("Exception Occurred")
                value.close()

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

    def BroadcastNewBiddingRound(self):
        # This function will tell all connected clients that another round of bidding has started
        dataToSend = pickle.dumps(("NewRound", self._items))

        for key, value in self._connections.items():
            value.send(dataToSend)

        # self.BroadcastToWinner()
    
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

            # Create a new entry in the hashtable.
            self._items[newItem.GetID()] = (newItem, None, int(words[i + 2]))

            self.StartAuction(newItem)
            i += 3

    def BroadcastToWinner(self):
        # Check to see if the high bidder is still connected
        try:
            self._currentHighestBidder[0].send((self._currentItem, self._currentHighestBidder[1]))
        except socket.error:
            del self._connections[self._currentHighestBidder[0]]

        self._isAuctionActive = False
    
    def ServerLoop(self):
        print("ServerLoop")

        while True:
            self.BroadcastNewBiddingRound()
            self.GetBidsFromClients()
    
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