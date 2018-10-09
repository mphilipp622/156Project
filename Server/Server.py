import socket
import sys
sys.path.append("..") # Adds higher directory to python modules path.

import Item as itemPackage

class Server:

    def __init__(self, inputFile, newIP, newPort):
        self._ipAddress = newIP
        self._portNumber = newPort
        self._currentItem = None # current item being auctioned
        self._currentHighestBidder = "" # IP address of the current highest bidder
        self._isAuctionActive = False # sets true if an auction is active
        self._items = dict() # hashtable of (Item, currentHighestBid) KV pairs
        self._connections = dict() # hashtable of (connection, ipaddress) KV pairs
        self.PopulateItems(inputFile)
        self.StartServerListener()
    
    def StartServerListener(self):
        self._serverSocket = socket.socket()
        self._serverSocket.bind((self._ipAddress, self._portNumber))
        print "Socket Created"

    def StartNewAuction(self):
        # This function should randomize a new item to auction and broadcast the new item to all connected clients
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
        return

    
def main():
    # Server Execution Goes Here
    return

if __name__ == "__main__":
    # call main when this program is run. This if statement ensures this code is not run if imported as a module
    main()