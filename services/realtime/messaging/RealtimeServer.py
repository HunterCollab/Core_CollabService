import socketserver
import threading
import time
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
        try:
            self.thread = threading.Thread(target=self.listener, args=())
            self.thread.daemon = True
            self.thread.start()
            time.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            RMSUtil.log("Shutting down RMS Server ... ")

    def addClient(self, username, rmsClient):
        RMSUtil.log("Adding " + username + " to active client list.")
        self.clients[username] = rmsClient

    def removeClient(self, username):
        if username in self.clients: self.clients.pop(username)

    def pingClients(self, users):
        for username in users:
            if username in self.clients: self.clients[username].ping()


def getInstance():  # /r/ilikejava
    return RealtimeServer.getInstance()
