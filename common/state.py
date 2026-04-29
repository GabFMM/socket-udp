import time

class State:
    def __init__(self, endpoint):
        # default
        self.expectedAck = None
        self.lastDataPacketSent = None
        self.lastSendTime = None
        self.endpoint = endpoint

        # for archive process
        self.isProcessingFile = False
        self.filePath = ""
        self.currentNumChunk = 1
