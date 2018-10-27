# import uuid

# This class is used to track auction data. The server will create instances of this class and send them over the network.

class Auction:
    def __init__(self, newItem):
        self._item = newItem
        self._currentBid = newItem.GetInitialPrice()
        self._currentHighestBidder = None
        self._numberOfRoundsWithoutBid = 0 # this will track how many rounds this auction has had no bids
        self._receivedBidThisRound = False
        # self._id = uuid.uuid4().hex

    def GetItem(self):
        return self._item

    def GetCurrentBid(self):
        return self._currentBid

    def GetCurrentHighestBidder(self):
        return self._currentHighestBidder
    
    def SetNewHighestBid(self, newBidder, newBid):
        # updates the current bid and current highest bidder
        self._currentBid = newBid
        self._currentHighestBidder = newBidder
        self._receivedBidThisRound = True

    def ReceivedNoBids(self):
        if not self._receivedBidThisRound:
            self._numberOfRoundsWithoutBid += 1
        else:
            self._numberOfRoundsWithoutBid = 0
        
        self._receivedBidThisRound = False  # reset this to False so the logic works properly on the next round

    def GetNumberOfRoundsWithoutBid(self):
        return self._numberOfRoundsWithoutBid

    def IsFinished(self):
        # returns true if this auction has gone 3 rounds with no bids and has a current bidder
        return self._currentHighestBidder != None and self._numberOfRoundsWithoutBid >= 3

    def ResetAuction(self):
        # resets all the main stats for the auction. Will be called by server
        self._numberOfRoundsWithoutBid = 0
        self._currentHighestBidder = None
        self._currentBid = self._item.GetInitialPrice()
        self._receivedBidThisRound = False