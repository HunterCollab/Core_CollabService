import socketserver
import threading
import services.realtime.messaging.RMSUtil as RMSUtil
from services.realtime.messaging.RMSClient import RMSClient


class RealtimeServer(object):

    instance = None

    @staticmethod
    def getInstance():  # Bean declaration --> oh wait, fuck you PEP-8.
        if RealtimeServer.instance is None:
            RealtimeServer.instance = RealtimeServer()
        return RealtimeServer.instance

    @staticmethod
    def listener():
        RMSUtil.log("Starting Realtime Messaging Server on PORT 8484 ... ")
        # Listen on 8484 and pass the handle to RMSClient
        server = socketserver.TCPServer(("0.0.0.0", 8484), RMSClient)
        server.serve_forever()

    def __init__(self):
        # Init
        self.clients = {}
        # Start a new thread for the listener
        self.thread = threading.Thread(target=self.listener, args=())
        self.thread.daemon = True
        self.thread.start()

    def addClient(self, username, rmsClient):
        self.clients[username] = rmsClient

    def removeClient(self, username):
        rmsClient = self.clients.pop(username)



