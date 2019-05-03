import socketserver
import services.realtime.messaging.RMSUtil as RMSUtil
import services.realtime.messaging.RMSProtocol as RMSProtocol
import services.realtime.messaging.RealtimeServer as RealtimeServer
from security.JWT import decode_auth_token


class RMSClient(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        self.socket = None
        self.addr = None
        self.username = None
        super().__init__(request, client_address, server)

    def handle(self):
        try:
            self.socket = self.request
            self.addr = self.client_address[0]

            self.log("New Session")
            # The first message is the JWT token.
            token = self.readNextMessage()
            if token is None:
                self.log("Session Ended PRE_HANDSHAKE")
                return

            self.log("Token Received: " + token)

            username = decode_auth_token(token)
            if username.startswith('SUCCESS'):
                self.username = username[7:]
                RealtimeServer.getInstance().addClient(self.username, self)
                self.writeMessage("AUTH_SUCCESS")
                self.log("Handshake Successful")
                msg = self.readNextMessage()
                while (msg):
                    if not msg == "DONE":
                        msg = self.readNextMessage()
            else:
                self.writeMessage("AUTH_FAIL")
                self.log("Invalid Auth - Closing Session")
                return

            # just send back the same data, but upper-cased
            self.writeMessage(token.upper())
        except Exception as e:
            print(e)
            self.log("EXCEPTION @ RMSClient.handle")

    def readNextMessage(self):
        return RMSProtocol.readUTF(self.socket)

    def writeMessage(self, msg):
        RMSProtocol.writeUTF(self.socket, msg)

    def ping(self):
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

