import struct   # String <==> Binary


def writeUTF(sock, msg):
    _bytes = bytes(msg, 'utf-8')
    rawWrite(sock, _bytes)


def readUTF(sock):
    raw = rawRead(sock)
    if raw is None: return None
    return str(raw, 'utf-8')


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
