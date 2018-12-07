import socket
import pickle
import random
import select
import sys
import time     # used for sleeping the server between updates

# import thread module 
import threading
sys.path.append("..") # Adds higher directory to python modules path. This allows us to grab Item.py

import Item as itemPackage
import Auction
import uuid

class Server:

    def __init__(self, inputFile, newIP, newPort, newMaxNumberOfClients):
        self._ipAddress = newIP
        self._portNumber = newPort
        self._currentItem = None # current item being auctioned
        self._currentHighestBidder = (None, 0) # (socket, currentBid) of the current highest bidder
        self._isAuctionActive = False # sets true if an auction is active
        self._maxNumberOfClients = newMaxNumberOfClients # Specifies the max number of clients server accepts
        self._connections = dict() # hashtable of (userID, socket) KV pairs
        self._auctions = dict() # hashtable of auctionID key with a value of Auction
        self._getBidLock = threading.Lock()
        self._lifetimeConnectionCount = 0 # tracks how many clients have connected over the lifetime of execution. Used for grabbing sockets from _connections

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

        while True:
            clientSocket, clientAddress = self._serverSocket.accept()

            clientSocket.settimeout(60)

            print('Got connection from', clientAddress)

            self._lifetimeConnectionCount += 1
            self._connections[self._lifetimeConnectionCount] = clientSocket # add this client to the dictionary of connections    

    def StartAuction(self, itemForSale):
        auctionMessage = "New Auction Started for item " + itemForSale.GetName() + ". Starting bid is $" + str(itemForSale.GetInitialPrice()) + "\n"
        print(auctionMessage)

        # Create a new entry in the hashtable.
        self._auctions[uuid.uuid4().hex] = Auction.Auction(itemForSale)

    def CloseAuction(self, auctionID):
        # decrement the number of units on the item
        self._auctions[auctionID].GetItem().RemoveUnit()

        if self._auctions[auctionID].GetItem().GetUnits() <= 0:
            # if the item has no more units, delete it from the dictionary
            del self._auctions[auctionID]
        else:
            # otherwise, reset the auction
            self._auctions[auctionID].ResetAuction()


    def GetBidsFromClients(self):

        # Non-threaded implementation. Pool the clients and get all their bids.
        if len(self._connections) == 0:
            return

        for clientID, clientSocket in self._connections.items():
            
            # should receive a tuple (itemName, clientBid) from client
            auctionID, clientBid = self.ReceiveDataFromClient(clientSocket)
            
            item = self._auctions[auctionID].GetItem() # grab the Item instance
            print(auctionID)
            print(item.GetName())

            if clientBid > self._auctions[auctionID].GetCurrentBid():
                self._auctions[auctionID].SetNewHighestBid(clientID, clientBid)
                print("Client " + str(clientID) + " Has Highest Bid on " + item.GetName() + ":\t$" + str(clientBid))

        # iterate over the auctions and update the number of rounds since receiving a bid
        for auctionID, auction in self._auctions.items():
            auction.ReceivedNoBids()

    def BroadcastNewBiddingRound(self):
        # This function will tell all connected clients that another round of bidding has started
        dataToSend = pickle.dumps(("NewRound", self._auctions))

        for clientID, clientSocket in self._connections.items():
            self.SendDataToClient(clientSocket, "NewRound", self._auctions)
    
    def PopulateItems(self, inputFile):
        # This function is called from constructor. It will parse the input file and start auctions for each item
        
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

            self.StartAuction(newItem)
            i += 3

    def BroadcastToWinner(self):
        # Check the auctions and see if any have finished. If an auction has finished, broadcast the winning to the bidder
        
        if len(self._connections) == 0:
            return

        for auctionID, auction in self._auctions.items():
            if auction.IsFinished():
                try:
                    # send a tuple to the client of ("AuctionWon", (item, finalBid))
                    tupleToSend = (auction.GetItem(), auction.GetCurrentBid())
                    clientSocket = self._connections[auction.GetCurrentHighestBidder()]
                    self.SendDataToClient(clientSocket, "AuctionWon", tupleToSend)
                    self.CloseAuction(auctionID)
                except socket.error:
                    print("Failed to deliver item to winner Client " + str(auction.GetCurrentHighestBidder()) )
                    # del self._connections[self._currentHighestBidder[0]]
    
    def SendDataToClient(self, clientSocket, message, data):
        # helper function that packages data and sends it to a client
        clientACK = "notReceived"
        dataToSend = pickle.dumps((message, data)) # ("NewRound", dict())

        while clientACK == "notReceived":

            clientSocket.sendall(str(len(dataToSend)).encode())
            receivedSize = clientSocket.recv(1024).decode()
            
            if receivedSize != "receivedSize":
                continue

            print("Client received size")
            
            clientSocket.sendall(dataToSend)
            while clientACK == "notReceived":
                clientACK = clientSocket.recv(1024).decode()
            print("Client received ACK")
            # print(clientACK)
    
    # helper function for properly receivin data from server
    def ReceiveDataFromClient(self, socket):
        amountrecv = 0
        packetsize = int(socket.recv(1024))

        socket.sendall("receivedSize".encode())
        data = b""

        while amountrecv < packetsize:
            try:
                rec = socket.recv(1024)
            except:
                print("Exception Occurred")
                socket.close()

            amountrecv += len(rec)

            data += rec
        
        socket.sendall("received".encode())
        return pickle.loads(data)
        
    def ServerLoop(self):
        print("ServerLoop")

        while True:
            self.BroadcastNewBiddingRound()
            self.GetBidsFromClients()
            self.BroadcastToWinner()
            time.sleep(1)   # sleep thread between bidding rounds
    
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