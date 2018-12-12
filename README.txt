CSCI 156 Auction Project

-----------------------
Group Members
-----------------------
Mark Philipp
Joseph Sesate
Andrew Valenzuela

-----------------------
Prerequisites
-----------------------
Python 3.6 or higher must be installed
Python _socket library must be installed. This should come by default with Python 3.6

-----------------------
How to Run the Server
-----------------------
open a terminal that has python capabilities and navigate to the project directory and open the "Server" directory.

Run the following:
python Server.py input.txt

This will start the server and start auctions for all the items listed in the input.txt file.

-----------------------
How to Run the Client
-----------------------
Open a terminal that has python capabilities and navigate to the project directory and open the "Client" directory.

Run the following:
python Client.py <ipaddress> <startingBalance>

<ipaddress> is the IP address of the machine running the Server.py file. If you want to run on the localhost, put 127.0.0.1
<startingBalance> is the amount of money the client starts with. This is how much money the client has to bid on items with.

Example compilation:
python Client.py 192.168.1.10 2500

this will create a new client that connects to the server at 192.168.1.10 with $2500 to spend.

-----------------------
Quitting client or server
-----------------------
For some reason, the program only exits using CTRL + pause/break. CTRL + C will not work.

The client will quit under the following conditions:
	- The connection to server was lost or timed out
	- The client is out of money
	- There are no more items the client can afford to bid on
	- The server closed the auction house
	- Keyboard interrupt
	- Runtime failure for any other reason
	
The server will quit under the following conditions:
	- Some kind of runtime failure occurs
	- There are no more items to put to auction

---------------------------------------
Client Highest Acceptable Prices
---------------------------------------
Each client creates a highest acceptable bid per auction in real-time. The amount they choose is based upon their remaining balance, the starting bid of the tiem, and a random number generator. This means that each auction a client joins, the amount they're willing to spend might change.

This function is defined in Client.py line 22. The function is called SetBidCeiling(self, startingBid)

---------------------------------------
Server Implementation
---------------------------------------
The server accepts connections on a separate thread from the main server loop. However, the server does not use multithreading for sending and receiving data to and from clients. Instead, it uses polling, which is inefficient. We ran out of time to implement multithreading, unfortunately.