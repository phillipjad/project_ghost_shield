from multiprocessing import Process, Queue
from time import sleep
# from queue import Queue

from mc_lib.multicast_client import MulticastClient
from mc_lib.multicast_server import MulticastServer

c = MulticastClient(port=50000)
# s = MulticastServer(port=50001)
q = Queue()

if __name__ == "__main__":
    Process(target=c.listen, args=[q], daemon=True).start()
    # while True:
    #     s.send_message("HeLLLow multicast".encode())
    #     sleep(1)