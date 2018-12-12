import socket
import pickle
import sys
sys.path.append("..") # Adds higher directory to python modules path.
import Item
import random
import Auction
import math

class Client:

    # Recommend referring to this site for basic intro: https://www.geeksforgeeks.org/socket-programming-python/
    # Recommend installing Python plugins for VS Code. The intellisense is awesome

    def __init__(self, serverIP, newBalance):
        self._balance = newBalance      # the amount of money this client has
        self._activeAuction = None      # this Will be used to determine which auction the client is engaged in. Recommend a Tuple of (GUID, Auction). GUID is passed from the server
        self._inventory = dict()        # list containing the items this client has won.
        self._server = None             # Server socket the client is connected to
        self._clientLastBid = None
        self._bidCeiling = None
        
        self.ConnectToServer(serverIP)

    def SetBidCeiling(self, startingBid):
        multiplier = random.randint(2, 10)

        # highest bid will be 2 - 10 times the startingBid
        
        self._bidCeiling = startingBid + (startingBid * multiplier)

        if self._bidCeiling > self._balance:
            self._bidCeiling = self._balance    # handle the case where the ceilinge exceeds our balance.

    def ConnectToServer(self, serverIP):
        # this function should connect the client to the server.
        self._server = socket.socket()
        self._server.settimeout(10)
        self._server.connect((serverIP, 12345))   # connect to localhost on port 12345, which is specified in server file
    
    def ClientLoop(self):
        # This is the main execution loop for the client that's called from main(). Some example code is shown below.
        # The loop should run a series of Functions that are defined in this class. Recommend having a look at Server.ServerLoop() for an example

        while True:                           # Infinite Loop
            dataDecomp = self.ReceiveDataFromServer()
           
            if dataDecomp[0] == "AuctionsClosed":
                self.CloseClient("No More Items to Bid On. Closing Connection\n")

            if dataDecomp[0] == "AuctionLost":
                print("LOST AUCTION for " + self._activeAuction[1].GetItem().GetName() + "\n")
                self.LeaveAuction()

            # The server sends tuples in the form of ("Message", data)
            if dataDecomp[0] == "AuctionWon":
                # If server sends "AuctionWon" message, it will contain Tuple data (Item, finalBidPrice)
                print("WON " + dataDecomp[1][0].GetName() + "\n")
                self.GetWonItem(dataDecomp)
                print("New Balance: " + str(self._balance) + "\n")

            if dataDecomp[0] == "NewRound":
                if self._activeAuction is not None:
                    self._activeAuction = self.GetUpdatedPriceForAuction(dataDecomp)
                else:
                    self.JoinAuction(dataDecomp)                

                self.SendBid(dataDecomp)

    def JoinAuction(self, data):
        if(self._activeAuction is not None):
            return
        else: #it is None, so pull list of auctions
            # iterate over all the auctions and add the ones the client can afford to a separate list.
            auctionsICanAfford = list()

            for key, value in data[1].items():
                if value.GetCurrentBid() < self._balance:
                    auctionsICanAfford.append(key)

            if len(auctionsICanAfford) == 0:
                self.CloseClient("Cannot afford anymore items. Closing Connection\n")

            auctionChoice = random.choice(auctionsICanAfford)
            self._activeAuction = (auctionChoice, data[1][auctionChoice])
            print("JOIN AUCTION for " + self._activeAuction[1].GetItem().GetName() + "\n")
            self.SetBidCeiling(self._activeAuction[1].GetCurrentBid())
    
    def LeaveAuction(self):
        self._activeAuction = None
        self._clientLastBid = None
        self._bidCeiling = None

    def SendBid(self, data):
        if self._activeAuction is not None:
            currentBid = self._activeAuction[1].GetCurrentBid()

            if currentBid == self._clientLastBid:
                self.SendDataToServer(None, None)
            elif currentBid >= self._bidCeiling:
                print("CEILING REACHED. Leaving auction\n")

                self.SendDataToServer(self._activeAuction[0], "LeaveAuction")
                self.LeaveAuction()
            elif random.random() > 0.3:  # RNG 70% chance to bid
                maxBid = currentBid + math.ceil(int((self._bidCeiling - currentBid) * 0.25)) + 1 # only bids up to 25% of the difference between bid ceiling and current bid at a time
                randomBid = random.randint(currentBid + 1, maxBid)

                self._clientLastBid = randomBid

                print("BID $" + str(randomBid) + " on " + self._activeAuction[1].GetItem().GetName() + "\n")

                self.SendDataToServer(self._activeAuction[0], randomBid)
            else:
                print("NO BID on " + self._activeAuction[1].GetItem().GetName() + "\n")
                self.SendDataToServer(None, None)
        else:
            self.SendDataToServer(None, None)

    def CloseClient(self, closeMessage):
        print(closeMessage)
        
        self._server.close()

        print("Final Inventory:\n\tName\tQuantity\n\t----\t--------")

        for key, value in self._inventory.items():
            print("\t" + key + "\t" + str(value))

        exit()

    def GetWonItem(self, dataDecomp):
        itemName = dataDecomp[1][0].GetName()

        if itemName not in self._inventory:
            self._inventory[itemName] = 1
        else:
            self._inventory[itemName] += 1

        self._balance = self._balance -  self._activeAuction[1].GetCurrentBid()
        self.LeaveAuction()

    def GetUpdatedPriceForAuction(self, data):
        return (self._activeAuction[0], data[1][self._activeAuction[0]])

    def SendDataToServer(self, message, data):
        # helper function that packages data and sends it to a client
        serverACK = "notReceived"
        dataToSend = pickle.dumps((message, data)) # ("NewRound", dict())

        while serverACK == "notReceived":

            try:
                self._server.send(str(len(dataToSend)).encode()) # send the packet size
                receivedSize = self._server.recv(4096).decode()  # wait for server acknowledgement
                
                if receivedSize != "receivedSize":
                    continue

                # print("S received size")
                
                self._server.sendall(dataToSend)
                while serverACK == "notReceived":
                    serverACK = self._server.recv(4096).decode()
            except:
                self.CloseClient("No more items to bid on. Quitting.")
            # print("Client received ACK")
            # print(clientACK)

    def ReceiveDataFromServer(self):
        amountrecv = 0

        try:
            packetsize = int(self._server.recv(4096).decode())

            self._server.sendall("receivedSize".encode())
            # print(packetsize)
            data = b""
            while amountrecv < packetsize:
                # print(amountrecv)

                rec = self._server.recv(4096)    # This listens for data from the server. Program execution is blocked here until data is received
                # print(type(pickle.loads(rec)))
                amountrecv += len(rec)
                data += rec

            # print(amountrecv)

            self._server.sendall("received".encode())
        except:
            self.CloseClient("Connection Error. Quitting.")

        return pickle.loads(data)

def main():
    # implement main client execution here. I imagine this is for a single client.
    # We can do multiple clients by opening multiple consoles and running python Client.py
    # could also put Client.py, Item.py, and Auction.py on another computer and run Client.py. That should work on a LAN.
    if len(sys.argv) < 3:
        print("Error: Please put in an IP address for the server and a starting balance for the client. E.G: python Client.py 192.168.1.1 500")
        exit()
    
    testClient = Client(sys.argv[1], int(sys.argv[2]))
    testClient.ClientLoop()
    
if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
    main()
