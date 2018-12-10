import socket
import pickle
import sys
sys.path.append("..") # Adds higher directory to python modules path.
import Item
import random
import Auction

class Client:

    # Recommend referring to this site for basic intro: https://www.geeksforgeeks.org/socket-programming-python/
    # Recommend installing Python plugins for VS Code. The intellisense is awesome

    def __init__(self, serverIP, newBalance):
        self._balance = newBalance      # the amount of money this client has
        self._activeAuction = None      # this Will be used to determine which auction the client is engaged in. Recommend a Tuple of (GUID, Auction). GUID is passed from the server
        self._inventory = dict()        # list containing the items this client has won.
        self._server = None             # Server socket the client is connected to
        self._clientLastBid = None
        
        self.ConnectToServer(serverIP)

    def ConnectToServer(self, serverIP):
        # this function should connect the client to the server.
        self._server = socket.socket()
        self._server.connect((serverIP, 12345))   # connect to localhost on port 12345, which is specified in server file
    
    def ClientLoop(self):
        # This is the main execution loop for the client that's called from main(). Some example code is shown below.
        # The loop should run a series of Functions that are defined in this class. Recommend having a look at Server.ServerLoop() for an example

        while True:                           # Infinite Loop
            dataDecomp = self.ReceiveDataFromServer()
           
            if dataDecomp[0] == "AuctionsClosed":
                self.CloseClient("No More Items to Bid On. Closing Connection\n")

            elif dataDecomp[0] == "AuctionLost":
                self._activeAuction = None

            # The server sends tuples in the form of ("Message", data)
            elif dataDecomp[0] == "AuctionWon":
                # If server sends "AuctionWon" message, it will contain Tuple data (Item, finalBidPrice)
                print("Won " + dataDecomp[1][0].GetName() + "\n")
                self.GetWonItem(dataDecomp)
                print("Balance: " + str(self._balance) + "\n")

            elif dataDecomp[0] == "NewRound":
                if self._activeAuction is not None:
                    self._activeAuction = self.GetUpdatedPriceForAuction(dataDecomp)
                else:
                    self.JoinAuction(dataDecomp)
                    auctionChoice = random.choice(list(dataDecomp[1])) # randomly picks an auction to go for
                    self._activeAuction = (auctionChoice, dataDecomp[1][auctionChoice])
                

                self.SendBid(dataDecomp)

    def JoinAuction(self, data):
        if(self._activeAuction is not None):
            return
        else: #it is None, so pull list of auctions
            # iterate over all the auctions and add the ones the client can afford to a separate list.
            auctionsICanAfford = list()

            for key, value in data[1].items():
                if value.GetCurrentBid() <= self._balance:
                    auctionsICanAfford.append(key)

            if len(auctionsICanAfford) == 0:
                self.CloseClient("Cannot afford anymore items. Closing Connection\n")

            auctionChoice = random.choice(auctionsICanAfford)
            self._activeAuction = (auctionChoice, data[1][auctionChoice])
    
    def SendBid(self, data):
        if(self._activeAuction is not None):
            currentBid = self._activeAuction[1].GetCurrentBid()
            if(currentBid == self._clientLastBid or currentBid > self._balance):
                if(currentBid == self._clientLastBid):
                    print("I HAVE HIGHEST BID CURRENTLY\n")
                    self.SendDataToServer(self._activeAuction[0], 0)
                else:
                    print("I CANNOT BID DUE TO LOW BALANCE\n")
                    self.SendDataToServer(self._activeAuction[0], 0)
            elif random.randint(0, 100) > 30:  # RNG 30% chance to bid
                randomBid = random.randint(currentBid, self._balance)
                self._clientLastBid = randomBid
                print("I AM BIDDING " + str(randomBid) + "\n")
                self.SendDataToServer(self._activeAuction[0], randomBid)
            else:
                print("NOT BIDDING\n")
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
        self._activeAuction = None
        self._clientLastBid = None

    def GetUpdatedPriceForAuction(self, data):
        return (self._activeAuction[0], data[1][self._activeAuction[0]])

    def SendDataToServer(self, message, data):
        # helper function that packages data and sends it to a client
        serverACK = "notReceived"
        dataToSend = pickle.dumps((message, data)) # ("NewRound", dict())

        while serverACK == "notReceived":

            try:
                self._server.send(str(len(dataToSend)).encode()) # send the packet size
                receivedSize = self._server.recv(1024).decode()  # wait for server acknowledgement
                
                if receivedSize != "receivedSize":
                    continue

                # print("S received size")
                
                self._server.sendall(dataToSend)
                while serverACK == "notReceived":
                    serverACK = self._server.recv(1024).decode()
            except:
                self.CloseClient("No more items to bid on. Quitting.")
            # print("Client received ACK")
            # print(clientACK)

    def ReceiveDataFromServer(self):
        amountrecv = 0

        try:
            packetsize = int(self._server.recv(1024).decode())

            self._server.sendall("receivedSize".encode())
            # print(packetsize)
            data = b""
            while amountrecv < packetsize:
                # print(amountrecv)

                rec = self._server.recv(1024)    # This listens for data from the server. Program execution is blocked here until data is received
                # print(type(pickle.loads(rec)))
                amountrecv += len(rec)
                data += rec

            # print(amountrecv)

            self._server.sendall("received".encode())
        except:
            self.CloseClient("No more items to bid on. Quitting.")
            return

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
