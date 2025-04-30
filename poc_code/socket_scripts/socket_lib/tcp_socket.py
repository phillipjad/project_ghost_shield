import socket
import selectors
from queue import Queue
from typing import Optional


class TCPSocket:
    def __init__(self) -> None:
        self.sock: Optional[socket.socket] = None
        self.sel: Optional[selectors.DefaultSelector] = None
        self.running = False

    def connect(self, ip: str, port: int) -> None:
        self.disconnect()  # Disconnect first if already connected

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(True)

        try:
            self.sock.connect((ip, port))
        except BlockingIOError:
            pass  # Expected for non-blocking connect

        self.sel = selectors.DefaultSelector()
        self.sel.register(self.sock, selectors.EVENT_READ, self.receive_message)
        self.running = True

    def receive_message(self, sock: socket.socket, queue: Queue) -> None:
        try:
            data = sock.recv(1024)
            if data:
                queue.put(data)
            else:
                queue.put(b"DISCONNECTED")
        except Exception as e:
            queue.put(f"ERROR={e}".encode())

    def send_message(self, msg: bytes) -> None:
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
                events = self.sel.select(timeout=0.5)
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj, queue)
        except Exception as e:
            if self.running:
                print(f"Exception encountered while listening.\n{e}", flush=True)
        finally:
            self.cleanup()

    def disconnect(self) -> None:
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
        self.disconnect()  # Reset if needed
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen()
        self.sock.setblocking(True)  # Accept is blocking
        self.running = False  # Not in listen mode yet

    def accept(self):
        conn, addr = self.sock.accept()
        conn.setblocking(True)
        new_conn = TCPSocket()
        new_conn.sock = conn
        new_conn.sel = selectors.DefaultSelector()
        new_conn.sel.register(new_conn.sock, selectors.EVENT_READ, new_conn.receive_message)
        new_conn.running = True
        return new_conn, addr