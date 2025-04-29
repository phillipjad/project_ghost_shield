# tcp_server.py
import selectors
import socket
import threading


class TCPServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 12345) -> None:
        self.host: str = host
        self.port: int = port
        self.lock: threading.Lock = threading.Lock()
        self.sel: selectors.DefaultSelector = selectors.DefaultSelector()

        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        self.sock.setblocking(False)
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept_connection)

        self.connections: list[socket.socket] = []
        self.running: bool = True

    def accept_connection(self, sock: socket.socket) -> None:
        conn, addr = sock.accept()
        conn.setblocking(False)
        self.connections.append(conn)
        self.sel.register(conn, selectors.EVENT_READ, self.handle_client)
        print(f"Accepted connection from {addr}")

    def handle_client(self, conn: socket.socket) -> None:
        try:
            data = conn.recv(1024)
            if not data:
                self.close_connection(conn)
            else:
                # Echo the data or process it
                print(f"Received from client: {data.decode()}")
        except Exception as e:
            print(f"Error handling client: {e}")
            self.close_connection(conn)

    def send_message(self, msg: bytes) -> None:
        with self.lock:
            for conn in self.connections:
                try:
                    conn.sendall(msg)
                except Exception:
                    self.close_connection(conn)

    def close_connection(self, conn: socket.socket) -> None:
        self.sel.unregister(conn)
        conn.close()
        self.connections.remove(conn)

    def run(self) -> None:
        try:
            while True:
                events = self.sel.select(timeout=None)
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj)
        except Exception as e:
            print(f"Server encountered an error: {e}")
        finally:
            self.sel.close()
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