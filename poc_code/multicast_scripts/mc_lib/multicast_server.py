import socket
import selectors
import threading


class MulticastServer:
    def __init__(self, group: str = "239.255.255.250", port: int = 12345, ttl: int = 255):
        self.group: str = group
        self.port: int = port
        self.ttl: int = ttl
        self.lock: threading.Lock = threading.Lock()
        self.sel: selectors.DefaultSelector = selectors.DefaultSelector()

        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.group))
        self.sock.setblocking(False)


    def send_message(self, msg: bytes):
        with self.lock:
            self.sock.sendto(msg, (self.group, self.port))
