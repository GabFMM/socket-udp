from common.constants import *
from common.packet import Packet
from common.myHttp import MyHttp
from common.state import State

from pathlib import Path
import socket
import json
import math
import time
import hashlib

def processACK(sock, packet, clientState, clientAddress, clientsAddress):
    print(f"Received ACK {packet.ack} from ({clientAddress[0]},{clientAddress[1]})")

    # ACK correto
    if packet.ack == clientState.expectedAck:
        if clientState.isProcessingFile:
            readFileAndResponse(sock, clientState, clientAddress, clientState.filePath, packet)
        else:
            clientsAddress.pop(clientAddress)

    # ACK duplicado → IGNORA
    elif packet.ack == (1 - clientState.expectedAck):
        print(f"Ignoring duplicate ACK {packet.ack} from ({clientAddress[0]},{clientAddress[1]})")
    
    # ACK inválido real (raro)
    else:
        print(f"Resent packet DATA to ({clientAddress[0]},{clientAddress[1]}). Detail: invalid ACK")
        sock.sendto(json.dumps(clientState.lastDataPacketSent.to_dict()).encode(), clientAddress)

def processRequest(sock, packet, clientState, clientAddress):
    print(f"Received request {packet.data.endpoint} from ({clientAddress[0]},{clientAddress[1]})")

    if getMapping(packet, PING_ENDPOINT):
        defaultResponse(sock, clientState, clientAddress, packet.seq, True, PING_ENDPOINT, "pong")
    
    elif getMapping(packet, ARCHIVE_TEST_ENDPOINT):
        clientState.filePath = "server/archive-test.txt"
        clientState.isProcessingFile = True
        readFileAndResponse(sock, clientState, clientAddress, clientState.filePath, packet)

    elif getMapping(packet, ARCHIVE_1MB_ENDPOINT):
        clientState.filePath = "server/archive-1mb.txt"
        clientState.isProcessingFile = True
        readFileAndResponse(sock, clientState, clientAddress, clientState.filePath, packet)

    elif getMapping(packet, ARCHIVE_10MB_ENDPOINT):
        clientState.filePath = "server/archive-10mb.txt"
        clientState.isProcessingFile = True
        readFileAndResponse(sock, clientState, clientAddress, clientState.filePath, packet)

    elif getMapping(packet, ARCHIVE_INTEGRAL_ENDPOINT):
        clientState.filePath = f"server/{packet.data.data}"
        generateHashFileAndResponse(sock, clientState, clientAddress, clientState.filePath, packet)
    
    elif getMapping(packet):
        defaultResponse(sock, clientState, clientAddress, packet.seq, True, packet.data.endpoint, "Invalid endpoint")

def isRequest(packet):
    return (
        isinstance(packet, Packet) and
        packet.type == Packet.Type.DATA and
        isinstance(packet.data, MyHttp) and
        packet.data.method != MyHttp.Method.RESPONSE
    )

def isACK(packet):
    return (
        isinstance(packet, Packet) and
        packet.type == Packet.Type.ACK
    )

def processPacket(sock, packet, clientState, clientAddress, clientsAddress):
    if isRequest(packet):
        processRequest(sock, packet, clientState, clientAddress)
    elif isACK(packet):
        processACK(sock, packet, clientState, clientAddress, clientsAddress)

# similar to Spring GetMapping annotation
# if endpoint equals None, so it is a default return
def getMapping(packet, endpoint=None):
    return (
        packet.type == Packet.Type.DATA and
        isinstance(packet.data, MyHttp) and
        packet.data.method == MyHttp.Method.GET and
        (packet.data.endpoint == endpoint or endpoint == None)
    )

# create the response packet and send to client
def defaultResponse(sock, clientState, clientAddress, seq, end, endpoint, data):
    response = MyHttp(
        MyHttp.Method.RESPONSE,
        endpoint,
        data
    )

    dataPacket = Packet(
        seq=seq,
        ack=None,
        end=end,
        type=Packet.Type.DATA,
        data=response
    )

    clientState.lastDataPacketSent = dataPacket
    clientState.lastSendTime = time.time()
    clientState.expectedAck = seq

    sock.sendto(json.dumps(dataPacket.to_dict()).encode(), clientAddress)
    print(f"Sent packet DATA to ({clientAddress[0]},{clientAddress[1]}). SEQ = {seq}")

def readFileAndResponse(sock, clientState, clientAddress, filePath, packet):
    if packet.ack == None: # only in requests / first read
        seq = 0
    else:
        seq = 1 - packet.ack

    path = Path(filePath)

    if not path.is_file():
        defaultResponse(sock, clientState, clientAddress, seq, True, clientState.endpoint, "Archive does not exist")
        return

    with open(filePath, "rb") as f:
        fileSize = Path(filePath).stat().st_size
        numChunks = math.ceil(fileSize / CHUNK_SIZE)

        # Pula direto pro chunk desejado
        # -1, because currentNumChunk begins in 1
        offset = (clientState.currentNumChunk - 1) * CHUNK_SIZE
        f.seek(offset)
        
        chunk = f.read(CHUNK_SIZE)

        isLast = clientState.currentNumChunk >= numChunks
        clientState.isProcessingFile = not isLast

        clientState.currentNumChunk += 1
        defaultResponse(sock, clientState, clientAddress, seq, isLast, clientState.endpoint, chunk)

def generateHashFileAndResponse(sock, clientState, clientAddress, filePath, packet):
    seq = packet.seq

    path = Path(filePath)

    if not path.is_file():
        defaultResponse(sock, clientState, clientAddress, seq, True, clientState.endpoint, "Archive does not exist")
        return
    
    sha256 = hashlib.sha256()

    with open(filePath, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            sha256.update(chunk)

    generatedHash = sha256.hexdigest()

    defaultResponse(sock, clientState, clientAddress, seq, True, clientState.endpoint, generatedHash)

if __name__ == "__main__":
    # AF_NET is a tuple: (host, port)
    # host is the domain name or a IPv4
    # port is a integer number
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    sock.settimeout(TIMEOUT_SERVER)

    clientsAddress = {}

    while True:
        # Tenta receber pacote (não bloqueante infinito)
        try:
            packet, clientAddress = sock.recvfrom(BUFFER_SIZE)

            packet = Packet.from_dict(json.loads(packet.decode()))

            if not packet.isIntegral():
                print(f"Invalid packet from {clientAddress}")
                continue

            if clientAddress not in clientsAddress:
                clientsAddress[clientAddress] = State(packet.data.endpoint)

            processPacket(sock, packet, clientsAddress[clientAddress], clientAddress, clientsAddress)

        except socket.timeout:
            # do nothing
            # only exit the infinite wait of recvfrom
            pass

        now = time.time()

        # Verifica timeout de TODOS os clientes
        for addr, state in clientsAddress.items():
            if state.lastDataPacketSent is None:
                continue

            if now - state.lastSendTime > TIMEOUT_SERVER:
                sock.sendto(json.dumps(state.lastDataPacketSent.to_dict()).encode(), addr)

                state.lastSendTime = now

                print(f"Timeout occured. Resent last packet DATA to ({addr[0]},{addr[1]}). SEQ = {state.lastDataPacketSent.seq}")