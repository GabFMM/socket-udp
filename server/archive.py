import random
import string

def createRandomTXT(name, byteSize):
    chars = string.ascii_letters + string.digits
    
    with open(name, "w") as f:
        for _ in range(byteSize):
            f.write(random.choice(chars))

def createTestTXT():
    with open("archive-test.txt", "w") as f:
        f.write("Test\nALPHA\nLOrem is si merOL")

if __name__ == "__main__":
    createTestTXT()
    createRandomTXT("archive-1mb.txt", 1_000_000)
    createRandomTXT("archive-10mb.txt", 10_000_000)