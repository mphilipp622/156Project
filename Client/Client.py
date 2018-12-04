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
        self._inventory = list()        # list containing the items this client has won. Can use Item.AddUnit() to increase the number of units of the item
        self._server = None             # Server socket the client is connected to
        self.ConnectToServer(serverIP)

    def ConnectToServer(self, serverIP):
        # this function should connect the client to the server.
        self._server = socket.socket()
        self._server.connect((serverIP, 12345))   # connect to localhost on port 12345, which is specified in server file
    def ClientLoop(self):
        # This is the main execution loop for the client that's called from main(). Some example code is shown below.
        # The loop should run a series of Functions that are defined in this class. Recommend having a look at Server.ServerLoop() for an example

        while True:                           # Infinite Loop
            data = self.ReceiveDataFromServer()

            dataDecomp = pickle.loads(data)   # This decompresses the data sent from the server. This allows us to get a Tuple object from the server.
            #return
            print(dataDecomp[0])

            # The server sends tuples in the form of ("Message", data)
            if dataDecomp[0] == "AuctionWon":
                # If server sends "AuctionWon" message, it will contain Tuple data (Item, finalBidPrice)
                print("Won " + dataDecomp[1][0].GetName())

            elif dataDecomp[0] == "NewRound":
                # If server sends "NewRound" message, it will contain a dictionary of auction items
                # The dictionary has keys of GUID strings with values of Auction type.
                # You'll probably want to keep track of the client's active auction's GUID.
                auctionChoice = random.choice(list(dataDecomp[1])) # randomly picks an auction to go for
                # dataToSend = pickle.dumps((auctionChoice, 3999))   # sends a bid to the auction for $3999
                self.SendDataToServer(auctionChoice, 3999)                      # sends the bid to the server. Server handles the rest

    def JoinAuction(self):
        # This function should first check if this client has an active auction or not.
        # If we don't have an active auction, then we want to receive the list of auctions from the server and let the client pick one
        # The server sends a list of auctions in this format:
            # ("NewRound", auctionDictionary)
            # auctionDictionary has GUID strings as a key and Auction class objects as types.
            # You'll want to save the GUID of the auction that the client chooses. You'll need it to send a bid to the server.
        
        return
    
    def SendBid(self):
        # If this client has an active auction, it should send a new bid for that auction to the server.
        # Client should NOT be able to bid if the amount they are looking to spend is larger than their current balance
        # Client should send None if it is not bidding on an item
        # According to Ming Li, the client has a 30% chance of NOT bidding
        # Client should send a tuple (auctionGUID, bidAmount)

        return

    def GetWonItem(self):
        # this function should listen for the server to send an item to this client upon winning a bid.
        # The item will be sent as an (Item, finalBidPrice) tuple
        # The client should add the new item to the inventory list and subtract the cost from their current balance
        return

    def SendDataToServer(self, message, data):
        # helper function that packages data and sends it to a client
        serverACK = "notReceived"
        dataToSend = pickle.dumps((message, data)) # ("NewRound", dict())

        while serverACK == "notReceived":

            self._server.send(str(len(dataToSend)).encode()) # send the packet size
            receivedSize = self._server.recv(1024).decode()  # wait for server acknowledgement
            
            if receivedSize != "receivedSize":
                continue

            # print("S received size")
            
            self._server.sendall(dataToSend)
            while serverACK == "notReceived":
                serverACK = self._server.recv(1024).decode()
            # print("Client received ACK")
            # print(clientACK)

    def ReceiveDataFromServer(self):
        amountrecv = 0
        packetsize = int(self._server.recv(1024).decode())

        self._server.sendall("receivedSize".encode())
        print(packetsize)
        data = b""
        while amountrecv < packetsize:
            print(amountrecv)

            rec = self._server.recv(1024)    # This listens for data from the server. Program execution is blocked here until data is received
            # print(type(pickle.loads(rec)))
            amountrecv += len(rec)
            data += rec

        print(amountrecv)

        self._server.sendall("received".encode())
        return data

def main():
    # implement main client execution here. I imagine this is for a single client.
    # We can do multiple clients by opening multiple consoles and running python Client.py
    # could also put Client.py, Item.py, and Auction.py on another computer and run Client.py. That should work on a LAN.
    if len(sys.argv) < 2:
        print("Error: Please put in an IP address for the server. E.G: python Client.py 192.168.1.1")
        exit()
    
    testClient = Client(sys.argv[1], 150)    # client has $150 balance
    testClient.ClientLoop()
    
if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
    main()
