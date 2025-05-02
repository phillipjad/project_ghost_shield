import socket
import selectors
from queue import Queue
from typing import Optional
from threading import Lock


class TCPSocket:
    def __init__(self) -> None:
        self.sock: Optional[socket.socket] = None
        self.sel: Optional[selectors.DefaultSelector] = None
        self.running = False
        self.lock = Lock()

    def connect(self, ip: str, port: int) -> None:
        if self.sock:
            self.disconnect()  # Disconnect first if already connected
        with self.lock:

            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setblocking(True)

            self.sock.connect((ip, port))

            self.sel = selectors.DefaultSelector()
            self.sel.register(self.sock, selectors.EVENT_READ, self.receive_message)
            self.running = True

    def receive_message(self, sock: socket.socket, queue: Queue) -> None:
        try:
            data = sock.recv(1024)
            if data:
                queue.put(data)
        except Exception as e:
            queue.put(f"ERROR={e}".encode())

    def send_message(self, msg: bytes) -> None:
        with self.lock:
            if self.sock:
                try:
                    self.sock.sendall(msg)
                except Exception as e:
                    print(f"Error sending message: {e}")

    def listen(self, queue: Queue) -> None:
        if not self.sel:
            print("No active connection to listen on.")
            return

        try:
            while self.running:
                events = self.sel.select(timeout=None)
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj, queue)
        except Exception as e:
            if self.running:
                print(f"Exception encountered while listening.\n{e}", flush=True)
        finally:
            self.cleanup()

    def disconnect(self) -> None:
        with self.lock:
            self.running = False
            if self.sel and self.sock:
                try:
                    self.sel.unregister(self.sock)
                except Exception:
                    pass
                self.sel.close()
                self.sel = None
            if self.sock:
                self.sock.close()
                self.sock = None

    def cleanup(self) -> None:
        with self.lock:
            if self.sel and self.sock:
                try:
                    self.sel.unregister(self.sock)
                except Exception:
                    pass
                self.sel.close()
                self.sock.close()
                self.sel = None
                self.sock = None

    def bind_and_listen(self, ip: str, port: int):
        if self.sock:
            self.disconnect()
        with self.lock:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setblocking(True)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((ip, port))
            self.sock.listen()
            self.running = False

    def accept(self):
        with self.lock:
            conn, addr = self.sock.accept()
            conn.setblocking(True)
            new_conn = TCPSocket()
            new_conn.sock = conn
            new_conn.sel = selectors.DefaultSelector()
            new_conn.sel.register(new_conn.sock, selectors.EVENT_READ, new_conn.receive_message)
            new_conn.running = True
            return new_conn, addr