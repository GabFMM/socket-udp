from enum import Enum
import base64

class MyHttp:
    def __init__(self, method, endpoint, data):
        self.method = method
        self.endpoint = endpoint
        self.data = data

    def to_dict(self):
        if isinstance(self.data, bytes):
            data = base64.b64encode(self.data).decode()
            dataType = "bytes"
        else:
            data = self.data
            dataType = "string"

        return {
            "method": self.method.value,
            "endpoint": self.endpoint,
            "dataType": dataType,
            "data": data
        }

    @staticmethod
    def from_dict(d):
        # breakpoint()
        if d["dataType"] == "bytes":
            data = base64.b64decode(d["data"])
        elif d["dataType"] == "string":
            data = d["data"]
        else:
            dataType = d["dataType"]
            raise ValueError(f"Unknown data type: {dataType}")

        return MyHttp (
            MyHttp.Method(d["method"]),
            d["endpoint"],
            data
        )

    class Method(Enum):
        RESPONSE = "RESPONSE"
        GET = "GET"
    