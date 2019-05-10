import socketserver
import threading
import time
import services.realtime.messaging.RMSUtil as RMSUtil
from services.realtime.messaging.RMSClient import RMSClient


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class RealtimeServer(object):

    instance = None

    @staticmethod
    def getInstance():  # Bean declaration --> oh wait, fuck you PEP-8.
        if RealtimeServer.instance is None:
            RealtimeServer.instance = RealtimeServer()
        return RealtimeServer.instance

    def __init__(self):
        # Init
        self.clients = {}
        self.server = None
        # Start a new thread for the listener
        try:
            RMSUtil.log("Starting Realtime Messaging Server on PORT 8484 ... ")
            self.server = ThreadedTCPServer(("0.0.0.0", 8484), RMSClient)
            server_thread = threading.Thread(target=self.server.serve_forever)
            # Exit the server thread when the main thread terminates
            server_thread.daemon = True
            server_thread.start()
        except (KeyboardInterrupt, SystemExit):
            self.server.shutdown(1)
            self.server.close()
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
