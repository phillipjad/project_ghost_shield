from queue import Queue
import socket
import struct
import selectors


class MulticastClient:
    def __init__(self, group: str = "239.255.255.250", port: int = 12345):
        self.group: str = group
        self.port: int = port
        self.sel: selectors.DefaultSelector = selectors.DefaultSelector()

        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))

        # Join multicast group
        mreq: bytes = struct.pack("4s4s", socket.inet_aton(self.group), socket.inet_aton("0.0.0.0"))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, self.receive_message)

    def receive_message(self, sock: socket.socket, queue: Queue):
        try:
            data, addr = sock.recvfrom(1024)
            queue.put(data)
            print(f"[Client] Received message: {data.decode()} from {addr}")
        except Exception as e:
            print(f"[Client] Error receiving data: {e}")

    def listen(self, queue: Queue):
        print("[Client] Listening for multicast messages...")
        try:
            while True:
                events = self.sel.select(timeout=None)
                if not events:
                    print("[Client] Timeout: no messages received.")
                    continue
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj, queue)
        except KeyboardInterrupt:
            print("[Client] Shutting down...")
        finally:
            self.sel.unregister(self.sock)
            self.sock.close()
