import socket
import struct
import selectors


class MulticastClient:
    def __init__(self, group="239.255.255.250", port=12345, timeout=5.0):
        self.group = group
        self.port = port
        self.timeout = timeout
        self.sel = selectors.DefaultSelector()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))

        # Join multicast group
        mreq = struct.pack("4s4s", socket.inet_aton(self.group), socket.inet_aton("0.0.0.0"))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, self.receive_message)

    def receive_message(self, sock):
        try:
            print("RECEIVING")
            data, addr = sock.recvfrom(1024)
            print(f"[Client] Received message: {data.decode()} from {addr}")
        except Exception as e:
            print(f"[Client] Error receiving data: {e}")

    def run(self):
        print("[Client] Listening for multicast messages...")
        try:
            while True:
                events = self.sel.select(timeout=self.timeout)
                if not events:
                    print("[Client] Timeout: no messages received.")
                    continue
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj)
        except KeyboardInterrupt:
            print("[Client] Shutting down...")
        finally:
            self.sel.unregister(self.sock)
            self.sock.close()


if __name__ == "__main__":
    client = MulticastClient()
    client.run()
