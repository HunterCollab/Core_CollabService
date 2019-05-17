import socketserver
import services.realtime.messaging.RMSUtil as RMSUtil
import services.realtime.messaging.RMSProtocol as RMSProtocol
import services.realtime.messaging.RealtimeServer as RealtimeServer
import security.JWT


class RMSClient(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.socket = None
        self.addr = None
        self.username = None
        super().__init__(request, client_address, server)

    def handle(self):
        try:
            self.socket = self.request # First get the reference to the socket.
            self.addr = self.client_address[0] #Get the address

            self.log("New Session") #Log
            # The first message is the JWT token. Read it
            token = self.readNextMessage()
            if token is None:
                self.log("Session Ended PRE_HANDSHAKE")
                return

            self.log("Token Received: " + token)

            username = security.JWT.decode_auth_token(token) #Decode the auth token
            if username.startswith('SUCCESS'): #On success
                self.username = username[7:]
                RealtimeServer.getInstance().addClient(self.username, self)
                self.writeMessage("AUTH_SUCCESS")
                self.log("Handshake Successful")
                msg = self.readNextMessage()
                while (msg):
                    if not msg == "DONE":
                        msg = self.readNextMessage()
            else: #Decoding failed
                self.writeMessage("AUTH_FAIL")
                self.log("Invalid Auth - Closing Session")
                return

            # just send back the same data, but upper-cased
            self.writeMessage(token.upper())
        except Exception as e:
            self.log(e)
            self.log("EXCEPTION @ RMSClient.handle")

    def readNextMessage(self):
        return RMSProtocol.readUTF(self.socket)

    def writeMessage(self, msg):
        RMSProtocol.writeUTF(self.socket, msg)

    def ping(self): #Send "PING" across the socket
        self.log("Pinged")
        self.writeMessage("PING")

    def log(self, msg):
        if self.username is None:
            RMSUtil.logAddr(self.addr, msg)
        else:
            RMSUtil.logAddr(self.username, msg)

    def finish(self):
        RealtimeServer.getInstance().removeClient(self.username)
        self.log("FINISH Called - Session Purged")

