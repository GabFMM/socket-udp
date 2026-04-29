from common.myHttp import MyHttp
from enum import Enum
import zlib
import json

class Packet:
    def __init__(self, seq, ack, end, type, data):
        self.seq = seq # 0 or 1
        self.ack = ack # 0 or 1
        self.end = end # False or True (indicates if the archive ended)
        self.type = type
        self.data = data
        self.crc32 = self.calculateCRC32()

    def calculateCRC32(self):
        if isinstance(self.data, MyHttp):
            data = self.data.to_dict()
        else:
            data = self.data

        dic = {
            "seq": self.seq,
            "ack": self.ack,
            "end": self.end,
            "type": self.type.value,
            "data": data
        }

        return zlib.crc32(
            json.dumps(dic, sort_keys=True).encode()
        )
    
    def isIntegral(self):
        return self.calculateCRC32() == self.crc32

    def to_dict(self):   
        if isinstance(self.data, MyHttp):
            data = self.data.to_dict()
            data_type = "myhttp"
        else:
            data = self.data
            data_type = "raw"

        return {
            "seq": self.seq,
            "ack": self.ack,
            "end": self.end,
            "type": self.type.value,
            "data": data,
            "data_type": data_type,
            "crc32": self.crc32
        }
    
    @staticmethod
    def from_dict(d):
        data_type = d.get("data_type")

        if data_type == "myhttp":
            data = MyHttp.from_dict(d["data"])
        else:
            data = d["data"]

        packet = Packet(
            d["seq"],
            d["ack"],
            d["end"],
            Packet.Type(d["type"]),
            data
        )

        packet.crc32 = d["crc32"]  # importante: não recalcular aqui
        return packet

    class Type(Enum):
        ACK = "ACK"   # packet is a confirmation
        DATA = "DATA" # packet is a request or contains data