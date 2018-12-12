import socket
import pickle
import sys
sys.path.append("..") # Adds higher directory to python modules path.
import Item
import random
import Auction
import math

class Client:

    def __init__(self, serverIP, newBalance):
        self._balance = newBalance      # the amount of money this client has
        self._activeAuction = None      # this Will be used to determine which auction the client is engaged in. Recommend a Tuple of (GUID, Auction). GUID is passed from the server
        self._server = None             # Server socket the client is connected to
        self._clientLastBid = None      # the last bid the client sent for the current auction
        self._bidCeiling = None         # the highest amount of money the client is willing to spend on the current auction
        
        self._inventory = dict()        # list containing the items this client has won.

        self.ConnectToServer(serverIP)

    def SetBidCeiling(self, startingBid):
        # Sets the maximum amount the client will spend on the current auction.

        multiplier = random.randint(2, 10)

        self._bidCeiling = startingBid * multiplier     # take 2 - 10 times the starting bid of the item

        if self._bidCeiling > self._balance:
            self._bidCeiling = self._balance            # handle the case where the ceilinge exceeds our balance.

    def ConnectToServer(self, serverIP):
        # this function connects the client to the server.
        self._server = socket.socket()
        self._server.settimeout(10)                 # 10 second timeout for the server. If client receives nothing from server after 10 seconds, timeout exception occurs
        self._server.connect((serverIP, 12345))     # connect to localhost on port 12345, which is specified in server file
    
    def ClientLoop(self):
        # This is the main execution loop for the client that's called from main().
        # This loop handles messages sent from the server and runs client behavior accordingly.

        while True:  # Infinite Loop
            dataDecomp = self.ReceiveDataFromServer()   # get a message from the server as a tuple ("message", data)
           
            if dataDecomp[0] == "AuctionsClosed":
                self.CloseClient("No More Items to Bid On. Closing Connection\n")

            if dataDecomp[0] == "AuctionLost":
                print("LOST AUCTION for " + self._activeAuction[1].GetItem().GetName() + "\n")
                self.LeaveAuction()

            if dataDecomp[0] == "AuctionWon":
                # If server sends "AuctionWon" message, it will contain a data tuple (Item, finalBidPrice)
                print("WON " + dataDecomp[1][0].GetName() + "\n")
                self.GetWonItem(dataDecomp)
                print("New Balance: " + str(self._balance) + "\n")

            if dataDecomp[0] == "NewRound":
                # a New bidding round has occurred
                if self._activeAuction is not None:
                    self._activeAuction = self.GetUpdatedPriceForAuction(dataDecomp)
                else:
                    self.JoinAuction(dataDecomp)                

                self.SendBid(dataDecomp)

    def JoinAuction(self, data):
        # This function joins an auction if the client is not already involved in one.

        if(self._activeAuction is not None):
            return
        else: 
            # Client doesn't have an auction, so look at the list of available auctions and choose one.
            auctionsICanAfford = list()
            
            # figure out which auctions client can afford
            for key, value in data[1].items():
                if value.GetCurrentBid() < self._balance:
                    auctionsICanAfford.append(key)

            # if client can't afford any auctions, quit the program.
            if len(auctionsICanAfford) == 0:
                self.CloseClient("Cannot afford anymore items. Closing Connection\n")

            auctionChoice = random.choice(auctionsICanAfford)                       # select a random auction from our list of available auctions.
            self._activeAuction = (auctionChoice, data[1][auctionChoice])           # set the active auction
            print("JOIN AUCTION for " + self._activeAuction[1].GetItem().GetName() + "\n")
            self.SetBidCeiling(self._activeAuction[1].GetItem().GetInitialPrice())  # set a bid ceiling for the new auction
    
    def LeaveAuction(self):
        # Resets auction-specific values back to default upon leaving an auction
        self._activeAuction = None
        self._clientLastBid = None
        self._bidCeiling = None

    def SendBid(self, data):
        # Handles the logic of sending a bid and sends it to the server

        if self._activeAuction is not None:
            currentBid = self._activeAuction[1].GetCurrentBid() # get current highest bid

            if currentBid == self._clientLastBid:  
                # If the current bid on the auction is the same bid we just sent, then we know we have the current highest bid.
                self.SendDataToServer(None, None)   # tell the server we aren't bidding.
            elif currentBid >= self._bidCeiling:
                # if the current bid exceeds our ceiling, leave the auction.
                print("CEILING REACHED. Leaving auction\n")

                self.SendDataToServer(self._activeAuction[0], "LeaveAuction")
                self.LeaveAuction()
            elif random.random() > 0.3:  # RNG 70% chance to bid
                maxBid = currentBid + math.ceil(int(self._bidCeiling * 0.25)) + 1 # only bids up to 25% of the difference between bid ceiling and current bid at a time
                randomBid = random.randint(currentBid + 1, maxBid)

                self._clientLastBid = randomBid

                print("BID $" + str(randomBid) + " on " + self._activeAuction[1].GetItem().GetName() + "\n")

                self.SendDataToServer(self._activeAuction[0], randomBid)    # send our bid to server
            else:
                # if we RNG a 30% chance, then we tell the server we aren't bidding.
                print("NO BID on " + self._activeAuction[1].GetItem().GetName() + "\n")
                self.SendDataToServer(None, None)
        else:
            self.SendDataToServer(None, None)   # if we don't have an active auction, tell the server we aren't bidding.

    def CloseClient(self, closeMessage):
        # Safely closes the client and prints the final inventory out to the console.

        print(closeMessage)
        
        self._server.close()

        print("Final Inventory:\n\tName\tQuantity\n\t----\t--------")

        for key, value in self._inventory.items():
            print("\t" + key + "\t" + str(value))

        exit()

    def GetWonItem(self, dataDecomp):
        # Get the item we won and add it to our inventory. Leave the auction afterwards.

        itemName = dataDecomp[1][0].GetName()

        # add item to dictionary if we don't already have it. Otherwise, increment count.
        if itemName not in self._inventory:
            self._inventory[itemName] = 1
        else:
            self._inventory[itemName] += 1

        self._balance = self._balance -  self._activeAuction[1].GetCurrentBid() # subtract final cost from balance.
        self.LeaveAuction()

    def GetUpdatedPriceForAuction(self, data):
        # Return the new highest bid from the last round of bidding on our active auction
        return (self._activeAuction[0], data[1][self._activeAuction[0]])

    def SendDataToServer(self, message, data):
        # helper function that packages data and sends it to a client
        serverACK = "notReceived"
        dataToSend = pickle.dumps((message, data))  # package the data into a tuple for the server.

        while serverACK == "notReceived":
            # while the server hasn't received all our data, continue to send it
            try:
                self._server.send(str(len(dataToSend)).encode())    # send the packet size
                receivedSize = self._server.recv(4096).decode()     # wait for server acknowledgement
                
                if receivedSize != "receivedSize":
                    continue
                
                self._server.sendall(dataToSend)                    # server received the data size, now send the data
                while serverACK == "notReceived":
                    # wait for acknowledgement from server that it got the package
                    serverACK = self._server.recv(4096).decode()
            except:
                self.CloseClient("No more items to bid on. Quitting.")

    def ReceiveDataFromServer(self):
        amountrecv = 0  # will track how much of the data we have received from the server

        try:
            packetsize = int(self._server.recv(4096).decode())  # get the packet size from the server so we know how much to expect

            self._server.sendall("receivedSize".encode())       # tell the server we got the packet size

            data = b""  # will store our data into this bit string

            while amountrecv < packetsize:
                # as long as we haven't received the whole packet, we will loop

                rec = self._server.recv(4096)    # This listens for data from the server. Program execution is blocked here until data is received

                amountrecv += len(rec)  # add to the amount of data we've received
                data += rec             # concatenate the new data received with the data we've received up to this point.

            self._server.sendall("received".encode())   # send ACK to server
        except:
            self.CloseClient("Connection Error. Quitting.")

        return pickle.loads(data)       # return decoded data

def main():
    # Called on when program is run from terminal

    if len(sys.argv) < 3:
        # ensure proper compilation from command line
        print("Error: Please put in an IP address for the server and a starting balance for the client. E.G: python Client.py 192.168.1.1 500")
        exit()
    
    # create the new client
    thisClient = Client(sys.argv[1], int(sys.argv[2]))
    thisClient.ClientLoop()     # start the client loop
    
if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
    main()
