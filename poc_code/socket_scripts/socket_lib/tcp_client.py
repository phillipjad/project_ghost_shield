# tcp_client.py
import socket
import selectors
from queue import Queue
from collections.abc import Callable


class TCPClient:
    def __init__(self, server_ip: str = "127.0.0.1", server_port: int = 12345) -> None:
        self.server_ip: str = server_ip
        self.server_port: int = server_port
        self.sel: selectors.DefaultSelector = selectors.DefaultSelector()

        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(False)

        try:
            self.sock.connect((self.server_ip, self.server_port))
        except BlockingIOError:
            pass  # Expected for non-blocking connect

        self.sel.register(self.sock, selectors.EVENT_READ, self.receive_message)
        self.running: bool = True

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
        try:
            self.sock.sendall(msg)
        except Exception as e:
            print(f"Error sending message: {e}")

    def listen(self, queue: Queue) -> None:
        try:
            while self.running:
                events = self.sel.select(timeout=None)
                if not events:
                    continue
                for key, _ in events:
                    callback: Callable[[socket.socket, Queue], None] = key.data
                    callback(key.fileobj, queue)
        except Exception as e:
            print(f"Exception encountered while listening.\n{e}", flush=True)
        finally:
            self.sel.unregister(self.sock)
            self.sock.close()

    def shutdown(self) -> None:
        self.running = False
        try:
            dummy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            dummy.connect((self.host, self.port))
            dummy.close()
        except Exception:
            pass
    
    def cleanup(self) -> None:
        try:
            self.sel.unregister(self.sock)
        except Exception:
            pass
        self.sock.close()
        self.sel.close()