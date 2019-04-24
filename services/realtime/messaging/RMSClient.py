import socketserver
import services.realtime.messaging.RMSUtil as RMSUtil
import services.realtime.messaging.RMSProtocol as RMSProtocol


class RMSClient(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.socket = None

    def handle(self):
        self.socket = self.request
        RMSUtil.log("New Session - " + self.client_address[0])
        # The first message is the JWT token.
        token = self.readNextMessage()
        RMSUtil.log("Token Received: " + token)
        # just send back the same data, but upper-cased
        self.writeMessage(token.upper())

    def readNextMessage(self):
        return RMSProtocol.readUTF(self.socket)

    def writeMessage(self, msg):
        return RMSProtocol.writeUTF(self.socket, msg)


