#Author: Sunil Lal

#This is a simple HTTP server which listens on port 8080, accepts connection request, and processes the client request 
#in sepearte threads. It implements basic service functions (methods) which generate HTTP response to service the HTTP requests. 
#Currently there are 3 service functions; default, welcome and getFile. The process function maps the requet URL pattern to the service function.
#When the requested resource in the URL is empty, the default function is called which currently invokes the welcome function.
#The welcome service function responds with a simple HTTP response: "Welcome to my homepage".
#The getFile service function fetches the requested html or img file and generates an HTTP response containing the file contents and appropriate headers.

#To extend this server's functionality, define your service function(s), and map it to suitable URL pattern in the process function.

#This web server runs on python v3
#Usage: execute this program, open your browser (preferably chrome) and type http://servername:8080
#e.g. if server.py and browser are running on the same machine, then use http://localhost:8080



from socket import *
import _thread
import base64
import json
import http.client
import os

serverSocket = socket(AF_INET, SOCK_STREAM)

serverPort = 8080
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(("", serverPort))

API_KEY = "pk_b8175220ccdb4571a7c028e1941693e8"

serverSocket.listen(5)
print('The server is running')	
# Server should be up and running and listening to the incoming connections

#Extract the given header value from the HTTP request message
def getHeader(message, header):
	if message.find(header) > -1:
		value = message.split(header)[1].split("\r\n")[0]
	else:
		value = None
	return value

def getMethod(message):
	value = message.split()[0]
	return value

def getBody(message):
	lines = message.split("\r\n")
	body="\r\n".join(lines[lines.index(""):])
	return(body)
#service function to fetch the requested file, and send the contents back to the client in a HTTP response.
def getFile(filename):

	try:

		# open and read the file contents. This becomes the body of the HTTP response
		f = open(filename, "rb")
		
		body = f.read()


		header = ("HTTP/1.1 200 OK\r\n\r\n").encode()

	except IOError:

		# Send HTTP response message for resource not found
		header = "HTTP/1.1 404 Not Found\r\n\r\n".encode()
		body = "<html><head></head><body><h1>404 Not Found</h1></body></html>\r\n".encode()

	return header, body

#service function to generate HTTP response with a simple welcome message
def welcome(message):


	header = "HTTP/1.1 200 OK\r\n\r\n".encode()
	body = ("<html><head></head><body><h1>Welcome to my homepage</h1></body></html>\r\n").encode()


	return header, body

def auth(message):
	is_authorized = False
	authen_header = getHeader(message, 'Authorization: ')
	if authen_header == None:
		header = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic\r\n\r\n".encode()
		body = ("<html><head></head><body><h1>Unauthorize</h1></body></html>\r\n").encode()

		return is_authorized, header, body

	encoded_authentication = authen_header.split(' ')[1]

	if (encoded_authentication == None):
		header = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic\r\n\r\n".encode()
		body = ("<html><head></head><body><h1>Unauthorsize</h1></body></html>\r\n").encode()

		return is_authorized, header, body

	decoded_authentication = base64.b64decode(authen_header.split(' ')[1]).decode()
	username, password = decoded_authentication.split(':')
	if username != "20022519" or password != "20022519":
		header = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic\r\n\r\n".encode()
		body = ("<html><head></head><body><h1>Unauthorsize</h1></body></html>\r\n").encode()

		return is_authorized, header, body
	else:
		is_authorized = True

	return is_authorized, None, None

#default service function
def default(message):
	header, body = welcome(message)

	return header, body

def get_portfolio(message):
	accept_value = getHeader(message, "Accept")
	if accept_value is not None and "application/json" in accept_value:
		header = ("HTTP/1.1 200 OK\r\n\r\n").encode()
		with open("portfolio.json", "a+") as f:
			f.seek(0)
			stock = json.loads(f.read())

		symbols = list(stock)
		for symbol in symbols:
			gainLoss = calculateGainLoss(symbol, stock[symbol]['price'])
			stock[symbol]["gainLoss"] = gainLoss
		body = json.dumps(stock).encode()
		return header, body
	else:

		return getFile("./Portfolio.html")

def calculateGainLoss(symbol, price):
	connection = http.client.HTTPSConnection("cloud.iexapis.com")
	connection.request("GET",
					   "/stable/stock/" + symbol + "/quote?token=" + API_KEY)
	response = connection.getresponse()
	response = json.loads(response.read())
	latestPrice = response["latestPrice"]
	connection.close()
	gainLoss = (latestPrice - price) / price * 100
	return gainLoss

def post_portfolio(message):
	req_body = getBody(message)
	req_body = json.loads(req_body)
	with open("portfolio.json", "a+") as f:
		f.seek(0)
		stock = json.loads(f.read())

	stock_symbol = list(req_body)[0]
	# Verify symbol
	connection = http.client.HTTPSConnection("cloud.iexapis.com")
	connection.request("GET", "/stable/ref-data/symbols?token=" + API_KEY + "&filter=symbol,type")
	response = connection.getresponse()
	response = json.loads(response.read())
	try:
		symbol_index = response.index({"symbol": stock_symbol, "type": "cs"})
	except:
		header = ("HTTP/1.1 400 Bad Request\r\n\r\n").encode()
		body = ''.encode()
		return header, body
	connection.close()
	quantity = req_body[stock_symbol]['quantity']
	if not isinstance(quantity, (int, float)):
		header = ("HTTP/1.1 400 Bad Request\r\n\r\n").encode()
		body = ''.encode()
		return header, body
	price = req_body[stock_symbol]['price']
	if not isinstance(price, (int, float)):
		header = ("HTTP/1.1 400 Bad Request\r\n\r\n").encode()
		body = ''.encode()
		return header, body

	old_stock_symbol = stock.get(stock_symbol, None)
	if old_stock_symbol is None:
		if quantity < 0:
			header = ("HTTP/1.1 400 Bad Request\r\n\r\n").encode()
			body = ''.encode()
			return header, body
		else:
			stock[stock_symbol] = {"quantity": 0, "price": 0}

	old_quantity = stock[stock_symbol]['quantity']
	old_price = stock[stock_symbol]['price']
	if quantity + old_quantity < 0:
		header = ("HTTP/1.1 400 Bad Request\r\n\r\n").encode()
		body = ''.encode()
		return header, body
	elif quantity + old_quantity == 0:
		stock.pop(stock_symbol, None)
		body = json.dumps({"quantity": 0, "price": 0}).encode()
	else:
		stock[stock_symbol]['quantity'] += quantity
		stock[stock_symbol]['price'] = (old_price * old_quantity + price * abs(quantity)) / (old_quantity + quantity)
		fullDetails = {"gainLoss": calculateGainLoss(stock_symbol,stock[stock_symbol]['price'])}
		fullDetails.update(stock[stock_symbol])
		body = json.dumps(fullDetails).encode()

	with open("portfolio.json", "w+") as f:
		json.dump(stock, f)

	header = ("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n").encode()
	return header, body

def portfolioReset(message):
	with open("portfolio.json", "w+") as f:
		f.write('{}')
	header = ("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n").encode()
	body = "".encode()
	return header, body

def portfolio(message):
	method = getMethod(message)
	if method == "GET":
		header, body = get_portfolio(message)
	elif method == "POST":
		header, body = post_portfolio(message)

	return header, body

def stock(message):
	return getFile("./stock.html")

#We process client request here. The requested resource in the URL is mapped to a service function which generates the HTTP reponse 
#that is eventually returned to the client. 
def process(connectionSocket) :	
	# Receives the request message from the client
	message = connectionSocket.recv(1024).decode()
	# print(message)

	is_authorized, responseHeader, responseBody = auth(message)

	if is_authorized and len(message) > 1:


		# Extract the path of the requested object from the message
		# Because the extracted path of the HTTP request includes
		# a character '/', we read the path from the second character
		resource = message.split()[1][1:]

		#map requested resource (contained in the URL) to specific function which generates HTTP response 
		if resource == "":
			responseHeader, responseBody = default(message)
		elif resource == "welcome":
			responseHeader,responseBody = welcome(message)
		elif resource == "portfolio":
			responseHeader,responseBody = portfolio(message)
		elif resource == "portfolio/reset":
			responseHeader,responseBody = portfolioReset(message)
		elif resource == "stock":
			responseHeader,responseBody = stock(message)
		else:
			responseHeader,responseBody = getFile(resource)


	# Send the HTTP response header line to the connection socket
	connectionSocket.send(responseHeader)
	# Send the content of the HTTP body (e.g. requested file) to the connection socket
	connectionSocket.send(responseBody)
	# Close the client connection socket
	connectionSocket.close()


#Main web server loop. It simply accepts TCP connections, and get the request processed in seperate threads.
while True:
	
	# Set up a new connection from the client
	connectionSocket, addr = serverSocket.accept()
	#Clients timeout after 60 seconds of inactivity and must reconnect.
	connectionSocket.settimeout(60)
	# start new thread to handle incoming request
	_thread.start_new_thread(process,(connectionSocket,))





