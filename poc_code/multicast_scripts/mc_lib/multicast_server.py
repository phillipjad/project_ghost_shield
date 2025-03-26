import socket
import struct
import selectors
import time
import threading


class MulticastServer:
    def __init__(self, group="239.255.255.250", port=12345, ttl=255, interval=1.0, message="Hello World!"):
        self.group = group
        self.port = port
        self.ttl = ttl
        self.interval = interval
        self.message = message
        self.lock = threading.Lock()
        self.sel = selectors.DefaultSelector()
        self.last_sent = 0

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
        self.sock.setblocking(False)

        self.sel.register(self.sock, selectors.EVENT_WRITE, self.send_message)

    def send_message(self, sock):
        now = time.time()
        if now - self.last_sent >= self.interval:
            with self.lock:
                encoded_msg = self.message.encode()
                packed_msg = struct.pack(f"H{len(encoded_msg)}s", len(encoded_msg), encoded_msg)
                sock.sendto(packed_msg, (self.group, self.port))
                print(f"[Server] Sent: {self.message}")
                self.last_sent = now

    def run(self):
        print("[Server] Broadcasting messages...")
        try:
            while True:
                events = self.sel.select(timeout=0.1)
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj)
        except KeyboardInterrupt:
            print("[Server] Stopping...")
        finally:
            self.sel.unregister(self.sock)
            self.sock.close()

if __name__ == "__main__":
    server = MulticastServer()
    server.run()
