# socket
HOST = "localhost"
PORT = 5000
BUFFER_SIZE = 2048
TIMEOUT_CLIENT = 0.50 # 500 ms
TIMEOUT_SERVER = 0.125 # 125 ms

# endpoints
PING_ENDPOINT = "/ping"
ARCHIVE_TEST_ENDPOINT = "/archive-test.txt"
ARCHIVE_1MB_ENDPOINT = "/archive-1mb.txt"
ARCHIVE_10MB_ENDPOINT = "/archive-10mb.txt"
ARCHIVE_INTEGRAL_ENDPOINT = "/archive-integral"
FILENAME = "archive-10mb.txt" # sent to server to verify archive integral
CHOSEN_ENDPOINT = ARCHIVE_INTEGRAL_ENDPOINT # only for client

# how much the file will be read per packet
CHUNK_SIZE = 1000

# debug client
DEBUG = False
PACKET_LOSS_RATE = 0.2