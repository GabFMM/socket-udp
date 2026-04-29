from common.constants import *
from common.packet import Packet
from common.myHttp import MyHttp

from pathlib import Path
import socket
import json
import io
import random
import hashlib
import sys

def verifyArchiveIntegral(filename: str, receivedHash: str):
    sha256 = hashlib.sha256()

    with open(f"client/{filename}", "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            sha256.update(chunk)

    generatedHash = sha256.hexdigest()
    if(generatedHash == receivedHash):
        print("Arquivo transferido com sucesso")
    else:
        print("Arquivo transferido sem sucesso. Necessária retransferência.")

def openFile(endpoint):
    fileObj = None

    def createFile(filePath):
        path = Path(filePath)
        filename = path.stem
        fileExtension = path.suffix

        num = 1
        new_path = path

        while new_path.is_file():
            num += 1
            new_path = path.with_name(f"{filename}({num}){fileExtension}")

        return open(new_path, "ab")

    if endpoint == ARCHIVE_TEST_ENDPOINT:
        fileObj = createFile("client/archive-test.txt")
    elif endpoint == ARCHIVE_1MB_ENDPOINT:
        fileObj = createFile("client/archive-1mb.txt")
    elif endpoint == ARCHIVE_10MB_ENDPOINT:
        fileObj = createFile("client/archive-10mb.txt")
    
    return fileObj
        
def closeFile(file: io.IOBase | None):
    if file == None or file.closed:
        return

    file.close()

def processData(data, file, filename):
    if isinstance(data, MyHttp) and data.method == MyHttp.Method.RESPONSE:
        if data.endpoint == PING_ENDPOINT:
            print(data.data) # expected return: pong
        elif (
            data.endpoint == ARCHIVE_TEST_ENDPOINT or
            data.endpoint == ARCHIVE_1MB_ENDPOINT or
            data.endpoint == ARCHIVE_10MB_ENDPOINT
        ):
            file.write(data.data)
        elif data.endpoint == ARCHIVE_INTEGRAL_ENDPOINT:
            verifyArchiveIntegral(filename, data.data)
        else:
            print(data.data)
    else:
        print(data)

if __name__ == "__main__":
    # AF_NET is a tuple: (host, port)
    # host is the domain name or a IPv4
    # port is a integer number
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    expected_seq = 0

    # send request
    filename = FILENAME
    ack = None
    if(CHOSEN_ENDPOINT == "/archive-integral"):
        if(filename == ""):
            print("Filename not filled")
            sys.exit(1) # error
        else:
            myHttp = MyHttp(MyHttp.Method.GET, CHOSEN_ENDPOINT, filename)
    else:
        myHttp = MyHttp(MyHttp.Method.GET, CHOSEN_ENDPOINT, "")
    request = Packet(
        seq=0,
        ack=None,
        end=False,
        type=Packet.Type.DATA,
        data=myHttp
    )

    serverAddress = (HOST, PORT)
    sock.sendto(json.dumps(request.to_dict()).encode(), serverAddress)
    print(f"Sent request {request.data.endpoint} to ({serverAddress[0]},{serverAddress[1]})")

    file = openFile(request.data.endpoint)

    sock.settimeout(TIMEOUT_CLIENT)
    serverOnline = False # False if server received request, False if not
    while True:
        try:
            data, serverAddress = sock.recvfrom(BUFFER_SIZE)
            packet = Packet.from_dict(json.loads(data.decode()))
            print(f"Received packet DATA from ({serverAddress[0]},{serverAddress[1]})")

            if DEBUG and random.random() <= PACKET_LOSS_RATE:
                print(f"Simulated packet DATA loss from ({serverAddress[0]},{serverAddress[1]})")
                ack = 1 - expected_seq

            elif not packet.isIntegral():
                print(f"Invalid packet DATA from ({serverAddress[0]},{serverAddress[1]}). Detail: checksum CRC32 invalid")
                ack = 1 - expected_seq

            elif packet.seq == expected_seq:
                processData(packet.data, file, filename)

                ack = expected_seq
                expected_seq = 1 - expected_seq

            else:
                # duplicado
                print(f"Duplicated packet DATA from ({serverAddress[0]},{serverAddress[1]})")
                ack = 1 - expected_seq

            # envia ACK
            ack_packet = Packet(
                seq=None,
                ack=ack,
                end=True,
                type=Packet.Type.ACK,
                data=""
            )

            print(f"Sent packet ACK to ({serverAddress[0]},{serverAddress[1]}). ACK = {ack}")
            sock.sendto(json.dumps(ack_packet.to_dict()).encode(), serverAddress)

            if packet.end:
                print(f"Received final packet DATA from ({serverAddress[0]},{serverAddress[1]})")
                break

            serverOnline = True

        except socket.timeout:
            if serverOnline:
                # send last ACK
                ack_packet = Packet(
                    seq=None,
                    ack=ack,
                    end=True,
                    type=Packet.Type.ACK,
                    data=""
                )

                sock.sendto(json.dumps(ack_packet.to_dict()).encode(), serverAddress)
                print(f"Timeout occured. Resent last packet ACK to ({serverAddress[0]},{serverAddress[1]}). ACK = {ack}")
            else:
                # send request again
                sock.sendto(json.dumps(request.to_dict()).encode(), serverAddress)
                print(f"Timeout occured. Resent request to ({serverAddress[0]},{serverAddress[1]})")

    closeFile(file)