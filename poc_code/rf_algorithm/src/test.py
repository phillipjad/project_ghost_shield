from multiprocessing import Process, Queue
from time import sleep
# from queue import Queue

from mc_lib.multicast_client import MulticastClient
from mc_lib.multicast_server import MulticastServer

q = Queue()

def start_listen(q: Queue):
    c = MulticastClient(port=50001)
    c.listen(q)

def start_send():
    s = MulticastServer(port=50001)
    while True:
        s.send_message("HeLLLow multicast".encode())
        sleep(1)


if __name__ == "__main__":
    Process(target=start_listen, args=[q], daemon=True).start()
    Process(target=start_send, daemon=True).start()
    while (item := q.get()):
        print(item)