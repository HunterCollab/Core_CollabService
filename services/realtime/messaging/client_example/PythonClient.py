import socket
import requests
import struct


def writeUTF(sock, str):
    _bytes = bytes(str, 'utf-8')
    rawWrite(sock, _bytes)


def readUTF(sock):
    return str(rawRead(sock), 'utf-8')


def rawWrite(sock, message):
    # First 4 bytes = Length of message = Big Endian Unsigned Int
    # Packet = Length of message + the actual message
    packet = struct.pack('>I', len(message)) + message
    sock.sendall(packet)


def rawRead(sock):
    # Read the first 4 bytes = Length of message
    rawLength = readN(sock, 4)
    if not rawLength:
        return None
    # Convert from Big Endian Unsigned Int back to integer.
    length = struct.unpack('>I', rawLength)[0]
    # Read and return
    return readN(sock, length)


def readN(sock, n):
    # Reads 'n' bytes or until EOF.
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def connect(token):
    HOST, PORT = "localhost", 8484

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        writeUTF(sock, token)
        msg = readUTF(sock)
        if not msg == "AUTH_SUCCESS":
            return

        msg = readUTF(sock)
        while msg:
            if msg == "PING":
                print("Ping received.")
                msg = readUTF(sock)
            else:
                msg = False
    finally:
        sock.close()


if __name__ == "__main__":
    r = requests.get("https://huntercollabapi.herokuapp.com/auth/login?username=testuser1@myhunter.cuny.edu&password=password")
    token = r.json()['token']
    print(token)
    connect(token)

