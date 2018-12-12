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
        self._maxNumberOfClients = newMaxNumberOfClients    # Specifies the max number of clients server accepts
        self._currentItem = None                            # current item being auctioned
        self._currentHighestBidder = (None, 0)              # (socket, currentBid) of the current highest bidder
        self._isAuctionActive = False                       # sets true if an auction is active
        self._getBidLock = threading.Lock()
        self._lifetimeConnectionCount = 0                   # tracks how many clients have connected over the lifetime of execution. Used for grabbing sockets from _connections
        
        self._clientsToDelete = list()  # keeps a list of clients that have disconnected and need to be removed from connection dictionary
        self._auctionsToDelete = list() # will contain a list of auctions that need to be deleted after a round
        
        self._clientsToAdd = dict()     # keeps track of newly connected clients. We will add them after a round of bidding.
        self._connections = dict()      # hashtable of (userID, socket) KV pairs
        self._auctions = dict()         # hashtable of auctionID key with a value of Auction
        
        self.PopulateItems(inputFile)   # initialize random items
        self.StartServerListener()      # Start server
    
    def StartServerListener(self):

        # initialize server listener socket

        self._serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._serverSocket.bind((self._ipAddress, self._portNumber))

        self._serverSocket.listen(self._maxNumberOfClients)

        print("Socket Created\n")

    def CloseServer(self):
        # Closes the server and all connected sockets then exits program.
        self._serverSocket.close()
        for key, value in self._connections.items():
            self.CloseConnection(key, value)
        
        exit()

    def UpdateClientConnections(self):
        # Check for new clients and update our client dictionary. Runs on a separate thread from main server loop

        while True:

            try:
                clientSocket, clientAddress = self._serverSocket.accept()   # get the client

                if len(self._connections) >= self._maxNumberOfClients:
                    # reject client if we have too many clients connected
                    clientSocket.close()
                    continue

                clientSocket.settimeout(10)             # timeout error is thrown after 10 seconds of not getting data from this client

                print("Got connection from ", clientAddress)

                self._lifetimeConnectionCount += 1      # track lifetime connections. Used for client ID's
                self._clientsToAdd[self._lifetimeConnectionCount] = clientSocket    # add this client to the dictionary of connections
            except:
                break

    def AddNewClients(self):
        # Adds clients to the connections dictionary. Called on each round after client communications are done.

        for key, value in self._clientsToAdd.items():
            self._connections[key] = value
        
        self._clientsToAdd.clear()      # empty the dictionary

    def StartAuction(self, itemForSale):
        # starts an auction for itemForSale

        auctionMessage = "New Auction Started for item " + itemForSale.GetName() + ". Starting bid is $" + str(itemForSale.GetInitialPrice()) + "\n"
        print(auctionMessage)

        # Create a new entry in the hashtable with a unique auction ID
        self._auctions[uuid.uuid4().hex] = Auction.Auction(itemForSale)

    def CloseAuction(self, auctionID):
        # Closes the auction

        self._auctions[auctionID].GetItem().RemoveUnit()    # decrement the number of units on the item
        item = self._auctions[auctionID].GetItem()          # grab the auction's item for easy printing
        auction = self._auctions[auctionID]

        print("Auction for " + item.GetName() + " sold to " + \
        str(auction.GetCurrentHighestBidder()) + " for $" + str(auction.GetCurrentBid()) + \
        ". Remaining Quantity: " + str(item.GetUnits()) + "\n")

        if self._auctions[auctionID].GetItem().GetUnits() <= 0:
            # if the item has no more units, delete it from the dictionary
            self._auctionsToDelete.append(auctionID)
        else:
            # otherwise, reset the auction
            self._auctions[auctionID].ResetAuction()

    def DeleteInvalidAuctions(self):
        # removes auctions that no longer have any items left.

        for auctionID in self._auctionsToDelete:
            del self._auctions[auctionID]

        self._auctionsToDelete = []

        if len(self._auctions) == 0:
            # we've run out of items so close server
            print("No more items for auction. Closing Server\n")
            self.CloseServer()

    def GetBidsFromClients(self):

        # Non-threaded implementation. Poll the clients and get all their bids.
        if len(self._connections) == 0:
            return  # leave the function if we have no clients connected

        for clientID, clientSocket in self._connections.items():
            
            # should receive a tuple (itemName, clientBid) from client
            data = self.ReceiveDataFromClient(clientID, clientSocket)

            if data is None:
                # client has disconnected
                self.CloseConnection(clientID, clientSocket)
                continue

            if data[0] is None and data[1] is None:
                # client did not bid, so continue
                continue

            auctionID, clientBid = data

            if clientBid == "LeaveAuction":
                # client has left an auction.
                self._auctions[auctionID].RemoveBidder(clientID)    # remove the bidder from the auction
                continue

            item = self._auctions[auctionID].GetItem() # grab the Item instance

            self._auctions[auctionID].AddBidder(clientID)   # add the client as a bidder for this auction

            if clientBid > self._auctions[auctionID].GetCurrentBid():
                # if the client has set the new highest bid, update the auction's highest bidder
                self._auctions[auctionID].SetNewHighestBid(clientID, clientBid)
                print("Client " + str(clientID) + " Has Highest Bid on " + item.GetName() + ":\t$" + str(clientBid) + "\n")

        # iterate over the auctions and update the number of rounds since receiving a bid
        for auctionID, auction in self._auctions.items():
            auction.ReceivedNoBids()

        # Handle the removal of any clients that may have had a connection error
        self.DeleteDisconnectedClients()

    def BroadcastNewBiddingRound(self):
        # This function will tell all connected clients that another round of bidding has started

        if len(self._connections) == 0:
            # ignore the function if we have no clients connected
            return

        # iterate over each client and tell them a new round has started or that the auction house has closed
        for clientID, clientSocket in self._connections.items():
            if len(self._auctions) == 0:
                self.SendDataToClient(clientID, clientSocket, "AuctionsClosed", None)
            else:
                self.SendDataToClient(clientID, clientSocket, "NewRound", self._auctions)
        
        self.DeleteDisconnectedClients()
    
    def PopulateItems(self, inputFile):
        # This function is called from constructor. It will parse the input file and start auctions for each item
        
        words = list()

        for line in inputFile:
            for word in line.split():
                words.append(word)  # grab the individual words from the file

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
            # ignore function if no clients connected
            return

        for auctionID, auction in self._auctions.items():
            if auction.IsFinished():
                # send a tuple to the client of ("AuctionWon", (item, finalBid))
                tupleToSend = (auction.GetItem(), auction.GetCurrentBid())
                clientSocket = self._connections[auction.GetCurrentHighestBidder()]

                # Tell the client they won and send them the item and the final cost
                self.SendDataToClient(auction.GetCurrentHighestBidder(), clientSocket, "AuctionWon", tupleToSend)

                for bidderID in auction.GetBidders():
                    # tell all other bidders the auction is closed and they lost

                    if bidderID not in self._connections:
                        # handle edge case where a bidder has had a connection error but the connection hasn't been removed
                        continue
                    
                    if bidderID != auction.GetCurrentHighestBidder():
                        # ignore the other highest bidder
                        loserSocket = self._connections[bidderID]
                        self.SendDataToClient(bidderID, loserSocket, "AuctionLost", None)   # tell other clients they lost
                
                self.CloseAuction(auctionID)
                self.DeleteDisconnectedClients()
        
        self.DeleteDisconnectedClients()

    def CloseConnection(self, clientID, clientSocket):
        if clientID in self._clientsToDelete:
            return

        print("CLOSE CONNECTION " + str(clientID) + "\n")
        clientSocket.close()
        self._clientsToDelete.append(clientID)
    
    def DeleteDisconnectedClients(self):
        for clientID in self._clientsToDelete:
            del self._connections[clientID]

        self._clientsToDelete = []  # set the list of clients to delete back to empty
    
    def SendDataToClient(self, clientID, clientSocket, message, data):
        # helper function that packages data and sends it to a client
        clientACK = "notReceived"

        try:
            dataToSend = pickle.dumps((message, data))

            while clientACK == "notReceived":

                clientSocket.sendall(str(len(dataToSend)).encode()) # tell the client how large the data is
                receivedSize = clientSocket.recv(4096).decode()     # wait for client acknowledgement of data size
                
                if receivedSize != "receivedSize":
                    continue
                
                clientSocket.sendall(dataToSend)    # send the data to the client
                while clientACK == "notReceived":
                    clientACK = clientSocket.recv(4096).decode()    # get acknowledgement from client that they got the data
        
        except:
            self.CloseConnection(clientID, clientSocket)
    
    def ReceiveDataFromClient(self, clientID, clientSocket):
        # helper function for properly receiving data from server
        amountrecv = 0  # tracks how much of the data we've received.
        
        try:
            packetsize = int(clientSocket.recv(4096))       # get the size of the data the client is sending us

            clientSocket.sendall("receivedSize".encode())   # tell the client we got the data size
            data = b""  # This will hold our data in bit format

            while amountrecv < packetsize:
                # as long as we still have more data to receive, we will keep looping.

                rec = clientSocket.recv(4096)   # get data from the client

                amountrecv += len(rec)          # add the amount of data we just received to our total.

                data += rec                     # concatenate the new data onto the data we've received up to this point.
            
            clientSocket.sendall("received".encode())   # tell the client we got their data.
        except:
            self.CloseConnection(clientID, clientSocket)
            return None

        return pickle.loads(data)
        
    def ServerLoop(self):
        # This is the main loop for the server

        while True:
            # loops forever

            while len(self._connections) == 0 and len(self._clientsToAdd) == 0:
                continue    # if there's no connections, spin lock until we get a connection.

            self.BroadcastNewBiddingRound()
            self.GetBidsFromClients()
            self.BroadcastToWinner()

            self.DeleteInvalidAuctions()
            self.DeleteDisconnectedClients()
            self.AddNewClients()

            time.sleep(1)   # sleep thread between bidding rounds

    
def main():
    # Program Execution

    # handle terminal compilation
    if len(sys.argv) > 1:
        inputFile = sys.argv[1]
    else:
        print("Please provide an input txt file")
        exit()

    # port 12345. Max clients = 5. Blank IP for running on localhost
    server = Server(open(inputFile, 'r'), "", 12345, 5)

    threading.Thread(target = server.UpdateClientConnections).start()   # Thread for listening to new clients
    threading.Thread(target = server.ServerLoop).start()                # thread for main server loop

if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
   
    main()